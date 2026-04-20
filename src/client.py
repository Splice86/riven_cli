"""Riven API Client - connects to Riven API server.

For temp_riven: stateless API, session_id sent with each request.
For riven_core: session-based API with server-side sessions.
"""

import os
import uuid
import yaml
import requests
from typing import Optional, List, Dict
from src import styles

# ANSI colors
RED = "\033[91m"
RESET = "\033[0m"

# Session file location
SESSION_FILE = os.path.expanduser("~/.riven_session")


# ============== CONFIG ==============

def _load_config() -> dict:
    """Load CLI config from secrets.yaml."""
    config_path = os.path.join(os.path.dirname(__file__), "secrets.yaml")
    if os.path.exists(config_path):
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {"api": {"url": "http://localhost:8080", "timeout": 60}}

CONFIG = _load_config()
API_URL = CONFIG.get("api", {}).get("url", "http://localhost:8080")
API_TIMEOUT = CONFIG.get("api", {}).get("timeout", 60)


# ============== CLIENT ==============

class RivenClient:
    """Client for Riven API."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or API_URL
        self.session_id: Optional[str] = None
        self.shard_name: str = "default"
    
    def list_shards(self) -> List[Dict]:
        """List available shards."""
        resp = requests.get(f"{self.base_url}/api/v1/shards")
        resp.raise_for_status()
        return resp.json().get("shards", [])
    
    def create_session(self, shard_name: str = None) -> Dict:
        """Create a new session with a client-generated session ID.
        
        For temp_riven: session_id is generated client-side and sent with each request.
        No server-side session is created - it's stateless.
        """
        self.session_id = str(uuid.uuid4())
        return {
            "session_id": self.session_id,
            "shard_name": shard_name or "default",
            "ok": True,
        }
    
    def send_message(self, message: str, stream: bool = False) -> Dict:
        """Send a message to the current session."""
        if not self.session_id:
            raise ValueError("No session - call create_session first")
        
        resp = requests.post(
            f"{self.base_url}/api/v1/messages",
            json={
                "message": message,
                "stream": stream,
                "session_id": self.session_id,
                "shard_name": self.shard_name,
            }
        )
        resp.raise_for_status()
        
        if stream:
            return {"stream": True, "response": resp}
        
        return resp.json()
    
    def stream_message(self, message: str) -> str:
        """Send message and stream response - prints tokens as they arrive.
        
        Sections: thinking, tool, result, riven
        See src/styles.py for color definitions.
        """
        if not self.session_id:
            raise ValueError("No session - call create_session first")
        
        import json
        
        # Track which sections we've shown
        shown_thinking = False
        shown_tool_call = False
        shown_tool_result = False
        shown_response = False
        
        output = ""
        
        with requests.post(
            f"{self.base_url}/api/v1/messages",
            json={
                "message": message,
                "stream": True,
                "session_id": self.session_id,
                "shard_name": self.shard_name,
            },
            stream=True,
            timeout=60
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            
                            # Handle thinking events - only show if still in thinking section
                            if 'thinking' in data:
                                # Skip thinking once we've moved past it (tool or response shown)
                                if shown_tool_call or shown_response:
                                    continue
                                if not shown_thinking:
                                    print(styles.section_header('thinking'))
                                    shown_thinking = True
                                thinking = data.get('thinking', '').strip('\n')
                                if thinking:
                                    print(styles.section_content('thinking', thinking), end='', flush=True)
                                    output += thinking
                                continue
                            
                            # Handle tool_call events
                            if 'tool_call' in data:
                                if not shown_tool_call:
                                    print(styles.section_header('tool'))
                                    shown_tool_call = True
                                tc = data.get('tool_call', {})
                                args_str = json.dumps(tc.get('arguments', {}), indent=2)
                                tool_call_str = f"{tc.get('name')}({args_str})"
                                print(styles.section_content('tool', tool_call_str), end='', flush=True)
                                output += tool_call_str
                                continue
                            
                            # Handle tool_result events
                            if 'tool_result' in data:
                                if not shown_tool_result:
                                    print(styles.section_header('result'))
                                    shown_tool_result = True
                                tr = data.get('tool_result', {})
                                error = tr.get('error')
                                content = tr.get('content', '').strip('\n')
                                if error:
                                    result_str = f"[ERROR] {error}"
                                else:
                                    result_str = styles.truncate_output(content)
                                print(styles.section_content('result', result_str), end='', flush=True)
                                output += result_str
                                continue
                            
                            # Handle regular tokens (final response)
                            token = data.get('token', '').strip('\n')
                            if token:
                                if not shown_response:
                                    print(styles.section_header("riven"))
                                    shown_response = True
                                print(styles.section_content("riven", token), end="", flush=True)
                                output += token
                            
                            if data.get('done'):
                                break
                        except json.JSONDecodeError:
                            pass
        print()  # newline at end
        return output.strip()
    
    def poll_messages(self) -> List[str]:
        """Poll for messages from the session."""
        # Not available in temp_riven's stateless API
        return []
    
    def save_session(self) -> None:
        """Save session ID to file for persistence across CLI restarts."""
        if self.session_id:
            with open(SESSION_FILE, 'w') as f:
                f.write(self.session_id)

    def load_session(self) -> Optional[str]:
        """Load saved session ID from file if it exists."""
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE) as f:
                return f.read().strip()
        return None

    def delete_saved_session(self) -> None:
        """Delete saved session file (used on /clear)."""
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)

    def session_exists(self, session_id: str) -> bool:
        """Check if a session still exists on the server."""
        try:
            resp = requests.get(f"{self.base_url}/api/v1/sessions/{session_id}")
            return resp.status_code == 200
        except:
            return False

    def close_session(self) -> None:
        """Close the current session."""
        # Stateless API - nothing to close server-side
        # Just clear local session_id
        self.session_id = None

    def resume_session(self, shard_name: str = "codehammer") -> Optional[Dict]:
        """Try to resume a saved session.
        
        For temp_riven: session_id is client-side only, always resumable.
        """
        saved_id = self.load_session()
        if not saved_id:
            return None
        
        self.session_id = saved_id
        self.shard_name = shard_name
        return {
            "session_id": saved_id,
            "shard_name": shard_name,
            "ok": True,
            "resumed": True
        }


# ============== CONVENIENCE ==============

def get_client() -> RivenClient:
    """Get a Riven client instance."""
    return RivenClient()
