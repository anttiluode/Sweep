# Sweep

A head that looks without moving, then decides whether to go.

A frozen language model's word states are the map. Sweep walks that map with two separate
states:

- the **anchor**: the word it stands on. It moves only on a commit.
- the **probe**: where it is looking. Once per beat it reaches outward from the anchor at an
  angle, alternating left and right around an axis.

The idea comes from the entorhinal sweeps. In rats, the head-direction compass stays locked
to the head, while a separate internal direction signal in the parasubiculum alternates
about 30° to either side, can point at a target behind the animal, and steers the grid-cell
sweeps (Vollan, Schellenberger, Moser & Moser, 2026). Looking and moving are different
operations there, and they are here.

**Explore mode.** Gate 0 only checks that the parts move. Nothing in this repo is a kill gate.

## What is harvested, and from where

| Part | Source | Receipt (checked in the repo) |
|---|---|---|
| stable reference + low-travel alternating sampler + fast control vector | [KyberDyyni1](https://github.com/anttiluode/KyberDyyni1) | deterministic alternator 99.1% target-hit cycles (reliable cue), 83.9% (mixed); scalar relevance retargeting 93 steps, 100% success |
| width, beat and axis kept as separate knobs | KyberDyyni1 `FORK_CONCLUSION.md` | coupling them the biological way (narrow + fast + strong anchor) went to 334 steps, about 65% success |
| coverage trace (inhibition of return) | [ConjunctionReservoir](https://github.com/anttiluode/ConjunctionReservoir) | `coverage_decay = 0.04` |
| grain windows | [Maatuska](https://github.com/anttiluode/Maatuska) / [Theory](https://github.com/anttiluode/Theory) | label-free coarse-to-fine axis in Pythia and Qwen |
| bored → blur, noisy → sharpen | PerceptionLab homeostatic coupler, `edge_of_chaos` mode | the 2025 ECG loop |
| looking ≠ moving | Sol, Nov 26 | |

## Modes

- **forage**: no goal. A homeostat on grain: if the reads are nearly the same as the anchor
  (case twins, plurals) it blurs one step; if they are unrelated to it, it sharpens one step.
  Coherence is always measured in the full space, so a narrow band cannot win by inflating its
  own cosines (the bias Neon found in SweepSol's adaptive grain).
- **known**: a target word. The look plane is turned to contain it and the axis points at it.
  Checks that the probe can leave the heading while the anchor stays.
- **hidden**: a target the head never sees. It gets one number per read, the warmth (cosine
  to the target), and the axis drifts toward the warmer side. If a plane has nothing warmer
  for four beats, it hops to the next local plane. This is KyberDyyni1's Gate 5 on a real
  model's map. `--switch` swaps the target mid-run.

## Run

```
pip install numpy torch transformers
python sweep.py --self-test                         # toy map, no model, seconds

python bank.py --model EleutherAI/pythia-410m --device cuda      # a few minutes, once
python sweep.py --start oak                                       # forage
python sweep.py --bank ../SweepSol/bank.json --start oak         # Sol's Qwen map, no GPU needed
python sweep.py --start oak --mode known --target guitar
python sweep.py --start oak --mode hidden --target sauna --switch guitar --switch-at 80 --beats 300
```

Qwen: `python bank.py --model Qwen/Qwen3-1.7B --device cuda --batch 8`, then
`python sweep.py --bank banks/qwen3-1.7b.npz ...`.

`bank.py` reads every word in Theory's few-shot frame at the word's token (Theory's 64
concept words, a firewood/sauna/music neighbourhood, then 8000 generic single-token words as
in `ocular.py`). It saves three layers (quarter, middle, three-quarter); `--layer L6` etc.
picks another one in `sweep.py`. Multi-token extras are read at their last token; the bank
lists them.

## What a run writes

`runs/<tag>/path.txt` has one line per beat:

```
b012 L th=+0.61 ax=+0.00 [ b4_32] @oak            saw: birch maple lumber   -> birch
```

side, probe angle, axis, grain, anchor, the words the sweep passed, and the commit if one
happened. `REPORT.md` has the anchor path and, for forage, the same number of moves made by
two reference walks (greedy nearest neighbour, random of the 10 nearest), counted in distinct
anchors, revisits, k-means regions touched and mean step cosine. These are for reading the
path, not gates. For pursuit it reports when the target was first seen, whether it was
reached, and an oracle hill-climb that sees all ten neighbours' warmth.

## Horizon

By default the probe reads the nearest word anywhere on the map, so with a known target the
head simply sees it: oak to guitar in one step. `--horizon N` lets the eye reach only the
anchor's N nearest words, so a pursuit has to find stepping stones. On Sol's Qwen map:

| horizon | known target | hidden target (warmth only) |
|---|---|---|
| whole map | oak, guitar | |
| 50 | oak, piano, guitar | oak, coal, coin, doll, dress, bike, laptop, piano, guitar |
| 20 | oak, carrot, fruit (stuck) | oak, coal, coin, pen, knife, guitar |
| 10 | oak, axe, knife, gun, guitar | oak, axe, knife, gun, guitar |

At horizon 20 knowing the direction got stuck on a local hill, while the hidden walker, which
hops look-planes when a side stays cold, arrived.

## Not in v1

- the ECG loop as the clock (beats are fixed-length here);
- sweeping across layers (the bank already stores three);
- a page to watch it live and take the knobs by hand.

## First real map (SweepSol's bank, Nov 26)

`sweep.py` also reads SweepSol's `bank.json` (Qwen3-1.7B, layer 14, 8000 words, top 128 PCs,
82% of the energy). Runs are in `runs/sol_bank_*`.

- From Berlin: London, England, Spain, Asia, American, Muslims, Catholic, Korean, Greek, Egypt,
  Empire, Kingdom, Domain, domain, region, portion, fraction, integer, boolean, null, Invalid,
  valid, validate, evaluate, investigate, research, Search, Check, Close, open, ... design,
  classic, standard, normal, natural, Nature, Environment, atmosphere, then word pieces.
  100 moves, 101 distinct anchors; the random walk of the 10 nearest made 51 and stayed in 2
  k-means regions, Sweep touched 31.
- From oak: Wood, metal, plastic, artificial, automatic, manual, Internal, external, ...
  bigger, smaller, short, Long, dark, bright, brilliant, fantastic, fantasy, magic, smart,
  stupid, sad, glad, hope, Love, like, unlike, whereas, although, because, therefore, and, but,
  pero, untuk, dengan, como, then word pieces.
- Hidden pursuit oak to sauna (warmth only): oak, onion, marijuana, sauna at beat 22; after
  the switch to guitar: casino, newsletter, journal, violin, guitar.

Seen so far: steps often go through a second sense (Kingdom to Domain to domain, fraction to
integer to boolean) or an opposite (automatic/manual, internal/external, dark/bright, sad/glad).
Every long forage ends in a continent of word pieces (con, ext, Del, mel, vol...), linked by
one-letter edits; about 1239 of the 8000 tokens are three letters long. The first grain regulator did
not breathe on this map (full grain about 98% of beats); runs `sol_bank_*` are from that version.
The homeostat above replaced it (runs `v2_*`): all five grains are used, about 15 to 33% each.
From Berlin, v2 goes Brazil, Amazon, Apache, Oracle, Icon, logo, label, tag, bag, box, Table,
Paper, newspaper, television, telephone, Camera, speaker, readers, writers, wrote, talked,
walked, running, rolling, floating, falling, ... thick, thin, narrow, wider, bigger, greatest,
grand, then pieces, then back out: pan, pot, Hat, Bag, box, cases, packages, packet, pack, patch,
padding, binding.

## Status

Built Nov 26, 2026. Self-test passes on a toy map with two overlapping trees; `bank.py` was
checked on tiny random GPT-NeoX and Qwen3 models (bank state equals a single forward pass to
3e-5). No real-model run yet.
