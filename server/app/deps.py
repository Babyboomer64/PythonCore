# server/app/deps.py
# Shared FastAPI dependencies to access loaded config and DB adapter

from fastapi import HTTPException
from .lifecycle import state


def get_config():
    if not state.cfg:
        raise HTTPException(status_code=500, detail="Config not loaded")
    return state.cfg


def get_adapter():
    if not state.adapter:
        raise HTTPException(status_code=500, detail="DB adapter not available")
    return state.adapter