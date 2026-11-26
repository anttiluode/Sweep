# Sweep run: sol_bank_forage_oak

bank `bank.json:Qwen/Qwen3-1.7B L14 128 PCs`, mode `forage`, 300 beats, 1800 reads

## Anchor path

oak -> Oak -> Wood -> wood -> metal -> plastic -> artificial -> automatic -> manual -> Manual -> Internal -> external -> extern -> extrem -> extr -> intr -> inst -> Inst -> Ins -> Exp -> Expl -> Pract -> pract -> exerc -> exc -> conc -> concent -> concentr -> integr -> indic -> signific -> significant -> substantial -> massive -> huge -> bigger -> smaller -> small -> short -> Short -> Long -> Big -> Black -> black -> dark -> bright -> brilliant -> excellent -> awesome -> fantastic -> fantasy -> magic -> Magic -> Smart -> smart -> stupid -> crazy -> lazy -> sad -> glad -> hope -> Hope -> Love -> loves -> likes -> like -> unlike -> whereas -> although -> because -> since -> hence -> Therefore -> Then -> And -> and -> but -> pero -> untuk -> dengan -> como -> cada -> pued -> fue -> vie -> qui -> que -> che -> ble -> blo -> gro -> Gro -> Bru -> Bur -> Ber -> Mer -> mer -> ser -> cur -> mur -> mus -> Mus -> Mos -> Cos -> Col -> Del -> del -> der -> dar -> har -> hal -> Hal -> Hol -> Hon -> hon -> bon -> kon -> kom -> tok -> Tok -> Nik -> Nic -> Luc -> Lou -> Dou -> Dur -> dur -> dut -> tut -> tum -> trem -> stre -> ster -> ter -> Ter -> Tem -> Sem -> sem -> dem -> deg -> dec -> Dec -> Aug -> aug -> aut -> autom -> Autom -> Activ -> Adv -> adv -> adj

## Same number of moves, reference walks (descriptive, not gates)

| walk | moves | distinct anchors | revisits | regions touched | mean step cosine |
|---|---:|---:|---:|---:|---:|
| sweep | 150 | 151 | 0 | 31 | 0.659 |
| greedy nearest | 150 | 2 | 149 | 2 | 0.843 |
| random of 10 nearest | 150 | 125 | 26 | 21 | 0.6 |

- gate0: {'sides_alternate': '1.00 of beats switch side', 'grain_changes_reads': '16/16 probes read differently across grains; e.g. top8:nude / top16:date / b4_32:pine / top64:maple / full:maple', 'coverage_repels': 'distinct reads 118 with trace, 1 without'}
- grain use: {'b4_32': 2, 'top64': 2, 'full': 296}
