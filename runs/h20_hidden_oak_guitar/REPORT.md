# Sweep run: h20_hidden_oak_guitar

bank `bank.json:Qwen/Qwen3-1.7B L14 128 PCs`, mode `hidden`, 10 beats, 60 reads

## Anchor path

oak -> coal -> coin -> pen -> knife -> guitar

- gate0: {'sides_alternate': '1.00 of beats switch side', 'grain_changes_reads': '16/16 probes read differently across grains; e.g. top8:nude / top16:date / b4_32:pine / top64:maple / full:maple', 'coverage_repels': 'distinct reads 118 with trace, 1 without', 'probe_leaves_heading': 'axis +1.57 rad while anchor stays on oak'}
- reads to first see target: 50
- reached target as anchor: True
- oracle hill-climb reads (sees all 10 neighbours' warmth): 40
