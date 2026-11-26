"""Fields: ways for a hidden-target walker to leave a warmth hill that is not the target.

The plain hidden walker (sweep.py) commits only to something warmer than where it stands:
temperature zero. It fails when every word inside its horizon is colder, on a hill whose
top is not the target. Three different ways out, and combinations:

  glance      perception: at each new anchor, read the warmth of 6 random words anywhere
  temp        behaviour: when nothing is warmer, it heats up and may step downhill
              (Metropolis: accept with exp(dw/T)); an uphill step cools it again
  + reflex    loops: never step back onto a word already stood on (hard, inborn)
  + learned   loops: a fading trace on transitions; repeating a recent move x->y is
              refused, but going back once is allowed (so it can return and try another way)
  hot         control: T so high every stall steps to the warmest word read, colder or not
  blind       control: every commit goes to a random word read (warmth used only to
              recognise the target when it is read)
  aversion    memory: training walkers that failed leave a warning on the word they got
              stuck on, tagged with the goal they were after. A later walker reads the
              warmth of each tagged old goal under its own goal (one scalar call per old
              goal); where the old goal is warm (cosine above the map's 20th-neighbour
              cosine), it refuses to commit to those trap words.

Test sets (fresh starts, never used in training):
  seen   the same 20 goals the trainers sought
  near   new goals among the 10 nearest words of those 20 (does the warning transfer?)
  new    unrelated goals (does it hurt where it should not apply?)

Costs are counted three ways: map searches (each sweep tick is one nearest-word search in
the horizon), warmth calls (distinct words whose warmth was asked), and total reads.

Explore mode. Descriptive numbers and paired sign tests, no gates.

    python fields.py --bank ../SweepSol/bank.json
"""
import argparse
import json
import math
import time
from collections import Counter
from math import comb
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from sweep import Bank, Sweep
from swarm import Jumps, make_pairs


class Walker(Sweep):
    def __init__(self, bank, start, target, temp=0.0, heat=1.6, cool=0.5, tmax=0.5,
                 loops="none", loop_decay=0.02, traps=None, glance=0, blind=False, seed=0, **kw):
        self._wcache = {}
        roads = Jumps(np.arange(len(bank.words)), glance, seed=seed) if glance else None
        super().__init__(bank, start, mode="hidden", target=target, roads=roads, seed=seed, **kw)
        self.T0, self.temp = temp, temp
        self.heat, self.cool, self.tmax = heat, cool, tmax
        self.loops, self.loop_decay = loops, loop_decay
        self.blind = blind
        self.L = {}
        self.visited = {self.a}
        self.downhill = 0
        self.banned = set()
        if traps:                                         # goal-tagged warnings
            for old_goal, words in traps.items():
                if self.warmth(old_goal) > bank.coh_ref:
                    self.banned.update(words)
            self.banned.discard(self.g)
            self.banned.discard(self.a)
        self.banned_n = len(self.banned)

    def warmth(self, i):
        if i not in self._wcache:
            self._wcache[i] = super().warmth(i)
        return self._wcache[i]

    def _allowed(self, i):
        if i in self.banned:
            return False
        if self.loops == "reflex" and i in self.visited:
            return False
        if self.loops == "learned" and self.L.get((self.a, i), 0.0) > 0.5:
            return False
        return True

    def _decide(self, rec):
        if self.L:
            for k in list(self.L):
                self.L[k] *= (1.0 - self.loop_decay)
        pool = self.cands + self.road_cands
        if self.dwell < self.dwell_min or not pool:
            return False
        if self.g in [i for i, _ in pool]:
            best, val = self.g, 1.0
        else:
            ok = [(i, v) for i, v in pool if i != self.a and self._allowed(i)]
            if self.blind and ok:                     # control: a step to a random word read
                best, val = ok[int(self.rng.integers(len(ok)))]
            else:
                best, val = max(ok, key=lambda kv: kv[1]) if ok else (None, -1.0)
        aw = self.warmth(self.a)
        go = best is not None and (val > aw + 1e-9 or (self.blind and self.dwell >= self.dwell_min))
        down = False
        if not go and best is not None and self.T0 > 0:
            self.temp = min(self.tmax, self.temp * self.heat)
            if self.rng.random() < math.exp((val - aw) / self.temp):
                go, down = True, True
        if not go:
            self.stall += 1
            if self.stall >= 4:
                self.plane += 1
                self.b, self.stall = 0.0, 0
                self._orient()
            self.cands = self.cands[-self.T:]
            return False
        if not down and self.T0 > 0:
            self.temp = max(self.T0, self.temp * self.cool)
        old = self.a
        self.c[old] += 2.0
        self.a = best
        self.c[best] += 2.0
        step = self.B.Z[self.a] - self.B.Z[old]
        self.h = (lambda v: v / max(np.linalg.norm(v), 1e-12))(
            step / max(np.linalg.norm(step), 1e-12) + self.mom * self.h)
        self._orient()
        self.b = 0.0
        self.warm_side = {1: None, -1: None}
        self.dwell, self.stall, self.cands, self.road_cands = 0, 0, [], []
        self.anchors.append(self.a)
        self.visited.add(self.a)
        self.L[(old, best)] = self.L.get((old, best), 0.0) + 1.0
        self.downhill += down
        rec["commit"] = self.B.words[self.a]
        if down:
            rec["downhill"] = True
        return True


CONDS = {
    "none": {},
    "glance": {"glance": 6},
    "temp": {"temp": 0.01},
    "temp+reflex": {"temp": 0.01, "loops": "reflex"},
    "temp+learned": {"temp": 0.01, "loops": "learned"},
    "hot+reflex": {"temp": 10.0, "tmax": 10.0, "heat": 1.0, "cool": 1.0, "loops": "reflex"},
    "blind+reflex": {"blind": True, "loops": "reflex"},
    "aversion": {"traps": True},
    "aversion+glance": {"traps": True, "glance": 6},
    "temp+learned+glance": {"temp": 0.01, "loops": "learned", "glance": 6},
}

G = {}      # filled in the parent before the pool forks


def walk(s, g, cfg, seed):
    B = G["bank"]
    cfg = dict(cfg)
    if cfg.pop("traps", False):
        cfg["traps"] = G["traps"]
    w = Walker(B, B.words[s], B.words[g], horizon=G["horizon"], seed=seed, **cfg)
    w.run(G["beats"])
    p = w.anchors
    return {"start": B.words[s], "target": B.words[g], "arrived": bool(w.a == w.g),
            "reads": w.reads_total, "searches": len(w.log) * w.T, "warmth_calls": len(w._wcache),
            "moves": len(p) - 1, "revisits": len(p) - len(set(p)), "downhill": w.downhill,
            "banned": w.banned_n, "path": [B.words[i] for i in p]}


def job(args):
    sname, cname, pairs = args
    return sname, cname, [walk(s, g, CONDS[cname], 10 ** 7 + n) for n, (s, g) in enumerate(pairs)]


def sign_p(a, b):
    n, k = a + b, min(a, b)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bank", default="banks/pythia-410m.npz")
    ap.add_argument("--layer", default=None)
    ap.add_argument("--goals", type=int, default=20)
    ap.add_argument("--trainers", type=int, default=2000)
    ap.add_argument("--test", type=int, default=300)
    ap.add_argument("--beats", type=int, default=150)
    ap.add_argument("--horizon", type=int, default=20)
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    t0 = time.time()
    B = Bank.load(a.bank, a.layer)
    G.update(bank=B, horizon=a.horizon, beats=a.beats, traps={})
    rng = np.random.default_rng(a.seed)
    pool = [i for i, w in enumerate(B.words) if w.isalpha() and w.islower() and len(w) >= 4]
    goals = [int(x) for x in rng.choice(pool, a.goals, replace=False)]
    near = sorted({int(j) for f in goals for j in B.neighbours(f, 10)
                   if int(j) in set(pool) and int(j) not in goals})
    print(f"{B.label}: {a.goals} goals, {len(near)} near goals, horizon {a.horizon}")

    # ---- trainers: plain walkers to the goals; failures leave goal-tagged warnings
    train = make_pairs(B, pool, a.trainers, rng, targets=goals)
    with Pool(a.procs) as P:
        chunks = [("train", "none", train[i::a.procs]) for i in range(a.procs)]
        rows = [r for _, _, rr in P.map(job, chunks) for r in rr]
    traps = {}
    for r in rows:
        if not r["arrived"] and r["moves"] > 0:
            traps.setdefault(B.index[r["target"]], set()).add(B.index[r["path"][-1]])
    G["traps"] = traps
    n_fail = sum(1 for r in rows if not r["arrived"])
    print(f"  trainers arrived {1 - n_fail / len(rows):.0%}; "
          f"{sum(len(v) for v in traps.values())} trap words over {len(traps)} goals  ({time.time() - t0:.0f}s)")

    # ---- tests
    starts_used = {p[0] for p in train}
    banned = starts_used | set(goals) | set(near)
    sets = {"seen": make_pairs(B, pool, a.test, rng, banned_words=banned, targets=goals),
            "near": make_pairs(B, pool, a.test, rng, banned_words=banned, targets=near),
            "new": make_pairs(B, pool, a.test, rng, banned_words=banned)}
    jobs = [(s, c, p) for s, p in sets.items() for c in CONDS]
    with Pool(a.procs) as P:
        res = {}
        for s, c, rr in P.imap_unordered(job, jobs):
            res.setdefault(s, {})[c] = rr
            print(f"  {s:5s} {c:20s} arrived {np.mean([r['arrived'] for r in rr]):.0%}  ({time.time() - t0:.0f}s)")

    # ---- report
    out = Path(a.out or Path("runs") / f"fields_{Path(a.bank).stem}_h{a.horizon}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "test.json").write_text(json.dumps(res, ensure_ascii=False))
    (out / "traps.json").write_text(json.dumps(
        {B.words[g]: sorted(B.words[w] for w in ws) for g, ws in traps.items()}, ensure_ascii=False, indent=0))
    W = B.words
    L = [f"# Fields on {B.label}", "",
         f"Hidden-target walkers, horizon {a.horizon}, {a.beats} beats. {a.goals} goals: "
         + ", ".join(W[g] for g in goals) + f". {a.trainers} trainers walked to them with the plain walker; "
         f"{n_fail} failed and left {sum(len(v) for v in traps.values())} goal-tagged trap words. "
         f"Test starts were never trainer starts. Explore mode: descriptive only.", "",
         "Columns: arrived; mean map searches, warmth calls and total reads per walker "
         "(a walker that never arrives spends its whole budget); mean downhill steps; mean revisits "
         "of an anchor; mean trap words in force.", ""]
    order = list(CONDS)
    for s in sets:
        L += [f"## {s} goals ({len(sets[s])} pairs)", "",
              "| condition | arrived | searches | warmth calls | reads | downhill | revisits | traps in force |",
              "|---|---|---|---|---|---|---|---|"]
        for c in order:
            rr = res[s][c]
            m = lambda k: np.mean([r[k] for r in rr])
            L.append(f"| {c} | {m('arrived'):.0%} | {m('searches'):.0f} | {m('warmth_calls'):.0f} | "
                     f"{m('reads'):.0f} | {m('downhill'):.1f} | {m('revisits'):.1f} | {m('banned'):.1f} |")
        L.append("")
        for c, ref in [(c, "none") for c in order[1:]] + [(c, "glance") for c in order[2:]]:
            x, y = res[s][c], res[s][ref]
            A = sum(1 for p, q in zip(x, y) if p["arrived"] and not q["arrived"])
            Bn = sum(1 for p, q in zip(x, y) if q["arrived"] and not p["arrived"])
            L.append(f"- {c} vs {ref}: only {c} {A}, only {ref} {Bn} (sign test p={sign_p(A, Bn):.2g})")
        L.append("")
    big = Counter({W[g]: len(v) for g, v in traps.items()})
    L += ["## Traps", "", "Trap words per goal: " + ", ".join(f"{g} {n}" for g, n in big.most_common()), "",
          "Full lists in `traps.json`.", "", f"Ran in {time.time() - t0:.0f}s on CPU ({a.procs} processes)."]
    (out / "REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out}/REPORT.md")


if __name__ == "__main__":
    main()
