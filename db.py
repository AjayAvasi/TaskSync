from pymongo import MongoClient
import uuid
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is required")

client = MongoClient(MONGO_URI)
db = client['rooms_db']

try:
    db.command("ping")
    print("MongoDB connection: SUCCESS")
except Exception as e:
    print("MongoDB connection: FAILED", e)


def generate_room_code():
    return uuid.uuid4().hex[:6].upper()


def normalize_members(members):
    """Convert legacy string members to object format"""
    normalized = []
    for member in members:
        if isinstance(member, str):
            # Legacy format: convert string to object
            normalized.append({
                "username": member,
                "tasks": [],
                "role": "member"
            })
        elif isinstance(member, dict):
            # Already in correct format
            normalized.append(member)
    return normalized


def get_member_usernames(members):
    """Safely extract usernames from members array"""
    usernames = []
    for member in members:
        if isinstance(member, str):
            usernames.append(member)
        elif isinstance(member, dict) and "username" in member:
            usernames.append(member["username"])
    return usernames


def create_room(owner, room_name):
    for _ in range(5):
        room_code = generate_room_code()
        if not db.rooms.find_one({"room_code": room_code}):
            room = {
                "room_code": room_code,
                "room_name": room_name,
                "owner": owner,
                "members": [
                    {
                        "username": owner,
                        "tasks": [],
                        "role": "host"
                    }
                ],
                "created_at": datetime.utcnow()
            }
            try:
                db.rooms.insert_one(room)
                return room_code
            except Exception as e:
                print("Error inserting room:", e)
                return None
    print("Failed to generate a unique room code.")
    return None


def join_room(room_code, username):
    room = db.rooms.find_one({"room_code": room_code})
    if not room:
        return False, "Room not found"

    # Get existing member usernames safely
    existing_usernames = get_member_usernames(room.get("members", []))

    # Check if user is already in room
    if username in existing_usernames:
        return False, "User already in room"

    # Add new member
    db.rooms.update_one(
        {"room_code": room_code},
        {"$push": {"members": {"username": username, "tasks": [], "role": "member"}}}
    )
    return True, "Joined room successfully"


def get_room(room_code):
    room = db.rooms.find_one({"room_code": room_code})
    if room and "members" in room:
        # Normalize members format
        room["members"] = normalize_members(room["members"])
        # Update the database with normalized format
        db.rooms.update_one(
            {"room_code": room_code},
            {"$set": {"members": room["members"]}}
        )
    return room


def add_task_to_user_in_room(room_code, creator, assigned_to, title, description=""):
    room = db.rooms.find_one({"room_code": room_code})
    if not room:
        return False, "Room not found"
    if room["owner"] != creator:
        return False, "Only room owner can create tasks"

    # Handle both string and dict formats for members
    member_usernames = []
    for m in room.get("members", []):
        if isinstance(m, str):
            member_usernames.append(m)
        elif isinstance(m, dict) and "username" in m:
            member_usernames.append(m["username"])

    if assigned_to not in member_usernames:
        return False, "Assigned user not in room"

    task = {
        "task_id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "created_by": creator,
        "timestamp": datetime.utcnow()
    }

    # Find the member and update their tasks
    members = room.get("members", [])
    for i, member in enumerate(members):
        if isinstance(member, str) and member == assigned_to:
            # Convert string to dict format and add task
            members[i] = {
                "username": member,
                "tasks": [task],
                "role": "host" if member == room["owner"] else "member"
            }
            break
        elif isinstance(member, dict) and member.get("username") == assigned_to:
            # Add task to existing dict
            if "tasks" not in member:
                member["tasks"] = []
            member["tasks"].append(task)
            break

    # Update the entire members array
    result = db.rooms.update_one(
        {"room_code": room_code},
        {"$set": {"members": members}}
    )

    if result.modified_count == 1:
        return True, task
    else:
        return False, "Failed to add task"


def get_tasks_for_user_in_room(room_code, username):
    room = db.rooms.find_one({"room_code": room_code})
    if not room:
        return None

    # Get existing usernames safely
    existing_usernames = []
    for m in room.get("members", []):
        if isinstance(m, str):
            existing_usernames.append(m)
        elif isinstance(m, dict) and "username" in m:
            existing_usernames.append(m["username"])

    member = next((m for m in room["members"] if isinstance(m, dict) and m.get("username") == username), None)
    if member:
        return member.get("tasks", [])
    return None


# NEW FUNCTION: Get all rooms for a user
def get_user_rooms(username):
    """Get all rooms where the user is either the owner or a member"""
    try:
        # Find rooms where user is owner OR user is in members array
        rooms = list(db.rooms.find({
            "$or": [
                {"owner": username},
                {"members.username": username},
                {"members": username}  # Handle legacy string format
            ]
        }))

        return rooms
    except Exception as e:
        print(f"Error in get_user_rooms: {e}")
        return []

def get_room_by_name(room_name):
    room = db.rooms.find_one({"room_name": room_name})
    if room and "members" in room:
        # Normalize members format
        room["members"] = normalize_members(room["members"])
        # Update the database with normalized format
        db.rooms.update_one(
            {"room_name": room_name},
            {"$set": {"members": room["members"]}}
        )
    return room