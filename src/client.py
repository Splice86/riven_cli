"""Riven API Client - connects to Riven API server.

For temp_riven: stateless API, session_id sent with each request.
For riven_core: session-based API with server-side sessions.
"""

import json
import os
import uuid

import requests
import yaml
from typing import Optional, List, Dict

from src import styles

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
DEFAULT_SHARD = CONFIG.get("default_shard", "default")


# ============== CLIENT ==============

class RivenClient:
    """Client for Riven API."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or API_URL
        self.session_id: Optional[str] = None
        self.shard_name: str = DEFAULT_SHARD
    
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

        last_key = None
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
            timeout=API_TIMEOUT
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                        except json.JSONDecodeError:
                            continue

                        # New turn starting - reset so headers re-print
                        if data.get('context_rebuilt'):
                            last_key = None
                            continue

                        if data.get('done'):
                            break

                        # Determine which key this event belongs to
                        key = None
                        raw_content = ""
                        
                        if 'thinking' in data:
                            key = 'thinking'
                            raw_content = data.get('thinking', '')
                        elif 'tool_call' in data:
                            key = 'tool'
                            tc = data.get('tool_call', {})
                            args_str = json.dumps(tc.get('arguments', {}), indent=2)
                            raw_content = f"{tc.get('name')}({args_str})"
                        elif 'tool_result' in data:
                            key = 'result'
                            tr = data.get('tool_result', {})
                            if tr.get('error'):
                                raw_content = f"[ERROR] {tr.get('error')}"
                            else:
                                raw_content = styles.truncate_output(tr.get('content', ''))
                        elif 'token' in data:
                            key = 'riven'
                            raw_content = data.get('token', '')

                        if key is None:
                            continue

                        # Print blank line before header when switching to a new section with real content
                        if key != last_key and raw_content and not raw_content.isspace():
                            if last_key is not None:
                                print()  # blank line before new section header
                            print(styles.section_header(key))
                        
                        # Print content
                        if raw_content:
                            print(styles.section_content(key, raw_content), end='', flush=True)
                            output += raw_content

                        if raw_content and not raw_content.isspace():
                            last_key = key

        print()  # newline at end
        return output

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
        except requests.RequestException:
            return False

    def close_session(self) -> None:
        """Close the current session."""
        self.session_id = None

    def resume_session(self, shard_name: str = None) -> Optional[Dict]:
        """Try to resume a saved session."""
        saved_id = self.load_session()
        if not saved_id:
            return None
        
        self.session_id = saved_id
        self.shard_name = shard_name or DEFAULT_SHARD
        return {
            "session_id": saved_id,
            "shard_name": self.shard_name,
            "ok": True,
            "resumed": True
        }


# ============== CONVENIENCE ==============

def get_client() -> RivenClient:
    """Get a Riven client instance."""
    return RivenClient()
