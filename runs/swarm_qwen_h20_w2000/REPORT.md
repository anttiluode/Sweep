# Swarm on bank.json:Qwen/Qwen3-1.7B L14 128 PCs

2000 hidden-target walkers, one after another, horizon 20, 150 beats each (900 sweep reads), trails read k=6 per anchor, evaporation 0.001 per walker, seed 0. Each walker seeks a random word. Explore mode: descriptive only.

## While laying trails

| walkers | arrived | mean cost (reads) | trail-only commits | trail edges |
|---|---|---|---|---|
| 200 | 46% | 525 | 4 | 548 |
| 400 | 52% | 481 | 12 | 1158 |
| 600 | 49% | 498 | 19 | 1661 |
| 800 | 54% | 460 | 35 | 2221 |
| 1000 | 50% | 488 | 47 | 2694 |
| 1200 | 45% | 539 | 52 | 3153 |
| 1400 | 49% | 505 | 48 | 3628 |
| 1600 | 48% | 518 | 44 | 4117 |
| 1800 | 50% | 500 | 59 | 4570 |
| 2000 | 57% | 442 | 69 | 5082 |

Each block of 200 is a different set of random pairs, so this curve mixes pair difficulty with trail growth; the test below holds the pairs fixed.

Trail graph: 5082 edges over 3546 words. 533 edges (10%) join words outside each other's 20-word horizon (tunnels); median edge cosine 0.528 (map: 20th-neighbour cosine 0.466).

## Fresh pairs, same seed, six ways

Cost counts every read, trail reads included; a walker that never arrives costs the whole budget.

### fresh_pairs (300 pairs)

| trails | arrived | mean cost | median reads (arrived) | mean moves (arrived) | trail-only commits |
|---|---|---|---|---|---|
| none | 43% | 544 | 78.0 | 5.9 | 0 |
| roads | 47% | 523 | 84.0 | 5.7 | 108 |
| relabel | 56% | 443 | 81.0 | 5.2 | 170 |
| random | 53% | 468 | 78.0 | 5.5 | 139 |
| hub_jumps | 66% | 375 | 90.0 | 4.8 | 292 |
| any_jumps | 60% | 424 | 90.0 | 4.9 | 266 |

- roads vs none: only roads arrived 22, only none arrived 11; both arrived 119, roads cheaper in 15, dearer in 103
- relabel vs none: only relabel arrived 53, only none arrived 14; both arrived 116, relabel cheaper in 28, dearer in 86
- random vs none: only random arrived 40, only none arrived 11; both arrived 119, random cheaper in 20, dearer in 99
- hub_jumps vs none: only hub_jumps arrived 84, only none arrived 16; both arrived 114, hub_jumps cheaper in 27, dearer in 82
- any_jumps vs none: only any_jumps arrived 70, only none arrived 19; both arrived 111, any_jumps cheaper in 28, dearer in 78

### fresh_words (300 pairs)

| trails | arrived | mean cost | median reads (arrived) | mean moves (arrived) | trail-only commits |
|---|---|---|---|---|---|
| none | 47% | 515 | 72.0 | 5.6 | 0 |
| roads | 49% | 506 | 82.0 | 5.6 | 92 |
| relabel | 56% | 445 | 76.0 | 5.2 | 131 |
| random | 53% | 470 | 76.5 | 5.4 | 98 |
| hub_jumps | 63% | 403 | 90.0 | 4.8 | 269 |
| any_jumps | 60% | 422 | 90.0 | 4.7 | 267 |

- roads vs none: only roads arrived 15, only none arrived 8; both arrived 132, roads cheaper in 10, dearer in 117
- relabel vs none: only relabel arrived 42, only none arrived 14; both arrived 126, relabel cheaper in 16, dearer in 106
- random vs none: only random arrived 26, only none arrived 8; both arrived 132, random cheaper in 20, dearer in 111
- hub_jumps vs none: only hub_jumps arrived 66, only none arrived 18; both arrived 122, hub_jumps cheaper in 24, dearer in 92
- any_jumps vs none: only any_jumps arrived 68, only none arrived 27; both arrived 113, any_jumps cheaper in 19, dearer in 89

## Door census

Words inside arrived paths (loops cut), most frequent first. Full list in `doors.txt`.

contribution 9, accompl 8, competition 8, discussion 8, employee 7, restaurant 7, announcement 7, walking 7, characteristics 7, impressive 7, describes 7, efficiency 6, leader 6, reached 6, wallet 6, contributions 6, creates 6, explanation 6, engine 6, programs 6, reach 6, violence 6, government 6, prediction 6, meetings 6, observed 6, traffic 6, employ 6, driving 6, innovative 6, appointment 6, procedure 6, frame 5, reporter 5, processes 5, requires 5, survive 5, suffered 5, obvious 5, appropriate 5, expanded 5, industrial 5, bars 5, boards 5, subsequent 5, destroyed 5, integrated 5, belief 5, challenging 5, reported 5, consumption 5, invest 5, intention 5, endorse 5, teacher 5, infrastructure 5, establishment 5, calculation 5, meeting 5, registration 5

## Strongest trails

describes–characteristics 2.6, transform–transf 2.4, website–database 2.3, distributed–distribution 2.2, email–emails 2.2, engine–engines 2.1, programs–engines 2.1, nations–populations 2.1, competition–competitive 2.1, constraint–barrier 2.0, purchased–supplied 2.0, parameters–variables 2.0, excited–angry 2.0, society–humanity 1.9, contribution–contributions 1.9, diseases–industries 1.9, represents–describes 1.9, victory–winner 1.8, challenge–challenging 1.8, schema–scheme 1.8, strip–bars 1.7, method–procedure 1.7, consequ–accompl 1.7, specifically–specify 1.7, virt–rit 1.7, subsequ–subsequent 1.7, easy–efficient 1.7, consum–consumption 1.7, land–farm 1.7, maximum–limited 1.7, debt–belief 1.7, fear–belief 1.7, rout–rit 1.7, features–characteristics 1.6, traff–traffic 1.6, excited–inspired 1.6, fight–hurt 1.6, distributed–demonstrated 1.6, aut–alt 1.6, writing–writer 1.6

Ran in 512s on CPU.
