"""Backend API with explicit policy attestation requirements."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.search.query_builder import build_query

POLICY_VERSION = "2026-04-22"
REQUIRED_ATTESTATION = "I have rights or permission to access/download this material."


class PolicyAcceptanceRequest(BaseModel):
    user_id: str = Field(min_length=1)
    attestation: str
    policy_version: str


class SearchRequest(BaseModel):
    user_id: str = Field(min_length=1)
    terms: List[str]
    rights_only: bool = False


@dataclass
class AcceptanceRecord:
    policy_version: str
    attestation: str
    accepted_at: str


app = FastAPI(title="Textbook Finder API")

# Replace with persistent DB in production.
_POLICY_ACCEPTANCE_STORE: Dict[str, AcceptanceRecord] = {}


@app.get("/policy")
def get_policy() -> dict:
    return {
        "policy_version": POLICY_VERSION,
        "required_attestation": REQUIRED_ATTESTATION,
    }


@app.post("/policy/accept")
def accept_policy(payload: PolicyAcceptanceRequest) -> dict:
    if payload.policy_version != POLICY_VERSION:
        raise HTTPException(status_code=400, detail="Policy version mismatch. Please refresh policy text.")
    if payload.attestation.strip() != REQUIRED_ATTESTATION:
        raise HTTPException(status_code=400, detail="Invalid attestation text.")

    accepted_at = datetime.now(timezone.utc).isoformat()
    _POLICY_ACCEPTANCE_STORE[payload.user_id] = AcceptanceRecord(
        policy_version=payload.policy_version,
        attestation=payload.attestation.strip(),
        accepted_at=accepted_at,
    )
    return {"status": "ok", "accepted_at": accepted_at, "policy_version": payload.policy_version}


@app.post("/search")
def search(payload: SearchRequest) -> dict:
    record = _POLICY_ACCEPTANCE_STORE.get(payload.user_id)
    if not record or record.policy_version != POLICY_VERSION:
        raise HTTPException(status_code=403, detail="Policy acceptance required before searching.")

    query = build_query(payload.terms, rights_only=payload.rights_only)
    return {
        "query": query,
        "rights_only": payload.rights_only,
        "policy_version": record.policy_version,
        "policy_accepted_at": record.accepted_at,
    }
