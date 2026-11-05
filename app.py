from pathlib import Path
from typing import Literal
from urllib.error import URLError

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, StringConstraints
from typing_extensions import Annotated

from audittrap import CASES, check

app = FastAPI(title="AuditTrap", description="An audit evidence prompt-injection lab.")


class AuditRequest(BaseModel):
    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
    corpus: Literal["clean", "poisoned"] = "clean"
    mode: Literal["baseline", "hardened"] = "hardened"
    backend: Literal["demo", "ollama"] = "demo"


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(Path(__file__).with_name("index.html"), media_type="text/html")


@app.get("/audit/cases")
def cases():
    return [
        {"id": case["id"], "question": case["question"], "has_attack": "attack" in case}
        for case in CASES
    ]


@app.post("/audit/check")
def audit(request: AuditRequest):
    try:
        return check(**request.model_dump())
    except (URLError, TimeoutError, ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=502,
            detail="Model request failed. Check that Ollama is running and the model is installed.",
        ) from None
