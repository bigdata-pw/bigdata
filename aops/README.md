# Art of Problem Solving

Art of Problem solving -> MongoDB

## MongoDB

Uses database `aops`.

Topics script creates collection `topics`.

Posts script creates collection `posts`.

## Usage (topics)

- Install `requirements.txt`
- Fill MongoDB uri
- Run with `--category_id` argument

## Usage (posts)

First, run `assign`, set `NODES` and `PER_NODE` according to your infrastructure. Each topic is assigned to allow distributed processing.

ID are in format `BIG_{node_id}-{instance_id}`.

- Install `requirements.txt`
- Fill MongoDB uri
- Run with `--bigdata_id` argument

## Notes

Topics are paginated by timestamp cursor, there aren't that many topics and 10 are retrieved per request, therefore we opt to process topics on a single node. If you desire distributed processing of topics assign a range of timestamps per node.

A very small number topics returned no `posts` field, we did not check why and simply mark these as complete.
