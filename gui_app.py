import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from typing import Optional

from habitat_genome_compiler.compiler import compile_mission
from habitat_genome_compiler.models import MissionSpec

app = FastAPI(title="OmniForge Habitat Compiler API")

# Mount the static directory for the front-end
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open(os.path.join(static_dir, "index.html"), "r") as f:
        return HTMLResponse(content=f.read())


@app.post("/api/compile")
async def api_compile(payload: dict):
    """
    Receives an entire MissionSpec JSON payload, compiles it,
    and returns the CompileResult JSON.
    """
    try:
        # Pydantic/dataclass parsing happens in compiler
        result = compile_mission(payload)
        return json.loads(result.to_json())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/templates/{name}")
async def get_template(name: str):
    """Serve local example JSON templates for rapid testing."""
    example_path = os.path.join(os.path.dirname(__file__), "examples", f"{name}.json")
    if not os.path.exists(example_path):
        raise HTTPException(status_code=404, detail="Template not found")
    
    with open(example_path, "r", encoding="utf-8") as f:
        return json.load(f)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("gui_app:app", host="127.0.0.1", port=8000, reload=True)
