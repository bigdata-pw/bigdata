# Gucci

## MongoDB

Uses database `gucci`.

Products script creates collections `products`.

## Usage

- Install `requirements.txt`
- Fill MongoDB uri
- Set `BASE_PATH`
- Change categories if required
- Run script

## Notes

- Product images are also downloaded.
- All fields are present with an added field `images` which combines and deduplicates images from `primaryImage`, `alternateGalleryImages`, `alternateImage`.
- Image style `DarkGray_Center_0_0_2400x2400` is the largest available, the component parts `DarkGray`, `Center`, `0`, `0`, and `2400x2400` adjust the background colour, position in the image combined with the second digit, for example `South_0_160` positions the product at the bottom of the image, invalid combinations return `404`. `White` is another known working colour.
