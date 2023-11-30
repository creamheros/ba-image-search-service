import json
import os

import jieba
import requests
from flask import Flask, request

app = Flask(__name__)

ES_HOST = os.environ.get("ES_HOST", "elasticsearch")
ES_PORT = os.environ.get("ES_PORT", "9200")
ES_URL = f"http://{ES_HOST}:{ES_PORT}"

HEADERS = {"Content-Type": "application/json"}
INDEX_NAME = "ba_images"
MAPPING = {
    "mappings": {
        "properties": {
            "text": {
                "type": "text",
                "analyzer": "whitespace",
            },
            "student": {
                "type": "keyword",
            },
            "student_info": {
                "type": "keyword",
            },
        }
    }
}

special_words = set()
names = set()
clubs = set()
schools = set()
student_info = {}
with open("data/students.json", "r") as f:
    raw_data = json.load(f)
    for student in raw_data:
        name_en = student["name"]["en"]
        student_info[name_en] = student
        special_words.add(student["name"]["en"].lower())
        special_words.add(student["name"]["cn"].lower())
        special_words.add(student["familyName"]["en"].lower())
        special_words.add(student["familyName"]["cn"].lower())
        names.add(student["name"]["en"].lower())
        names.add(student["name"]["cn"].lower())
        names.add(student["familyName"]["en"].lower())
        names.add(student["familyName"]["cn"].lower())
        special_words.add(student["club"].lower())
        clubs.add(student["club"].lower())
        special_words.add(student["affiliation"].lower())
        special_words.add(student["schoolCode"].lower())
        schools.add(student["affiliation"].lower())
        schools.add(student["schoolCode"].lower())
        for nickname in student["nickname"]:
            special_words.add(nickname.lower())
for word in special_words:
    jieba.add_word(word)


def cut_keywords(keywords):
    cut_keywords = []
    for keyword in keywords:
        cut_keywords.extend(list(set(list(jieba.cut_for_search(keyword)) + [keyword])))
    return cut_keywords


def wrap_response(response, process_fn=lambda x: x):
    status_code = response.status_code
    body = process_fn(response.json())
    final_response = ({"res": status_code, "data": body}, status_code)
    return final_response


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/test", methods=["GET", "POST"])
def test():
    """Test if the server is running."""
    return requests.get(ES_URL).json()


@app.route("/create", methods=["GET", "POST"])
def create():
    """Create the index."""
    response = requests.put(f"{ES_URL}/{INDEX_NAME}", json=MAPPING, headers=HEADERS)
    return wrap_response(response)


@app.route("/delete", methods=["GET", "POST"])
def delete():
    """Delete the index."""
    response = requests.delete(f"{ES_URL}/{INDEX_NAME}")
    return wrap_response(response)


def postprocess_doc(doc):
    if "student" not in doc:
        return
    all_student_keywords = []
    for student in doc["student"]:
        if student not in student_info:
            continue
        info = student_info[student]
        # app.logger.info(info)
        all_student_keywords.append(student)
        all_student_keywords.append(info["name"]["cn"])  # CN name
        all_student_keywords.append(info["familyName"]["en"])  # EN family name
        all_student_keywords.append(info["familyName"]["cn"])  # CN family name
        all_student_keywords.append(info["club"])
        all_student_keywords.append(info["affiliation"])
        all_student_keywords.append(info["schoolCode"])
        for nickname in info["nickname"]:
            all_student_keywords.append(nickname)
    doc["student_info"] = [x.lower() for x in cut_keywords(all_student_keywords)]


@app.route("/add_data", methods=["POST"])
def add_data():
    """Add data to the index."""
    data = request.get_json()
    bulk_data = []
    # app.logger.info(student_info)
    for doc in data:
        bulk_data.append({"index": {"_id": doc.pop("id")}})  # allow overwrite
        postprocess_doc(doc)
        bulk_data.append(doc)
    bulk_data = "\n".join([json.dumps(x) for x in bulk_data]) + "\n"
    response = requests.post(f"{ES_URL}/{INDEX_NAME}/_bulk", data=bulk_data, headers=HEADERS)
    return wrap_response(response)


@app.route("/doc/<id>", methods=["GET"])
def get_doc(id):
    """Get a document by id."""
    def process_fn(body):
        return {"_id": body["_id"], "found": body["found"], **body.get("_source", {})}

    response = requests.get(f"{ES_URL}/{INDEX_NAME}/_doc/{id}")
    return wrap_response(response, process_fn)


@app.route("/update/<id>", methods=["POST"])
def update_doc(id):
    """Update a document by id."""
    data = request.get_json()
    postprocess_doc(data)
    response = requests.post(
        f"{ES_URL}/{INDEX_NAME}/_update/{id}", json={"doc": data}, headers=HEADERS
    )
    return wrap_response(response)


@app.route("/search", methods=["POST"])
def search():
    """Search for documents in Chinese."""
    def process_fn(body):
        hits = body["hits"]["hits"]
        return [x["_id"] for x in hits]

    data = request.get_json()
    query = data["query"]
    app.logger.info(query)
    query_tokens = list(jieba.cut(query))
    query_tokens_text = [x for x in query_tokens if x not in special_words]
    query_tokens_student = [x for x in query_tokens if x in special_words]
    response = requests.post(
        f"{ES_URL}/{INDEX_NAME}/_search",
        json={
            "query": {
                "bool": {
                    "must": [
                        {"match": {"text": " ".join(query_tokens_text)}},
                    ],
                    "should": [
                        {"term": {"student_info": {"value": x}}} for x in query_tokens_student
                    ],
                }
            }
        },
        headers=HEADERS,
    )
    return wrap_response(response, process_fn)
