# Swarm on bank.json:Qwen/Qwen3-1.7B L14 128 PCs

2000 hidden-target walkers, one after another, horizon 20, 150 beats each (900 sweep reads), trails read k=6 per anchor, evaporation 0.001 per walker, seed 0. Walkers seek only 20 fixed targets: precis, yield, nullptr, latitude, judge, crew, relation, measurements, ease, responses, beaut, rewrite, intel, said, attached, prof, lifestyle, notification, requirement, same. Explore mode: descriptive only.

## While laying trails

| walkers | arrived | mean cost (reads) | trail-only commits | trail edges |
|---|---|---|---|---|
| 200 | 49% | 497 | 18 | 488 |
| 400 | 49% | 497 | 35 | 901 |
| 600 | 44% | 538 | 52 | 1234 |
| 800 | 49% | 498 | 72 | 1570 |
| 1000 | 46% | 520 | 85 | 1851 |
| 1200 | 45% | 535 | 95 | 2125 |
| 1400 | 50% | 491 | 92 | 2421 |
| 1600 | 50% | 501 | 124 | 2706 |
| 1800 | 50% | 493 | 101 | 2974 |
| 2000 | 55% | 459 | 134 | 3273 |

Each block of 200 is a different set of random pairs, so this curve mixes pair difficulty with trail growth; the test below holds the pairs fixed.

Trail graph: 3273 edges over 2538 words. 415 edges (13%) join words outside each other's 20-word horizon (tunnels); median edge cosine 0.522 (map: 20th-neighbour cosine 0.466).

## Fresh pairs, same seed, six ways

Cost counts every read, trail reads included; a walker that never arrives costs the whole budget.

### fresh_pairs (300 pairs)

| trails | arrived | mean cost | median reads (arrived) | mean moves (arrived) | trail-only commits |
|---|---|---|---|---|---|
| none | 51% | 479 | 72.0 | 5.8 | 0 |
| roads | 52% | 482 | 81.0 | 5.7 | 75 |
| relabel | 59% | 422 | 77.0 | 5.5 | 119 |
| random | 52% | 476 | 77.0 | 5.6 | 79 |
| hub_jumps | 65% | 382 | 90.0 | 4.9 | 267 |
| any_jumps | 64% | 395 | 90.0 | 5.1 | 276 |

- roads vs none: only roads arrived 12, only none arrived 11; both arrived 143, roads cheaper in 14, dearer in 120
- relabel vs none: only relabel arrived 35, only none arrived 13; both arrived 141, relabel cheaper in 16, dearer in 117
- random vs none: only random arrived 16, only none arrived 14; both arrived 140, random cheaper in 16, dearer in 118
- hub_jumps vs none: only hub_jumps arrived 66, only none arrived 24; both arrived 130, hub_jumps cheaper in 34, dearer in 90
- any_jumps vs none: only any_jumps arrived 64, only none arrived 26; both arrived 128, any_jumps cheaper in 23, dearer in 102

### fresh_words (300 pairs)

| trails | arrived | mean cost | median reads (arrived) | mean moves (arrived) | trail-only commits |
|---|---|---|---|---|---|
| none | 50% | 489 | 72.0 | 5.9 | 0 |
| roads | 50% | 494 | 77.0 | 5.7 | 66 |
| relabel | 56% | 443 | 79.0 | 5.7 | 107 |
| random | 55% | 450 | 79.5 | 5.9 | 80 |
| hub_jumps | 67% | 372 | 90.0 | 4.9 | 287 |
| any_jumps | 65% | 388 | 90.0 | 4.9 | 290 |

- roads vs none: only roads arrived 8, only none arrived 8; both arrived 142, roads cheaper in 15, dearer in 117
- relabel vs none: only relabel arrived 29, only none arrived 10; both arrived 140, relabel cheaper in 15, dearer in 114
- random vs none: only random arrived 22, only none arrived 6; both arrived 144, random cheaper in 9, dearer in 131
- hub_jumps vs none: only hub_jumps arrived 72, only none arrived 22; both arrived 128, hub_jumps cheaper in 34, dearer in 87
- any_jumps vs none: only any_jumps arrived 70, only none arrived 26; both arrived 124, any_jumps cheaper in 27, dearer in 95

### known_targets (300 pairs)

| trails | arrived | mean cost | median reads (arrived) | mean moves (arrived) | trail-only commits |
|---|---|---|---|---|---|
| none | 47% | 514 | 72.0 | 5.9 | 0 |
| roads | 47% | 519 | 79.0 | 5.5 | 178 |
| relabel | 54% | 458 | 78.0 | 5.4 | 102 |
| random | 51% | 488 | 81.0 | 5.9 | 75 |
| hub_jumps | 62% | 407 | 84.0 | 4.4 | 280 |
| any_jumps | 59% | 435 | 90.0 | 4.9 | 254 |

- roads vs none: only roads arrived 8, only none arrived 8; both arrived 133, roads cheaper in 36, dearer in 97
- relabel vs none: only relabel arrived 27, only none arrived 5; both arrived 136, relabel cheaper in 26, dearer in 110
- random vs none: only random arrived 18, only none arrived 7; both arrived 134, random cheaper in 9, dearer in 121
- hub_jumps vs none: only hub_jumps arrived 66, only none arrived 22; both arrived 119, hub_jumps cheaper in 43, dearer in 69
- any_jumps vs none: only any_jumps arrived 58, only none arrived 22; both arrived 119, any_jumps cheaper in 27, dearer in 88

## Door census

Words inside arrived paths (loops cut), most frequent first. Full list in `doors.txt`.

stated 42, frequency 39, longitude 37, relationship 36, requirements 28, sql 25, Excel 25, repeat 24, limitation 22, modify 22, crowd 21, predictions 21, temperature 20, required 19, told 19, jury 19, translate 17, conf 16, religion 16, null 16, different 16, court 16, undefined 16, governor 15, movements 15, inserted 15, repeated 15, similar 15, processor 14, removed 14, joke 14, payment 14, prov 13, cpu 13, director 13, course 13, Response 13, direction 13, such 12, attended 12, responsibility 11, attribute 11, declared 11, association 11, payments 11, deleted 11, replaced 11, profession 11, contained 11, which 10, squad 10, subscription 10, encode 10, debate 10, connected 10, position 10, voltage 10, write 10, annotation 10, grade 10

## Strongest trails

said–stated 18.9, longitude–latitude 16.7, relationship–relation 15.2, frequency–longitude 13.9, intel–Excel 12.1, sql–Excel 11.8, modify–rewrite 10.9, same–repeat 10.2, requirement–limitation 9.9, predictions–measurements 9.7, said–told 9.2, crowd–crew 8.2, required–requirement 7.8, judge–jury 7.7, conf–prof 7.6, judge–governor 7.1, undefined–nullptr 7.1, repeated–repeat 6.8, direction–frequency 6.7, court–crowd 6.5, requirements–responses 6.4, jury–joke 6.3, attached–inserted 6.1, attached–attended 6.1, undefined–deleted 6.0, temperature–latitude 6.0, null–nullptr 5.9, same–different 5.9, director–governor 5.9, same–similar 5.8, course–court 5.5, translate–rewrite 5.5, connected–attached 5.3, payments–predictions 5.3, stated–declared 5.2, relation–religion 5.2, sql–cpu 5.1, removed–deleted 5.0, attached–contained 4.8, profession–relation 4.8

Ran in 648s on CPU.
