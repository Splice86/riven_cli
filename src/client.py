"""Riven API Client - connects to Riven API server.

For temp_riven: stateless API, session_id sent with each request.
For riven_core: session-based API with server-side sessions.
"""

import os
import uuid
import yaml
import requests
from typing import Optional, List, Dict

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
        """Send message and stream response - prints tokens as they arrive."""
        if not self.session_id:
            raise ValueError("No session - call create_session first")
        
        import json
        
        # ANSI colors
        GREY = "\033[90m"
        ORANGE = "\033[33m"
        GREEN = "\033[92m"
        CYAN = "\033[96m"
        RESET = "\033[0m"
        
        output = ""
        in_thinking = False
        in_tool = False
        in_result = False
        tool_buffer = ""
        result_buffer = ""
        
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
                            # Handle thinking events - print in dim grey
                            if 'thinking' in data:
                                thinking = data.get('thinking', '')
                                if thinking and thinking.strip():
                                    print(f"{GREY}{thinking}{RESET}", end="", flush=True)
                                    output += thinking
                                continue
                            
                            if 'error' in data:
                                print(f"\n{RED}Error: {data['error']}{RESET}")
                                break
                            
                            token = data.get('token', '')
                            if token:
                                # Print with colors as tokens arrive
                                while token:
                                    if in_thinking:
                                        end = token.find('</think>')
                                        if end != -1:
                                            print(f"{GREY}{token[:end]}{RESET}", end="", flush=True)
                                            output += token[:end]
                                            token = token[end + 8:]
                                            in_thinking = False
                                            print()  # newline after thinking
                                        else:
                                            print(f"{GREY}{token}{RESET}", end="", flush=True)
                                            output += token
                                            break
                                    elif in_tool:
                                        end = token.find('</tool>')
                                        if end != -1:
                                            tool_buffer += token[:end]
                                            token = token[end + 8:]
                                            print(f"{ORANGE}{tool_buffer}{RESET}", end="", flush=True)
                                            output += tool_buffer
                                            tool_buffer = ""
                                            in_tool = False
                                            print()  # newline after tool
                                        else:
                                            tool_buffer += token
                                            break
                                    elif in_result:
                                        end = token.find('</result>')
                                        if end != -1:
                                            result_buffer += token[:end]
                                            token = token[end + 9:]
                                            print(f"{GREEN}{result_buffer}{RESET}", end="", flush=True)
                                            output += result_buffer
                                            result_buffer = ""
                                            in_result = False
                                            print()  # newline after result
                                        else:
                                            result_buffer += token
                                            break
                                    else:
                                        start = token.find('<think>')
                                        if start != -1:
                                            print(f"{CYAN}{token[:start]}{RESET}", end="", flush=True)
                                            output += token[:start]
                                            token = token[start + 7:]
                                            in_thinking = True
                                        else:
                                            start = token.find('<tool>')
                                            if start != -1:
                                                print(f"{CYAN}{token[:start]}{RESET}", end="", flush=True)
                                                output += token[:start]
                                                token = token[start + 6:]
                                                in_tool = True
                                            else:
                                                # Check for result start
                                                start = token.find('<result>')
                                                if start != -1:
                                                    print(f"{CYAN}{token[:start]}{RESET}", end="", flush=True)
                                                    output += token[:start]
                                                    token = token[start + 8:]
                                                    in_result = True
                                                else:
                                                    print(f"{CYAN}{token}{RESET}", end="", flush=True)
                                                    output += token
                                                    break
                            
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