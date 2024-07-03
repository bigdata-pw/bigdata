# Civitai

Civitai API -> MongoDB

## MongoDB

Uses database `civitai`.

Models script creates collections `lora`, `checkpoint`, `textual_inversion`, `hypernetwork`, `aesthetic_gradient`, `controlnet`, `poses`.

Images script creates collection `images`.

## Usage (models)

- Install `requirements.txt`
- Fill MongoDB uri
- Choose `sort`, `period` and `limit`, by default `Oldest`, `AllTime`, `100`
- Call `get_models`, by default `get_models` is called for all model types

## Usage (images)

- Install `requirements.txt`
- Fill MongoDB uri
- Choose `sort`, `period` and `limit`, by default `Newest`, `AllTime`, `100`
- Call `get_images`

## Notes

Existing ids are retrieved from each collection to avoid duplicates.
