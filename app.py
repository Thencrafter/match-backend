import json
import os
import sys
from datetime import datetime
import pytz
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

sample = {
    "Name": "placeholder",
    "Age": 0,
    "TimeZone": 0,
    "DM": "Open",
    "Pronouns": "pro/noun",
    "Match": "Both",
    "Gender": "Other",
    "Likes": ["Music", "Games", "Media", "Going out", "Cooking", "Time", "Books"],
    "Extra": "This will not be used by the program, and is used for the matchmaker to make a better decision",
    "AgeLower": 0,
    "AgeUpper": 0,
    "GenderPref": "Any",
    "TimeDiff": 0,
    "LikesPref": ["Music", "Games", "Media", "Going out", "Cooking", "Time", "Books"]
}


UTC = pytz.utc
app = Flask(__name__)
CORS(app)


@app.route('/get_json', methods=['GET'])
def get_json():
    return send_file("data.json", mimetype="application/json", as_attachment=True)


@app.route('/api/users', methods=['GET'])
def get_users():
    global people_list
    people_list = sortUserList(people_list)
    return jsonify(people_list)


@app.route('/api/users', methods=['POST'])
def addPeople(sample=sample):
    global people_list
    data = request.get_json()
    info = data.get('text')
    new_people = []
    info_list = info.split("\n")
    for person in info_list:
        i = 0
        new_person = sample.copy()
        person_info_list = person.split("\t")
        for category in new_person.keys():
            info_item = person_info_list[i]
            if category == "Likes" or category == "LikesPref":
                info_item = info_item.split(",")
                info_item = [s.strip() for s in info_item]
                info_item = [s.lower() for s in info_item]
            if category == "Age" or category == "TimeZone" or category == "TimeDiff" or category == "AgeUpper" or category == "AgeLower":
                info_item = int(info_item)
            new_person[category] = info_item
            i += 1
        new_person["Matched"] = False
        new_person["MatchedWith"] = None
        new_person["PrevMatchedWith"] = []
        new_person["TimeSinceAction"] = datetime.now(
            UTC).strftime("%Y/%m/%d, %H:%M:%S")
        deleteUser(new_person["Name"])
        people_list.append(new_person)
    people_list = sortUserList(people_list)
    file_path = "data.json"
    with open(file_path, "w") as json_file:
        json.dump(people_list, json_file, indent=4)
    return "Success"


@app.route('/api/users/<user_id>&<edit>', methods=['POST'])
def editInfo(user_id, edit):
    user = findPersonByName(user_id)
    data = request.get_json()
    info = data.get('content')
    user[edit] = info
    with open("data.json", "w") as json_file:
        json.dump(people_list, json_file, indent=4)
    return "Success"


@app.route('/api/users/<user>', methods=['DELETE'])
def deleteUser(user):
    global people_list
    person = findPersonByName(user)
    if person[0] == "None":
        return "The user doesn't exist", 404
    people_list.remove(person)
    people_list = sortUserList(people_list)
    with open("data.json", "w") as json_file:
        json.dump(people_list, json_file, indent=4)
    return "Success"


@app.route('/api/users/<name>', methods=['GET'])
def findPersonByName(name):
    global people_list
    for i in people_list:
        if name == i["Name"]:
            return i
    return "None", 404


@app.route('/api/find_match/<name>', methods=['GET'])
def findMatch(name):
    person = findPersonByName(name)
    possible_matches = []
    global people_list
    if not person:
        return []

    if person["Matched"]:
        return "User is already matched"

    for i in people_list:
        if i == person:
            continue

        age_check = (person["AgeLower"] <= i["Age"] <= person["AgeUpper"] and
                     i["AgeLower"] <= person["Age"] <= i["AgeUpper"])

        timezone_check = (abs(person["TimeZone"] - i["TimeZone"]) <= person["TimeDiff"] and
                          abs(person["TimeZone"] - i["TimeZone"]) <= i["TimeDiff"])

        match_check = (person["Match"] == "Both" or
                       i["Match"] == "Both" or
                       person["Match"] == i["Match"])

        gender_check = ((person["GenderPref"] == i["Gender"] or
                         person["GenderPref"] == "Any") and
                        (i["GenderPref"] == person["Gender"] or
                         i["GenderPref"] == "Any"))

        common_likes_check = (set(person["Likes"]) and set(i["LikesPref"]) or
                              set(i["Likes"]) and set(person["LikesPref"])) or "any" in person["LikesPref"] or "any" in i["LikesPref"]

        check_prev_matched = not (i["Name"] in person["PrevMatchedWith"])

        if (age_check and timezone_check and match_check and gender_check and common_likes_check and not i["Matched"] and check_prev_matched):
            possible_matches.append(i)
    possible_matches = sortUserList(possible_matches)
    return possible_matches


@app.route('/api/find_match/<name1>&<name2>', methods=['POST'])
def createMatch(name1, name2):
    global people_list
    user1 = findPersonByName(name1)
    user2 = findPersonByName(name2)
    if user1["Matched"] == True or user2["Matched"] == True:
        return "One or both of the users are already matched", 409
    user1["Matched"] = True
    user1["MatchedWith"] = user2["Name"]
    user1["PrevMatchedWith"].append(user2["Name"])
    user1["TimeSinceAction"] = datetime.now(UTC).strftime("%Y/%m/%d, %H:%M:%S")
    user2["Matched"] = True
    user2["MatchedWith"] = user1["Name"]
    user2["PrevMatchedWith"].append(user1["Name"])
    user2["TimeSinceAction"] = datetime.now(UTC).strftime("%Y/%m/%d, %H:%M:%S")
    people_list = sortUserList(people_list)
    with open("data.json", "w") as json_file:
        json.dump(people_list, json_file, indent=4)
    return "Success"


@app.route('/api/delete_match/<name>', methods=['POST'])
def removeMatch(name):
    global people_list
    user = findPersonByName(name)
    user["Matched"] = False
    matched_user = findPersonByName(
        user["MatchedWith"])
    matched_user["Matched"] = False
    matched_user["MatchedWith"] = None
    matched_user["TimeSinceAction"] = datetime.now(
        UTC).strftime("%Y/%m/%d, %H:%M:%S")
    user["MatchedWith"] = None
    user["TimeSinceAction"] = datetime.now(UTC).strftime("%Y/%m/%d, %H:%M:%S")
    people_list = sortUserList(people_list)
    with open("data.json", "w") as json_file:
        json.dump(people_list, json_file, indent=4)
    return matched_user["Name"]


def sortUserList(list):
    return sorted(list, key=lambda d: (d["Matched"], d["TimeSinceAction"]))


with open('data.json', 'r') as file:
    people_list = json.load(file)

if __name__ == '__main__':
    app.run(port=5000)
