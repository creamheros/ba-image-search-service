import json
import jieba
from math import log2, ceil
import os


def cut_keywords(keywords):
    cut_keywords = []
    for keyword in keywords:
        cut_keywords.extend(list(set(list(jieba.cut_for_search(keyword)) + [keyword])))
    return cut_keywords


def weigh_student(detected: list):
    student = []
    for detect in detected:
        names, probs = [], []
        for k, v in detect.items():
            names.append(k)
            probs.append(v)
        # guess1, guess2 = [], []
        # guess1.extend([names[0]] * ceil(log2(min(probs[0] / probs[1], 10)) + 1))
        # guess2.extend([names[1]] * ceil(log2(probs[1] / probs[0]) + 1))
        # student.extend(guess1 + guess2)
        student.append(names[0])  # just use the first guess
    return student


if __name__ == "__main__":
    student_info = {}
    with open("students.json", "r") as f:
        raw_data = json.load(f)
        for student in raw_data:
            name_en = student["name"]["en"]
            student_info[name_en] = student

    with open("detected_students.json", "r") as f:
        detected_students = json.load(f)

    with open("llm_features.json", "r") as fin:
        llm_features_data = json.load(fin)
        final_data = []
        for doc in llm_features_data:
            id_ = doc["filename"]
            # fout.write(json.dumps({"create": {"_id": id_}}) + "\n")
            es_doc = {"id": id_}
            all_llm_keywords = []
            for item in doc["keywords"]:
                if item["role"] == "all":
                    all_llm_keywords.extend(item["keywords"])
            all_student_keywords = []
            weighted_student = weigh_student(detected_students[id_])
            # print(id_ + ".jpg", weighted_student)
            for student in weighted_student:
                if student not in student_info:
                    continue
                info = student_info[student]
                all_student_keywords.append(student)  # EN name
                # all_student_keywords.append(info["name"]["cn"])  # CN name
                # all_student_keywords.append(info["familyName"]["en"])  # EN family name
                # all_student_keywords.append(info["familyName"]["cn"])  # CN family name
                # all_student_keywords.append(info["club"])
                # all_student_keywords.append(info["affiliation"])
                # all_student_keywords.append(info["schoolCode"])
                # for nickname in info["nickname"]:
                #     all_student_keywords.append(nickname)
            # print(all_student_keywords)
            es_doc["text"] = " ".join(list(set(all_llm_keywords)))
            es_doc["student"] = all_student_keywords
            final_data.append(es_doc)
    
    with open("bulk_docs.json", "w") as fout:
        json.dump(final_data, fout, indent=2, ensure_ascii=False)