"""Develop: can a walker read the map before the model can?

Theory's access.py found, in Pythia-410m, the map before the reader: by step 1000 the word
states already sort held-out words into their families (0.78) and sit next to their own
category word (0.69), while the model's own yes/no answers are at 0.08. Its answers peak at
0.58 and end at 0.39; the outside reader ends at 0.97.

fields.py found the same shape on Qwen with a different reader: the warmth map is navigable
(98-100% with temperature) while the plain walker, which never steps down, gets about 50%.

This script puts the two together. For each training checkpoint it builds a bank (the
same words, the same frame, as bank.py) and sends the same fixed pairs through:

  plain   commits only to something warmer (temperature zero)
  temp    may step down when stuck (fields.py)
  hot     always steps to the warmest word read, colder or not
  blind   steps to a random word read (navigability without warmth)

Arrival says whether the map of that checkpoint is navigable by its own warmth. That alone
does not say the map means anything: a random cloud can be navigable too, which is what
step 0 is for. So every path found on a young map is also scored in the final map: the
mean final-map cosine between consecutive anchors ("would the grown model call these
steps"), next to the same number for the final map's own paths and for random pairs of
words.

    python develop.py --model EleutherAI/pythia-410m --steps 0,512,1000,2000,4000,16000,143000
    python develop.py --banks a.npz,b.npz,c.npz          # banks you already have; the last is "final"

Explore mode: descriptive only.
"""
import argparse
import json
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from sweep import Bank
from fields import Walker
from swarm import make_pairs

CONDS = {
    "plain": {},
    "temp": {"temp": 0.01},
    "hot": {"temp": 10.0, "tmax": 10.0, "heat": 1.0, "cool": 1.0, "loops": "reflex"},
    "blind": {"blind": True, "loops": "reflex"},
}
G = {}


def job(args):
    label, cname, pairs = args
    B = G["banks"][label]
    F = G["final"]
    rows = []
    for n, (s, g) in enumerate(pairs):
        w = Walker(B, s, g, horizon=G["horizon"], seed=10 ** 7 + n, **CONDS[cname])
        w.run(G["beats"])
        p = [B.words[i] for i in w.anchors]
        fi = [F.index[x] for x in p]
        steps = [float(F.full[a] @ F.full[b]) for a, b in zip(fi[:-1], fi[1:])]
        rows.append({"start": s, "target": g, "arrived": bool(w.a == w.g), "reads": w.reads_total,
                     "searches": len(w.log) * w.T, "warmth_calls": len(w._wcache),
                     "moves": len(p) - 1, "final_step_cos": float(np.mean(steps)) if steps else None,
                     "path": p})
    return label, cname, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="EleutherAI/pythia-410m")
    ap.add_argument("--steps", default="0,512,1000,2000,4000,16000,143000")
    ap.add_argument("--banks", default=None, help="comma-separated bank files instead of building them")
    ap.add_argument("--layer", default=None)
    ap.add_argument("--device", default=None)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--pairs", type=int, default=300)
    ap.add_argument("--beats", type=int, default=150)
    ap.add_argument("--horizon", type=int, default=20)
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    t0 = time.time()

    # ---- the maps
    if a.banks:
        files = [Path(x) for x in a.banks.split(",")]
        labels = [f.stem for f in files]
    else:
        import torch
        from bank import load_and_build
        device = a.device or ("cuda" if torch.cuda.is_available() else "cpu")
        files, labels = [], []
        for s in [x.strip() for x in a.steps.split(",") if x.strip()]:
            f = Path("banks") / f"{a.model.split('/')[-1].lower()}-step{s}.npz"
            if not f.exists():
                load_and_build(a.model, device, batch=a.batch, revision=f"step{s}", out=f)
            files.append(f)
            labels.append(f"step{s}")
    banks = {lab: Bank.load(f, a.layer) for lab, f in zip(labels, files)}
    final = banks[labels[-1]]
    for lab, B in banks.items():
        if B.words != final.words:
            raise SystemExit(f"{lab} has a different word list from {labels[-1]}")
    G.update(banks=banks, final=final, horizon=a.horizon, beats=a.beats)
    print(f"{len(banks)} maps: {', '.join(labels)}; final {final.label}  ({time.time() - t0:.0f}s)")

    # ---- the same pairs on every map, chosen on the final one
    rng = np.random.default_rng(a.seed)
    pool = [i for i, w in enumerate(final.words) if w.isalpha() and w.islower() and len(w) >= 4]
    pairs = [(final.words[s], final.words[g]) for s, g in make_pairs(final, pool, a.pairs, rng)]
    rnd = rng.choice(len(final.words), size=(2000, 2))
    base_cos = float(np.mean([final.full[i] @ final.full[j] for i, j in rnd if i != j]))

    jobs = [(lab, c, pairs) for lab in labels for c in CONDS]
    res = {}
    with Pool(a.procs) as P:
        for lab, c, rows in P.imap_unordered(job, jobs):
            res.setdefault(lab, {})[c] = rows
            print(f"  {lab:12s} {c:6s} arrived {np.mean([r['arrived'] for r in rows]):.0%}  "
                  f"({time.time() - t0:.0f}s)")

    # ---- report
    name = Path(files[-1]).stem.split("-step")[0] if not a.banks else "banks"
    out = Path(a.out or Path("runs") / f"develop_{name}_h{a.horizon}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "develop.json").write_text(json.dumps({"labels": labels, "pairs": pairs, "results": res},
                                                 ensure_ascii=False))
    L = [f"# Develop: {', '.join(labels)}", "",
         f"Final map: {final.label}. {len(pairs)} pairs chosen on the final map (targets outside the start's "
         f"50 nearest), the same on every checkpoint; horizon {a.horizon}, {a.beats} beats. "
         "Explore mode: descriptive only.", "",
         "Arrived (each map navigated by its own warmth):", "",
         "| map | plain | temp | hot | blind | temp: searches | temp: warmth calls |", "|---|---|---|---|---|---|---|"]
    for lab in labels:
        m = {c: np.mean([r["arrived"] for r in res[lab][c]]) for c in CONDS}
        tr = res[lab]["temp"]
        L.append(f"| {lab} | {m['plain']:.0%} | {m['temp']:.0%} | {m['hot']:.0%} | {m['blind']:.0%} | "
                 f"{np.mean([r['searches'] for r in tr]):.0f} | {np.mean([r['warmth_calls'] for r in tr]):.0f} |")
    L += ["", f"Steps judged by the final map: mean final-map cosine between consecutive anchors of arrived "
          f"temp paths (random word pairs: {base_cos:.3f}).", "",
          "| map | final-map step cosine | mean moves |", "|---|---|---|"]
    for lab in labels:
        arr = [r for r in res[lab]["temp"] if r["arrived"] and r["final_step_cos"] is not None]
        L.append(f"| {lab} | {np.mean([r['final_step_cos'] for r in arr]):.3f} | "
                 f"{np.mean([r['moves'] for r in arr]):.1f} |" if arr else f"| {lab} | | |")
    L += ["", "Example temp paths on each map (first five pairs):", ""]
    for lab in labels:
        L.append(f"**{lab}**")
        L.append("")
        for r in res[lab]["temp"][:5]:
            L.append(f"- {' → '.join(r['path'][:14])}{' …' if len(r['path']) > 14 else ''}"
                     f"{'' if r['arrived'] else '  (not arrived)'}")
        L.append("")
    L.append(f"Ran in {time.time() - t0:.0f}s.")
    (out / "REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out}/REPORT.md")


if __name__ == "__main__":
    main()
