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

SORT = "Oldest"
PERIOD = "AllTime"
LIMIT = 100

URL = "https://civitai.com/api/v1/models?limit={limit}&types={type}&period={period}&sort={sort}&nsfw=true"

db = client.civitai
LORA = db["lora"]
CHECKPOINT = db["checkpoint"]
TEXTUAL_INVERSION = db["textual_inversion"]
HYPERNETWORK = db["hypernetwork"]
AESTHETIC_GRADIENT = db["aesthetic_gradient"]
CONTROLNET = db["controlnet"]
POSES = db["poses"]

lora_ids = set(LORA.distinct('id'))
checkpoint_ids = set(CHECKPOINT.distinct("id"))
textual_inversion_ids = set(TEXTUAL_INVERSION.distinct("id"))
hypernetwork_ids = set(HYPERNETWORK.distinct("id"))
aesthetic_gradient_ids = set(AESTHETIC_GRADIENT.distinct("id"))
controlnet_ids = set(CONTROLNET.distinct("id"))
poses_ids = set(POSES.distinct("id"))

pbar = tqdm.tqdm()


def get_models(
    progress_bar: tqdm.tqdm,
    ids_set: set,
    model_type: str,
    collection: Collection,
    url: str = None,
):
    if url is None:
        url = URL.format(type=model_type, limit=LIMIT, period=PERIOD, sort=SORT)
        progress_bar.close()
        progress_bar = tqdm.tqdm()
    data = curl_requests.get(
        url,
        impersonate="chrome",
        timeout=10,
    ).json()

    bulk_writes = []

    next_page = data["metadata"].get("nextPage", None)
    next_cursor = data["metadata"].get("nextCursor", None)
    items = data["items"]
    for item in items:
        if item["id"] in ids_set:
            continue
        ids_set.add(item["id"])
        bulk_writes.append(InsertOne(item))

    progress_bar.set_postfix(
        {"nextCursor": next_cursor, "count": len(ids_set), "type": model_type}
    )
    progress_bar.update()
    if bulk_writes:
        collection.bulk_write(bulk_writes, ordered=False)
    if next_page is not None:
        time.sleep(random.uniform(0.5, 1.5))
        get_models(progress_bar, ids_set, model_type, collection, next_page)


get_models(progress_bar=pbar, ids_set=lora_ids, model_type="LORA", collection=LORA)
get_models(
    progress_bar=pbar,
    ids_set=checkpoint_ids,
    model_type="Checkpoint",
    collection=CHECKPOINT,
)
get_models(
    progress_bar=pbar,
    ids_set=textual_inversion_ids,
    model_type="TextualInversion",
    collection=TEXTUAL_INVERSION,
)
get_models(
    progress_bar=pbar,
    ids_set=hypernetwork_ids,
    model_type="Hypernetwork",
    collection=HYPERNETWORK,
)
get_models(
    progress_bar=pbar,
    ids_set=aesthetic_gradient_ids,
    model_type="AestheticGradient",
    collection=AESTHETIC_GRADIENT,
)
get_models(
    progress_bar=pbar,
    ids_set=controlnet_ids,
    model_type="Controlnet",
    collection=CONTROLNET,
)
get_models(progress_bar=pbar, ids_set=poses_ids, model_type="Poses", collection=POSES)
