# Unlock on bank.json:Qwen/Qwen3-1.7B L14 128 PCs

Conjunction of two cues = unit(a + b) in the centred full space; k = 20. 6000 pairs (4000 random, 2000 a word with one of its 50 nearest), binned by the cues' own cosine. Explore mode: descriptive only.

| cue cosine | pairs | unlocked of 20 | median depth (better single-cue rank) | relation to both (min cosine) | package (mean pairwise cosine) |
|---|---|---|---|---|---|
| -0.34 to -0.07 | 1000 | 10.4 | 80 | 0.142 | 0.287 |
| -0.07 to +0.01 | 1000 | 9.8 | 66 | 0.198 | 0.305 |
| +0.01 to +0.11 | 1000 | 8.9 | 52 | 0.249 | 0.333 |
| +0.11 to +0.34 | 1000 | 7.0 | 38 | 0.311 | 0.357 |
| +0.34 to +0.45 | 1000 | 3.5 | 27 | 0.379 | 0.361 |
| +0.45 to +0.86 | 1000 | 2.4 | 25 | 0.433 | 0.398 |

Controls: a cue plus a random unit direction unlocks 10.0 of 20, median depth 56, package 0.308. A single cue's own 20 nearest: package 0.364. Twenty random words: package 0.000. Map: 20th-neighbour cosine 0.466.

Sinks: over all pairs, 41961 unlocked words, 6169 distinct; the 20 most frequent are 1.4% of them (encouraged 33, expectations 32, predictions 31, decisions 30, significantly 29, conspir 29, effective 29, database 28).

## Examples

Unlocked words (in the conjunction's 20 nearest, in neither cue's 20 nearest), closest first, with the median depth behind the single cues. Grains are PCA windows (Maatuska): the conjunction is formed and read in that window.

**bird+shadow** (cue cosine 0.32)

- top16: bean  (median depth 23)
- top64: star, island, bone, arrow, child, alien  (median depth 27)
- full: star, island, bone, arrow  (median depth 30)

**bird+winter** (cue cosine 0.29)

- top16: moon, forest, river, mountain, sun, garden, grass, lake, island, hair, water, farm, star  (median depth 45)
- top64: river, mountain, star, sky, forest, moon, island  (median depth 26)
- full: sky, star, forest, river, rain, beach, mountain, city  (median depth 39)

**shadow+winter** (cue cosine 0.19)

- top16: moon, mountain, storm, air, sun, wind, grass, river, death  (median depth 38)
- top64: moon, storm, star, day, stars, island  (median depth 32)
- full: storm, mountain, ocean, sun, moon, forest, star, day, stars, death, river  (median depth 33)

**sun+low** (cue cosine 0.07)

- top16: blue, top, eight, date, east, far, hip, five, night  (median depth 50)
- top64: well, sol, light, top, hot, out, south  (median depth 62)
- full: light, sol, top, well, south  (median depth 27)

**shadow+sun** (cue cosine 0.40)

- top16: head  (median depth 24)
- top64: island, eye  (median depth 25)
- full: light  (median depth 21)

**bird+shadow+winter** (cue cosine 0.32, 0.29, 0.19)

- top16: moon, mountain, sun, grass, lake, star, river  (median depth 48)
- top64: star, moon, island, river, storm, stars, child  (median depth 27)
- full: star, mountain, storm, sun, moon, island, forest, river, ocean, wing  (median depth 29)

**bird+shadow+evening** (cue cosine 0.32, 0.12, 0.12)

- top16: mountain, moon, earth, ocean, sky, sun, head, grass, wall, river, forest  (median depth 52)
- top64: moon, island, snow, storm, river, beach, eye, ocean, star  (median depth 27)
- full: moon, storm, island, beach, star, eye, mountain, forest, river  (median depth 33)

**bird+love** (cue cosine 0.06)

- top16: hair, heart, brain, money, eye, god, blood, nose, face, mouth, milk, boy, child, sky  (median depth 90)
- top64: god, heart, moon, brain, boy, hair, wind, eye, blood, voice, friend, fruit, God  (median depth 50)
- full: wind, moon, heart, god, voice, cloud, eye, sky, girl, hair, fire  (median depth 68)

**shadow+memory** (cue cosine 0.30)

- top16: letter, voice, atom, reflection, image, flavor  (median depth 64)
- top64: voice, thoughts, thought, eye  (median depth 38)
- full: heart, voice, signature, thought, thoughts  (median depth 56)

**corner+light** (cue cosine 0.08)

- top16: path, circle, cloud, height, cross, mountain, arm, hour, field  (median depth 36)
- top64: line, mountain, finger, road, floor, wall, window, grid, foot, wheel, star, gear  (median depth 56)
- full: line, window, finger, mountain, direction, head, road, foot, tower, height, layer  (median depth 41)

**oak+guitar** (cue cosine 0.33)

- top16: bread, lettuce, iron, sword, mouse  (median depth 33)
- top64: diamond, carrot, bread  (median depth 28)
- full: diamond, cabinet, desk, poker  (median depth 30)

**fire+water** (cue cosine 0.57)

- top16: (nothing new)
- top64: (nothing new)
- full: power  (median depth 23)

**winter+home** (cue cosine 0.23)

- top16: river, holiday, space, year  (median depth 25)
- top64: forest, sky, world, day, city, moon, mountain  (median depth 31)
- full: forest, outdoor, sky, outside  (median depth 30)

