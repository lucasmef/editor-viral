#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p .runtime/models/whisper-small
curl -fL --retry 2 --max-time 180 'https://huggingface.co/mlx-community/whisper-small-mlx/resolve/main/weights.npz' -o .runtime/models/whisper-small/weights.npz
curl -fL --retry 2 --max-time 30 'https://huggingface.co/mlx-community/whisper-small-mlx/resolve/main/config.json' -o .runtime/models/whisper-small/config.json
