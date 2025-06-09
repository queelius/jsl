"""
FastAPI micro-service for the tuple-style JSON language (spec v0.2).

POST /evaluate  – accepts a JSON program, returns the evaluated JSON result
GET  /health    – simple liveness probe
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, RootModel, Field
from typing import Any, Dict

from jsl import (
    run_program,
    to_json,           # <-- the cycle-safe serializer you added
)

app = FastAPI(title="JSON-Lang v0.2 Interpreter", version="0.1.0")

# ---------- Pydantic models ----------

class ProgramRequest(RootModel):
    root: Dict[str, Any]

class ResultResponse(BaseModel):
    result: Any

# ---------- Endpoints ----------

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.post("/evaluate", response_model=ResultResponse)
def evaluate(req: ProgramRequest) -> ResultResponse:
    try:
        result = run_program(req.root)
        return ResultResponse(result=to_json(result))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
