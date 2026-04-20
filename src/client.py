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

        # Track which sections we've shown
        shown_thinking = False
        shown_tool_call = False
        shown_tool_result = False
        shown_response = False
        content_printed = False  # Track if we've printed content this turn
        
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
                            print(f"\n[DODEBUG] keys={list(data.keys())} token={repr(data.get('token','')[:30] if data.get('token') else '')} thinking={repr(data.get('thinking','')[:30] if data.get('thinking') else '')} tool_call={data.get('tool_call') is not None} tool_result={data.get('tool_result') is not None} done={data.get('done')} ctx_rebuilt={data.get('context_rebuilt')}", flush=True)
                            
                            # Handle thinking events - always show with header
                            if 'thinking' in data:
                                if not shown_thinking:
                                    if content_printed:
                                        print()  # blank line before header
                                    print(styles.section_header('thinking'))
                                shown_thinking = True
                                thinking = data.get('thinking', '')
                                if thinking:
                                    print(styles.section_content('thinking', thinking), end='', flush=True)
                                    output += thinking
                                    content_printed = True
                                continue
                            
                            # Handle turn boundary - tool_result signals new turn
                            # Reset thinking flag so next thinking gets a header
                            if 'tool_result' in data:
                                shown_thinking = False  # Reset for next turn's thinking
                                if not shown_tool_result:
                                    if content_printed:
                                        print()  # blank line before header
                                    print(styles.section_header('result'))
                                shown_tool_result = True
                                tr = data.get('tool_result', {})
                                error = tr.get('error')
                                content = tr.get('content', '')
                                if error:
                                    result_str = f"[ERROR] {error}"
                                else:
                                    result_str = styles.truncate_output(content)
                                print(styles.section_content('result', result_str), end='', flush=True)
                                output += result_str
                                content_printed = True
                                continue
                            
                            # Handle tool_call events
                            if 'tool_call' in data:
                                if not shown_tool_call:
                                    if content_printed:
                                        print()  # blank line before header
                                    print(styles.section_header('tool'))
                                shown_tool_call = True
                                tc = data.get('tool_call', {})
                                args_str = json.dumps(tc.get('arguments', {}), indent=2)
                                tool_call_str = f"{tc.get('name')}({args_str})"
                                print(styles.section_content('tool', tool_call_str), end='', flush=True)
                                output += tool_call_str
                                content_printed = True
                                continue
                            

                            
                            # Handle regular tokens (final response)
                            token = data.get('token', '')
                            if token:
                                if not shown_response:
                                    if content_printed:
                                        print()  # blank line before header
                                    print(styles.section_header("riven"))
                                shown_response = True
                                print(styles.section_content("riven", token), end="", flush=True)
                                output += token
                                content_printed = True
                            
                            if data.get('context_rebuilt'):
                                # Next turn starting - reset output state so new headers print
                                shown_thinking = False
                                shown_tool_call = False
                                shown_tool_result = False
                                shown_response = False
                                content_printed = False
                                continue

                            if data.get('done'):
                                break
                        except json.JSONDecodeError:
                            pass
        print()  # newline at end
        return output.strip()

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
        # Stateless API - nothing to close server-side
        # Just clear local session_id
        self.session_id = None

    def resume_session(self, shard_name: str = None) -> Optional[Dict]:
        """Try to resume a saved session.
        
        For temp_riven: session_id is client-side only, always resumable.
        """
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
