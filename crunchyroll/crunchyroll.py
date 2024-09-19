from curl_cffi import requests
from pymongo import InsertOne
from pymongo.errors import BulkWriteError
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import tqdm
import json

uri = ""
client = MongoClient(uri, server_api=ServerApi("1"))

db = client.crunchyroll
SERIES = db["series"]
SERIES.create_index([("id", 1)], unique=True)
SEASONS = db["seasons"]
SEASONS.create_index([("id", 1)], unique=True)
EPISODES = db["episodes"]
EPISODES.create_index([("id", 1)], unique=True)


URL = "https://www.crunchyroll.com/content/v2/discover/browse?start={start}&n={n}&sort_by=alphabetical&ratings=true&locale=en-US"
SEASONS_URL = "https://www.crunchyroll.com/content/v2/cms/series/{series}/seasons?force_locale=&locale=en-US"
EPISODES_URL = (
    "https://www.crunchyroll.com/content/v2/cms/seasons/{season}/episodes?locale=en-US"
)
TOKEN_URL = "https://www.crunchyroll.com/auth/v1/token"
TOKEN_PAYLOAD = {"grant_type": "client_id"}
HEADERS = {"Authorization": "Basic Y3Jfd2ViOg=="}

r = requests.post(TOKEN_URL, data=TOKEN_PAYLOAD, headers=HEADERS, impersonate="chrome")
j = r.json()
access_token = j["access_token"]
HEADERS["Authorization"] = f"Bearer {access_token}"

total = None
start = 0
n = 50

pbar = tqdm.tqdm(desc="crunchyroll")

bulk_writes = []
write_after = 250
postfix = {}
while total is None or (isinstance(total, int) and start <= total):
    postfix.update(
        {
            "start": str(start),
            "total": str(total),
            "series": str(SERIES.estimated_document_count()),
        }
    )
    pbar.set_postfix(postfix)
    try:
        r = requests.get(
            URL.format(start=start, n=n), headers=HEADERS, impersonate="chrome"
        )
    except (requests.errors.CurlError, requests.errors.RequestsError):
        continue
    if not r.ok:
        continue
    try:
        j = r.json()
    except json.decoder.JSONDecodeError:
        continue
    if "data" not in j:
        continue
    total = int(j["total"])
    data = j["data"]
    bulk_writes.extend([InsertOne(item) for item in data])
    if len(bulk_writes) >= write_after:
        try:
            result = SERIES.bulk_write(bulk_writes, ordered=False)
        except BulkWriteError as e:
            result = e.details
        if isinstance(result, dict):
            inserted_count = result["nInserted"]
        else:
            inserted_count = result.inserted_count
        postfix.update({"inserted": str(inserted_count)})
        pbar.set_postfix(postfix)
        bulk_writes = []
    start += n
    pbar.update()

if bulk_writes:
    try:
        result = SERIES.bulk_write(bulk_writes, ordered=False)
    except BulkWriteError as e:
        result = e.details
    if isinstance(result, dict):
        inserted_count = result["nInserted"]
    else:
        inserted_count = result.inserted_count
    postfix.update({"inserted": str(inserted_count)})
    pbar.set_postfix(postfix)
    bulk_writes = []

pbar.close()

pbar = tqdm.tqdm(desc="crunchyroll")

postfix = {}

process = True
while process:
    try:
        task = SERIES.find_one({"complete": None})
        if task is None:
            break
        postfix.update(
            {"series": task["id"], "seasons": str(SEASONS.estimated_document_count())}
        )
        pbar.set_postfix(postfix)
        try:
            r = requests.get(
                SEASONS_URL.format(series=task["id"]),
                headers=HEADERS,
                impersonate="chrome",
            )
        except (requests.errors.CurlError, requests.errors.RequestsError):
            continue
        if not r.ok:
            continue
        try:
            j = r.json()
        except json.decoder.JSONDecodeError:
            continue
        if "data" not in j:
            continue
        data = j["data"]
        bulk_writes.extend([InsertOne(item) for item in data])
        if len(bulk_writes) >= write_after:
            try:
                result = SEASONS.bulk_write(bulk_writes, ordered=False)
            except BulkWriteError as e:
                result = e.details
            if isinstance(result, dict):
                inserted_count = result["nInserted"]
            else:
                inserted_count = result.inserted_count
            postfix.update({"inserted": str(inserted_count)})
            pbar.set_postfix(postfix)
            bulk_writes = []
        pbar.update()
        SERIES.find_one_and_update({"_id": task["_id"]}, {"$set": {"complete": True}})
    except KeyboardInterrupt:
        process = False

if bulk_writes:
    try:
        result = SEASONS.bulk_write(bulk_writes, ordered=False)
    except BulkWriteError as e:
        result = e.details
    if isinstance(result, dict):
        inserted_count = result["nInserted"]
    else:
        inserted_count = result.inserted_count
    postfix.update({"inserted": str(inserted_count)})
    pbar.set_postfix(postfix)
    bulk_writes = []

pbar.close()

pbar = tqdm.tqdm(desc="crunchyroll")

postfix = {}

process = True
while process:
    try:
        task = SEASONS.find_one({"complete": None})
        if task is None:
            break
        postfix.update(
            {"season": task["id"], "seasons": str(EPISODES.estimated_document_count())}
        )
        pbar.set_postfix(postfix)
        try:
            r = requests.get(
                EPISODES_URL.format(series=task["id"]),
                headers=HEADERS,
                impersonate="chrome",
            )
        except (requests.errors.CurlError, requests.errors.RequestsError):
            continue
        if not r.ok:
            continue
        try:
            j = r.json()
        except json.decoder.JSONDecodeError:
            continue
        if "data" not in j:
            continue
        data = j["data"]
        bulk_writes.extend([InsertOne(item) for item in data])
        if len(bulk_writes) >= write_after:
            try:
                result = EPISODES.bulk_write(bulk_writes, ordered=False)
            except BulkWriteError as e:
                result = e.details
            if isinstance(result, dict):
                inserted_count = result["nInserted"]
            else:
                inserted_count = result.inserted_count
            postfix.update({"inserted": str(inserted_count)})
            pbar.set_postfix(postfix)
            bulk_writes = []
        pbar.update()
        SEASONS.find_one_and_update({"_id": task["_id"]}, {"$set": {"complete": True}})
    except KeyboardInterrupt:
        process = False

if bulk_writes:
    try:
        result = EPISODES.bulk_write(bulk_writes, ordered=False)
    except BulkWriteError as e:
        result = e.details
    if isinstance(result, dict):
        inserted_count = result["nInserted"]
    else:
        inserted_count = result.inserted_count
    postfix.update({"inserted": str(inserted_count)})
    pbar.set_postfix(postfix)
    bulk_writes = []
