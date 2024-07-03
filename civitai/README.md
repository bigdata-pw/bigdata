# Civitai

Civitai API -> MongoDB

## MongoDB

This script uses database `civitai` and creates collections `lora`, `checkpoint`, `textual_inversion`, `hypernetwork`, `aesthetic_gradient`, `controlnet`, `poses`.

## Usage

- Install `requirements.txt`
- Fill MongoDB uri
- Choose `sort`, `period` and `limit`, by default `Oldest`, `AllTime`, `100`
- Call `get_models`, by default `get_models` is called for all model types

## Notes

Existing ids are retrieved from each collection to avoid duplicates.
