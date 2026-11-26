"""Sweep: a head that looks without moving, then decides whether to go.

A frozen language model's word states are the map. Sweep walks it with two separate
states, the way the entorhinal compass and the internal direction signal are separate
(Vollan, Schellenberger, Moser & Moser 2026):

    anchor   the word it stands on (moves only on commit)
    probe    where it is looking: an angle that alternates left/right around an axis,
             reaching outward from the anchor once per beat

The control machinery is ported from KyberDyyni1 (stable reference + structured
low-travel alternating sampler + fast control vector), with ConjunctionReservoir's
coverage trace as inhibition of return and a grain knob (Maatuska-style PCA windows).
Width, beat length, axis and grain are separate knobs; nothing couples them
(KyberDyyni1's FORK_CONCLUSION: copying the biological narrow+fast coupling hurt).

Modes
    forage   no goal. A regulator keeps reads between bored and noisy by changing grain.
    known    a target word; the axis points at it (does the probe decouple and steer?)
    hidden   a target word the head never sees; it only gets one warmth number per read
             and must find the direction (KyberDyyni1 Gate 5, on a real model's map)

Run
    python sweep.py --self-test
    python sweep.py --bank banks/pythia-410m.npz --start oak
    python sweep.py --bank banks/pythia-410m.npz --start oak --mode hidden --target guitar --switch fire

Explore mode: Gate 0 checks only that the parts move. Nothing here is a kill gate.
Needs only NumPy. The bank comes from bank.py (needs torch + transformers).
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np

# coarse -> fine. (name, first component, width); None = the full state
GRAINS = [("top8", 0, 8), ("top16", 0, 16), ("b4_32", 4, 32), ("top64", 0, 64),
          ("top256", 0, 256), ("full", None, None)]


def unit(v, axis=-1):
    n = np.linalg.norm(v, axis=axis, keepdims=True)
    return v / np.maximum(n, 1e-12)


# ================================================================ the map
class Bank:
    def __init__(self, words, X, centered=True, label="", tags=None):
        X = np.asarray(X, dtype=np.float64)
        if centered:                       # angles as LayerNorm sees them
            X = X - X.mean(1, keepdims=True)
        self.Z = X - X.mean(0)
        self.words = [str(w) for w in words]
        self.index = {w: i for i, w in enumerate(self.words)}
        self.tags = tags
        self.label = label
        n, d = self.Z.shape
        evals, evecs = np.linalg.eigh(self.Z.T @ self.Z)
        self.V = evecs[:, ::-1]
        self.grains, self.E = [], {}
        for name, k0, w in GRAINS:
            if k0 is not None and k0 + w > d:
                continue
            P = self.Z if k0 is None else self.Z @ self.V[:, k0:k0 + w]
            self.grains.append((name, k0, w))
            self.E[name] = unit(P)
        self.full = self.E["full"]
        rng = np.random.default_rng(0)
        sample = rng.choice(n, size=min(400, n), replace=False)
        sims = self.full[sample] @ self.full.T
        srt = -np.sort(-sims, axis=1)
        k = min(20, n - 1)
        self.coh_ref = float(np.median(srt[:, k]))        # typical cosine to the 20th neighbour
        nb20 = np.argsort(-sims, axis=1)[:, k]
        self.reach = float(np.median(np.linalg.norm(self.Z[sample] - self.Z[nb20], axis=1)))

    @classmethod
    def load(cls, path, layer=None):
        if str(path).endswith(".json"):                  # SweepSol's bank.json (PCA coordinates)
            import json as _json
            b = _json.loads(Path(path).read_text(encoding="utf-8"))
            m = b.get("meta", {})
            return cls(b["words"], np.array(b["vectors"], dtype=np.float64), False,
                       label=f"{Path(path).name}:{m.get('source', '?')} L{m.get('layer', '?')} {m.get('pcs', '?')} PCs")
        f = np.load(path, allow_pickle=False)
        layer = layer or str(f["default_layer"])
        X = f[layer]
        return cls(f["words"], X, bool(f["centered"]), label=f"{Path(path).stem}:{layer}")

    def project(self, p, grain):
        name, k0, w = grain
        q = p if k0 is None else p @ self.V[:, k0:k0 + w]
        return q / max(np.linalg.norm(q), 1e-12)

    def neighbours(self, i, k):
        s = self.full @ self.full[i]
        s[i] = -np.inf
        return np.argsort(-s)[:k]


# ================================================================ the head
class Sweep:
    def __init__(self, bank, start, mode="forage", target=None, switch=None, switch_at=None,
                 width=0.6, ticks=6, vmax=0.35, reach=1.0, grain=2, regulate=True,
                 coverage=True, cover_decay=0.04, cover_w=0.15, alternate=True,
                 dwell_min=2, dwell_max=6, eta=0.25, momentum=0.5, seed=0):
        self.B = bank
        self.a = self._idx(start)
        self.mode = mode
        self.g = self._idx(target) if target is not None else None
        self.switch = self._idx(switch) if switch is not None else None
        self.switch_at = switch_at
        self.W, self.T, self.vmax, self.reach_k = width, ticks, vmax, reach
        self.gi = min(grain, len(bank.grains) - 1)
        self.regulate = regulate and mode == "forage"
        self.coverage, self.decay, self.cw = coverage, cover_decay, cover_w
        self.alternate = alternate
        self.dwell_min, self.dwell_max = dwell_min, dwell_max
        self.eta, self.mom = eta, momentum
        self.rng = np.random.default_rng(seed)
        n = len(bank.words)
        self.c = np.zeros(n)
        self.theta, self.b, self.side = 0.0, 0.0, 1
        self.plane = 0
        self.h = None
        self.s = None
        self._orient(initial=True)
        self.dwell, self.stall = 0, 0
        self.cands = []                     # reads from the last two beats
        self.warm_side = {1: None, -1: None}
        self.beat = 0
        self.log, self.anchors = [], [self.a]
        self.reads_total = 0
        self.found_at = None

    def _idx(self, w):
        if w not in self.B.index:
            raise SystemExit(f"{w!r} is not in the bank (add it with bank.py --extra)")
        return self.B.index[w]

    # ---- geometry of the look
    def _local_axes(self, k=20):
        nb = self.B.neighbours(self.a, k)
        D = self.B.Z[nb] - self.B.Z[self.a]
        if self.h is not None:
            D = D - np.outer(D @ self.h, self.h)
        _, _, vt = np.linalg.svd(D, full_matrices=False)
        return vt

    def _orient(self, initial=False):
        """Heading h and side axis s for the current anchor."""
        if initial:
            nb = self.B.neighbours(self.a, 1)[0]
            self.h = unit(self.B.Z[nb] - self.B.Z[self.a])
        axes = self._local_axes()
        k = self.plane % len(axes)
        s = axes[k] - (axes[k] @ self.h) * self.h
        s = unit(s)
        if self.s is not None and s @ self.s < 0:
            s = -s
        self.s = s

    def _target_frame(self):
        """Known target: put the target in the look plane, axis pointing at it."""
        t = self.B.Z[self.g] - self.B.Z[self.a]
        perp = t - (t @ self.h) * self.h
        if np.linalg.norm(perp) > 1e-9:
            self.s = unit(perp)
        self.b = math.atan2(t @ self.s, t @ self.h)

    def warmth(self, i):
        return float(self.B.full[i] @ self.B.full[self.g])

    # ---- one beat: a sweep out to one side
    def step(self):
        if self.switch is not None and self.switch_at is not None and self.beat == self.switch_at:
            self.g, self.switch = self.switch, None
            self.found_at = None
            self.stall = 0
        if self.mode == "known":
            self._target_frame()
        grain = self.B.grains[self.gi]
        target = self.b + (self.side * self.W if self.alternate else self.W)
        c_start = self.c.copy()
        reads = []
        for t in range(self.T):
            d = target - self.theta                      # low-travel move toward the side target
            self.theta += max(-self.vmax, min(self.vmax, d))
            rho = self.reach_k * self.B.reach * (t + 1) / self.T
            u = math.cos(self.theta) * self.h + math.sin(self.theta) * self.s
            p = self.B.Z[self.a] + rho * u
            q = self.B.project(p, grain)
            score = self.B.E[grain[0]] @ q
            if self.coverage:
                score = score - self.cw * self.c
            score[self.a] = -np.inf
            r = int(np.argmax(score))
            reads.append(r)
            self.c[r] += 1.0
            self.reads_total += 1
            if self.g is not None and r == self.g and self.found_at is None:
                self.found_at = self.reads_total
        self.c *= (1.0 - self.decay)
        uniq = list(dict.fromkeys(reads))
        rec = {"beat": self.beat, "side": "L" if self.side > 0 else "R", "theta": round(self.theta, 3),
               "axis": round(self.b, 3), "grain": grain[0], "anchor": self.B.words[self.a],
               "reads": [self.B.words[r] for r in uniq]}
        coh = [float(self.B.full[self.a] @ self.B.full[r]) for r in uniq]
        nov = [math.exp(-c_start[r]) for r in uniq]
        rec["coherence"] = round(float(np.mean(coh)), 3)
        rec["novelty"] = round(float(np.mean([1.0 if c_start[r] < 0.5 else 0.0 for r in uniq])), 3)
        if self.g is not None:
            w = [self.warmth(r) for r in uniq]
            rec["warmth"] = round(max(w), 3)
            rec["anchor_warmth"] = round(self.warmth(self.a), 3)
            self.warm_side[self.side] = max(w)
            self.cands.extend(zip(uniq, w))
        else:
            self.cands.extend(zip(uniq, [c * n for c, n in zip(coh, nov)]))
        self.dwell += 1
        moved = self._decide(rec)
        if self.mode == "hidden" and not moved:
            self._steer_hidden()
        if self.regulate and self.beat % 2 == 1:
            self._regulate()
        if self.alternate:
            self.side = -self.side
        self.log.append(rec)
        self.beat += 1
        return rec

    def _decide(self, rec):
        """Commit: the anchor moves only here."""
        if self.dwell < self.dwell_min or not self.cands:
            return False
        best, val = max(self.cands, key=lambda kv: kv[1])
        if self.g is not None:
            if self.g in [i for i, _ in self.cands]:
                best, val = self.g, 1.0
            go = val > self.warmth(self.a) + 1e-9
            if not go:
                self.stall += 1
                if self.stall >= 4:                      # this plane has nothing warmer: hop
                    self.plane += 1
                    self.b, self.stall = 0.0, 0
                    self._orient()
                    self.cands = self.cands[-self.T:]
                return False
        else:
            go = val >= 0.9 * self.B.coh_ref or self.dwell >= self.dwell_max
        if not go:
            self.cands = self.cands[-self.T:]
            return False
        old = self.a
        self.c[old] += 2.0                               # inhibition of return on places stood on
        self.a = best
        self.c[best] += 2.0
        step = self.B.Z[self.a] - self.B.Z[old]
        self.h = unit(unit(step) + self.mom * self.h)    # heading keeps a residue of the last one
        self._orient()
        if self.mode == "hidden":
            self.b = 0.0
            self.warm_side = {1: None, -1: None}
        self.dwell, self.stall, self.cands = 0, 0, []
        if self.regulate and self.gi < len(self.B.grains) - 1:
            self.gi += 1                                 # arrived: sharpen to look at the new place
        self.anchors.append(self.a)
        rec["commit"] = self.B.words[self.a]
        return True

    def _steer_hidden(self):
        """Fast control vector: the axis drifts toward the warmer side (scalar only)."""
        wl, wr = self.warm_side[1], self.warm_side[-1]
        if wl is None or wr is None:
            return
        self.b += self.eta * (1 if wl > wr else -1 if wr > wl else 0)
        self.b = (self.b + math.pi) % (2 * math.pi) - math.pi

    def _regulate(self):
        """Edge-of-chaos rule on grain: bored -> coarser (opens doors); noisy -> sharper.
        A commit also sharpens one step, so grain breathes: blur to find a door, go through,
        focus on the new place."""
        recent = self.log[-2:]
        if len(recent) < 2:
            return
        nov = np.mean([r["novelty"] for r in recent])
        coh = np.mean([r["coherence"] for r in recent])
        if nov < 0.35 and self.gi > 0:
            self.gi -= 1
        elif coh < self.B.coh_ref and self.gi < len(self.B.grains) - 1:
            self.gi += 1

    def run(self, beats):
        for _ in range(beats):
            self.step()
            if self.g is not None and self.a == self.g and self.switch is None:
                break
        return self.log


# ================================================================ reference walks (not gates)
def ref_walk(bank, start, moves, kind, seed=0):
    rng = np.random.default_rng(seed)
    a, path = bank.index[start], [bank.index[start]]
    for _ in range(moves):
        nb = bank.neighbours(a, 10)
        a = int(nb[0]) if kind == "greedy" else int(rng.choice(nb))
        path.append(a)
    return path


def hill_climb(bank, start, target, budget):
    """Oracle reference: knows warmth of all 10 neighbours each step (10 reads per step)."""
    a, g, reads = bank.index[start], bank.index[target], 0
    while reads < budget:
        if a == g:
            return reads
        nb = bank.neighbours(a, 10)
        reads += len(nb)
        if g in nb:
            return reads
        w = bank.full[nb] @ bank.full[g]
        if w.max() <= bank.full[a] @ bank.full[g]:
            return None                                  # stuck on a local hill
        a = int(nb[int(np.argmax(w))])
    return None


def kmeans_regions(bank, k=64, iters=20, seed=0):
    X = bank.full
    rng = np.random.default_rng(seed)
    Cc = X[rng.choice(len(X), size=min(k, len(X)), replace=False)]
    for _ in range(iters):
        lab = np.argmax(X @ Cc.T, axis=1)
        for j in range(len(Cc)):
            m = X[lab == j]
            if len(m):
                Cc[j] = unit(m.mean(0))
    return np.argmax(X @ Cc.T, axis=1)


def path_stats(bank, path, regions):
    moves = len(path) - 1
    seen, revisits = set(), 0
    for i in path:
        if i in seen:
            revisits += 1
        seen.add(i)
    steps = [float(bank.full[a] @ bank.full[b]) for a, b in zip(path, path[1:])]
    return {"moves": moves, "distinct": len(seen), "revisits": revisits,
            "regions": len({int(regions[i]) for i in path}),
            "step_cos": round(float(np.mean(steps)), 3) if steps else None}


# ================================================================ Gate 0: do the parts move?
def gate0(bank, start, target=None, log=print):
    out = {}
    s = Sweep(bank, start, regulate=False, dwell_min=10 ** 9)
    s.run(24)
    signs = [np.sign(r["theta"] - r["axis"]) for r in s.log[2:]]
    flips = np.mean([a != b for a, b in zip(signs, signs[1:])])
    out["sides_alternate"] = (bool(flips >= 0.8), f"{flips:.2f} of beats switch side")

    s = Sweep(bank, start, regulate=False, coverage=False)
    differ, example = 0, None
    for ang in np.linspace(-math.pi, math.pi, 8, endpoint=False):
        for rho in (1.0, 2.0):
            p = bank.Z[s.a] + rho * bank.reach * (math.cos(ang) * s.h + math.sin(ang) * s.s)
            seen = []
            for gr in bank.grains:
                sc = bank.E[gr[0]] @ bank.project(p, gr)
                sc[s.a] = -np.inf
                seen.append(bank.words[int(np.argmax(sc))])
            if len(set(seen)) >= 2:
                differ += 1
                example = example or " / ".join(f"{g[0]}:{w}" for g, w in zip(bank.grains, seen))
    out["grain_changes_reads"] = (differ > 0, f"{differ}/16 probes read differently across grains; e.g. {example}")

    d = {}
    for cov in (True, False):
        s = Sweep(bank, start, regulate=False, coverage=cov, dwell_min=10 ** 9)
        s.run(30)
        d[cov] = len({w for r in s.log for w in r["reads"]})
    out["coverage_repels"] = (d[True] > d[False], f"distinct reads {d[True]} with trace, {d[False]} without")

    if target is not None:
        s = Sweep(bank, start, mode="known", target=target)
        s.step()
        f = Sweep(bank, start)
        f.step()
        moved = abs(s.b) > 0.1 and s.a == bank.index[start]
        out["probe_leaves_heading"] = (moved, f"axis {s.b:+.2f} rad while anchor stays on {start}")
    for k, (ok, msg) in out.items():
        log(f"  Gate 0  {k:22s} {'ok ' if ok else 'NO '} {msg}")
    return out


# ================================================================ reporting
def write_run(outdir, bank, sw, refs, extra):
    outdir.mkdir(parents=True, exist_ok=True)
    lines = []
    for r in sw.log:
        s = f"b{r['beat']:03d} {r['side']} th={r['theta']:+.2f} ax={r['axis']:+.2f} [{r['grain']:>6}] @{r['anchor']:<14} saw: {' '.join(r['reads'])}"
        if "warmth" in r:
            s += f"   warm {r['anchor_warmth']:+.2f}->{r['warmth']:+.2f}"
        if "commit" in r:
            s += f"   -> {r['commit']}"
        lines.append(s)
    (outdir / "path.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (outdir / "trace.json").write_text(json.dumps({"log": sw.log, "refs": refs, **extra}, indent=1), encoding="utf-8")
    anchors = " -> ".join(bank.words[i] for i in sw.anchors)
    rep = [f"# Sweep run: {extra['tag']}", "", f"bank `{bank.label}`, mode `{sw.mode}`, {len(sw.log)} beats, "
           f"{sw.reads_total} reads", "", "## Anchor path", "", anchors, ""]
    if refs:
        rep += ["## Same number of moves, reference walks (descriptive, not gates)", "",
                "| walk | moves | distinct anchors | revisits | regions touched | mean step cosine |",
                "|---|---:|---:|---:|---:|---:|"]
        for k, v in refs.items():
            rep.append(f"| {k} | {v['moves']} | {v['distinct']} | {v['revisits']} | {v['regions']} | {v['step_cos']} |")
        rep.append("")
    for k, v in extra.items():
        if k not in ("tag",):
            rep.append(f"- {k}: {v}")
    (outdir / "REPORT.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    return anchors


def main_run(bank, a, log=print):
    tag = a.tag or f"{a.mode}_{a.start}" + (f"_{a.target}" if a.target else "") + (f"_{a.switch}" if a.switch else "")
    log(f"bank {bank.label}: {len(bank.words)} words, d={bank.Z.shape[1]}, "
        f"grains {[g[0] for g in bank.grains]}, reach {bank.reach:.3f}, coh_ref {bank.coh_ref:.3f}")
    g0 = gate0(bank, a.start, a.target, log)
    sw = Sweep(bank, a.start, mode=a.mode, target=a.target, switch=a.switch, switch_at=a.switch_at,
               width=a.width, ticks=a.ticks, grain=a.grain, coverage=not a.no_coverage,
               alternate=not a.no_alternate, seed=a.seed)
    sw.run(a.beats)
    refs, extra = {}, {"tag": tag, "gate0": {k: v[1] for k, v in g0.items()}}
    if a.mode == "forage":
        regions = kmeans_regions(bank)
        moves = len(sw.anchors) - 1
        refs["sweep"] = path_stats(bank, sw.anchors, regions)
        refs["greedy nearest"] = path_stats(bank, ref_walk(bank, a.start, moves, "greedy"), regions)
        refs["random of 10 nearest"] = path_stats(bank, ref_walk(bank, a.start, moves, "random", a.seed), regions)
        grains = [r["grain"] for r in sw.log]
        extra["grain use"] = {g: grains.count(g) for g in dict.fromkeys(grains)}
    else:
        extra["reads to first see target"] = sw.found_at
        extra["reached target as anchor"] = bank.words[sw.a] == bank.words[sw.g]
        hc = hill_climb(bank, a.start, bank.words[sw.g], sw.reads_total * 4)
        extra["oracle hill-climb reads (sees all 10 neighbours' warmth)"] = hc
    anchors = write_run(Path(a.out) / tag, bank, sw, refs, extra)
    log(f"\nanchor path: {anchors}\n")
    for k, v in refs.items():
        log(f"  {k:22s} {v}")
    for k, v in extra.items():
        if k not in ("tag", "gate0"):
            log(f"  {k}: {v}")
    log(f"\nwrote {Path(a.out) / tag}/path.txt, trace.json, REPORT.md")
    return sw


# ================================================================ self-test on a toy map
def toy_bank(seed=0, d=64):
    """Two overlapping trees: kingdom/family/leaf, plus a 'use' that crosses families,
    the way oak is a tree and also firewood."""
    rng = np.random.default_rng(seed)
    K, F, L, U = 3, 4, 6, 4
    ku = rng.normal(size=(K, d)) * 3.0
    fu = rng.normal(size=(K, F, d)) * 2.0
    uu = rng.normal(size=(U, d)) * 2.0
    words, X, tags = [], [], []
    for k in range(K):
        for f in range(F):
            for l in range(L):
                u = int(rng.integers(U))
                words.append(f"k{k}f{f}l{l}u{u}")
                X.append(ku[k] + fu[k, f] + uu[u] + rng.normal(size=d))
                tags.append((k, f, u))
    return Bank(words, np.array(X), centered=False, label="toy", tags=tags)


def self_test():
    B = toy_bank()
    start = B.words[0]
    print("toy map:", len(B.words), "words; start", start)
    g0 = gate0(B, start, target=B.words[-1])
    assert all(ok for ok, _ in g0.values()), "a part does not move"
    sw = Sweep(B, start)
    sw.run(80)
    fam_change_same_use = sum(1 for a, b in zip(sw.anchors, sw.anchors[1:])
                              if B.tags[a][:2] != B.tags[b][:2] and B.tags[a][2] == B.tags[b][2])
    print(f"forage: {len(sw.anchors) - 1} commits, {len(set(sw.anchors))} distinct, "
          f"{fam_change_same_use} lateral steps through the 'use' tree")
    for mode in ("known", "hidden"):
        sw = Sweep(B, start, mode=mode, target=B.words[-1])
        sw.run(200)
        print(f"{mode:6s}: reached={B.words[sw.a] == B.words[-1]} first seen at read {sw.found_at}, "
              f"{len(sw.anchors) - 1} commits")
        assert B.words[sw.a] == B.words[-1], f"{mode} pursuit did not reach the target on the toy map"
    sw = Sweep(B, start, mode="hidden", target=B.words[40], switch=B.words[-1], switch_at=40)
    sw.run(300)
    print(f"switch: ends on {B.words[sw.a]} (second target {B.words[-1]})")
    print("self-test passed (parts move; toy pursuits arrive)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--bank", default="banks/pythia-410m.npz")
    ap.add_argument("--layer", default=None, help="bank key, e.g. L12 (default: the bank's default)")
    ap.add_argument("--start", default="oak")
    ap.add_argument("--mode", default="forage", choices=["forage", "known", "hidden"])
    ap.add_argument("--target")
    ap.add_argument("--switch", help="second target, swapped in at --switch-at")
    ap.add_argument("--switch-at", type=int, default=60)
    ap.add_argument("--beats", type=int, default=200)
    ap.add_argument("--width", type=float, default=0.6, help="half-width of the alternation, radians")
    ap.add_argument("--ticks", type=int, default=6, help="reads per beat")
    ap.add_argument("--grain", type=int, default=2, help="starting grain index, 0 = coarsest")
    ap.add_argument("--no-coverage", action="store_true")
    ap.add_argument("--no-alternate", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="runs")
    ap.add_argument("--tag")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return
    if a.mode != "forage" and not a.target:
        raise SystemExit("--target is needed for known and hidden modes")
    main_run(Bank.load(a.bank, a.layer), a)


if __name__ == "__main__":
    main()
