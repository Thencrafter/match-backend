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
    return send_file("data.json", mimetype="application/json")


@app.route('/api/users', methods=['GET'])
def get_users():
    global people_list
    people_list = sortUserList(people_list)
    return jsonify(people_list)


@app.route('/api/users', methods=['POST'])
def addPerson(sample=sample):
    global people_list
    data = request.get_json()
    info = data.get('text')
    new_person = sample.copy()
    info_list = info.split("]\t")
    i = 0
    for category in new_person.keys():
        info_item = info_list[i].strip("[]")
        if category == "Likes" or category == "LikesPref":
            info_item = info_item.split(", ")
        if category == "Age" or category == "TimeZone" or category == "TimeDiff" or category == "AgeUpper" or category == "AgeLower":
            info_item = int(info_item)
        if category == "Matched":
            new_person["Matched"] = False
        new_person[category] = info_item
        i += 1
    new_person["Matched"] = False
    new_person["MatchedWith"] = None
    new_person["PrevMatchedWith"] = []
    new_person["TimeSinceAction"] = datetime.now(UTC)
    for i in range(len(people_list)):
        if people_list[i]["Name"] == new_person["Name"]:
            people_list[i] = new_person
            return "Success"
    people_list.append(new_person)
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


def findPersonByName(name):
    global people_list
    for i in people_list:
        if name == i["Name"]:
            return i


@app.route('/api/find_match/<name>', methods=['GET'])
def findMatch(name):
    person = None
    possible_matches = []
    global people_list
    for p in people_list:
        if p["Name"] == name:
            person = p
            break

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
            i["Name"] in person["PrevMatchedWith"] or person["Name"] in i["PrevMatchedWith"])

        if (age_check and timezone_check and match_check and gender_check and common_likes_check and not i["Matched"] and check_prev_matched):
            possible_matches.append(i)
    possible_matches = sortUserList(possible_matches)
    return possible_matches


@app.route('/api/find_match', methods=['POST'])
def createMatch():
    global people_list
    name1 = request.args.get('user1')
    name2 = request.args.get('user2')
    user1 = findPersonByName(name1)
    user2 = findPersonByName(name2)
    user1["Matched"] = True
    user1["MatchedWith"] = user2["Name"]
    user1["PrevMatchedWith"].append(user2["Name"])
    user2["Matched"] = True
    user2["MatchedWith"] = user1["Name"]
    user2["PrevMatchedWith"].append(user1["Name"])
    people_list = sortUserList(people_list)
    with open("data.json", "w") as json_file:
        json.dump(people_list, json_file, indent=4)
    return "Success"


@app.route('/api/delete_match/<name>', methods=['POST'])
def removeMatch(name):
    global people_list
    user = findPersonByName(name)
    user["Matched"] = False
    findPersonByName(user["MatchedWith"])["Matched"] = False
    findPersonByName(user["MatchedWith"])["MatchedWith"] = None
    findPersonByName(user["MatchedWith"])[
        "TimeSinceAction"] = datetime.now(UTC)
    user["MatchedWith"] = None
    user["TimeSinceAction"] = datetime.now(UTC)
    people_list = sortUserList(people_list)
    with open("data.json", "w") as json_file:
        json.dump(people_list, json_file, indent=4)
    return "Success"


def sortUserList(list):
    return (sorted(list), key=lambda d: (d["TimeSinceAction"], d["Matched"])))


with open('data.json', 'r') as file:
    people_list = json.load(file)

if __name__ == '__main__':
    app.run(port=5000)
    '''upload_file("data.json", "data.json")
    download_file("1Mrgq7IycdMYb7NzDeqnP7D6MAAliCg_O", "data.json")'''
    # Example usage:

    # Create a new folder
    # create_folder("MyNewFolder")

    # List folders and files
    # list_folder()

    # Delete a file or folder by ID
    # delete_files("your_file_or_folder_id")

    # Download a file by its ID
    # download_file("your_file_id", "destination_path/file_name.extension")'''


'''info = input()
addPerson(info, sample)
info = input()
addPerson(info, sample)'''
