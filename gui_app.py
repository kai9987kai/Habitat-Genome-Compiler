import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from habitat_genome_compiler.compiler import compile_mission
from habitat_genome_compiler.mission_generator import generate_mission_spec
from habitat_genome_compiler.presets import list_templates, load_template
from habitat_genome_compiler.run_store import save_run

app = FastAPI(title="OmniForge Habitat Compiler API")

# Mount the static directory for the front-end
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
    try:
        result = compile_mission(payload)
        saved_run = save_run(result)
        response = json.loads(result.to_json())
        response["saved_run"] = saved_run.to_dict()
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/templates")
async def get_templates():
    return {"templates": list_templates()}


@app.get("/api/templates/{name}")
async def get_template(name: str):
    try:
        return load_template(name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Template not found") from exc


@app.post("/api/generate-mission")
async def api_generate_mission(payload: dict):
    try:
        return generate_mission_spec(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("gui_app:app", host="127.0.0.1", port=8000, reload=True)
