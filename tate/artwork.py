import curl_cffi.requests as curl_requests
from pymongo import InsertOne
from pymongo.errors import BulkWriteError
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import tqdm

URL = "https://www.tate.org.uk/api/v2/artworks/?fields=*&offset={offset}"

uri = ""
client = MongoClient(uri, server_api=ServerApi("1"))

db = client.tate
IMAGES = db["images"]
IMAGES.create_index([("id", 1)], unique=True)

HEADERS = {"accept": "application/json"}

offset = 0
per_page = 20

pbar = tqdm.tqdm()

while True:
    try:
        pbar.set_postfix({"offset": offset})
        updates = []
        try:
            response = curl_requests.get(
                URL.format(offset=offset), headers=HEADERS, impersonate="chrome"
            )
        except curl_requests.errors.RequestsError:
            # Some offset timeout, 503
            # likely a specific record is the issue
            # could increase by 1 each time until it works
            # max 20 missing though 🤷‍♂️
            offset += per_page
            continue
        data = response.json()
        items = data["items"]
        if not items:
            break
        for item in items:
            if not item["master_images"]:
                # when no images are available
                continue
            if not item["master_images"][0]["sizes"]:
                # when no images are 'cleared'/copyright issues
                continue
            item["image"] = item["master_images"][0]["sizes"][-1][-1]
            item["bigdata_downloaded"] = False
            updates.append(InsertOne(item))
        try:
            result = IMAGES.bulk_write(updates, ordered=False) if updates else None
        except BulkWriteError:
            pass
        offset += per_page
        pbar.update()
    except KeyboardInterrupt:
        break
