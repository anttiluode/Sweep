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

## Swarm (`swarm.py`)

Many hidden-target walkers on the same frozen map, one after another, as in an ant colony:
each arrived walker lays its anchor path (loops cut) down as a trail, trails evaporate a
little after every walker, and a later walker reads the 6 strongest trails out of each
anchor it stands on (one read each; a trail may lead past the horizon). Then fresh pairs,
each walked six ways with the same seed: no trails, the swarm's trails, the same trail graph
with its words shuffled, the same number of random edges, 6 random swarm-visited words at
every anchor, and 6 random words of the whole map at every anchor.

```
python swarm.py --bank ../SweepSol/bank.json                 # 2000 walkers, random pairs
python swarm.py --bank ../SweepSol/bank.json --targets 20    # 20 fixed "food" words
```

Sol's Qwen map, horizon 20, 2000 walkers, 300 fresh pairs per set (`runs/swarm_qwen_*`):

| arrived | none | roads | shuffled | random edges | swarm-word jumps | any-word jumps |
|---|---|---|---|---|---|---|
| random pairs: fresh pairs | 43% | 47% | 56% | 53% | 66% | 60% |
| random pairs: fresh words | 47% | 49% | 56% | 53% | 63% | 60% |
| 20 food words: fresh pairs | 51% | 52% | 59% | 52% | 65% | 64% |
| 20 food words: fresh words | 50% | 50% | 56% | 55% | 67% | 65% |
| 20 food words: new starts, same food | 47% | 47% | 54% | 51% | 62% | 59% |

The swarm's roads did not help: paired against no trails, 22/11, 15/8, 12/11, 8/8, 8/8
(pairs only one of them reached), and they cost more reads. About 90% of the trail edges
lie inside the horizon (median edge cosine 0.53 against 0.47 for a 20th neighbour), so a
road mostly shows the walker what it would have seen anyway: said–stated,
longitude–latitude, judge–jury, email–emails.

What helped was looking far. Jumps to random words of the whole map beat no trails in every
set (70/19, 68/27, 64/26, 70/26, 58/22; sign test p < 1e-4 each). The shuffled graph beat the
real one in every set (p from 0.0009 to 0.015): same places, edges made long. Jumps to
swarm-visited words were ahead of jumps to any word in all five sets, but not clearly
(52/35, 44/37, 46/42, 51/45, 42/34). The failures were walkers stuck on a warmth hill
inside their horizon; one warmer read from far away lets them leave it.

So on this map many heads give a census of where paths pass (`doors.txt`: with 20 food
words stated, frequency, longitude, relationship, sql, Excel, court, null; with random pairs
contribution, competition, discussion, restaurant, announcement), not shortcuts. Walkers are
sequential, so this is many heads over time, not at once. The far glance needs no swarm: it
is one head whose sweep sometimes reaches across the map.

## Fields (`fields.py`): temperature, loop aversion, goal-tagged aversion

The plain hidden walker steps only to something warmer: temperature zero. `fields.py` tries
three ways off a hill that is not the target, on the same pairs with the same seeds:
perception (the far glance: 6 random words' warmth at each new anchor), behaviour
(temperature: when nothing is warmer it heats up and may step to the warmest word it read
even if colder, accepted with exp(dw/T); an uphill step cools it) and memory (2000 plain
trainers sought 20 goals; each failure left its last word as a trap tagged with its goal; a
later walker reads the warmth of each old goal under its own goal, one call each, and avoids
the traps of old goals warmer than a 20th-neighbour cosine). Loops get a hard reflex (never
step back onto a stood-on word) or a learned trace (a recent move x→y is refused, a single
return allowed). Two controls: hot (always step to the warmest word read, colder or not) and
blind (step to a random word read).

```
python fields.py --bank ../SweepSol/bank.json
```

Sol's Qwen map, horizon 20, 150 beats, 300 fresh pairs per set (`runs/fields_qwen_h20`):

| arrived | seen goals | near goals (new) | new goals | searches / warmth calls (seen) |
|---|---|---|---|---|
| plain | 49% | 55% | 55% | 500 / 54 |
| far glance | 59% | 71% | 68% | 409 / 79 |
| temperature | 95% | 100% | 98% | 200 / 132 |
| temperature + reflex | 96% | 99% | 98% | 198 / 135 |
| temperature + learned loops | 95% | 100% | 98% | 200 / 132 |
| hot (control) | 91% | 99% | 97% | 242 / 172 |
| blind (control) | 5% | 8% | 5% | 877 / 575 |
| aversion | 58% | 55% | 55% | 423 / 75 |
| aversion + glance | 69% | 71% | 68% | 327 / 99 |
| temperature + learned + glance | 97% | 100% | 98% | 155 / 173 |

- Temperature does nearly all of it: against the plain walker 138/0, 133/0, 130/0 (pairs
  only one reached), with 2 to 5 downhill steps per journey and about 2.5 times fewer map
  searches, though more warmth calls. Hot does about as well; blind almost never arrives. So
  the warmth landscape is good almost everywhere; its hills are shallow, and the plain walker
  failed because it would never step down.
- Loops had nothing to do: with temperature a walker revisits a word 0.1 to 0.7 times per
  journey, because the coverage trace (inhibition of return) is already an inborn reflex.
  The learned loop trace changed no outcome. On this map no runaway loops formed.
- Aversion works only for goals it was learned on: seen goals 49% to 58% (29/0, p 4e-9), and
  it adds to the glance (59% to 69%, 30/0). For new goals near the old ones it was in force
  (12 trap words per walker) and did nothing (2/3); for unrelated goals it hardly applied
  and did no harm. What a walker learned chasing rewrite did not help a walker chasing a
  neighbour of rewrite. The traps were also the plain walker's hills, which a warm walker
  crosses anyway.

## Map before reader (`develop.py`)

Theory's `access.py` found the map before the reader in Pythia-410m: by step 1000 the word
states sort held-out words into their families (0.78) and sit next to their own category
word (0.69), while the model's own yes/no answers are at 0.08; at the end the outside
reader is at 0.97 and the model's answers at 0.39. `fields.py` found the same shape with a
walker on Qwen: the map is navigable (98–100% with temperature), the plain walker, which
never steps down, gets about 50%. In both, what was missing was not knowledge in the map
but flexibility in the reader. Gopnik ([2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7293160))
describes childhood as the high-temperature phase of a simulated annealing: broad search
first, narrowing later.

`develop.py` asks the developmental version: is the map walkable before the model can
answer from it? It builds a bank at each Pythia checkpoint (`bank.py --revision stepN`, same
words and frame) and sends the same 300 pairs through plain, temp, hot and blind walkers.

Arrival alone is not meaning. A calibration here: on a random cloud with the Qwen bank's
shape, the temperature walker still arrives 85% of the time (plain 38%, blind 5%). So each
path found on a young map is also scored in the final map, as the mean final-map cosine
between consecutive anchors. On that random cloud it is 0.004; on a half-random mix 0.33; on
the Qwen map itself 0.55. (Random word pairs: 0.003.)

```
python develop.py --model EleutherAI/pythia-410m --steps 0,512,1000,2000,4000,16000,143000
```

Prediction, written before the run: at step 1000 the temperature walker arrives and its
paths already make sense to the grown model (final-map step cosine well above random),
while Pythia's own answers are at 0.08. At step 0 it may arrive too, with step cosine near
random.

Run on Nov 26 (Antti's machine, `runs/develop_pythia-410m_h20`), layer 12, 300 pairs.
Pythia's own family answers are from Theory's `access.py`:

| step | plain | temp | blind | final-map step cosine | moves | shares a waypoint with the final route | Pythia's own answers |
|---|---|---|---|---|---|---|---|
| 0 | 31% | 93% | 9% | 0.003 | 16.0 | 2% | 0.19 |
| 512 | 28% | 74% | 6% | 0.270 | 14.8 | 12% | 0.08 |
| 1000 | 40% | 91% | 5% | 0.369 | 12.7 | 26% | 0.08 |
| 2000 | 53% | 96% | 10% | 0.418 | 10.5 | 40% | 0.19 |
| 4000 | 54% | 98% | 6% | 0.441 | 9.8 | 46% | 0.58 |
| 16000 | 58% | 98% | 9% | 0.464 | 10.0 | 53% | 0.42 |
| 143000 | 54% | 98% | 7% | 0.484 | 10.5 | 100% | 0.39 |

- The prediction holds. The untrained network's map is walkable (93%) and its paths mean
  nothing to the grown model (0.003; random pairs 0.000). At step 1000 the walker arrives
  91% of the time along steps already 76% as related as the grown model's own (0.369 of
  0.484), while Pythia answers 0.08.
- Step 512 is harder to walk than step 0 (74%, 384 searches against 270). The first
  structure is a sink: Spain, Afghanistan, Russia, Syria, Africa and Italy are the most
  frequent waypoints (42, 38, 38, 36, 30, 26 of the temp paths' intermediate words), and the
  place names stay frequent waypoints at every later step (US states at the end).
- The plain walker never catches up: from step 2000 on it stays at 53–58% while temp is at
  96–98%. Temperature rescued 119 to 188 pairs per checkpoint and lost at most one.
- Young walkers arrive by their own routes. The share of pairs whose route shares any
  intermediate word with the final model's route grows from 2% to 53% at step 16000.
- Example, golf to worried: step 1000 goes hunting, fought, wounded, arrested, fired,
  attacked, killed, burned, ...; step 4000 goes hunting, fighting, struggling, confused,
  surprised, scared, worried.

## Unlock (`unlock.py`): do two cues open what neither opens alone?

From Antti's bird: an object Katrina bought, and a shadow it casts only when the sun is this
low; neither opens anything on an ordinary day, together they open a whole package. On the
frozen map: the conjunction of cues a and b is the unit vector of a + b; the words it
unlocks are its 20 nearest that are in neither cue's 20 nearest. Sol's Qwen bank, 6000 pairs
binned by how related the two cues are (`runs/unlock_qwen`):

| cue cosine | unlocked of 20 | depth behind the single cues (median rank) | relation to both (min cosine) | package (mean pairwise cosine) |
|---|---|---|---|---|
| −0.34 to −0.07 | 10.4 | 80 | 0.14 | 0.29 |
| −0.07 to +0.01 | 9.8 | 66 | 0.20 | 0.31 |
| +0.01 to +0.11 | 8.9 | 52 | 0.25 | 0.33 |
| +0.11 to +0.34 | 7.0 | 38 | 0.31 | 0.36 |
| +0.34 to +0.45 | 3.5 | 27 | 0.38 | 0.36 |
| +0.45 to +0.86 | 2.4 | 25 | 0.43 | 0.40 |
| control: a cue + a random direction | 10.0 | 56 | | 0.31 |

A single cue's own 20 nearest have package 0.36. No sink: the 20 most frequent unlocked
words are 1.4% of all of them.

- Unrelated cues unlock the most and the deepest, but no better than adding a random
  direction: their package (0.29) is below the noise control (0.31). That is arithmetic,
  not a key.
- Closely related cues unlock little, just past the horizon, but what they open is tighter
  than either cue's own neighbourhood (0.40 against 0.36).
- Between them, at cue cosine about 0.1 to 0.35, a pair opens 7 new words from about rank
  38 behind each cue, related to both, as coherent as a single cue's neighbourhood. The
  cues of the story sit there: bird–shadow 0.32, bird–winter 0.29, shadow–winter 0.19.
- What they open on this map is generic: bird + winter gives sky, star, forest, river,
  rain, beach, mountain, city; shadow + winter gives storm, mountain, ocean, sun, moon,
  forest, star, day, stars, death, river; bird + shadow + winter gives star, mountain,
  storm, sun, moon, island, forest, river, ocean, wing. The model's map holds the scene, not
  the person. The tag that makes a package someone's own is not in the frozen weights.
- Grain changes the package. bird + love: at the 16 coarsest PCs hair, heart, brain, money,
  eye, god, blood (depth 90); in the full space wind, moon, heart, god, voice, cloud, eye,
  sky, girl (depth 68). shadow + memory: at 16 PCs letter, voice, atom, reflection, image;
  in full heart, voice, signature, thought, thoughts.

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
