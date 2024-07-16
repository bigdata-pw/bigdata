import curl_cffi.requests as curl_requests
import random
from pymongo import InsertOne
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import BulkWriteError
from datetime import datetime
from bs4 import BeautifulSoup
import json
import time
import tqdm
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--category_id", required=True, type=str)
args = parser.parse_args()
CATEGORY_ID: str = args.category_id

uri = ""
client = MongoClient(uri, server_api=ServerApi("1"))

db = client.aops
TOPICS = db["topics"]
TOPICS.create_index([("topic_id", 1)], unique=True)


def session_id() -> str:
    r = curl_requests.get(
        "https://artofproblemsolving.com/community/c7", impersonate="chrome"
    )
    soup = BeautifulSoup(r.text, "html.parser")
    session_data = (
        [
            line
            for line in soup.find_all("script")[2].text.split("\n")
            if "session" in line
        ][0]
        .strip()
        .replace("AoPS.session = ", "")
        .strip()
        .replace(";", "")
    )
    session_data = json.loads(session_data)
    return session_data["id"]


def random_delay(start: float = 0.5, end: float = 1.2):
    time.sleep(random.uniform(start, end))


URL = "https://artofproblemsolving.com/m/community/ajax.php"
SESSION_ID = session_id()

data = {
    "category_type": "forum",
    "log_visit": "0",  # originally "1"
    "required_tag": "",
    "fetch_before": str(int(datetime.now().timestamp())),
    "user_id": "0",
    "fetch_archived": "1",
    "fetch_announcements": "1",
    "category_id": CATEGORY_ID,
    "a": "fetch_topics",
    "aops_logged_in": "false",
    "aops_user_id": "1",
    "aops_session_id": SESSION_ID,
}

pbar = tqdm.tqdm()

while True:
    try:
        r = curl_requests.post(URL, data=data, impersonate="chrome")
        if not r.ok:
            continue
        try:
            j = r.json()
        except json.decoder.JSONDecodeError:
            continue
        topics = j["response"]["topics"]
        try:
            result = TOPICS.bulk_write(
                [InsertOne(topic) for topic in topics], ordered=False
            )
        except BulkWriteError as e:
            pass
        next_fetch_before = [topic["last_post_time"] for topic in topics][-1]
        data["fetch_before"] = str(next_fetch_before)
        pbar.update()
        random_delay()
    except KeyboardInterrupt:
        break
