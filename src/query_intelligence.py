from __future__ import annotations

import os
import re
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from src.utils import parse_json_from_text, safe_float

load_dotenv()

QueryClass = Literal[
    "factual_lookup",
    "recommendation",
    "comparison",
    "price_filter",
    "location_query",
    "transfer_query",
    "out_of_scope",
]


class QueryFilters(BaseModel):
    location: str | None = None
    activity: str | None = None
    page_type: str | None = None
    min_price_eur: float | None = None
    max_price_eur: float | None = None


class QueryAnalysis(BaseModel):
    original_query: str
    rewritten_query: str
    query_class: QueryClass
    filters: QueryFilters = Field(default_factory=QueryFilters)


LOCATIONS = [
    "Hurghada",
    "Marsa Alam",
    "Sharm El Sheikh",
    "Sharm el Sheikh",
    "Luxor",
    "Cairo",
    "Giza",
    "El Gouna",
    "Makadi Bay",
    "Port Ghalib",
    "Tiran Island",
    "Ras Mohammed",
]

ACTIVITIES = {
    "snorkeling": ["snorkel", "snorkeling", "reef", "coral"],
    "diving": ["diving", "dive"],
    "desert_safari": ["safari", "quad", "buggy", "camel", "desert"],
    "culture_history": ["luxor", "cairo", "pyramid", "museum", "temple", "monastery", "history"],
    "boat_trip": ["boat", "yacht", "island", "catamaran", "dolphin", "submarine"],
    "transfer": ["transfer", "airport", "pickup", "drop off", "drop-off"],
    "family": ["family", "children", "kids"],
}

TRAVEL_KEYWORDS = [
    "egypt", "tour", "trip", "travel", "holiday", "hurghada", "marsa", "sharm", "luxor",
    "cairo", "airport", "transfer", "snorkeling", "diving", "safari", "hotel", "red sea",
    "price", "eur", "recommend", "compare", "children", "family",
]


def rewrite_locally(query: str) -> str:
    rewritten = re.sub(r"\s+", " ", query.strip())
    replacements = {
        "u ": "you ",
        "ur ": "your ",
        "euro": "EUR",
        "€": "EUR",
        "cheap": "low price",
    }
    for old, new in replacements.items():
        rewritten = re.sub(old, new, rewritten, flags=re.I)
    return rewritten


def classify_locally(query: str) -> QueryClass:
    q = query.lower()
    if not any(k in q for k in TRAVEL_KEYWORDS):
        return "out_of_scope"
    if any(k in q for k in ["transfer", "airport", "pickup", "drop-off", "drop off"]):
        return "transfer_query"
    if any(k in q for k in ["compare", "difference", "versus", "vs", "better"]):
        return "comparison"
    if any(k in q for k in ["recommend", "best", "suggest", "suitable", "good for"]):
        return "recommendation"
    if any(k in q for k in ["under", "below", "less than", "price", "cost", "cheap", "eur", "€"]):
        return "price_filter"
    if any(loc.lower() in q for loc in LOCATIONS):
        return "location_query"
    return "factual_lookup"


def extract_filters_locally(query: str) -> QueryFilters:
    q = query.lower()
    filters = QueryFilters()

    for loc in LOCATIONS:
        if loc.lower() in q:
            filters.location = loc
            break

    for activity, keywords in ACTIVITIES.items():
        if any(keyword in q for keyword in keywords):
            filters.activity = activity
            break

    if "transfer" in q or "airport" in q:
        filters.page_type = "transfer"
    elif "blog" in q or "guide" in q:
        filters.page_type = "blog"
    elif "tour" in q or "trip" in q:
        filters.page_type = "tour"

    # under/below/less than 40 EUR
    max_match = re.search(r"(?:under|below|less than|maximum|max|up to)\s*(?:eur|€)?\s*([0-9]+(?:\.[0-9]+)?)", q)
    if not max_match:
        max_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(?:eur|€)\s*(?:or less|max|maximum)", q)
    if max_match:
        filters.max_price_eur = safe_float(max_match.group(1))

    min_match = re.search(r"(?:over|above|more than|minimum|min)\s*(?:eur|€)?\s*([0-9]+(?:\.[0-9]+)?)", q)
    if min_match:
        filters.min_price_eur = safe_float(min_match.group(1))

    return filters


def analyze_with_gemini(query: str) -> QueryAnalysis | None:
    """Optional Gemini-based query intelligence. Falls back to local rules on any error."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        prompt = f"""
You analyze user questions for an Egypt travel website RAG system.
Return ONLY valid JSON with this schema:
{{
  "rewritten_query": "clean English query",
  "query_class": "one of factual_lookup, recommendation, comparison, price_filter, location_query, transfer_query, out_of_scope",
  "filters": {{
    "location": "Hurghada/Marsa Alam/Sharm El Sheikh/etc or null",
    "activity": "snorkeling/diving/desert_safari/culture_history/boat_trip/transfer/family or null",
    "page_type": "tour/blog/transfer/destination/package/general or null",
    "min_price_eur": number or null,
    "max_price_eur": number or null
  }}
}}

User question: {query}
""".strip()
        response = client.models.generate_content(model=model, contents=prompt)
        data = parse_json_from_text(response.text or "{}")
        return QueryAnalysis(
            original_query=query,
            rewritten_query=data.get("rewritten_query") or rewrite_locally(query),
            query_class=data.get("query_class") or classify_locally(query),
            filters=QueryFilters(**(data.get("filters") or {})),
        )
    except Exception:
        return None


def analyze_query(query: str, use_gemini: bool = True) -> QueryAnalysis:
    if use_gemini:
        gemini_result = analyze_with_gemini(query)
        if gemini_result is not None:
            return gemini_result
    rewritten = rewrite_locally(query)
    return QueryAnalysis(
        original_query=query,
        rewritten_query=rewritten,
        query_class=classify_locally(query),
        filters=extract_filters_locally(query),
    )
