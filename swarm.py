"""Swarm: many hidden-target walkers on one frozen map, laying trails.

One walker at a time (so "many walkers" means many over time, as in an ant colony where
each ant leaves pheromone for the next). Every walker is the ordinary Sweep head in
hidden mode with a horizon: it gets one warmth number per read and can see only the
anchor's N nearest words. When it arrives, its anchor path (with loops cut out) is laid
down as a trail: +1 on each edge, both ways. Trails evaporate a little after every walker.

A later walker standing on a word also reads the k strongest trails out of it, once on
arrival, at the cost of one read each. A trail can lead past the horizon.

Then fresh pairs, each run four ways with the same seed:
  none      no trails
  roads     the trails the swarm laid
  relabel   the same trail graph with its words shuffled (same shape, wrong places)
  random    the same number of edges between random words, same weights
  hub_jumps at every anchor, k trail words drawn afresh (where the swarm went, no edges)
  any_jumps at every anchor, k words of the whole map drawn afresh
The controls are what roads must beat: more reads per anchor, a graph of that size, or
just jumping somewhere.

The door census is the words that most often lie inside arrived paths.

Explore mode: descriptive numbers, no gates.

    python swarm.py --bank ../SweepSol/bank.json
"""
import argparse
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from sweep import Bank, Sweep


# ---------------------------------------------------------------- trails
class Trails:
    def __init__(self, evap=0.002, k=6):
        self.w = defaultdict(dict)      # stored as raw / scale, so evaporation is one multiply
        self.scale = 1.0
        self.evap, self.k = evap, k
        self._top = {}

    def deposit(self, path, amount=1.0):
        for a, b in zip(path[:-1], path[1:]):
            if a == b:
                continue
            for i, j in ((a, b), (b, a)):
                self.w[i][j] = self.w[i].get(j, 0.0) + amount / self.scale
                self._top.pop(i, None)

    def evaporate(self):
        self.scale *= (1.0 - self.evap)
        if self.scale < 1e-6:           # renormalise before it underflows
            for i in self.w:
                for j in self.w[i]:
                    self.w[i][j] *= self.scale
            self.scale = 1.0

    def __call__(self, a):
        if a not in self._top:
            nb = self.w.get(a)
            self._top[a] = [] if not nb else sorted(nb, key=nb.get, reverse=True)[:self.k]
        return self._top[a]

    def edges(self):
        out = []
        for i, nb in self.w.items():
            for j, v in nb.items():
                if i < j:
                    out.append((i, j, v * self.scale))
        return out

    @classmethod
    def from_edges(cls, edges, k):
        t = cls(evap=0.0, k=k)
        for i, j, v in edges:
            if i == j:
                continue
            t.w[i][j] = t.w[i].get(j, 0.0) + v
            t.w[j][i] = t.w[j].get(i, 0.0) + v
        return t


class Jumps:
    """k words drawn afresh at every anchor from a fixed list (no edges, no learned structure)."""
    def __init__(self, words, k, seed=0):
        self.words, self.k = np.asarray(words), k
        self.rng = np.random.default_rng(seed)
        self._cache = {}

    def __call__(self, a):
        if a not in self._cache:
            self._cache[a] = [int(x) for x in self.rng.choice(self.words, self.k, replace=False)]
        return self._cache[a]


def loop_erase(path):
    out, pos = [], {}
    for a in path:
        if a in pos:
            cut = pos[a]
            for b in out[cut + 1:]:
                pos.pop(b, None)
            out = out[:cut + 1]
        else:
            pos[a] = len(out)
            out.append(a)
    return out


# ---------------------------------------------------------------- one walker
def walk(bank, s, g, roads, beats, horizon, seed):
    sw = Sweep(bank, bank.words[s], mode="hidden", target=bank.words[g],
               horizon=horizon, roads=roads, seed=seed)
    sw.run(beats)
    arrived = sw.a == sw.g
    road_commits = 0
    for rec in sw.log:
        if road_set(sw, rec):
            road_commits += 1
    return {"start": bank.words[s], "target": bank.words[g], "arrived": bool(arrived),
            "reads": sw.reads_total, "road_reads": sw.road_reads, "beats": len(sw.log),
            "first_seen": sw.found_at, "path": [int(a) for a in sw.anchors],
            "road_commits": road_commits}


def road_set(sw, rec):
    """Words a commit could have taken only by trail: not read by the sweep in the last two beats."""
    if "commit" not in rec or sw.roads is None:
        return set()
    b = rec["beat"]
    seen = set()
    for r in sw.log[max(0, b - 1):b + 1]:
        seen.update(r["reads"])
    roads = set()
    for r in sw.log[:b + 1]:
        roads.update(r.get("road", []))
    return {rec["commit"]} if rec["commit"] in roads and rec["commit"] not in seen else set()


def make_pairs(bank, pool, n, rng, banned_pairs=(), banned_words=(), far=50, targets=None):
    out, seen = [], set(banned_pairs)
    banned_words = set(banned_words)
    cand = [i for i in pool if i not in banned_words]
    tries = 0
    while len(out) < n and tries < n * 50:
        tries += 1
        s, g = (int(x) for x in rng.choice(cand, 2, replace=False))
        if targets is not None:
            g = int(rng.choice(targets))
            if g == s:
                continue
        if (s, g) in seen or (g, s) in seen:
            continue
        if g in set(bank.neighbours(s, far).tolist()):   # not a neighbour: there must be a route to find
            continue
        seen.add((s, g))
        out.append((s, g))
    return out


# ---------------------------------------------------------------- report helpers
def summarise(rows, budget_reads):
    n = len(rows)
    arr = [r for r in rows if r["arrived"]]
    cost = [r["reads"] if r["arrived"] else max(r["reads"], budget_reads) for r in rows]
    return {"n": n, "arrived": len(arr), "rate": len(arr) / max(n, 1),
            "median_reads_arrived": float(np.median([r["reads"] for r in arr])) if arr else None,
            "mean_cost": float(np.mean(cost)),
            "mean_moves_arrived": float(np.mean([len(r["path"]) - 1 for r in arr])) if arr else None,
            "road_commits": int(sum(r["road_commits"] for r in rows))}


def paired(a, b):
    """a and b: rows for the same pairs. Counts where only one of them arrived."""
    only_a = sum(1 for x, y in zip(a, b) if x["arrived"] and not y["arrived"])
    only_b = sum(1 for x, y in zip(a, b) if y["arrived"] and not x["arrived"])
    both = [(x["reads"], y["reads"]) for x, y in zip(a, b) if x["arrived"] and y["arrived"]]
    faster = sum(1 for x, y in both if x < y)
    slower = sum(1 for x, y in both if x > y)
    return only_a, only_b, faster, slower, len(both)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bank", default="banks/pythia-410m.npz")
    ap.add_argument("--layer", default=None)
    ap.add_argument("--walkers", type=int, default=2000, help="walkers that lay trails")
    ap.add_argument("--test", type=int, default=300, help="fresh pairs per test set")
    ap.add_argument("--beats", type=int, default=150)
    ap.add_argument("--horizon", type=int, default=20)
    ap.add_argument("--k", type=int, default=6, help="trails read out of each anchor")
    ap.add_argument("--evap", type=float, default=0.001, help="evaporation per walker")
    ap.add_argument("--targets", type=int, default=0,
                    help="if >0, walkers seek only this many fixed words (food sources); 0: any word")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--tag", default=None)
    a = ap.parse_args()

    t0 = time.time()
    bank = Bank.load(a.bank, a.layer)
    pool = [i for i, w in enumerate(bank.words) if w.isalpha() and w.islower() and len(w) >= 4]
    rng = np.random.default_rng(a.seed)
    budget = a.beats * 6
    print(f"{bank.label}: {len(bank.words)} words, pool {len(pool)}, horizon {a.horizon}, "
          f"{a.walkers} walkers, k={a.k}, evap={a.evap}")

    # ---- the swarm lays trails
    trails = Trails(evap=a.evap, k=a.k)
    food = [int(x) for x in rng.choice(pool, a.targets, replace=False)] if a.targets else None
    train_pairs = make_pairs(bank, pool, a.walkers, rng, targets=food)
    train, curve, window = [], [], []
    for n, (s, g) in enumerate(train_pairs):
        r = walk(bank, s, g, trails, a.beats, a.horizon, seed=a.seed * 100003 + n)
        if r["arrived"]:
            trails.deposit(loop_erase(r["path"]))
        trails.evaporate()
        train.append(r)
        window.append(r)
        if len(window) == 200:
            curve.append(summarise(window, budget) | {"upto": n + 1, "edges": len(trails.edges())})
            window = []
            c = curve[-1]
            print(f"  walkers {n + 1:5d}: arrived {c['rate']:.0%}, mean cost {c['mean_cost']:.0f} reads, "
                  f"trail-only commits {c['road_commits']}, edges {c['edges']}  ({time.time() - t0:.0f}s)")
    trained = trails.edges()
    trail_words = sorted({i for e in trained for i in e[:2]})

    # ---- controls with the same size
    k = a.k
    perm = rng.permutation(len(trail_words))
    relabel_map = {w: trail_words[p] for w, p in zip(trail_words, perm)}
    relabel = Trails.from_edges([(relabel_map[i], relabel_map[j], v) for i, j, v in trained], k)
    n_words = len(bank.words)
    rand = Trails.from_edges([(int(rng.integers(n_words)), int(rng.integers(n_words)), v)
                              for _, _, v in trained], k)
    frozen = Trails.from_edges(trained, k)
    conds = {"none": None, "roads": frozen, "relabel": relabel, "random": rand,
             "hub_jumps": "hubs", "any_jumps": "any"}

    # ---- fresh pairs
    used_pairs = set(train_pairs)
    used_words = {x for p in train_pairs for x in p}
    sets = {"fresh_pairs": make_pairs(bank, pool, a.test, rng, banned_pairs=used_pairs),
            "fresh_words": make_pairs(bank, pool, a.test, rng, banned_pairs=used_pairs,
                                      banned_words=used_words)}
    if food:                            # new ants, old food: fresh starts, the same targets
        starts_used = {p[0] for p in train_pairs}
        sets["known_targets"] = make_pairs(bank, pool, a.test, rng, banned_pairs=used_pairs,
                                           banned_words=starts_used | set(food), targets=food)
    results = {}
    for sname, pairs in sets.items():
        results[sname] = {}
        for cname, roads in conds.items():
            rows = []
            for n, (s, g) in enumerate(pairs):
                r = roads
                if r == "hubs":                     # every anchor: k fresh trail words, anywhere
                    r = Jumps(trail_words, k, seed=n)
                elif r == "any":                    # every anchor: k fresh words of the whole map
                    r = Jumps(np.arange(n_words), k, seed=n)
                rows.append(walk(bank, s, g, r, a.beats, a.horizon, seed=10 ** 7 + n))
            results[sname][cname] = rows
        print(f"  {sname}: " + ", ".join(f"{c} {summarise(results[sname][c], budget)['rate']:.0%}"
                                         for c in conds) + f"  ({time.time() - t0:.0f}s)")

    # ---- census
    doors = Counter()
    for r in train:
        if r["arrived"]:
            p = loop_erase(r["path"])
            doors.update(p[1:-1])
    strength = Counter()
    for i, j, v in trained:
        strength[i] += v
        strength[j] += v
    near = {}
    tunnels = 0
    for i, j, v in trained:
        if i not in near:
            near[i] = set(bank.neighbours(i, a.horizon).tolist())
        if j not in near[i]:
            tunnels += 1
    cosines = [float(bank.full[i] @ bank.full[j]) for i, j, _ in trained]

    # ---- write
    tag = a.tag or (f"swarm_{Path(a.bank).stem}_h{a.horizon}_w{a.walkers}"
                    + (f"_t{a.targets}" if a.targets else ""))
    out = Path(a.out or Path("runs") / tag)
    out.mkdir(parents=True, exist_ok=True)
    W = bank.words
    top_edges = sorted(trained, key=lambda e: -e[2])
    (out / "trails.json").write_text(json.dumps(
        [{"a": W[i], "b": W[j], "w": round(v, 3)} for i, j, v in top_edges], ensure_ascii=False))
    (out / "doors.txt").write_text("\n".join(
        f"{c:5d}  {W[i]}" for i, c in doors.most_common()) + "\n", encoding="utf-8")
    slim = {s: {c: [{k2: v2 for k2, v2 in r.items() if k2 != "path"} | {"path": [W[x] for x in r["path"]]}
                    for r in rows] for c, rows in d.items()} for s, d in results.items()}
    (out / "test.json").write_text(json.dumps(slim, ensure_ascii=False, indent=0))
    (out / "curve.json").write_text(json.dumps(curve, indent=1))

    L = [f"# Swarm on {bank.label}", "",
         f"{a.walkers} hidden-target walkers, one after another, horizon {a.horizon}, "
         f"{a.beats} beats each ({budget} sweep reads), trails read k={a.k} per anchor, "
         f"evaporation {a.evap} per walker, seed {a.seed}. "
         + (f"Walkers seek only {a.targets} fixed targets: {', '.join(W[i] for i in food)}. " if food else
            "Each walker seeks a random word. ")
         + "Explore mode: descriptive only.", "",
         "## While laying trails", "",
         "| walkers | arrived | mean cost (reads) | trail-only commits | trail edges |",
         "|---|---|---|---|---|"]
    for c in curve:
        L.append(f"| {c['upto']} | {c['rate']:.0%} | {c['mean_cost']:.0f} | {c['road_commits']} | {c['edges']} |")
    L += ["", "Each block of 200 is a different set of random pairs, so this curve mixes pair "
          "difficulty with trail growth; the test below holds the pairs fixed.", "",
          f"Trail graph: {len(trained)} edges over {len(trail_words)} words. "
          f"{tunnels} edges ({tunnels / max(len(trained), 1):.0%}) join words outside each other's "
          f"{a.horizon}-word horizon (tunnels); median edge cosine "
          f"{np.median(cosines):.3f} (map: 20th-neighbour cosine {bank.coh_ref:.3f}).", "",
          "## Fresh pairs, same seed, four ways", "",
          "Cost counts every read, trail reads included; a walker that never arrives costs the "
          "whole budget.", ""]
    for sname, d in results.items():
        L += [f"### {sname} ({len(sets[sname])} pairs)", "",
              "| trails | arrived | mean cost | median reads (arrived) | mean moves (arrived) | trail-only commits |",
              "|---|---|---|---|---|---|"]
        for cname, rows in d.items():
            m = summarise(rows, budget)
            L.append(f"| {cname} | {m['rate']:.0%} | {m['mean_cost']:.0f} | "
                     f"{m['median_reads_arrived']} | "
                     f"{'' if m['mean_moves_arrived'] is None else round(m['mean_moves_arrived'], 1)} | "
                     f"{m['road_commits']} |")
        L.append("")
        for cname in [c for c in conds if c != "none"]:
            oa, ob, fa, sl, nb = paired(d[cname], d["none"])
            L.append(f"- {cname} vs none: only {cname} arrived {oa}, only none arrived {ob}; "
                     f"both arrived {nb}, {cname} cheaper in {fa}, dearer in {sl}")
        L.append("")
    L += ["## Door census", "",
          "Words inside arrived paths (loops cut), most frequent first. Full list in `doors.txt`.", "",
          ", ".join(f"{W[i]} {c}" for i, c in doors.most_common(60)), "",
          "## Strongest trails", "",
          ", ".join(f"{W[i]}–{W[j]} {v:.1f}" for i, j, v in top_edges[:40]), "",
          f"Ran in {time.time() - t0:.0f}s on CPU."]
    (out / "REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out}/REPORT.md")


if __name__ == "__main__":
    main()
