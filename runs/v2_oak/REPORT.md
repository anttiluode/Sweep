# Sweep run: v2_oak

bank `bank.json:Qwen/Qwen3-1.7B L14 128 PCs`, mode `forage`, 300 beats, 1800 reads

## Anchor path

oak -> Oak -> Wood -> wood -> metal -> plastic -> artificial -> automatic -> manual -> Manual -> Internal -> external -> extern -> extrem -> extr -> intr -> inst -> Inst -> Ins -> Enc -> enc -> rec -> Rec -> Reg -> reg -> res -> pres -> Pres -> Sup -> sup -> sub -> subs -> vars -> var -> val -> Val -> Wil -> Gil -> Ken -> Ben -> Bob -> Mike -> Peter -> Thomas -> Charles -> Johnson -> Jackson -> Jack -> Frank -> Paul -> Sarah -> Sam -> sam -> tom -> tod -> tid -> wid -> wis -> Wis -> Vis -> Ver -> Ter -> ter -> per -> ber -> cer -> ser -> ele -> fle -> ble -> spl -> scr -> shr -> bur -> bul -> Bul -> Sil -> sil -> fil -> fol -> flo -> gro -> Gro -> Bro -> Bre -> Tre -> Spe -> Spi -> Tra -> Tri -> Tur -> Terr -> Trib -> Nob -> nob -> nov -> Nov -> Jul -> Jud -> jud -> jur -> zur -> zum -> hun -> Hun -> Han -> Dan -> dan -> ben -> dem -> der -> ther -> fer -> mer -> rem -> reg -> deg -> enh -> emph -> emphas -> estim -> optim -> opt -> apt -> pert -> pers -> Pers -> Pres -> Pre -> pre -> fre -> fri -> pri -> priv -> prov -> proven -> reven -> reve -> surve -> surv -> surg -> emerg -> Emer -> Dem -> Tem -> tem -> ter -> terr -> Terr -> Mort -> mort

## Same number of moves, reference walks (descriptive, not gates)

| walk | moves | distinct anchors | revisits | regions touched | mean step cosine |
|---|---:|---:|---:|---:|---:|
| sweep | 150 | 147 | 4 | 21 | 0.667 |
| greedy nearest | 150 | 2 | 149 | 2 | 0.843 |
| random of 10 nearest | 150 | 125 | 26 | 21 | 0.6 |

- gate0: {'sides_alternate': '1.00 of beats switch side', 'grain_changes_reads': '16/16 probes read differently across grains; e.g. top8:nude / top16:date / b4_32:pine / top64:maple / full:maple', 'coverage_repels': 'distinct reads 118 with trace, 1 without'}
- grain use: {'b4_32': 74, 'top64': 94, 'full': 76, 'top16': 40, 'top8': 16}
