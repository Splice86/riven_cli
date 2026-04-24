#!/usr/bin/env python3
"""Riven CLI - connects to Riven API server."""

import argparse
import json
import sys
import os
import time

import requests

from src import styles
from src.client import get_client, DEFAULT_SHARD
from src.styles import (
    RED, GREEN, YELLOW, MAGENTA, CYAN, WHITE, GREY, RESET, BOLD, DIM,
)

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
    return f"{GREY}[{session_id[:8]}]{RESET}"


def _process_list(args):
    """Handle `riven process list`."""
    client = get_client()
    try:
        procs = client.list_processes(shard_name=args.shard, status=args.status)
        if not procs:
            print(f"{GREY}No processes found.{RESET}")
            return
        for p in procs:
            status_color = {
                "running": GREEN,
                "idle": YELLOW,
                "done": GREY,
                "stopped": RED,
            }.get(p["status"], "")
            elapsed = f" ({p['elapsed_seconds']:.1f}s)" if p.get("elapsed_seconds") else ""
            print(f"{status_color}{p['status']:8}{RESET} {CYAN}{p['process_id'][:20]:20}{RESET}  "
                  f"{p['shard_name']}  {GREY}{p['created_at'][:19]}{RESET}{elapsed}")
    except requests.RequestException as e:
        print(f"{RED}Error: {e}{RESET}")


def _process_status(args):
    """Handle `riven process status <id>`."""
    client = get_client()
    try:
        info = client.get_process(args.process_id)
        print(f"{CYAN}Process:{RESET} {info['process_id']}")
        print(f"{CYAN}Shard:{RESET}  {info['shard_name']}")
        print(f"{CYAN}Status:{RESET}  {info['status']}")
        if info.get('elapsed_seconds'):
            print(f"{CYAN}Elapsed:{RESET} {info['elapsed_seconds']:.1f}s")
        if info.get('started_at'):
            print(f"{CYAN}Started:{RESET} {info['started_at']}")
        if info.get('completed_at'):
            print(f"{CYAN}Ended:{RESET}   {info['completed_at']}")
    except requests.RequestException as e:
        print(f"{RED}Error: {e}{RESET}")


def _process_output(args):
    """Handle `riven process output <id>`."""
    client = get_client()
    try:
        since = float(args.since) if args.since else None
        data = client.get_process_output(
            args.process_id,
            messages=not args.tokens_only or True,  # all on by default
            thinking=args.include_thinking,
            tool_calls=args.include_tool_calls,
            tool_results=args.include_tool_results,
            errors=args.include_errors,
            last_only=args.last_only,
            since=since,
        )
        print(f"{GREY}Status: {data['status']}  ({len(data['output'])} events){RESET}")
        if not data["output"]:
            print(f"{GREY}(no output){RESET}")
            return
        for event in data["output"]:
            etype = event.get("type", "?")
            content = event.get("content", "") or event.get("error", "") or ""
            name = event.get("name", "")
            if etype == "token":
                print(content, end="", flush=True)
            elif etype == "tool_call":
                args_str = json.dumps(event.get("args", {}), indent=2)
                print(f"\n{CYAN}[call]{RESET} {MAGENTA}{name}({args_str}){RESET}")
            elif etype == "tool_result":
                result_info = event.get("result", {})
                if result_info.get("error"):
                    print(f"\n{RED}[result ERROR]{RESET} {result_info['error']}")
                else:
                    print(f"\n{GREEN}[result]{RESET} {styles.truncate_output(result_info.get('content', ''))}")
            elif etype == "error":
                print(f"\n{RED}[ERROR]{RESET} {content}")
            elif etype == "done":
                print(f"\n{GREY}[done]{RESET}")
            elif etype == "thinking":
                print(f"\n{GREY}--- thinking ---")
                print(content.strip())
                print(f"{GREY}---{RESET}")
        print()
    except requests.RequestException as e:
        print(f"{RED}Error: {e}{RESET}")


def _process_stream(args):
    """Handle `riven process stream <id>`."""
    client = get_client()
    params = {
        "messages": True,
        "thinking": args.include_thinking,
        "tool_calls": args.include_tool_calls,
        "tool_results": args.include_tool_results,
        "errors": args.include_errors,
    }
    try:
        with requests.get(
            f"{client.base_url}/processes/{args.process_id}/output/stream",
            params=params,
            stream=True,
            timeout=3600,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("event: "):
                        continue
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[5:])
                            etype = data.get("type", "?")
                            content = data.get("content", "") or data.get("error", "") or ""
                            name = data.get("name", "")
                            if etype == "token":
                                print(content, end="", flush=True)
                            elif etype == "tool_call":
                                args_str = json.dumps(data.get("args", {}), indent=2)
                                print(f"\n{CYAN}[call]{RESET} {MAGENTA}{name}({args_str})")
                            elif etype == "tool_result":
                                result = data.get("result", {})
                                if result.get("error"):
                                    print(f"\n{RED}[result ERROR]{RESET} {result['error']}")
                                else:
                                    print(f"\n{GREEN}[result]{RESET} {styles.truncate_output(result.get('content', ''))}")
                            elif etype == "error":
                                print(f"\n{RED}[ERROR]{RESET} {content}")
                            elif etype == "done":
                                print(f"\n{GREY}[done]{RESET}")
                            elif etype == "thinking":
                                print(f"\n{GREY}--- thinking ---")
                                print(content.strip())
                                print(f"{GREY}---{RESET}")
                            elif etype == "status":
                                print(f"\n{GREY}status: {data.get('status', '?')}{RESET}")
                        except json.JSONDecodeError:
                            pass
        print()
    except requests.RequestException as e:
        print(f"\n{RED}Error: {e}{RESET}")


def _process_send(args):
    """Handle `riven process send <id> <message>`."""
    client = get_client()
    try:
        result = client.send_process_message(args.process_id, args.message)
        print(f"{GREEN}Message queued.{RESET}")
    except requests.RequestException as e:
        print(f"{RED}Error: {e}{RESET}")


def _process_kill(args):
    """Handle `riven process kill <id>`."""
    client = get_client()
    try:
        result = client.stop_process(args.process_id)
        print(f"{YELLOW}Process stopped.{RESET}")
    except requests.RequestException as e:
        print(f"{RED}Error: {e}{RESET}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Riven CLI")
    sub = parser.add_subparsers(dest="command", help="Command")

    # process subcommand
    proc = sub.add_parser("process", help="Manage background processes")
    proc_sub = proc.add_subparsers(dest="process_command", help="Process command")

    p_list = proc_sub.add_parser("list", help="List all processes")
    p_list.add_argument("--shard", help="Filter by shard name")
    p_list.add_argument("--status", help="Filter by status (idle/running/done/stopped)")
    p_list.set_defaults(fn=_process_list)

    p_status = proc_sub.add_parser("status", help="Get process status")
    p_status.add_argument("process_id", help="Process ID")
    p_status.set_defaults(fn=_process_status)

    p_output = proc_sub.add_parser("output", help="Get process output")
    p_output.add_argument("process_id", help="Process ID")
    p_output.add_argument("--last-only", action="store_true", help="Only new events since last poll")
    p_output.add_argument("--since", help="Timestamp to filter events after")
    p_output.add_argument("--thinking", dest="include_thinking", action="store_true")
    p_output.add_argument("--tool-calls", dest="include_tool_calls", action="store_true")
    p_output.add_argument("--tool-results", dest="include_tool_results", action="store_true")
    p_output.add_argument("--errors", dest="include_errors", action="store_true")
    p_output.set_defaults(fn=_process_output)

    p_stream = proc_sub.add_parser("stream", help="Stream process output (like tail -f)")
    p_stream.add_argument("process_id", help="Process ID")
    p_stream.add_argument("--thinking", dest="include_thinking", action="store_true")
    p_stream.add_argument("--tool-calls", dest="include_tool_calls", action="store_true")
    p_stream.add_argument("--tool-results", dest="include_tool_results", action="store_true")
    p_stream.add_argument("--errors", dest="include_errors", action="store_true")
    p_stream.set_defaults(fn=_process_stream)

    p_send = proc_sub.add_parser("send", help="Send a message to a process")
    p_send.add_argument("process_id", help="Process ID")
    p_send.add_argument("message", help="Message to send")
    p_send.set_defaults(fn=_process_send)

    p_kill = proc_sub.add_parser("kill", help="Stop a running process")
    p_kill.add_argument("process_id", help="Process ID")
    p_kill.set_defaults(fn=_process_kill)

    return parser


def main():
    """Run CLI."""
    parser = _build_parser()
    args = parser.parse_args()

    # Handle process subcommands (stateless, no session needed)
    if args.command == "process" and args.process_command:
        args.fn(args)
        return

    # Fall through to interactive shell
    print_banner()

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
    shard = DEFAULT_SHARD
    result = client.resume_session(shard_name=shard)
    if not result:
        result = client.create_session(shard_name=shard)
        client.save_session()
    
    if not result.get("ok"):
        print(f"{RED}Error: {result.get('message')}{RESET}")
        sys.exit(1)
    
    session = result["session_id"]
    resumed = result.get("resumed", False)
    
    print(f"Using core: {shard}")
    if resumed:
        print(f"Session: {session[:8]} (resumed)")
    else:
        print(f"Session: {session[:8]}")
    print("Riven agent ready. Type '/exit' to stop, '/clear' to reset session.\n")
    
    prompt_prefix = get_prompt_prefix(shard)
    
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
