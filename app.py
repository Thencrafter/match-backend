import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, io, MediaFileUpload
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext
import daytime
from flask import Flask, request, jsonify
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

people_list = [

]

app = Flask(__name__)
CORS(app)

class MatchmakingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Matchmaking App")
        
        # Main frame
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        
        # Add User button
        self.add_user_btn = tk.Button(self.main_frame, text="Add User", command=self.show_add_user_window)
        self.add_user_btn.pack(pady=5)
        
        # Users list frame
        self.users_frame = tk.Frame(self.main_frame)
        self.users_frame.pack(fill=tk.BOTH, expand=True)
        
        
        

        # Title for users list
        tk.Label(self.users_frame, text="User List", font=('Arial', 12, 'bold')).pack()
        
        # Canvas and scrollbar for users list
        self.canvas = tk.Canvas(self.users_frame)
        self.scrollbar = tk.Scrollbar(self.users_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all"),
                height=500,
                width= 1000
            )
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Placeholder for displaying users
        self.display_users([])
        
    def display_users(self, users):
        """Display the list of users in the scrollable frame"""
        # Clear the frame first
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        if not users:
            tk.Label(self.scrollable_frame, text="No users available").pack()
            return
        
        # User rows
        for i, user in enumerate(users, start=1):
            user_frame = tk.Frame(self.scrollable_frame)
            user_frame.pack(fill=tk.X, pady=2)
            
            # Display user info
            tk.Label(user_frame, text=user.get("Name", ""), width=12).grid(row=0, column=0, padx=5)
            tk.Label(user_frame, text="Age: " + str(user.get("Age", "")), width=6).grid(row=0, column=1, padx=5)
            tk.Label(user_frame, text=user.get("Gender", ""), width=5).grid(row=0, column=2, padx=5)
            tk.Label(user_frame, text=user.get("Pronouns", ""), width=7).grid(row=0, column=3, padx=5)
            # Display likes (truncated if too long)
            likes = ", ".join(user.get("Likes", []))
            if len(likes) > 50:
                likes = likes[:50] + "..."
            tk.Label(user_frame, text=likes, width=30, height=2, wraplength=200).grid(row=0, column=4, padx=5)
            tk.Label(user_frame, text="Extra: " + user.get("Extra", ""), width=30, height=2, wraplength=200).grid(row=0, column=5, padx=5)
            if user.get("MatchedWith", ""): tk.Label(user_frame, text="Matched With: " + user.get("MatchedWith", ""), width=20).grid(row=0, column=6, padx=5)
            else: tk.Label(user_frame, text="Matched With: None", width=20).grid(row=0, column=6, padx=5)
            # Matched status
            matched_status = "Yes" if user.get("Matched", False) else "No"
            tk.Label(user_frame, text=matched_status).grid(row=0, column=7, padx=5)
            
            # Find Match button
            if not user.get("Matched", False):
                tk.Button(user_frame, text="Find Match", 
                         command=lambda u=user: self.show_matches(u)).grid(row=0, column=8, padx=5)
            else:
                # For matched users, show "Remove Match" button
                tk.Button(user_frame, text="Remove Match", 
                         command=lambda u=user: self.remove_match(u)).grid(row=0, column=7, padx=5)
    
    def remove_match(self, user):
        """Remove the match status from a user"""
        user["Matched"] = False
        findPersonByName(user["MatchedWith"])["Matched"] = False
        findPersonByName(user["MatchedWith"])["MatchedWith"] = None
        user["MatchedWith"] = None  
        messagebox.showinfo("Match Removed", f"{user.get('Name', 'User')} is no longer matched")
        # Refresh the display
        with open("data.json", "w") as json_file:
            json.dump(people_list, json_file, indent=4)
        self.display_users(people_list)  # Note: 'users' should be your actual user list

    def show_matches(self, user):
        """Show potential matches for a user"""
        # Call the findMatch function (placeholder)
        matches = findMatch(user["Name"])
        
        # Create a new window to display matches
        match_window = tk.Toplevel(self.root, width=1000)
        match_window.title(f"Matches for {user.get('Name', 'User')}")
        
        tk.Label(match_window, text=f"Potential matches for {user.get('Name', 'User')}", 
                 font=('Arial', 12, 'bold')).pack(pady=5)
        
        if not matches:
            tk.Label(match_window, text="No matches found").pack()
            return
            
        # Display matches
        for match in matches:
            match_frame = tk.Frame(match_window)
            match_frame.pack(fill=tk.X, pady=2)
            
            # Match info
            tk.Label(match_frame, text=match.get("Name", ""), width=12).grid(row=0, column=0, padx=5)
            tk.Label(match_frame, text="Age: " + str(match.get("Age", "")), width=6).grid(row=0, column=1, padx=5)
            tk.Label(match_frame, text=match.get("Gender", ""), width=5).grid(row=0, column=2, padx=5)
            tk.Label(match_frame, text=match.get("Pronouns", ""), width=7).grid(row=0, column=3, padx=5)
            # Display likes (truncated if too long)
            likes = ", ".join(match.get("Likes", []))
            if len(likes) > 50:
                likes = likes[:50] + "..."
            tk.Label(match_frame, text=likes, width=30, height=2, wraplength=200).grid(row=0, column=4, padx=5)
            tk.Label(match_frame, text="Extra: " + user.get("Extra", ""), width=30, height=2, wraplength=200).grid(row=0, column=5, padx=5)
            
            # Match button
            tk.Button(match_frame, text="Match", 
                     command=lambda u1=user, u2=match: self.create_match(u1, u2)).grid(row=0, column=6, padx=5)
    
    def create_match(self, user1, user2):
        """Create a match between two users"""
        user1["Matched"] = True
        user1["MatchedWith"] = user2["Name"]
        user1["PrevMatchedWith"].append(user2["Name"])
        user2["Matched"] = True
        user2["MatchedWith"] = user1["Name"]
        user2["PrevMatchedWith"].append(user1["Name"])
        messagebox.showinfo("Match Created", f"{user1.get('Name', 'User1')} and {user2.get('Name', 'User2')} are now matched!")
        # Refresh the display
        with open("data.json", "w") as json_file:
            json.dump(people_list, json_file, indent=4)
        self.display_users(people_list)  # Note: 'users' should be your actual user list
    
    def show_add_user_window(self):
        """Show window for adding a new user"""
        add_window = tk.Toplevel(self.root)
        add_window.title("Add New User")
        
        tk.Label(add_window, text="Enter user data:", font=('Arial', 10)).pack(pady=5)
        
        # Text area for user input
        self.user_input = scrolledtext.ScrolledText(add_window, width=60, height=20)
        self.user_input.pack(padx=10, pady=5)

        self.user_input.insert(tk.INSERT, chars="")
        
        # Confirm button
        tk.Button(add_window, text="Confirm", 
                 command=lambda: self.add_user(self.user_input.get("1.0", tk.END), add_window)).pack(pady=5)
    
    def add_user(self, user_data, window):
        """Add a new user"""
        try:
            # Call the addPerson function (placeholder)
            addPerson(user_data, sample)
            window.destroy()
            messagebox.showinfo("Success", "User added successfully!")
            # Refresh the display
            self.display_users(people_list)  # Note: 'users' should be your actual user list
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add user: {str(e)}")

'''# Define the Google Drive API scopes and service account file path
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = "match-464708-871cf3d71c4a.json"

# Create credentials using the service account file
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Build the Google Drive service
drive_service = build('drive', 'v3', credentials=credentials)

def download_file(file_id, destination_path):
    """Download a file from Google Drive by its ID."""
    global people_list
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.FileIO(destination_path, mode='wb')
    
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")
    with open('data.json', 'r') as file:
        people_list = json.load(file)
    app.display_users(people_list)

def upload_file(file_path, file_name, id, mime_type='text/plain', parent_folder_id=None):
    """Upload a file to Google Drive."""
    file_metadata = {
        'name': file_name,
        'parents': [parent_folder_id] if parent_folder_id else []
   }
    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    file = drive_service.files().update(
    fileId=id, media_body=media).execute()
    print(f"Uploaded file with ID: {file.get('id')}")

def list_folder(parent_folder_id=None, delete=False):
    """List folders and files in Google Drive."""
    results = drive_service.files().list(
        q=f"'{parent_folder_id}' in parents and trashed=false" if parent_folder_id else None,
        pageSize=1000,
        fields="nextPageToken, files(id, name, mimeType)"
    ).execute()
    items = results.get('files', [])

    if not items:
        print("No folders or files found in Google Drive.")
    else:
        print("Folders and files in Google Drive:")
        for item in items:
            print(f"Name: {item['name']}, ID: {item['id']}, Type: {item['mimeType']}")'''
            
@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify(people_list)

@app.route('/api/users', methods=['POST'])
def addPerson(sample = sample):
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
    for i in range(len(people_list)):
        if people_list[i]["Name"] == new_person["Name"]:
            people_list[i] = new_person
            return "Success"
    people_list.append(new_person)
    file_path = "data.json"
    with open(file_path, "w") as json_file:
        json.dump(people_list, json_file, indent=4)
    return "Success"

@app.route('/api/users/<name>', methods=['GET'])
def findPeopleByName(name):
    filtered_list = []
    for i in people_list:
        if name in i["Name"]:
            filtered_list.append(i)
    return jsonify(filtered_list)

def findPersonByName(name):
    for i in people_list:
        if name == i["Name"]:
            return i

@app.route('/api/find_match/<name>', methods=['GET'])
def findMatch(name):
    person = None
    possible_matches = []

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
        
        check_prev_matched = not (i["Name"] in person["PrevMatchedWith"] or person["Name"] in i["PrevMatchedWith"])
        
        if(age_check and timezone_check and match_check and gender_check and common_likes_check and not i["Matched"] and check_prev_matched):
            possible_matches.append(i)
    print(possible_matches)
    return possible_matches

@app.route('/api/find_match', methods=['POST'])
def createMatch():
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
        with open("data.json", "w") as json_file:
            json.dump(people_list, json_file, indent=4)
        return "Success"

@app.route('/api/delete_match/<name>', methods=['POST'])
def removeMatch(name):
        user = findPersonByName(name)
        user["Matched"] = False
        findPersonByName(user["MatchedWith"])["Matched"] = False
        findPersonByName(user["MatchedWith"])["MatchedWith"] = None
        user["MatchedWith"] = None  
        with open("data.json", "w") as json_file:
            json.dump(people_list, json_file, indent=4)
        return "Success"

with open('data.json', 'r') as file:
    people_list = json.load(file)

if __name__ == '__main__':
    app.run(port=5000)
    root = tk.Tk()
    new_app = MatchmakingApp(root)
    new_app.display_users(people_list)  # Display the sample users
    root.mainloop()
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

