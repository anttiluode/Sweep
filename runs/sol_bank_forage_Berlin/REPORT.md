# Sweep run: sol_bank_forage_Berlin

bank `bank.json:Qwen/Qwen3-1.7B L14 128 PCs`, mode `forage`, 200 beats, 1200 reads

## Anchor path

Berlin -> London -> England -> Spain -> Asia -> Asian -> American -> Americans -> Muslims -> Muslim -> Catholic -> Korean -> Greek -> Egypt -> Empire -> Kingdom -> Domain -> domain -> region -> regions -> sections -> portions -> portion -> proportion -> fraction -> integer -> boolean -> bool -> nil -> null -> Invalid -> invalid -> valid -> validate -> evaluate -> investigate -> investigation -> research -> Research -> Search -> Check -> Close -> close -> open -> opens -> holds -> held -> carried -> carrying -> bringing -> brings -> comes -> came -> became -> become -> appear -> occur -> involve -> involving -> featuring -> featured -> displayed -> displays -> designs -> design -> designer -> classic -> Classic -> Standard -> standard -> regular -> normal -> natural -> Natural -> Nature -> Environment -> environment -> atmosphere -> atmos -> circum -> circ -> inc -> ins -> Ins -> Inf -> Int -> int -> ext -> extr -> expl -> Expl -> Enc -> Con -> Col -> Del -> del -> mel -> mol -> vol -> Vol -> Ver

## Same number of moves, reference walks (descriptive, not gates)

| walk | moves | distinct anchors | revisits | regions touched | mean step cosine |
|---|---:|---:|---:|---:|---:|
| sweep | 100 | 101 | 0 | 31 | 0.66 |
| greedy nearest | 100 | 5 | 96 | 1 | 0.802 |
| random of 10 nearest | 100 | 51 | 50 | 2 | 0.702 |

- gate0: {'sides_alternate': '1.00 of beats switch side', 'grain_changes_reads': '15/16 probes read differently across grains; e.g. top8:Jackson / top16:Brazil / b4_32:California / top64:Brazil / full:German', 'coverage_repels': 'distinct reads 104 with trace, 2 without'}
- grain use: {'b4_32': 2, 'top64': 2, 'full': 196}
