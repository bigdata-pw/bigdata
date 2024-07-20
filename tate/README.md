# Tate

## MongoDB

Uses database `tate`.

Artwork script creates collection `images`.

## Usage

- Install `requirements.txt`
- Fill MongoDB uri
- Run script

## Notes

- Endpoint is very slow, expect 7-10s per offset.
- All fields present with the addition of `image` which is the largest size available taken from `master_images`.
