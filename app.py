from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room as socket_join_room, leave_room as socket_leave_room
from db import create_room, join_room as db_join_room, get_room, add_task_to_user_in_room, get_tasks_for_user_in_room, get_user_rooms, get_room_by_name
from flask_cors import CORS
import uuid
from collections import defaultdict
import os
import sys
import base64
import json
import tempfile
import assemblyai as aai
from datetime import datetime
from video_call import VideoCall
from tasksync import extract_tasks
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'fallback-secret-key')

# Get AssemblyAI API key from environment
assemblyai_api_key = os.getenv('ASSEMBLYAI_API_KEY')
if not assemblyai_api_key:
    raise ValueError("ASSEMBLYAI_API_KEY environment variable is required")

aai.settings.api_key = assemblyai_api_key


# Enable CORS for all routes
CORS(app, origins="*")

# Configure SocketIO with comprehensive CORS settings
socketio = SocketIO(app, 
                   cors_allowed_origins="*", 
                   logger=True, 
                   engineio_logger=True,
                   transports=['polling', 'websocket'],
                   allow_upgrades=True)

# Store room users with their names
rooms = defaultdict(dict)  # {room: {userId: {"name": "John", "socketId": "abc123"}}}
user_rooms = {}  # {socketId: room}

# Store VideoCall objects for each room
video_calls = {}  # {room: VideoCall}

# Store transcriptions for each room (deprecated - kept for backward compatibility)
transcriptions = defaultdict(list)  # {room: [{"speaker": "John", "transcription": "Hello world"}]}
transcript_files = {}  # {room: file_path} - Track transcript files for each room (deprecated)

def create_transcript_file(room_name):
    """Create a new transcript file for a room"""
    room_uuid = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"transcript_{room_name}_{timestamp}_{room_uuid[:8]}.txt"
    filepath = os.path.join("/Users/ajayavasi/Code/TaskSync/transcripts", filename)
    
    # Create transcripts directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Create the file with header
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Video Call Transcript\n")
        f.write(f"Room: {room_name}\n")
        f.write(f"UUID: {room_uuid}\n")
        f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
    
    transcript_files[room_name] = filepath
    print(f"Created transcript file: {filepath}")
    return filepath

def append_to_transcript_file(room_name, speaker, transcription, timestamp):
    """Append a new transcription to the room's transcript file"""
    if room_name not in transcript_files:
        create_transcript_file(room_name)
    
    filepath = transcript_files[room_name]
    
    try:
        with open(filepath, 'a', encoding='utf-8') as f:
            time_str = datetime.fromtimestamp(timestamp / 1000).strftime('%H:%M:%S') if timestamp else datetime.now().strftime('%H:%M:%S')
            f.write(f"[{time_str}] {speaker}: {transcription}\n")
        print(f"Appended transcription to {filepath}")
    except Exception as e:
        print(f"Error writing to transcript file {filepath}: {e}")

def transcribe_audio(audio_file_path, speaker_name):
    """
    Transcribe audio from file path.
    The file will be deleted after processing.
    """
    try:
       config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.universal)
       transcript = aai.Transcriber(config=config).transcribe(audio_file_path)
       if transcript.status == "error":
           raise RuntimeError(f"Transcription failed: {transcript.error}")
       return transcript.text
    finally:
        # Always delete the file after processing
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)
            print(f"Deleted temporary audio file: {audio_file_path}")

@app.route('/transcriptions/<room_name>')
def get_transcriptions(room_name):
    """Get all transcriptions for a specific room from VideoCall object"""
    if room_name in video_calls:
        # Get transcriptions from VideoCall object
        room_transcriptions = video_calls[room_name].get_transcript()
        return json.dumps(room_transcriptions, indent=2)
    else:
        # Fallback to legacy storage for backward compatibility
        room_transcriptions = transcriptions.get(room_name, [])
        return json.dumps(room_transcriptions, indent=2)

@app.route('/videocall/<room_name>')
def get_video_call_info(room_name):
    """Get complete VideoCall information for a specific room"""
    if room_name in video_calls:
        video_call_info = video_calls[room_name].to_dict()
        return json.dumps(video_call_info, indent=2)
    else:
        return json.dumps({"error": "Room not found"}, indent=2), 404

@app.route('/videocalls')
def get_all_video_calls():
    """Get information about all active video calls"""
    all_calls = {}
    for room_name, video_call in video_calls.items():
        all_calls[room_name] = video_call.to_dict()
    return json.dumps(all_calls, indent=2)

@app.route('/')
def index():
    # Serve the HTML file directly from the server
    try:
        with open('index.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return """
        <h1>File not found</h1>
        <p>Please make sure 'index.html' is in the same directory as the server script.</p>
        """

@app.route('/create-room', methods=['POST'])
def api_create_room():
    data = request.json
    room_name = data.get('room_name')
    user_name = data.get('user_name')

    if not room_name or not user_name:
        return jsonify({"error": "room_name and user_name required"}), 400

    room_code = create_room(user_name, room_name)
    if not room_code:
        return jsonify({"error": "Could not create room"}), 500

    return jsonify({
        "status": "Room created",
        "room_code": room_code,
        "room_name": room_name,
        "owner": user_name,
        "members": [user_name]  # Host included in members
    }), 201


@app.route('/join-room', methods=['POST'])
def api_join_room():
    print("=== JOIN ROOM REQUEST ===")
    data = request.json
    print(f"Request data: {data}")

    room_code = data.get('room_code')
    user_name = data.get('user_name')

    print(f"Room code: {room_code}, User name: {user_name}")

    if not room_code or not user_name:
        return jsonify({"error": "room_code and user_name required"}), 400

    success, message = db_join_room(room_code, user_name)
    print(f"Join result: success={success}, message={message}")

    if success:
        room = get_room(room_code)
        if room:
            member_list = [m["username"] for m in room["members"]]
            response_data = {
                "status": message,
                "room_code": room_code,
                "room_name": room["room_name"],
                "owner": room["owner"],
                "members": member_list
            }
            print(f"Success response: {response_data}")
            return jsonify(response_data), 200
        else:
            return jsonify({"error": "Room not found after join"}), 500
    else:
        print(f"Join failed: {message}")
        return jsonify({"error": message}), 400


@app.route('/create-task', methods=['POST'])
def api_create_task():
    data = request.json
    room_code = data.get('room_code')
    creator = data.get('creator')
    assigned_to = data.get('assigned_to')
    title = data.get('title')
    description = data.get('description', "")

    if not all([room_code, creator, assigned_to, title]):
        return jsonify({"error": "room_code, creator, assigned_to, and title required"}), 400

    success, result = add_task_to_user_in_room(room_code, creator, assigned_to, title, description)
    if success:
        return jsonify({"status": "Task created", "task": result}), 201
    else:
        return jsonify({"error": result}), 400


@app.route('/tasks/<room_code>/<username>', methods=['GET'])
def api_get_tasks(room_code, username):
    tasks = get_tasks_for_user_in_room(room_code, username)
    if tasks is None:
        return jsonify({"error": "Room or user not found"}), 404
    return jsonify({"tasks": tasks}), 200


@app.route('/room/<room_code>', methods=['GET'])
def api_get_room(room_code):
    room = get_room(room_code)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    if "_id" in room:
        room["_id"] = str(room["_id"])

    # Safe transformation with error handling
    members_dict = {}
    for member in room.get("members", []):
        if isinstance(member, dict) and "username" in member:
            members_dict[member["username"]] = member.get("tasks", [])
        elif isinstance(member, str):
            # Handle legacy data where members might be just strings
            members_dict[member] = []

    room["members"] = members_dict
    return jsonify(room), 200


# NEW ENDPOINT: Get all rooms for a user
@app.route('/user/<username>/rooms', methods=['GET'])
def api_get_user_rooms(username):
    """Get all rooms that a user is part of (either as owner or member)"""
    try:
        rooms = get_user_rooms(username)

        # Format the response
        formatted_rooms = []
        for room in rooms:
            if "_id" in room:
                room["_id"] = str(room["_id"])

            # Get member count
            member_count = len(room.get("members", []))

            formatted_room = {
                "id": room["room_code"],
                "name": room["room_name"],
                "owner": room["owner"],
                "member_count": member_count,
                "created_at": room.get("created_at")
            }
            formatted_rooms.append(formatted_room)

        return jsonify({"rooms": formatted_rooms}), 200
    except Exception as e:
        print(f"Error getting user rooms: {e}")
        return jsonify({"error": "Failed to get user rooms"}), 500


@socketio.on('audio-chunk')
def handle_audio_chunk(data):
    user_id = request.sid
    
    if user_id not in user_rooms:
        print(f'Received audio chunk from user not in room: {user_id}')
        print(f'Current user_rooms: {user_rooms}')
        print(f'Current rooms: {dict(rooms)}')
        return
    
    room = user_rooms[user_id]
    speaker_name = data.get('speaker', 'Unknown')
    audio_data = data.get('audioData', '')
    timestamp = data.get('timestamp', 0)
    audio_format = data.get('format', 'wav')  # Default to wav if not specified
    
    try:
        # Decode base64 audio data
        audio_bytes = base64.b64decode(audio_data)
        
        # Create temporary file
        temp_dir = tempfile.gettempdir()
        temp_filename = f"audio_{user_id}_{timestamp}.{audio_format}"
        temp_file_path = os.path.join(temp_dir, temp_filename)
        
        # Save audio data to temporary file
        with open(temp_file_path, 'wb') as f:
            f.write(audio_bytes)
        
        print(f"Saved audio chunk to: {temp_file_path}")
        
        # Transcribe audio (file will be deleted inside this function)
        transcription_text = transcribe_audio(temp_file_path, speaker_name)
        
        # Store transcription in VideoCall object
        if room in video_calls:
            video_calls[room].add_transcript_entry(speaker_name, transcription_text, timestamp)
            print(f'Added transcription to VideoCall object for room {room}')
        
        # Store transcription in legacy format for backward compatibility
        transcription_entry = {
            "speaker": speaker_name,
            "transcription": transcription_text,
            "timestamp": timestamp
        }
        
        transcriptions[room].append(transcription_entry)
        
        # Save to transcript file (backward compatibility)        
        # Emit transcription to all users in the room
        emit('new-transcription', transcription_entry, room=room)
        
        print(f'Transcribed audio from {speaker_name} in room {room}: "{transcription_text}"')
        
    except Exception as e:
        print(f'Error processing audio chunk: {e}')
        # Clean up file if there was an error and file still exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"Cleaned up file after error: {temp_file_path}")

@socketio.on('connect')
def handle_connect():
    user_id = str(uuid.uuid4())
    print(f'User {user_id} connected from {request.remote_addr}')

@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.sid
    if user_id in user_rooms:
        room = user_rooms[user_id]
        socket_leave_room(room)
        
        # Remove user from room
        if user_id in rooms[room]:
            del rooms[room][user_id]
        
        # Remove from VideoCall object if it exists
        if room in video_calls:
            video_calls[room].remove_attendee(user_id)
        
        del user_rooms[user_id]
        
        # Notify other users in the room
        emit('user-left', user_id, room=room)
        
        # Send updated user list
        user_list = [{"userId": uid, "name": data["name"]} for uid, data in rooms[room].items()]
        emit('room-users', user_list, room=room)
        
        print(f'User {user_id} disconnected from room {room}')

        if(len(user_list) == 0):
            print(f"No users left in room {room}")
            create_and_save_tasks(room)
        
            

@socketio.on('join-room')
def handle_join_room(data):
    user_id = request.sid
    
    # Extract room and name from data
    if isinstance(data, dict):
        room_name = data.get('room', 'default')
        user_name = data.get('name', 'Anonymous')
    else:
        # Backward compatibility for old format
        room_name = data
        user_name = 'Anonymous'
    
    # Leave previous room if any
    if user_id in user_rooms:
        old_room = user_rooms[user_id]
        socket_leave_room(old_room)
        if user_id in rooms[old_room]:
            del rooms[old_room][user_id]
        
        # Remove from VideoCall object if it exists
        if old_room in video_calls:
            video_calls[old_room].remove_attendee(user_id)
        
        # Notify old room
        emit('user-left', user_id, room=old_room)
        user_list = [{"userId": uid, "name": data["name"]} for uid, data in rooms[old_room].items()]
        emit('room-users', user_list, room=old_room)
    
    # Join new room
    socket_join_room(room_name)
    rooms[room_name][user_id] = {"name": user_name, "socketId": user_id}
    user_rooms[user_id] = room_name
    
    # Create VideoCall object for new room if it doesn't exist
    if room_name not in video_calls:
        video_calls[room_name] = VideoCall(room_name)
        print(f"Created new VideoCall object for room: {room_name}")
    
    # Add attendee to VideoCall object
    video_calls[room_name].add_attendee(user_id, user_name, user_id)
    
    # Create transcript file for new room if it doesn't exist (backward compatibility)
    if room_name not in transcript_files:
        create_transcript_file(room_name)
    
    # Notify existing users about new user
    emit('user-joined', {"userId": user_id, "name": user_name}, room=room_name, include_self=False)
    
    # Send current users list to everyone in room
    user_list = [{"userId": uid, "name": user_data["name"]} for uid, user_data in rooms[room_name].items()]
    emit('room-users', user_list, room=room_name)
    
    print(f'User {user_id} ({user_name}) joined room {room_name}')
    print(f'Room {room_name} now has {len(rooms[room_name])} users')
    print(f'VideoCall object attendees: {video_calls[room_name].get_attendees_count()}')
    print(f'Updated user_rooms: {user_rooms}')
    print(f'Updated rooms[{room_name}]: {rooms[room_name]}')
    

@socketio.on('update-name')
def handle_update_name(new_name):
    user_id = request.sid
    
    if user_id in user_rooms:
        room = user_rooms[user_id]
        if user_id in rooms[room]:
            # Update the user's name
            rooms[room][user_id]["name"] = new_name or 'Anonymous'
            
            # Update name in VideoCall object if it exists
            if room in video_calls:
                video_calls[room].update_attendee_name(user_id, new_name or 'Anonymous')
            
            # Notify other users about the name change
            emit('user-name-updated', {"userId": user_id, "name": new_name}, room=room, include_self=False)
            
            # Send updated user list
            user_list = [{"userId": uid, "name": user_data["name"]} for uid, user_data in rooms[room].items()]
            emit('room-users', user_list, room=room)
            
            print(f'User {user_id} updated name to: {new_name}')

@socketio.on('leave-room')
def handle_leave_room(room_name):
    user_id = request.sid
    
    if user_id in user_rooms and user_rooms[user_id] == room_name:
        socket_leave_room(room_name)
        if user_id in rooms[room_name]:
            del rooms[room_name][user_id]
        
        # Remove from VideoCall object if it exists
        if room_name in video_calls:
            video_calls[room_name].remove_attendee(user_id)
        
        del user_rooms[user_id]
        
        # Notify other users in the room
        emit('user-left', user_id, room=room_name)
        
        # Send updated user list
        user_list = [{"userId": uid, "name": data["name"]} for uid, data in rooms[room_name].items()]
        emit('room-users', user_list, room=room_name)
        
        print(f'User {user_id} left room {room_name}')
        if(len(user_list) == 0):
            print(f"No users left in room {room_name}")
            create_and_save_tasks(room_name)

def create_and_save_tasks(room_name):
    if room_name not in video_calls:
        print(f"No VideoCall object for room {room_name}, cannot create tasks.")
        return
    
    video_call = video_calls[room_name]
    transcript = video_call.get_transcript()
    if not transcript:
        print(f"No transcript available for room {room_name}, cannot create tasks.")
        return
    transcript_text = "\n".join([f"{entry['speaker']}: {entry['transcription']}" for entry in transcript])
    room_data = get_room(room_name)
    if not room_data:
        print(f"No room data found for room name {room_name}, cannot create tasks.")
        return
    attendees = [{"username": m["username"], "role": m["role"]} for m in room_data.get("members", []) if isinstance(m, dict) and "username" in m]
    transcript_text += "\n\nTeam Members and Roles:\n"
    for attendee in attendees:
        transcript_text += f"- {attendee['username']}: {attendee.get('role', 'member')}\n"
    gen_tasks = extract_tasks(transcript_text)
    print("Generated tasks:", gen_tasks)



@socketio.on('offer')
def handle_offer(data):
    user_id = request.sid
    target_user = data['userId']
    offer = data['offer']
    
    emit('offer', {
        'userId': user_id,
        'offer': offer
    }, room=target_user)

@socketio.on('answer')
def handle_answer(data):
    user_id = request.sid
    target_user = data['userId']
    answer = data['answer']
    
    emit('answer', {
        'userId': user_id,
        'answer': answer
    }, room=target_user)

@socketio.on('ice-candidate')
def handle_ice_candidate(data):
    user_id = request.sid
    target_user = data['userId']
    candidate = data['candidate']
    
    emit('ice-candidate', {
        'userId': user_id,
        'candidate': candidate
    }, room=target_user)

if __name__ == '__main__':
    # Get port from command line argument or default to 5001
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
    
    print("Starting minimal video call server...")
    print(f"Server will run on port {port}")
    print("Open your browser and go to:")
    print(f"  http://localhost:{port}?room=yourroom")
    print("")
    print("Note: For camera/microphone access, you may need HTTPS.")
    print("If you're not on localhost, consider using a reverse proxy")
    print("like ngrok or deploying with HTTPS certificates.")
    print("")
    
    # Check if we should use HTTPS
    cert_file = 'cert.pem'
    key_file = 'key.pem'
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print("Found SSL certificates, starting with HTTPS...")
        print(f"  https://localhost:{port}?room=yourroom")
        socketio.run(app, host='0.0.0.0', port=port, debug=True, 
                    ssl_context=(cert_file, key_file))
    else:
        print("No SSL certificates found, starting with HTTP...")
        print("For production use, generate SSL certificates:")
        print("  openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes")
        socketio.run(app, host='0.0.0.0', port=port, debug=True)