# civicrecap/

This branch is upstream audio.cpp v0.9.6 (04a37f2e80ff2dbcdd84cc67848a970bd02a73e0) plus
`zh-cangjie.patch` (Mandarin for Chatterbox through upstream's Cangjie
encoding) and `en-multilingual.patch` (the session option
`chatterbox.english_t3=multilingual`, which reads English through the
multilingual T3 like every other language), built by `.github/workflows/civicrecap-release.yml` for CivicRecap's
narration. It is made by `infra/audiocpp/prepare-fork.sh` in the CivicRecap
repository, which is the source of truth for everything in this directory:
change it there and remake the branch, never edit it here.
