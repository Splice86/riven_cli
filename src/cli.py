#!/usr/bin/env python3
"""Riven CLI - connects to Riven API server."""

import sys
import os

# ANSI colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
GREY = "\033[90m"
RESET = "\033[0m"

BOLD = "\033[1m"
DIM = "\033[2m"

TAGLINE = "⬡ ̸S̵I̷G̴N̷A̵L̷S̴ ̷◆̷ ̷IN̶̶ ̵T̷H̷E̴ ̷V̴O̵I̶D̸ ⬡"


def print_banner():
    """Print cyberpunk ASCII art banner with vertical gradient."""
    try:
        import pyfiglet
        result = pyfiglet.figlet_format("RIVEN", font="slant")
        
        # Aggressive cyberpunk gradient for 5 lines: neon red -> hot pink -> neon purple -> electric blue -> cyan
        gradient = [91, 91, 95, 95, 96]
        
        lines = result.split('\n')
        nonempty = [l for l in lines if l.strip()]
        num_lines = len(nonempty)
        
        for i, line in enumerate(nonempty):
            color_idx = int(i / max(num_lines - 1, 1) * (len(gradient) - 1))
            color_idx = min(color_idx, len(gradient) - 1)
            color = gradient[color_idx]
            print(f"\033[{color}m{line}\033[0m")
        
        print(f"{' ' * 28}\033[95m◆ CODEHAMMER ◆\033[0m")
        print()
        print(f"{CYAN}┌────────────────────────────────────────┐{RESET}")
        print(f"{CYAN}│{RESET}{MAGENTA}        {TAGLINE}{CYAN}{' ' * 7}{RESET}{CYAN}│{RESET}")
        print(f"{CYAN}└────────────────────────────────────────┘{RESET}")
    except ImportError:
        print("RIVEN")
        print("------")


def get_prompt_prefix(core_name: str) -> str:
    return f"{CYAN}Riven - {core_name}{RESET}"


def get_session_line(session_id: str) -> str:
    return f"\033[90m[{session_id[:8]}]{RESET}"


def main():
    """Run CLI."""
    print_banner()
    
    from src.client import get_client
    import requests
    
    client = get_client()
    
    # Check API health
    try:
        resp = requests.get(f"{client.base_url}/")
        if resp.status_code != 200:
            print(f"{RED}Error: API not responding correctly{RESET}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"{RED}Error: Cannot connect to API at {client.base_url}{RESET}")
        print("Make sure the Riven API server is running:")
        print(f"  python -m uvicorn api:app")
        sys.exit(1)
    
    # Try to resume saved session, or create new one
    shard = "codehammer"
    result = client.resume_session(shard_name=shard)
    if not result:
        result = client.create_session(shard_name=shard)
        client.save_session()
    
    if not result.get("ok"):
        print(f"{RED}Error: {result.get('message')}{RESET}")
        sys.exit(1)
    
    session = result["session_id"]
    resumed = result.get("resumed", False)
    
    print(f"Using core: codehammer")
    if resumed:
        print(f"Session: {session[:8]} (resumed)")
    else:
        print(f"Session: {session[:8]}")
    print("Riven agent ready. Type '/exit' to stop, '/clear' to reset session.\n")
    
    prompt_prefix = get_prompt_prefix("codehammer")
    
    # Input loop
    try:
        while True:
            user_input = input(f"{get_session_line(session)}\n{prompt_prefix} > ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == '/exit':
                break
            
            if user_input.lower() == '/clear':
                client.close_session()
                client.delete_saved_session()
                result = client.create_session(shard_name=shard)
                client.save_session()
                session = result["session_id"]
                print(f"✓ Session cleared. New session: {session[:8]}")
                continue
            
            # Send message with streaming (client prints during stream)
            try:
                client.stream_message(user_input)
            except Exception as e:
                print(f"\n{RED}Error: {e}{RESET}\n")
    
    except KeyboardInterrupt:
        print("\n^C Interrupted")
    except EOFError:
        print("\nGoodbye!")
    finally:
        # Keep session alive for persistence - don't close on exit
        print("Disconnected (session preserved)")


if __name__ == "__main__":
    main()
