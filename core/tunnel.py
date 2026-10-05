import socket
import subprocess
import threading
import re
import time
from typing import Optional

_public_url: Optional[str] = None
_tunnel_process: Optional[subprocess.Popen] = None

def get_lan_ip() -> str:
    """Gets the machine's local Wi-Fi / LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def start_public_tunnel(port: int = 8000) -> Optional[str]:
    """
    Spawns an automatic SSH reverse tunnel via localhost.run to give
    a free, secure public HTTPS URL accessible from mobile or any PC worldwide.
    """
    global _public_url, _tunnel_process

    if _public_url:
        return _public_url

    cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=NUL",
        "-T",
        "-R", f"80:localhost:{port}",
        "nokey@localhost.run"
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        _tunnel_process = proc

        # Monitor stdout for the generated domain
        def monitor_output():
            global _public_url
            for line in proc.stdout:
                # e.g. "xxxxxx.lhr.life tunneled with tls termination, https://xxxxxx.lhr.life"
                match = re.search(r"https://[a-zA-Z0-9\-\.]+\.lhr\.life", line)
                if match:
                    _public_url = match.group(0)
                    print(f"\n[+] Public Tunnel URL established: {_public_url}\n", flush=True)
                    break

        t = threading.Thread(target=monitor_output, daemon=True)
        t.start()

        # Wait up to 6 seconds for the tunnel URL to appear
        for _ in range(12):
            if _public_url:
                break
            time.sleep(0.5)

        return _public_url
    except Exception as e:
        print(f"[!] Could not start public SSH tunnel: {e}")
        return None

def get_tunnel_status(port: int = 8000):
    lan_ip = get_lan_ip()
    return {
        "lan_ip": lan_ip,
        "localhost_url": f"http://localhost:{port}",
        "lan_url": f"http://{lan_ip}:{port}",
        "public_url": _public_url
    }
