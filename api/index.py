"""
Vercel serverless entry point.
Vercel imports this file and looks for the `app` variable (ASGI app).
"""
import sys
import os

# Make the project root importable so validator_core, resources, etc. are found
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app  # noqa: F401 — Vercel needs this name
