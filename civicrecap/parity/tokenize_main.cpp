// Prints audio.cpp's Chatterbox multilingual token ids for each input line, so
// compare.py can diff them against upstream Chatterbox's Python tokenizer.
//
// Usage: tokenize_main <tokenizer.json> <Cangjie5_TC.json> <lines.tsv>
// Each input line is "<language>\t<text>"; each output line is the ids,
// space-separated. Empty and '#' lines are echoed as empty output lines so
// the two sides stay aligned line for line.
#include "engine/models/chatterbox/text_tokenizer.h"

#include <fstream>
#include <iostream>
#include <string>

int main(int argc, char ** argv) {
    if (argc != 4) {
        std::cerr << "usage: tokenize_main <tokenizer.json> <Cangjie5_TC.json> <lines.tsv>\n";
        return 2;
    }
    using namespace engine::models::chatterbox;
    const auto tokenizer = load_chatterbox_english_tokenizer(argv[1], argv[2]);
    std::ifstream in(argv[3]);
    if (!in) {
        std::cerr << "cannot open " << argv[3] << "\n";
        return 2;
    }
    std::string line;
    while (std::getline(in, line)) {
        if (!line.empty() && line.back() == '\r') {
            line.pop_back();
        }
        const auto tab = line.find('\t');
        if (line.empty() || line[0] == '#' || tab == std::string::npos) {
            std::cout << "\n";
            continue;
        }
        const auto ids = encode_chatterbox_multilingual_text(*tokenizer, line.substr(tab + 1), line.substr(0, tab));
        for (size_t i = 0; i < ids.size(); ++i) {
            std::cout << (i ? " " : "") << ids[i];
        }
        std::cout << "\n";
    }
    return 0;
}
