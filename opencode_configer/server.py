"""
FastAPI application and API routes for opencode-configer.
"""
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from opencode_configer import config_io
from opencode_configer.models import (
    ApplyRequest,
    ConfigSet,
    DiscoveredModel,
    FetchModelsRequest,
    ModelEntry,
    SaveSetRequest,
)

app = FastAPI(title="opencode-configer")

_STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


# ---------------------------------------------------------------------------
# Config endpoints
# ---------------------------------------------------------------------------


@app.get("/api/config")
async def get_config() -> dict[str, Any]:
    """
    Return the active opencode config.json contents.

    :return: Parsed config.json.
    :rtype: dict[str, Any]
    """
    return config_io.read_active_opencode()


@app.get("/api/oh-my-opencode")
async def get_oh_my_opencode() -> dict[str, Any]:
    """
    Return the active oh-my-opencode.json contents.

    :return: Parsed oh-my-opencode.json.
    :rtype: dict[str, Any]
    """
    return config_io.read_active_oh_my_opencode()


@app.post("/api/apply")
async def apply_configs(req: ApplyRequest) -> dict[str, str]:
    """
    Write both configs directly to the active paths.

    :param req: Request body containing both config dicts.
    :type req: ApplyRequest
    :return: Success message.
    :rtype: dict[str, str]
    """
    config_io.write_active_opencode(req.opencode_config)
    config_io.write_active_oh_my_opencode(req.oh_my_opencode_config)
    return {"status": "ok", "message": "Configs applied successfully."}


# ---------------------------------------------------------------------------
# Provider model discovery
# ---------------------------------------------------------------------------


@app.post("/api/providers/models", response_model=list[DiscoveredModel])
async def fetch_provider_models(req: FetchModelsRequest) -> list[DiscoveredModel]:
    """
    Fetch available models from a provider's /v1/models endpoint.

    Merges discovered models with any already present in the request's
    existing_models by returning enabled=True for those present.

    :param req: Provider connection details.
    :type req: FetchModelsRequest
    :return: List of discovered model entries.
    :rtype: list[DiscoveredModel]
    :raises HTTPException: If the provider endpoint is unreachable or returns an error.
    """
    url = req.base_url.rstrip("/") + "/models"
    headers: dict[str, str] = {}
    if req.api_key:
        headers["Authorization"] = f"Bearer {req.api_key}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail=f"Provider returned {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Could not reach provider: {exc}") from exc

    data = resp.json()
    raw_models: list[dict[str, Any]] = data.get("data", data) if isinstance(data, dict) else data
    if not isinstance(raw_models, list):
        raise HTTPException(status_code=502, detail="Unexpected response format from /v1/models")

    return [DiscoveredModel(id=m.get("id", str(m))) for m in raw_models if isinstance(m, dict) and m.get("id")]


# ---------------------------------------------------------------------------
# Config set management
# ---------------------------------------------------------------------------


@app.get("/api/sets", response_model=list[ConfigSet])
async def list_sets() -> list[ConfigSet]:
    """
    List all named config sets.

    :return: List of config set metadata.
    :rtype: list[ConfigSet]
    """
    return config_io.list_sets()


@app.post("/api/sets/{name}/save")
async def save_set(name: str, req: SaveSetRequest) -> dict[str, str]:
    """
    Save both configs as a named set.

    :param name: Set name (becomes a subdirectory of ~/.config/opencode/).
    :type name: str
    :param req: Both config dicts to save.
    :type req: SaveSetRequest
    :return: Success message.
    :rtype: dict[str, str]
    :raises HTTPException: If the name is invalid.
    """
    try:
        config_io.save_set(name, req.opencode_config, req.oh_my_opencode_config)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "ok", "message": f"Set '{name}' saved."}


@app.get("/api/sets/{name}/load")
async def load_set(name: str) -> dict[str, Any]:
    """
    Load a named config set and return both configs.

    :param name: Set name to load.
    :type name: str
    :return: Dict with keys 'opencode_config' and 'oh_my_opencode_config'.
    :rtype: dict[str, Any]
    :raises HTTPException: If the set does not exist.
    """
    try:
        opencode, oh_my = config_io.load_set(name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"opencode_config": opencode, "oh_my_opencode_config": oh_my}


@app.post("/api/sets/{name}/apply")
async def apply_set(name: str) -> dict[str, str]:
    """
    Copy a named config set to the active paths.

    :param name: Set name to apply.
    :type name: str
    :return: Success message.
    :rtype: dict[str, str]
    :raises HTTPException: If the set does not exist.
    """
    try:
        config_io.apply_set(name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "ok", "message": f"Set '{name}' applied."}


@app.delete("/api/sets/{name}")
async def delete_set(name: str) -> dict[str, str]:
    """
    Delete a named config set.

    :param name: Set name to delete.
    :type name: str
    :return: Success message.
    :rtype: dict[str, str]
    :raises HTTPException: If the set does not exist.
    """
    try:
        config_io.delete_set(name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "ok", "message": f"Set '{name}' deleted."}


# ---------------------------------------------------------------------------
# Root — serve the SPA
# ---------------------------------------------------------------------------


@app.get("/")
async def index():
    """
    Serve the main SPA HTML file.

    :return: HTML response.
    """
    from fastapi.responses import FileResponse
    return FileResponse(str(_STATIC_DIR / "index.html"))
