import curl_cffi.requests as curl_requests
import random
from pymongo import InsertOne
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import BulkWriteError
from bs4 import BeautifulSoup
import json
import time
import tqdm
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--bigdata_id", required=True, type=str)
args = parser.parse_args()

BIGDATA_ID: str = args.bigdata_id

uri = ""
client = MongoClient(uri, server_api=ServerApi("1"))

db = client.aops
TOPICS = db["topics"]
TOPICS.create_index([("bigdata_complete", 1)])
TOPICS.create_index([("bigdata_id", 1)])
POSTS = db["posts"]
POSTS.create_index([("post_id", 1)], unique=True)


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
HASH = int(random.random() * 1e7)

data_post = {
    "topic_fetch": "initial",
    "new_topic_id": "",
    "new_category_id": "",
    "fetch_first": "1",
    "fetch_all": "1",
    "old_topic_id": "0",
    "source": "master",
    "hash": HASH,
    "is_office_hours": "0",
    "a": "change_focus_topic",
    "aops_logged_in": "false",
    "aops_user_id": "1",
    "aops_session_id": SESSION_ID,
}

pbar = tqdm.tqdm()

query = {
    "$and": [
        {"bigdata_complete": {"$exists": False}},
        {"bigdata_id": BIGDATA_ID},
    ]
}

postfix = {}

while True:
    try:
        topic = TOPICS.find_one(query)
        if topic is None:
            break
        topic_id = str(topic["topic_id"])
        category_id = str(topic["category_id"])
        postfix.update({"topic": topic_id, "category": category_id})
        pbar.set_postfix(postfix)
        data_post["new_category_id"] = category_id
        data_post["new_topic_id"] = topic_id
        r = curl_requests.post(URL, data=data_post, impersonate="chrome")
        if not r.ok:
            continue
        try:
            j = r.json()
        except json.decoder.JSONDecodeError:
            continue
        posts: list = j["response"].get("posts", [])
        postfix.update({"posts": len(posts)})
        pbar.set_postfix(postfix)
        try:
            result = (
                POSTS.bulk_write([InsertOne(post) for post in posts], ordered=False)
                if posts
                else None
            )
        except BulkWriteError as e:
            pass
        updated = TOPICS.find_one_and_update(
            {"topic_id": topic["topic_id"]},
            {"$set": {"bigdata_complete": True}},
            new=True,
        )
        pbar.update()
        random_delay()
    except KeyboardInterrupt:
        break
