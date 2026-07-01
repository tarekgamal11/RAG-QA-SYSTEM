from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def format_context(results: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for i, result in enumerate(results, start=1):
        chunk = result["chunk"]
        metadata = chunk.get("metadata", {})
        blocks.append(
            f"[Source {i}]\n"
            f"Title: {metadata.get('title')}\n"
            f"URL: {metadata.get('url')}\n"
            f"Section: {metadata.get('section')}\n"
            f"Price EUR: {metadata.get('price_eur')}\n"
            f"Locations: {metadata.get('locations')}\n"
            f"Activities: {metadata.get('activities')}\n"
            f"Retrieval score: {result.get('score')}\n"
            f"Text:\n{chunk.get('text')}"
        )
    return "\n\n---\n\n".join(blocks)


def build_grounded_prompt(question: str, results: list[dict[str, Any]]) -> str:
    context = format_context(results)
    return f"""
You are an Egypt Travel Guide QA assistant.

Rules:
1. Answer ONLY using the provided context.
2. If the context does not contain the answer, say: "I could not find this information in the retrieved Egypt Travel Guide data."
3. Do not invent prices, locations, times, availability, warnings, or recommendations.
4. Mention the source titles used in the answer.
5. Keep the answer helpful and concise.

User question:
{question}

Retrieved context:
{context}

Final answer:
""".strip()


def generate_answer(question: str, results: list[dict[str, Any]]) -> str:
    if not results:
        return "I could not find relevant information in the retrieved Egypt Travel Guide data."

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return (
            "Gemini API key is missing. Add GEMINI_API_KEY to your .env file.\n\n"
            "Retrieved context is available, but the final LLM answer was not generated."
        )

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        prompt = build_grounded_prompt(question, results)
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text or "Gemini returned an empty response."
    except Exception as exc:
        return f"Gemini generation failed: {exc}"
