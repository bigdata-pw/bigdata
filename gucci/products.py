import curl_cffi.requests as curl_requests
from pymongo import InsertOne, UpdateOne
from pymongo.errors import BulkWriteError
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import tqdm
import json
import logging
import pathlib

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


uri = ""
client = MongoClient(uri, server_api=ServerApi("1"))

db = client.gucci
PRODUCTS = db["products"]
PRODUCTS.create_index([("productCode", 1)], unique=True)

PRODUCTS_URL = "https://www.gucci.com/{lang_code}/c/productgrid?categoryCode={category_code}&show=All&page={page}"
PRODUCT_DETAILS_URL = (
    "https://prod-catalog-api.guccidigital.io/v1/products/{product_code}"
)

DEFAULT_CATEGORIES = [
    "women",
    "men",
    "jewelry-watches",
]


LANG_CODE = "us/en"
LANGUAGE = "en"

IMAGE_STYLE = "DarkGray_Center_0_0_2400x2400"

PRODUCT_DETAILS = True

BASE_PATH = pathlib.Path("/bigdata/gucci/images")

PRODUCT_CODES = [
    product["productCode"] for product in list(PRODUCTS.find({}, {"productCode": 1}))
]


def get(url: str):
    response = curl_requests.get(url, impersonate="chrome")
    if not response.ok:
        logger.debug(f"Failed to get {url}")
        return None
    try:
        data = response.json()
        return data
    except json.JSONDecodeError:
        logger.debug(f"Failed to parse JSON from {url}")
        return None


def download(url: str, path: pathlib.Path):
    if path.exists():
        logger.debug(f"File {path} already exists")
        return
    response = curl_requests.get(
        url,
        impersonate="chrome",
    )
    if not response.ok:
        logger.debug(f"Failed to download {url}")
        return
    _ = path.write_bytes(response.content)
    logger.debug(f"Downloaded {url} to {path}")


def get_product_details(product_code: str):
    data = get(PRODUCT_DETAILS_URL.format(product_code=product_code))
    if data is None:
        logger.debug(f"Failed to get product details for {product_code}")
        return {}
    logger.debug(f"Product details for {product_code}: {data}")
    return data


def download_images():
    products = list(PRODUCTS.find({"bigdata_downloaded": False}))
    pbar = tqdm.tqdm(total=len(products))
    image_pbar = tqdm.tqdm()
    updates = []
    for product in products:
        product_code = product["productCode"]
        pbar.set_description(product_code)
        product_dir = BASE_PATH / product_code
        product_dir.mkdir(parents=True, exist_ok=True)
        images = product["images"]
        number_of_images = len(images)
        if (
            product_dir.exists()
            and len(list(product_dir.glob("*.jpg"))) == number_of_images
        ):
            pbar.update(1)
            logger.debug(f"Images already downloaded for {product_code}")
            continue
        image_pbar.total = number_of_images
        image_pbar.n = 0
        image_pbar.refresh()
        for _, image in enumerate(images):
            filename = image.split("/")[-1]
            image_path = product_dir / filename
            download(image, image_path)
            image_pbar.update(1)
        pbar.update(1)
        updates.append(
            UpdateOne({"_id": product["_id"]}, {"$set": {"bigdata_downloaded": True}})
        )
    try:
        _ = PRODUCTS.bulk_write(updates, ordered=False) if updates else None
    except BulkWriteError as e:
        pass


def get_products(category_code: str):
    def process_url(url: str) -> str:
        style = url.split("/")[4]
        logger.debug(f"Style: {style}")
        return "https:" + url.replace(style, IMAGE_STYLE)

    def deduplicate_images(images: list[str]) -> list[str]:
        filenames: set[str] = set()
        result: set[str] = set()
        for image in images:
            filename = image.split("/")[-1]
            logger.debug(f"Filename: {filename}")
            if "-" in filename:
                filename = filename.split("-")[0] + ".jpg"
                logger.debug(f"New filename: {filename}")
            if filename in filenames:
                logger.debug(f"Duplicate image {filename}")
                continue
            filenames.add(filename)
            result.add(image)
        return list(result)

    def process_images(product: dict) -> list[str]:
        primary_image = product["primaryImage"]
        alternate_gallery_images = product["alternateGalleryImages"]
        alternate_image = product["alternateImage"]
        images = [image["src"] for image in alternate_gallery_images]
        images.append(primary_image["src"])
        images.append(alternate_image["src"])
        images = [process_url(image) for image in images]
        images = deduplicate_images(images)
        return images

    page = 0
    number_of_pages = 1
    updates = []
    while page < number_of_pages:
        data = get(
            PRODUCTS_URL.format(
                lang_code=LANG_CODE, category_code=category_code, page=page
            )
        )
        if data is None:
            logger.debug(f"Failed to get products for {category_code} on page {page}")
            break
        number_of_pages = data["numberOfPages"]
        products = data["products"]
        count = len(products["items"])
        if count == 0:
            logger.debug(f"No products found for {category_code} on page {page}")
            break
        logger.debug(f"Found {count} products for {category_code} on page {page}")
        pbar = tqdm.tqdm(total=count)
        pbar.set_postfix(page=page, category=category_code)
        for _, product in enumerate(products["items"]):
            product_code = product["productCode"]
            if product_code in PRODUCT_CODES:
                logger.debug(f"{product_code} already exists")
                pbar.update(1)
                continue
            logger.debug(f"Processing product {product_code}")
            product["images"] = process_images(product)
            if PRODUCT_DETAILS:
                product.update(get_product_details(product_code))
            product["bigdata_downloaded"] = False
            updates.append(InsertOne(product))
            pbar.update(1)
        page += 1
    try:
        _ = PRODUCTS.bulk_write(updates, ordered=False) if updates else None
    except BulkWriteError as e:
        pass


for category in DEFAULT_CATEGORIES:
    get_products(category)

download_images()
