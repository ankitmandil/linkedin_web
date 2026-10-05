import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import argparse
import socket
from core.tunnel import get_lan_ip, start_public_tunnel

def main():
    parser = argparse.ArgumentParser(description="LinkedIn Executive Roles & Hiring Manager AI System")
    parser.add_argument("--web", action="store_true", help="Launch interactive Web Dashboard")
    parser.add_argument("--cli", action="store_true", help="Run interactive CLI analysis")
    parser.add_argument("--public", "--tunnel", dest="public", action="store_true", help="Generate public HTTPS tunnel accessible worldwide from mobile or any PC")
    parser.add_argument("--level", type=str, default="all", choices=["all", "higher", "similar"], help="Filter by level")
    parser.add_argument("--limit", type=int, default=5, help="Number of opportunities to discover")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind server (default: 8000)")
    args, unknown = parser.parse_known_args()

    if args.web or not args.cli:
        lan_ip = get_lan_ip()
        port = args.port

        print("=" * 70, flush=True)
        print("[*] CareerLead AI System - Web Server Starting...", flush=True)
        print(f"[*] Localhost Access:              http://localhost:{port}", flush=True)
        print(f"[*] Mobile / Other PC (Same Wi-Fi): http://{lan_ip}:{port}", flush=True)

        if args.public:
            print("[*] Generating free secure public HTTPS tunnel for mobile access...", flush=True)
            pub_url = start_public_tunnel(port)
            if pub_url:
                print(f"[+] PUBLIC HTTPS URL (Worldwide Mobile): {pub_url}", flush=True)
            else:
                print("[!] Tunnel in progress, check /api/network-info in dashboard.", flush=True)
        else:
            print(f"[*] Want access from anywhere without Wi-Fi? Launch with: python run.py --web --public", flush=True)
        print("=" * 70, flush=True)

        import uvicorn
        uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
    else:
        from cli import run_cli
        run_cli()

if __name__ == "__main__":
    main()
