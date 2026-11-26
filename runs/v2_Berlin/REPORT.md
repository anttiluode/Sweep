# Sweep run: v2_Berlin

bank `bank.json:Qwen/Qwen3-1.7B L14 128 PCs`, mode `forage`, 300 beats, 1800 reads

## Anchor path

Berlin -> London -> Japan -> Germany -> England -> Australia -> Pennsylvania -> California -> Brazil -> Amazon -> Apache -> Oracle -> Icon -> icon -> logo -> label -> tag -> tags -> bags -> bag -> box -> Box -> Table -> Paper -> paper -> newspaper -> television -> telephone -> Phone -> Camera -> camera -> speaker -> speakers -> readers -> writers -> writes -> wrote -> talked -> walked -> walking -> running -> rolling -> floating -> falling -> falls -> breaks -> break -> turn -> Turn -> Put -> put -> get -> find -> Find -> Write -> Use -> Have -> Are -> How -> When -> Where -> Here -> there -> here -> from -> From -> According -> according -> depending -> depends -> therefore -> hence -> indeed -> certainly -> clearly -> deeply -> heavily -> heavy -> thick -> thin -> narrow -> wider -> bigger -> biggest -> greatest -> great -> grand -> Grand -> Bon -> Hon -> hon -> hor -> mar -> par -> gar -> Gar -> Ger -> Sem -> Tem -> Sen -> San -> Van -> Pan -> pan -> pot -> Pot -> Mat -> Hat -> Bag -> bag -> box -> boxes -> cases -> packages -> packet -> pack -> patch -> padding -> binding -> bind -> bund -> batt -> att -> aff -> Aff -> Acc -> App -> Rep -> Rem -> rem -> dem -> ben -> dan -> kan -> kon -> con -> cor -> por -> pou -> mur -> vul -> vill -> polic -> offic -> occ -> loc -> Loc -> Cur -> Cor -> Con

## Same number of moves, reference walks (descriptive, not gates)

| walk | moves | distinct anchors | revisits | regions touched | mean step cosine |
|---|---:|---:|---:|---:|---:|
| sweep | 149 | 148 | 2 | 35 | 0.667 |
| greedy nearest | 149 | 5 | 145 | 1 | 0.803 |
| random of 10 nearest | 149 | 67 | 83 | 2 | 0.702 |

- gate0: {'sides_alternate': '1.00 of beats switch side', 'grain_changes_reads': '15/16 probes read differently across grains; e.g. top8:Jackson / top16:Brazil / b4_32:California / top64:Brazil / full:German', 'coverage_repels': 'distinct reads 104 with trace, 2 without'}
- grain use: {'b4_32': 66, 'top64': 98, 'top16': 42, 'top8': 36, 'full': 58}
