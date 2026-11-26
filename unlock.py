"""Unlock: do two cues together open neighbours that neither cue opens alone?

Antti, Nov 26: a bird Katrina bought, and a shadow it casts in a corner only when the sun is
this low, late in the year. Neither the bird nor the low sun opens anything on an ordinary
day; together they open a whole package of memories. "Surface values first, what resonates
today, combine it with something else and other things unlock."

On a frozen map this is a geometric question. For cues a and b (word states, unit vectors in
the centred full space) the conjunction is the unit vector of a + b. Its k nearest words,
minus each cue's own k nearest, are the words the pair unlocks. For each pair we measure:

  unlocked     how many of the conjunction's k nearest are in neither cue's k nearest
  depth        how deep they were behind each cue alone: the better of their two ranks
               in a's and b's full orderings (rank 30 is just past the horizon, rank 500
               is somewhere neither cue reaches near)
  both         how related they are to both cues: the smaller of their two cosines
  package      mean pairwise cosine among the unlocked words (a coherent whole, or scatter?)

Pairs are binned by how related the two cues are (their own cosine). Controls:
  noise        a cue plus a random direction (not a word), matched to a word's spread:
               how much "unlocking" is just the arithmetic of adding two vectors
  baseline     the package value of a single cue's own k nearest, and of k random words

Grain: the same conjunction at coarser PCA windows (Maatuska's grain), to see whether a
coarse look and a fine look open different packages.

Explore mode: descriptive only.

    python unlock.py --bank ../SweepSol/bank.json
"""
import argparse
import json
from pathlib import Path

import numpy as np

from sweep import Bank, unit


def ranks_from(F, v):
    """Rank of every word by cosine to direction v (0 = closest)."""
    order = np.argsort(-(F @ v))
    r = np.empty(len(order), dtype=np.int64)
    r[order] = np.arange(len(order))
    return r


def conj(F, idx, k, extra=None):
    """Nearest k to the conjunction of the words idx (plus an optional extra direction)."""
    v = unit(F[idx].sum(0) + (0 if extra is None else extra))
    s = F @ v
    s[idx] = -np.inf
    return np.argsort(-s)[:k], v


def near(F, i, k):
    s = F @ F[i]
    s[i] = -np.inf
    return np.argsort(-s)[:k]


def package(F, ids):
    if len(ids) < 2:
        return None
    S = F[ids] @ F[ids].T
    n = len(ids)
    return float((S.sum() - np.trace(S)) / (n * (n - 1)))


def measure(F, a, b, k, extra=None):
    na = set(near(F, a, k).tolist())
    nb = set() if b is None else set(near(F, b, k).tolist())
    nc, v = conj(F, [a] if b is None else [a, b], k, extra)
    un = [int(w) for w in nc if w not in na and w not in nb and w != b]
    ra = ranks_from(F, F[a])
    rb = ranks_from(F, F[b]) if b is not None else None
    depth = [int(min(ra[w], rb[w])) if rb is not None else int(ra[w]) for w in un]
    both = [float(min(F[w] @ F[a], F[w] @ F[b])) for w in un] if b is not None else []
    return {"unlocked": len(un), "words": un, "depth": float(np.median(depth)) if depth else None,
            "both": float(np.mean(both)) if both else None, "package": package(F, un)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bank", default="banks/pythia-410m.npz")
    ap.add_argument("--layer", default=None)
    ap.add_argument("--pairs", type=int, default=4000)
    ap.add_argument("--k", type=int, default=20)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--examples", default="bird+shadow,bird+winter,shadow+winter,sun+low,shadow+sun,"
                    "bird+shadow+winter,bird+shadow+evening,bird+love,shadow+memory,corner+light,"
                    "oak+guitar,fire+water,winter+home")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    B = Bank.load(a.bank, a.layer)
    F, W, k = B.full, B.words, a.k
    rng = np.random.default_rng(a.seed)
    pool = np.array([i for i, w in enumerate(W) if w.isalpha() and w.islower() and len(w) >= 4])

    # ---- random pairs, binned by the cues' own cosine
    P = rng.choice(pool, size=(a.pairs, 2))
    P = P[P[:, 0] != P[:, 1]]
    # add related pairs too (random pairs are mostly unrelated): a word and one of its 50 nearest
    rel = []
    for i in rng.choice(pool, size=a.pairs // 2):
        j = int(rng.choice(near(F, i, 50)))
        rel.append((int(i), j))
    P = np.vstack([P, np.array(rel)])
    rows = []
    for i, j in P:
        m = measure(F, int(i), int(j), k)
        m.update(a=int(i), b=int(j), cos=float(F[i] @ F[j]))
        rows.append(m)
    cos = np.array([r["cos"] for r in rows])
    edges = np.quantile(cos, np.linspace(0, 1, 7))

    # ---- controls
    noise = []
    for i in rng.choice(pool, size=1000):
        e = rng.standard_normal(F.shape[1])
        e = unit(e)                                  # unit, like a unit word direction
        noise.append(measure(F, int(i), None, k, extra=e))
    single = [package(F, near(F, int(i), k)) for i in rng.choice(pool, size=1000)]
    randset = [package(F, rng.choice(len(W), size=k, replace=False)) for _ in range(1000)]

    def agg(rs):
        g = lambda key: [r[key] for r in rs if r[key] is not None]
        return (np.mean(g("unlocked")), np.median(g("depth")) if g("depth") else float("nan"),
                np.mean(g("both")) if g("both") else float("nan"), np.mean(g("package")) if g("package") else float("nan"))

    L = [f"# Unlock on {B.label}", "",
         f"Conjunction of two cues = unit(a + b) in the centred full space; k = {k}. "
         f"{len(rows)} pairs ({len(P) - len(rel)} random, {len(rel)} a word with one of its 50 nearest), "
         "binned by the cues' own cosine. Explore mode: descriptive only.", "",
         "| cue cosine | pairs | unlocked of 20 | median depth (better single-cue rank) | relation to both (min cosine) | package (mean pairwise cosine) |",
         "|---|---|---|---|---|---|"]
    for lo, hi in zip(edges[:-1], edges[1:]):
        rs = [r for r in rows if lo <= r["cos"] <= hi]
        u, d, bo, pk = agg(rs)
        L.append(f"| {lo:+.2f} to {hi:+.2f} | {len(rs)} | {u:.1f} | {d:.0f} | {bo:.3f} | {pk:.3f} |")
    u, d, bo, pk = agg(noise)
    L += ["", f"Controls: a cue plus a random unit direction unlocks {u:.1f} of 20, median depth {d:.0f}, "
          f"package {pk:.3f}. A single cue's own 20 nearest: package {np.mean(single):.3f}. "
          f"Twenty random words: package {np.mean(randset):.3f}. "
          f"Map: 20th-neighbour cosine {B.coh_ref:.3f}.", ""]

    from collections import Counter
    cnt = Counter(w for r in rows for w in r["words"])
    tot = sum(cnt.values())
    L += [f"Sinks: over all pairs, {tot} unlocked words, {len(cnt)} distinct; the 20 most frequent are "
          f"{sum(v for _, v in cnt.most_common(20)) / max(tot, 1):.1%} of them ("
          + ", ".join(f"{W[w]} {v}" for w, v in cnt.most_common(8)) + ").", ""]

    # ---- examples, at three grains
    L += ["## Examples", "",
          "Unlocked words (in the conjunction's 20 nearest, in neither cue's 20 nearest), "
          "closest first, with the median depth behind the single cues. Grains are PCA windows "
          "(Maatuska): the conjunction is formed and read in that window.", ""]
    ex_out = {}
    for ex in [e.strip() for e in a.examples.split(",") if e.strip()]:
        ws = ex.split("+")
        if not all(w in B.index for w in ws):
            L.append(f"- {ex}: not in the bank")
            continue
        idx = [B.index[w] for w in ws]
        cs = [float(F[i] @ F[j]) for n, i in enumerate(idx) for j in idx[n + 1:]]
        L.append(f"**{ex}** (cue cosine {', '.join(f'{c:.2f}' for c in cs)})")
        L.append("")
        ex_out[ex] = {}
        for gname in [g[0] for g in B.grains if g[0] in ("top16", "top64", "full")]:
            G = B.E[gname]
            singles = set()
            for i in idx:
                singles.update(near(G, i, k).tolist())
            nc, _ = conj(G, idx, k)
            un = [int(w) for w in nc if w not in singles]
            R = [ranks_from(G, G[i]) for i in idx]
            dep = [int(min(r[w] for r in R)) for w in un]
            ex_out[ex][gname] = [W[w] for w in un]
            L.append(f"- {gname}: {', '.join(W[w] for w in un) or '(nothing new)'}"
                     + (f"  (median depth {int(np.median(dep))})" if dep else ""))
        L.append("")

    out = Path(a.out or Path("runs") / f"unlock_{Path(a.bank).stem}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (out / "pairs.json").write_text(json.dumps(
        [{"a": W[r["a"]], "b": W[r["b"]], "cos": round(r["cos"], 4), "unlocked": [W[w] for w in r["words"]],
          "depth": r["depth"], "both": r["both"], "package": r["package"]} for r in rows], ensure_ascii=False))
    (out / "examples.json").write_text(json.dumps(ex_out, ensure_ascii=False, indent=1))
    print("\n".join(L))


if __name__ == "__main__":
    main()
