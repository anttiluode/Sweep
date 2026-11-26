# Develop: step0, step512, step1000, step2000, step4000, step16000, step143000

Final map: pythia-410m-step143000:L12. 300 pairs chosen on the final map (targets outside the start's 50 nearest), the same on every checkpoint; horizon 20, 150 beats. Explore mode: descriptive only.

Arrived (each map navigated by its own warmth):

| map | plain | temp | hot | blind | temp: searches | temp: warmth calls |
|---|---|---|---|---|---|---|
| step0 | 31% | 93% | 90% | 9% | 270 | 200 |
| step512 | 28% | 74% | 74% | 6% | 384 | 162 |
| step1000 | 40% | 91% | 92% | 5% | 237 | 134 |
| step2000 | 53% | 96% | 96% | 10% | 168 | 112 |
| step4000 | 54% | 98% | 98% | 6% | 150 | 101 |
| step16000 | 58% | 98% | 98% | 9% | 152 | 102 |
| step143000 | 54% | 98% | 98% | 7% | 157 | 105 |

Steps judged by the final map: mean final-map cosine between consecutive anchors of arrived temp paths (random word pairs: 0.000).

| map | final-map step cosine | mean moves |
|---|---|---|
| step0 | 0.003 | 16.0 |
| step512 | 0.270 | 14.8 |
| step1000 | 0.369 | 12.7 |
| step2000 | 0.418 | 10.5 |
| step4000 | 0.441 | 9.8 |
| step16000 | 0.464 | 10.0 |
| step143000 | 0.484 | 10.5 |

Example temp paths on each map (first five pairs):

**step0**

- golf → motif → ure → increment → zone → abdom → challenged → dense → disclose → intr → payment → comparing → sod → revised …
- transmission → fetal → repeated → leaned → belong
- work → made → Willi → spray → barrier → snap → melt → sever → bomb → lock → sens
- amend → substantially → test → bicycle → restrictions → allowing → path → slice → thinking → coefficients → webs → preferably → tit → decl …
- moves → wand → weighted → James → landscape → hearts → worse → ideal → fight → hydroph → initi → animals → wrote → ent …

**step512**

- golf → dried → worn → burned → whispered → liked → acknowledged → realized → asserts → suggests → imply → assume → say → says …
- transmission → conversion → susceptibility → addition → refers → belong
- work → compete → incubated → fam → conc → contrad → innoc → acceler → elev → investig → conserv → evalu → communic → collabor …
- amend → challenge → apply → belongs → fails → easier → harder
- moves → drops → likes → resolve → verify → appreciate

**step1000**

- golf → hunting → fought → wounded → arrested → fired → attacked → killed → burned → worn → handled → validated → influenced → motivated …
- transmission → connectivity → interaction → fusion → attachment → damage → harm → danger → advantage → intention → intent → rights → behalf → wishes …
- work → works → stands → heads → arms → hands → bodies → particles → electrons → hydrogen → macrophages → nuclei → mutants → complexes …
- amend → restore → adapt → upgrade → backup → desktop → portable → expensive → nice → neat → quick → easier → harder
- moves → goes → comes → begins → began → begun → begin → fail → refuse → wants → deserve → appreciate

**step2000**

- golf → shopping → advertising → disclosure → information → insights → suggestions → thoughts → fears → worried
- transmission → transfer → transferred → deposited → buried → situated → lived → existed → exist → belong
- work → labor → administr → conjug → ven → vis → sens
- amend → changed → decreased → reduces → minimize → improve → strengthen → stronger → harder
- moves → goes → come → give → deny → acknowledge → appreciate

**step4000**

- golf → hunting → fighting → struggling → confused → surprised → scared → worried
- transmission → transmit → connect → bind → attach → refer → refers → corresponds → correspond → belong
- work → works → fits → likes → loves → fears → fear → shame → beauty → delight → revel → observ → spect → vit …
- amend → altered → improved → optimized → feasible → difficult → harder
- moves → move → proceed → continue → finish → achieve → accomplish → obtain → provide → include → exclude → eliminate → reject → accept …

**step16000**

- golf → sports → racing → fighting → struggling → wondering → curious → worried
- transmission → transmit → disclose → admit → believe → know → have → were → weren → haven → aren → are → have → want …
- work → works → comes → came → seemed → felt → feelings → fears → fear → desire → passion → spirit → sense → sens
- amend → improve → improved → increased → increasing → reducing → reduce → reduces → increases → varies → differ → different → differently → badly …
- moves → takes → needs → deserve → appreciate

**step143000**

- golf → gaming → playing → talking → thinking → wondering → worried
- transmission → transmit → contribute → belong
- work → labor → effort → eff → ess → ses → sus → soc → soci → situ → scen → sens
- amend → enhance → improved → better → worse → bigger → stronger → harder
- moves → move → remove → eliminate → evaluate → investigate → observe → acknowledge → appreciate

Ran in 3144s.
