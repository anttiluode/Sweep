"""Build the map Sweep walks: one word state per word, read from a frozen LM.

Each word is read in Theory's plain few-shot frame ("Item: oak. Is it?"), at the word's
token, so the states match Theory's iris/ocular runs. Saved: the middle layer (ocular's
selection layer) plus the quarter and three-quarter layers, for later sweeps across depth.

Run (on the GPU, a few minutes):
    python bank.py --model EleutherAI/pythia-410m --device cuda
    python bank.py --model Qwen/Qwen3-1.7B --device cuda --batch 8
Output: banks/<model>.npz  (words, L<k> arrays in float16, default_layer, centered)
"""
import argparse
import re
from pathlib import Path

import numpy as np
import torch

# Theory's few-shot frame (common.SHOTS), unchanged
SHOTS = ("Item: rose. Is it a flower? yes\n"
         "Item: lion. Is it a fish? no\n"
         "Item: chair. Is it a tool? no\n"
         "Item: wolf. Is it an animal? yes\n"
         "Item: cup. Is it a cup? yes\n"
         "Item: lion. Is it a tiger? no\n")
# Theory's concept tree words, so Sweep can start on them
THEORY = ("oak maple pine elm cedar birch willow spruce carrot potato onion cabbage lettuce cucumber "
          "garlic turnip eagle owl crow pigeon duck sparrow parrot swan salmon shark trout tuna cod carp "
          "herring eel ant bee beetle butterfly mosquito moth wasp termite hammer wrench drill shovel axe "
          "rake chisel spade car bus truck bicycle train tractor van taxi guitar piano violin drum flute "
          "trumpet harp cello").split()
# the oak-is-also-firewood neighbourhood, for pursuit targets
EXTRA = ("tree wood firewood lumber fire smoke heat sauna stove fireplace forest leaf door furniture table "
         "weapon music song river ocean winter summer").split()


def prompt(word):
    text = SHOTS + f"Item: {word}. Is it?"
    ws = text.rindex("Item: " + word + ".") + len("Item: ")
    return text, ws, ws + len(word)


def locate(tok, word):
    """(input ids, position of the word's last token, n tokens of the word)."""
    text, ws, we = prompt(word)
    enc = tok(text, add_special_tokens=False, return_offsets_mapping=True)
    hit = [i for i, (a, b) in enumerate(enc["offset_mapping"]) if a < we and b > ws]
    if not hit:
        return None
    return enc["input_ids"], hit[-1], len(hit)


def generic_words(tok, n, taken):
    """Ocular's pool: single-token words, 3+ letters, lowercase or title case, in vocab order."""
    vocab = sorted(tok.get_vocab().items(), key=lambda kv: kv[1])
    out, seen = [], set(w.lower() for w in taken)
    for t, _ in vocab:
        if t[:1] not in ("Ġ", "▁"):
            continue
        w = t[1:]
        if len(w) < 3 or not w.isalpha() or not (w.islower() or w.istitle()) or w.lower() in seen:
            continue
        loc = locate(tok, w)
        if loc is None or loc[2] != 1:
            continue
        seen.add(w.lower())
        out.append(w)
        if len(out) >= n:
            break
    return out


@torch.no_grad()
def capture(model, tok, words, layers, device, batch, log=print):
    """{layer: array [n_words, d]} of hidden states at each word's (last) token."""
    items = [(w, *locate(tok, w)) for w in words]
    by_len = {}
    for j, (w, ids, pos, _) in enumerate(items):
        by_len.setdefault(len(ids), []).append(j)
    out = {l: [None] * len(words) for l in layers}
    done = 0
    for L, idx in by_len.items():
        for s0 in range(0, len(idx), batch):
            chunk = idx[s0:s0 + batch]
            x = torch.tensor([items[j][1] for j in chunk], device=device)
            hs = model(input_ids=x, output_hidden_states=True).hidden_states
            for l in layers:
                h = hs[l + 1]                      # row l+1 = output of layer l (Theory's convention)
                for b, j in enumerate(chunk):
                    out[l][j] = h[b, items[j][2]].float().cpu().numpy()
            done += len(chunk)
            if done % (batch * 50) < batch:
                log(f"  states {done}/{len(words)}")
    return {l: np.stack(v) for l, v in out.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="EleutherAI/pythia-410m")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--n", type=int, default=8000, help="generic words added after Theory's and the extras")
    ap.add_argument("--extra", default="", help="comma-separated words to include (multi-token allowed: last token)")
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--dtype", default="float32", choices=["float32", "float16", "bfloat16"])
    ap.add_argument("--revision", default=None, help="a training checkpoint, e.g. step1000 for Pythia")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    load_and_build(a.model, a.device, a.n, a.extra, a.batch, a.dtype, a.revision, a.out)


def load_and_build(model_name, device, n=8000, extra="", batch=32, dtype="float32", revision=None, out=None,
                   log=print):

    from transformers import AutoModelForCausalLM, AutoTokenizer
    kw = {"revision": revision} if revision else {}
    tok = AutoTokenizer.from_pretrained(model_name, **kw)
    dt = getattr(torch, dtype)
    try:
        model = AutoModelForCausalLM.from_pretrained(model_name, dtype=dt, **kw)
    except TypeError:
        model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=dt, **kw)
    model = model.to(device).eval()
    name = model_name + (f"@{revision}" if revision else "")
    path = build(model, tok, name, device, n, EXTRA + [w.strip() for w in extra.split(",") if w.strip()],
                 batch, out, log)
    del model
    if device.startswith("cuda"):
        torch.cuda.empty_cache()
    return path


def build(model, tok, name, device, n, extra, batch, out=None, log=print):
    n_layers = model.config.num_hidden_layers
    layers = sorted({n_layers // 4, n_layers // 2, (3 * n_layers) // 4})
    centered = not any("RMSNorm" in type(m).__name__ for m in model.modules())
    fixed, multi = [], []
    for w in dict.fromkeys(THEORY + extra):
        loc = locate(tok, w)
        if loc is None:
            continue
        fixed.append(w)
        if loc[2] > 1:
            multi.append(w)
    words = fixed + generic_words(tok, n, fixed)
    log(f"{name}: {len(words)} words ({len(fixed)} fixed, {len(multi)} read at their last token: "
        f"{', '.join(multi[:12])}{'...' if len(multi) > 12 else ''}); layers {layers}; "
        f"{'LayerNorm (centred)' if centered else 'RMSNorm'}")
    S = capture(model, tok, words, layers, device, batch, log)
    out = Path(out or f"banks/{re.sub(r'[^A-Za-z0-9.]+', '-', name.split('/')[-1]).lower()}.npz")
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, words=np.array(words), default_layer=f"L{n_layers // 2}", centered=centered,
                        multi=np.array(multi), model=name,
                        **{f"L{l}": (S[l].astype(np.float16) if np.abs(S[l]).max() < 6e4 else S[l])
                           for l in layers})
    log(f"wrote {out}")
    return out


if __name__ == "__main__":
    main()
