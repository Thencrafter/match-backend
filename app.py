import json
import os
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext
from datetime import datetime
import pytz
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from github import Github
from dotenv import load_dotenv, dotenv_values
load_dotenv()

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

people_list = [

]

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
                info_item = info_item.split(", ")
            if category == "Age" or category == "TimeZone" or category == "TimeDiff" or category == "AgeUpper" or category == "AgeLower":
                info_item = int(info_item)
            new_person[category] = info_item
            i += 1
        new_person["Matched"] = False
        new_person["MatchedWith"] = None
        new_person["PrevMatchedWith"] = []
        new_person["TimeSinceAction"] = datetime.now(
            UTC).strftime("%Y/%m/%d, %H:%M:%S")
        j = 0
        for i in range(len(people_list)):
            if people_list[i]["Name"] == new_person["Name"]:
                j += 1
        new_person["Id"] = j
        new_people.append(new_person)
    people_list += new_people
    people_list = sortUserList(people_list)
    file_path = "data.json"
    with open(file_path, "w") as json_file:
        json.dump(people_list, json_file, indent=4)
    return "Success"


@app.route('/api/users/<name>', methods=['GET'])
def findPeopleByName(name):
    global people_list
    filtered_list = []
    for i in people_list:
        if name.lower() in i["Name"].lower():
            filtered_list.append(i)
    filtered_list = sortUserList(filtered_list)
    return jsonify(filtered_list)


def findPersonByNameAndId(name, id):
    global people_list
    for i in people_list:
        print(i["Name"])
        if name == i["Name"]:
            if int(id) == i["Id"]:
                return i


@app.route('/api/find_match/<name>&<id>', methods=['GET'])
def findMatch(name, id):
    person = findPersonByNameAndId(name, id)
    possible_matches = []
    global people_list
    print(person)
    if not person:
        return []

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
                              set(i["Likes"]) and set(person["LikesPref"]))

        check_prev_matched = not (
            any(d["Name"] == i["Name"] for d in person["PrevMatchedWith"]) or any(
                d["Name"] == person["Name"] for d in i["PrevMatchedWith"]))

        if (age_check and timezone_check and match_check and gender_check and common_likes_check and not i["Matched"] and check_prev_matched):
            possible_matches.append(i)
    possible_matches = sortUserList(possible_matches)
    return possible_matches


@app.route('/api/find_match/<name1>&<id1>&<name2>&<id2>', methods=['POST'])
def createMatch(name1, id1, name2, id2):
    global people_list
    print(id1)
    print(id2)
    user1 = findPersonByNameAndId(name1, id1)
    user2 = findPersonByNameAndId(name2, id2)
    user1["Matched"] = True
    user1["MatchedWith"] = {"Name": user2["Name"], "Id": user2["Id"]}
    user1["PrevMatchedWith"].append({"Name": user2["Name"], "Id": user2["Id"]})
    user1["TimeSinceAction"] = datetime.now(UTC).strftime("%Y/%m/%d, %H:%M:%S")
    user2["Matched"] = True
    user2["MatchedWith"] = {"Name": user1["Name"], "Id": user1["Id"]}
    user2["PrevMatchedWith"].append({"Name": user1["Name"], "Id": user1["Id"]})
    user2["TimeSinceAction"] = datetime.now(UTC).strftime("%Y/%m/%d, %H:%M:%S")
    people_list = sortUserList(people_list)
    with open("data.json", "w") as json_file:
        json.dump(people_list, json_file, indent=4)
    return "Success"


@app.route('/api/delete_match/<name>&<id>', methods=['POST'])
def removeMatch(name, id):
    global people_list
    user = findPersonByNameAndId(name, id)
    user["Matched"] = False
    matched_user = findPersonByNameAndId(
        user["MatchedWith"]["Name"], user["MatchedWith"]["Id"])
    matched_user["Matched"] = False
    matched_user["MatchedWith"] = None
    matched_user["TimeSinceAction"] = datetime.now(
        UTC).strftime("%Y/%m/%d, %H:%M:%S")
    user["MatchedWith"] = None
    user["TimeSinceAction"] = datetime.now(UTC).strftime("%Y/%m/%d, %H:%M:%S")
    people_list = sortUserList(people_list)
    with open("data.json", "w") as json_file:
        json.dump(people_list, json_file, indent=4)
    return "Success"


def sortUserList(list):
    return sorted(list, key=lambda d: (d["Matched"], d["TimeSinceAction"]))


with open('data.json', 'r') as file:
    people_list = json.load(file)

if __name__ == '__main__':
    app.run(port=5000)
