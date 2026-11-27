#!/bin/sh
# Compiles audio.cpp's Chatterbox text tokenizer on its own, with the few
# sources it needs, around tokenize_main.cpp. No ggml, no model, no cmake.
#
# Usage: build.sh <audio.cpp source tree> <output binary>
set -eu
SRC="${1:?usage: build.sh <audio.cpp source tree> <output binary>}"
OUT="${2:?usage: build.sh <audio.cpp source tree> <output binary>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
CC="${CC:-cc}"
CXX="${CXX:-c++}"
obj="$(mktemp -d)"
trap 'rm -rf "$obj"' EXIT
"$CC" -O2 -c "$SRC/external/cJSON/cJSON.c" -o "$obj/cJSON.o"
"$CXX" -std=c++17 -O2 \
    -I"$SRC/include" \
    -I"$SRC/external/llama_tokenizer" \
    -I"$SRC/external/cJSON" \
    -I"$SRC/src/framework/text" \
    "$HERE/tokenize_main.cpp" \
    "$SRC/src/models/chatterbox/text_tokenizer.cpp" \
    "$SRC/src/framework/io/json.cpp" \
    "$SRC/src/framework/io/filesystem.cpp" \
    "$SRC/src/framework/text/unicode_normalization.cpp" \
    "$SRC/external/llama_tokenizer/unicode.cpp" \
    "$SRC/external/llama_tokenizer/unicode-data.cpp" \
    "$obj/cJSON.o" \
    -o "$OUT"
