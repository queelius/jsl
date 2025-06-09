"""
FastAPI micro-service for the JSL (JSON Serializable Language) interpreter.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, RootModel, Field
from typing import Any, Dict

from jsl.jsl import (
    run_program,
    to_json,           # <-- the cycle-safe serializer you added
)

app = FastAPI(title="JSL Interpreter Service",
             description="A micro-service for evaluating JSL programs.",
             version="1.0.0",
             contact={
                 "name": "Alex Towell",
                 "email": "queelius@gmail.com",
                 "url": "www.github.com/queelius/jsl"
             },
             license={
                 "name": "MIT License",
                 "url": "https://opensource.org/license/mit/"
             })

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
        # Ensure prelude is initialized if your run_program expects it
        # This might require importing and calling make_prelude from jsl.jsl
        # For simplicity, assuming run_program handles its prelude internally or
        # it's initialized by an import elsewhere.
        # If not, you might need:
        # from .jsl import make_prelude, prelude as jsl_prelude
        # if jsl_prelude is None:
        #     make_prelude()
        
        result = run_program(req.root) # If run_program needs an env, you need to create it here
        return ResultResponse(result=to_json(result))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

def start_service():
    """Starts the FastAPI service with Uvicorn."""
    import uvicorn
    # You might want to make host and port configurable, e.g., via environment variables or CLI args
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_service()
