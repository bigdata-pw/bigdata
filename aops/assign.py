from pymongo import UpdateOne
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = ""
client = MongoClient(uri, server_api=ServerApi("1"))

db = client.aops
TOPICS = db["topics"]
POSTS = db["posts"]

query = {
    "$and": [
        {"bigdata_complete": {"$exists": False}},
        {"bigdata_id": {"$exists": False}},
    ]
}

PER_NODE = 2
NODES = 10

bigdata_ids = [
    f"BIG_{node_id}-{instance_id}"
    for node_id in range(NODES)
    for instance_id in range(PER_NODE)
]

bigdata_result = {bigdata: 0 for bigdata in bigdata_ids}

bulk_writes = []
while True:
    work = TOPICS.find(query).limit(10000)
    for item in work:
        bigdata_id = bigdata_ids.pop(0)
        bulk_writes.append(
            UpdateOne(
                {"topic_id": item["topic_id"]}, {"$set": {"bigdata_id": bigdata_id}}
            )
        )
        bigdata_result[bigdata_id] += 1
        bigdata_ids.append(bigdata_id)
    if bulk_writes:
        TOPICS.bulk_write(bulk_writes)
        bulk_writes = []
    else:
        break
    print(bigdata_result)
