import sys
from pathlib import Path

# Ensure UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
from core.orchestrator import ProductHiringManagerSystem
from core.tunnel import get_tunnel_status, start_public_tunnel, get_lan_ip
import uvicorn

app = FastAPI(title="LinkedIn Executive Roles & Hiring Manager AI System")
system = ProductHiringManagerSystem()

TEMPLATE_PATH = Path(__file__).parent / "templates" / "index.html"
SAMPLE_DIR = Path(__file__).parent / "sample_resumes"

class SearchRequest(BaseModel):
    resume_text: str
    level_filter: Optional[str] = "all"
    location: Optional[str] = "Bengaluru, Karnataka, India"
    page: Optional[int] = 1
    page_size: Optional[int] = 6
    sort_by: Optional[str] = "date" # 'date' (latest first) or 'match'

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    if not TEMPLATE_PATH.exists():
        raise HTTPException(status_code=404, detail="Template not found")
    return HTMLResponse(content=TEMPLATE_PATH.read_text(encoding="utf-8"))

@app.get("/api/network-info")
async def get_network_info():
    """Returns local LAN and public tunnel access URLs for mobile / remote PCs."""
    return get_tunnel_status(8000)

@app.post("/api/start-tunnel")
async def enable_public_tunnel():
    """Generates an instant public HTTPS tunnel URL for worldwide access."""
    url = start_public_tunnel(8000)
    return {
        "status": "success" if url else "failed",
        "public_url": url,
        "lan_url": f"http://{get_lan_ip()}:8000"
    }

@app.get("/api/presets")
async def get_presets():
    """Returns available sample resume presets for easy testing across roles."""
    presets = {}
    twisha = SAMPLE_DIR / "twisha_prasad.txt"
    aryan = SAMPLE_DIR / "aryan_sharma_data_science_lead.txt"
    sneha = SAMPLE_DIR / "sneha_rao_senior_data_scientist.txt"

    if twisha.exists():
        presets["product_leader"] = {
            "title": "Product Leadership (Twisha Prasad, 12+ YoE)",
            "track": "PRODUCT",
            "content": twisha.read_text(encoding="utf-8")
        }
    if aryan.exists():
        presets["ds_lead"] = {
            "title": "Data Science & AI Leadership (Dr. Aryan Sharma, 11+ YoE)",
            "track": "DATA_SCIENCE",
            "content": aryan.read_text(encoding="utf-8")
        }
    if sneha.exists():
        presets["ds_senior"] = {
            "title": "Senior Data Scientist (Sneha Rao, 6+ YoE)",
            "track": "DATA_SCIENCE",
            "content": sneha.read_text(encoding="utf-8")
        }
    return presets

@app.post("/api/search")
async def run_search(req: SearchRequest):
    if not req.resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text cannot be empty")
    
    try:
        results = system.run(
            resume_text=req.resume_text,
            level_filter=req.level_filter or "all",
            location=req.location or "Bengaluru, Karnataka, India",
            page=max(1, req.page or 1),
            page_size=min(20, max(1, req.page_size or 6)),
            sort_by=req.sort_by or "date"
        )
        return JSONResponse(content=results)
    except Exception as e:
        print(f"[!] Server Error in /api/search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    lan_ip = get_lan_ip()
    print("=" * 65)
    print(f"🚀 CareerLead AI Server Starting on 0.0.0.0:{port}")
    print(f"💻 Local PC Access:             http://localhost:{port}")
    print(f"📱 Mobile / Same Wi-Fi Access:   http://{lan_ip}:{port}")
    print("=" * 65, flush=True)
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
