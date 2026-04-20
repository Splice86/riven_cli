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
        """Send message and stream response - prints tokens as they arrive.
        
        Event colors:
        - thinking (grey): reasoning from LLM
        - tool_call (dark orange): function call with args
        - tool_result (bright orange): function result or error
        - token (cyan): regular text output
        - code blocks: dark background
        """
        if not self.session_id:
            raise ValueError("No session - call create_session first")
        
        import json
        import re
        
        # ANSI colors
        GREY = "\033[90m"
        MAGENTA = "\033[35m"            # Magenta for tool calls
        ORANGE = "\033[33m"             # Orange for tool results
        CYAN = "\033[96m"
        RESET = "\033[0m"
        
        # Code block styling (not currently used but available)
        # CODE_BG = "\033[48;5;235m"      # Dark grey background
        # CODE_TEXT = "\033[97m"          # White text
        # CODE_LANG = "\033[38;5;39m"     # Blue for language label
        
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
                            
                            # Handle thinking events - grey
                            if 'thinking' in data:
                                thinking = data.get('thinking', '')
                                if thinking and thinking.strip():
                                    print(f"{GREY}{thinking}{RESET}", end="", flush=True)
                                    output += thinking
                                continue
                            
                            # Handle tool_call events - magenta
                            if 'tool_call' in data:
                                tc = data.get('tool_call', {})
                                args_str = json.dumps(tc.get('arguments', {}), indent=2)
                                tool_call_str = f"{tc.get('name')}({args_str})"
                                print(f"{MAGENTA}{tool_call_str}{RESET}", end="", flush=True)
                                output += tool_call_str
                                continue
                            
                            # Handle tool_result events - orange
                            if 'tool_result' in data:
                                tr = data.get('tool_result', {})
                                error = tr.get('error')
                                content = tr.get('content', '')
                                if error:
                                    result_str = f"[ERROR] {error}"
                                else:
                                    result_str = content
                                print(f"{ORANGE}{result_str}{RESET}", end="", flush=True)
                                output += result_str
                                continue
                            
                            # Handle error events
                            if 'error' in data:
                                print(f"\n{RED}Error: {data['error']}{RESET}")
                                break
                            
                            # Handle regular tokens - cyan
                            # Also highlight code blocks with background
                            token = data.get('token', '')
                            if token:
                                # Check for code blocks
                                code_pattern = r'(```\w*\n[\s\S]*?```)'
                                parts = re.split(code_pattern, token)
                                for part in parts:
                                    if part.startswith('```'):
                                        # Extract language and content
                                        match = re.match(r'```(\w*)\n([\s\S]*?)```', part)
                                        if match:
                                            lang = match.group(1) or ''
                                            code = match.group(2)
                                            if lang:
                                                print(f"{CODE_BG}{CODE_LANG}{lang}{RESET}{CODE_BG}{CODE_TEXT}{code}{RESET}", end="", flush=True)
                                            else:
                                                print(f"{CODE_BG}{CODE_TEXT}{code}{RESET}", end="", flush=True)
                                            output += part
                                        else:
                                            print(f"{CYAN}{part}{RESET}", end="", flush=True)
                                            output += part
                                    else:
                                        print(f"{CYAN}{part}{RESET}", end="", flush=True)
                                        output += part
                            
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
