"""Token parity: audio.cpp's patched Chatterbox tokenizer against upstream's Python.

Runs upstream Chatterbox's own `MTLTokenizer` (src/chatterbox/models/tokenizers/
tokenizer.py, loaded by path) and the C++ driver built by build.sh over the same
lines, and fails on the first line whose token ids differ.

The upstream module imports torch and huggingface_hub at module level, for
tensors and downloads the tokenizer never needs here. Both are stubbed, and
neither stub touches text: `torch` only wraps ids into a tensor (we call
`encode`, which returns a plain list), and `hf_hub_download` returns the
pinned local Cangjie5_TC.json. pkuseg is blocked so the converter takes the
same no-segmentation path audio.cpp does (upstream logs a warning and skips
segmentation when it is absent).

Besides lines.tsv, every character Cangjie5_TC.json lists is tokenized as
`zh`, a few hundred to a line, so the whole mapping (and which characters
count as letters) is compared, not just the sample sentences.

Usage: compare.py <upstream tokenizer.py> <tokenizer json> <Cangjie5_TC.json>
                  <lines.tsv> <tokenize_main binary>
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import types

KEYS_PER_LINE = 400


def load_upstream(tokenizer_py, cangjie_path):
    torch = types.ModuleType("torch")

    class _Tensor:  # never reached by encode(); present so the import resolves
        pass

    torch.Tensor = _Tensor
    torch.IntTensor = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("torch stub"))
    sys.modules["torch"] = torch

    hub = types.ModuleType("huggingface_hub")
    hub.hf_hub_download = lambda *a, **k: cangjie_path
    sys.modules["huggingface_hub"] = hub

    # `from spacy_pkuseg import pkuseg` raises ImportError on a None entry.
    sys.modules["spacy_pkuseg"] = None

    spec = importlib.util.spec_from_file_location("upstream_chatterbox_tokenizer", tokenizer_py)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv):
    if len(argv) != 6:
        print(__doc__, file=sys.stderr)
        return 2
    tokenizer_py, tokenizer_json, cangjie_path, lines_path, binary = argv[1:]

    upstream = load_upstream(tokenizer_py, cangjie_path)
    mtl = upstream.MTLTokenizer(tokenizer_json)
    if mtl.cangjie_converter.segmenter is not None:
        print("pkuseg was importable; parity is defined without it", file=sys.stderr)
        return 2
    if not mtl.cangjie_converter.word2cj:
        print("upstream did not load the Cangjie mapping", file=sys.stderr)
        return 2

    with open(lines_path, encoding="utf-8") as fp:
        lines = fp.read().splitlines()
    case_count = sum(1 for l in lines if l and not l.startswith("#") and "\t" in l)

    with open(cangjie_path, encoding="utf-8") as fp:
        keys = []
        seen = set()
        for entry in json.load(fp):
            word = entry.split("\t")[0]
            if word not in seen and "\t" not in word and "\n" not in word:
                seen.add(word)
                keys.append(word)
    for i in range(0, len(keys), KEYS_PER_LINE):
        lines.append("zh\t" + "".join(keys[i:i + KEYS_PER_LINE]))

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".tsv", delete=False) as tmp:
        tmp.write("\n".join(lines) + "\n")
        all_path = tmp.name

    cpp = subprocess.run(
        [binary, tokenizer_json, cangjie_path, all_path],
        check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout.splitlines()
    if len(cpp) != len(lines):
        print(f"C++ printed {len(cpp)} lines for {len(lines)} inputs", file=sys.stderr)
        return 1

    vocab = {v: k for k, v in mtl.tokenizer.get_vocab().items()}
    compared = 0
    for n, (line, got) in enumerate(zip(lines, cpp), start=1):
        if not line or line.startswith("#") or "\t" not in line:
            continue
        lang, text = line.split("\t", 1)
        want = mtl.encode(text, language_id=lang)
        have = [int(t) for t in got.split()]
        compared += 1
        if want != have:
            at = next((i for i, (a, b) in enumerate(zip(want, have)) if a != b), min(len(want), len(have)))
            lo = max(0, at - 5)
            print(f"MISMATCH line {n} ({lang}): {text[:80]!r}", file=sys.stderr)
            print(f"  first difference at token {at}; python {len(want)} ids, c++ {len(have)} ids", file=sys.stderr)
            print(f"  python: {[vocab.get(i, i) for i in want[lo:at + 5]]}", file=sys.stderr)
            print(f"  c++:    {[vocab.get(i, i) for i in have[lo:at + 5]]}", file=sys.stderr)
            return 1
        if n <= len(lines) and compared <= case_count:
            print(f"ok {lang} {len(want):4d} ids  {text[:60]}")

    print(f"parity: {compared} lines identical ({case_count} cases + {compared - case_count} "
          f"lines covering all {len(keys)} Cangjie characters)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
