import curl_cffi.requests as curl_requests
from pymongo import InsertOne
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.collection import Collection
import random
import time
import tqdm

uri = ""
client = MongoClient(uri, server_api=ServerApi("1"))

SORT = "Newest"
PERIOD = "AllTime"
LIMIT = 100

URL = "https://civitai.com/api/v1/images?limit={limit}&period={period}&sort={sort}"

db = client.civitai
IMAGES = db["images"]

image_ids = set(IMAGES.distinct("id"))

pbar = tqdm.tqdm()


def get_images(
    progress_bar: tqdm.tqdm,
    ids_set: set,
    collection: Collection,
    url: str = None,
):
    if url is None:
        url = URL.format(limit=LIMIT, period=PERIOD, sort=SORT)
        progress_bar.close()
        progress_bar = tqdm.tqdm()
    data = curl_requests.get(
        url,
        impersonate="chrome",
        timeout=10,
    ).json()

    bulk_writes = []

    # received using `Oldest` sort
    if "error" in data:
        print(data)
        return
    next_page = data["metadata"].get("nextPage", None)
    next_cursor = data["metadata"].get("nextCursor", None)
    items = data["items"]
    for item in items:
        if item["id"] in ids_set:
            continue
        # Convert seed to str to avoid overflow
        meta = item.get('meta', {})
        seed = None
        if meta:
            seed = meta.get('seed', None)
        if seed:
            item['meta']['seed'] = str(seed)

        ids_set.add(item["id"])
        bulk_writes.append(InsertOne(item))

    progress_bar.set_postfix({"nextCursor": str(next_cursor), "count": len(ids_set)})
    progress_bar.update()
    if bulk_writes:
        collection.bulk_write(bulk_writes, ordered=False)
    if next_page is not None:
        time.sleep(random.uniform(0.5, 1.5))
        get_images(progress_bar, ids_set, collection, next_page)


get_images(progress_bar=pbar, ids_set=image_ids, collection=IMAGES)
