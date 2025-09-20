import uuid
from datetime import datetime
from typing import List, Dict, Any


class VideoCall:
    """
    VideoCall class to manage video call sessions and their data.
    
    Attributes:
        attendees (Dict[str, Dict[str, str]]): Dictionary of attendees with their socket IDs and names
        transcript (List[Dict[str, Any]]): List of transcript entries with speaker, text, and timestamp
        room_code (str): Unique room code for the video call
        uuid (str): Unique identifier for the video call session
        created_at (datetime): Timestamp when the video call was created
        file_path (str): Path to the transcript file (for backward compatibility)
    """
    
    def __init__(self, room_code: str, call_uuid: str = None):
        """
        Initialize a new VideoCall session.
        
        Args:
            room_code (str): The room code for the video call
            call_uuid (str, optional): Custom UUID for the call. If not provided, one will be generated.
        """
        self.room_code = room_code
        self.uuid = call_uuid or str(uuid.uuid4())
        self.attendees = {}  # {user_id: {"name": "John", "socketId": "abc123"}}
        self.transcript = []  # [{"speaker": "John", "transcription": "Hello", "timestamp": 1234567890}]
        self.created_at = datetime.now()
        self.file_path = None  # For backward compatibility if needed
        
    def add_attendee(self, user_id: str, name: str, socket_id: str):
        """
        Add an attendee to the video call.
        
        Args:
            user_id (str): Unique identifier for the user
            name (str): Display name of the user
            socket_id (str): Socket ID for the user's connection
        """
        self.attendees[user_id] = {
            "name": name,
            "socketId": socket_id
        }
        
    def remove_attendee(self, user_id: str):
        """
        Remove an attendee from the video call.
        
        Args:
            user_id (str): Unique identifier for the user to remove
        """
        if user_id in self.attendees:
            del self.attendees[user_id]
            
    def update_attendee_name(self, user_id: str, new_name: str):
        """
        Update an attendee's name.
        
        Args:
            user_id (str): Unique identifier for the user
            new_name (str): New display name for the user
        """
        if user_id in self.attendees:
            self.attendees[user_id]["name"] = new_name
            
    def add_transcript_entry(self, speaker: str, transcription: str, timestamp: int = None):
        """
        Add a new transcript entry to the video call.
        
        Args:
            speaker (str): Name of the person speaking
            transcription (str): The transcribed text
            timestamp (int, optional): Timestamp in milliseconds. If not provided, current time is used.
        """
        if timestamp is None:
            timestamp = int(datetime.now().timestamp() * 1000)
            
        transcript_entry = {
            "speaker": speaker,
            "transcription": transcription,
            "timestamp": timestamp
        }
        
        self.transcript.append(transcript_entry)
        
    def get_transcript(self) -> List[Dict[str, Any]]:
        """
        Get the complete transcript for the video call.
        
        Returns:
            List[Dict[str, Any]]: List of transcript entries
        """
        return self.transcript.copy()
        
    def get_attendees(self) -> List[Dict[str, str]]:
        """
        Get the list of attendees in a format suitable for client consumption.
        
        Returns:
            List[Dict[str, str]]: List of attendees with userId and name
        """
        return [
            {"userId": user_id, "name": data["name"]} 
            for user_id, data in self.attendees.items()
        ]
        
    def get_attendees_count(self) -> int:
        """
        Get the number of attendees in the video call.
        
        Returns:
            int: Number of attendees
        """
        return len(self.attendees)
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the VideoCall object to a dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the video call
        """
        return {
            "uuid": self.uuid,
            "room_code": self.room_code,
            "attendees": self.attendees,
            "transcript": self.transcript,
            "created_at": self.created_at.isoformat(),
            "attendees_count": self.get_attendees_count()
        }
        
    def __str__(self) -> str:
        """String representation of the VideoCall object."""
        return f"VideoCall(room_code='{self.room_code}', uuid='{self.uuid}', attendees={self.get_attendees_count()})"
        
    def __repr__(self) -> str:
        """Detailed string representation of the VideoCall object."""
        return (f"VideoCall(room_code='{self.room_code}', uuid='{self.uuid}', "
                f"attendees={self.attendees}, transcript_entries={len(self.transcript)}, "
                f"created_at='{self.created_at}')")