# ba-image-search-service

## Prepare the environment

This project uses Python, Flask, Elasticsearch, and uses Docker to pack them up.

Run `docker compose` to build and start the app:

```bash
docker compose up -d
```

Check the logs:

```bash
docker compose logs -f app
docker compose logs -f elasticsearch
```

Press Ctrl+C to terminate the log.

To stop:

```bash
docker compose down
```

## API

### Test the connection

```bash
curl "http://localhost:5001/test"
```

```
HTTP/1.1 200 OK
Server: Werkzeug/3.0.1 Python/3.9.18
Date: Thu, 30 Nov 2023 13:49:42 GMT
Content-Type: application/json
Content-Length: 526
Connection: close

{
  "cluster_name": "docker-cluster",
  "cluster_uuid": "74Lafh2pTWOQiLzNzP8L3A",
  "name": "8d5ea8dde047",
  "tagline": "You Know, for Search",
  "version": {
    "build_date": "2023-11-11T10:05:59.421038163Z",
    "build_flavor": "default",
    "build_hash": "6f9ff581fbcde658e6f69d6ce03050f060d1fd0c",
    "build_snapshot": false,
    "build_type": "docker",
    "lucene_version": "9.8.0",
    "minimum_index_compatibility_version": "7.0.0",
    "minimum_wire_compatibility_version": "7.17.0",
    "number": "8.11.1"
  }
}
```

### Create the index

```bash
curl "http://localhost:5001/create"
```

```
HTTP/1.1 200 OK
Server: Werkzeug/3.0.1 Python/3.9.18
Date: Thu, 30 Nov 2023 13:06:27 GMT
Content-Type: application/json
Content-Length: 118
Connection: close

{
  "data": {
    "acknowledged": true,
    "index": "ba_images",
    "shards_acknowledged": true
  },
  "res": 200
}
```

### Delete the index

```bash
curl "http://localhost:5001/delete"
```

```
HTTP/1.1 200 OK
Server: Werkzeug/3.0.1 Python/3.9.18
Date: Thu, 30 Nov 2023 13:06:25 GMT
Content-Type: application/json
Content-Length: 59
Connection: close

{
  "data": {
    "acknowledged": true
  },
  "res": 200
}
```

### Add documents to the index

```bash
curl -X "POST" "http://localhost:5001/add_data" \
     -H 'Content-Type: application/json; charset=utf-8' \
     -d "@data/bulk_docs.json"
```

### Fetch a document by id

```bash
curl "http://localhost:5001/doc/BG_CS_Rabbit_05.jpg"
```

```
HTTP/1.1 200 OK
Server: Werkzeug/3.0.1 Python/3.9.18
Date: Thu, 30 Nov 2023 13:59:18 GMT
Content-Type: application/json
Content-Length: 1997
Connection: close

{
  "data": {
    "_id": "BG_CS_Rabbit_05.jpg",
    "found": true,
    "student": [
      "Hifumi",
      "Hifumi",
      "Hifumi",
      "Miyu"
    ],
    "student_info": [
      ...
    ],
    "text": "..."
  },
  "res": 200
}

```

### Update a document

The following command set the student in `BG_CS_Rabbit_05.jpg` to `Shiroko`. This will automatically update the `student_info` field with the related info of Shiroko, such as the Chinese name 白子, club information 对策委员会, school information, etc.

```bash
curl -X "POST" "http://localhost:5001/update/BG_CS_Rabbit_05.jpg" \
     -H 'Content-Type: application/json; charset=utf-8' \
     -d $'{
  "student": [
    "Shiroko"
  ]
}'
```

```
HTTP/1.1 200 OK
Server: Werkzeug/3.0.1 Python/3.9.18
Date: Thu, 30 Nov 2023 12:33:13 GMT
Content-Type: application/json
Content-Length: 266
Connection: close

{
  "data": {
    "_id": "BG_CS_Rabbit_05.jpg",
    "_index": "ba_images",
    "_primary_term": 1,
    "_seq_no": 1157,
    "_shards": {
      "failed": 0,
      "successful": 1,
      "total": 2
    },
    "_version": 3,
    "result": "updated"
  },
  "res": 200
}
```

### Search

Finally, we can run search against the document index.

```bash
curl -X "POST" "http://localhost:5001/search" \
     -H 'Content-Type: application/json; charset=utf-8' \
     -d $'{
  "query": "自行车白子"
}'
```

A list of hit documents are returned in order of relevance.

```
HTTP/1.1 200 OK
Server: Werkzeug/3.0.1 Python/3.9.18
Date: Thu, 30 Nov 2023 13:41:37 GMT
Content-Type: application/json
Content-Length: 254
Connection: close

{
  "data": [
    "BG_CS_Abydos_02.jpg",
    "BG_CS_S1Final_17.jpg",
    "BG_HealthClub_Night.jpg",
    "BG_HealthClub.jpg",
    "BG_CS_PV4_001_2.jpg",
    "BG_CS_S1Final_15.jpg",
    "BG_BigBridge.jpg",
    "BG_BigBridge2_Night.jpg"
  ],
  "res": 200
}
```