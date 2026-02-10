"""
Helpers for resolving common intent parameters (project, location, time windows).

These functions are deterministic and do NOT call any external services.
They sit between the LLM decision and SQL execution to normalize parameters.
"""

from __future__ import annotations

from typing import Optional, Dict


def resolve_project(last_params: Optional[Dict] = None) -> str:
    """
    Resolve the project name.

    Current scope: only 'ercot_generic' is supported, so this is constant.
    We keep a function for future extensibility.
    """
    return "ercot_generic"


def normalize_location(raw: Optional[str]) -> Optional[str]:
    """
    Normalize various user / LLM location strings to canonical values.

    Canonical values (per data model):
      - 'rto'
      - 'north_raybn'
      - 'south_lcra_aen_cps'
      - 'west'
      - 'houston'
    """
    if not raw:
        return None

    text = raw.strip().lower()

    # Common aliases / variations
    mapping = {
        "rto": "rto",
        "ercot": "rto",
        "ercot-wide": "rto",
        "ercot wide": "rto",
        "ercot-wide (rto)": "rto",
        "north": "north_raybn",
        "north zone": "north_raybn",
        "north load zone": "north_raybn",
        "north_raybn": "north_raybn",
        "south": "south_lcra_aen_cps",
        "south zone": "south_lcra_aen_cps",
        "south load zone": "south_lcra_aen_cps",
        "south_lcra_aen_cps": "south_lcra_aen_cps",
        "west": "west",
        "west zone": "west",
        "west load zone": "west",
        "houston": "houston",
        "houston zone": "houston",
        "houston load zone": "houston",
    }

    return mapping.get(text, raw)


def resolve_location(
    raw_from_llm: Optional[str],
    last_params: Optional[Dict] = None,
    default_location: str = "rto",
) -> str:
    """
    Resolve the location parameter using a clear precedence:

    1. If LLM provided a location, normalize and use it (if recognized).
    2. Else, if last_params has a location, reuse that.
    3. Else, fall back to default_location ('rto').
    """
    # 1) Try LLM-provided value
    normalized = normalize_location(raw_from_llm)
    if normalized:
        return normalized

    # 2) Try previous successful params from session
    if last_params and "location" in last_params:
        prev_normalized = normalize_location(last_params["location"])
        if prev_normalized:
            return prev_normalized

    # 3) Fallback
    return default_location

