from __future__ import annotations

import argparse
import re
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from src.utils import clean_whitespace, safe_float, write_jsonl

BASE_URL = "https://www.egypttravelguide.com/"
DEFAULT_OUTPUT = "data/raw_pages.jsonl"

SEED_PATHS = [
    "/",
    "/hurghada",
    "/marsa-alam",
    "/sharm-el-sheikh",
    "/transfer",
    "/blog",
    "/package-tour",
]

LOCATION_KEYWORDS = [
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
    "Abu Dabbab",
    "Tiran Island",
    "Ras Mohammed",
]

ACTIVITY_KEYWORDS = {
    "snorkeling": ["snorkel", "snorkeling", "reef", "coral"],
    "diving": ["diving", "dive", "certified divers"],
    "desert_safari": ["safari", "quad", "buggy", "camel", "bedouin", "desert"],
    "culture_history": ["luxor", "cairo", "pyramids", "museum", "temple", "monastery", "dendera", "abydos"],
    "boat_trip": ["boat", "catamaran", "yacht", "island", "dolphin", "submarine"],
    "transfer": ["transfer", "airport", "pickup", "drop-off"],
    "family": ["family", "children", "kids", "aquarium", "water park", "submarine"],
}


@dataclass
class ScrapeConfig:
    base_url: str = BASE_URL
    max_pages: int = 120
    delay: float = 1.0
    output: str = DEFAULT_OUTPUT
    user_agent: str = "EgyptTravelGuideRAGStudentProject/1.0 (+educational use)"


def normalize_url(url: str, base_url: str = BASE_URL) -> str:
    absolute = urljoin(base_url, url)
    absolute, _fragment = urldefrag(absolute)
    parsed = urlparse(absolute)
    return parsed._replace(query="").geturl().rstrip("/") or base_url.rstrip("/")


def is_internal_url(url: str, base_url: str = BASE_URL) -> bool:
    parsed = urlparse(url)
    base = urlparse(base_url)
    return parsed.netloc == base.netloc and parsed.scheme in {"http", "https"}


def is_candidate_page(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    if any(path.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".svg", ".pdf", ".zip"]):
        return False
    blocked = ["/cart", "/checkout", "/account", "/login", "/wp-", "/cdn-cgi"]
    if any(b in path for b in blocked):
        return False
    useful = ["/tour/", "/blog", "/hurghada", "/marsa-alam", "/sharm-el-sheikh", "/transfer", "/package-tour", "/"]
    return any(path == u or path.startswith(u) for u in useful)


def build_robots(base_url: str, user_agent: str) -> RobotFileParser:
    robots = RobotFileParser()
    robots.set_url(urljoin(base_url, "/robots.txt"))
    try:
        robots.read()
    except Exception:
        # If robots.txt cannot be read during local testing, continue politely.
        pass
    return robots


def infer_page_type(url: str) -> str:
    path = urlparse(url).path.lower()
    if "/tour/" in path:
        return "tour"
    if "/blog" in path:
        return "blog"
    if "transfer" in path:
        return "transfer"
    if any(x in path for x in ["hurghada", "marsa-alam", "sharm-el-sheikh"]):
        return "destination"
    if "package" in path:
        return "package"
    return "general"


def infer_locations(text: str, url: str) -> list[str]:
    combined = f"{url}\n{text}".lower()
    found: list[str] = []
    for loc in LOCATION_KEYWORDS:
        if loc.lower() in combined and loc not in found:
            found.append(loc)
    return found


def infer_activities(text: str) -> list[str]:
    lower = text.lower()
    activities: list[str] = []
    for activity, keywords in ACTIVITY_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            activities.append(activity)
    return activities


def extract_sections(soup: BeautifulSoup) -> dict[str, str]:
    """Extract text grouped by headings where possible."""
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    container = soup.find("main") or soup.find("article") or soup.body or soup
    sections: dict[str, list[str]] = {"main": []}
    current = "main"

    for node in container.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th"], recursive=True):
        text = clean_whitespace(node.get_text(" ", strip=True))
        if not text or len(text) < 2:
            continue
        if node.name in {"h1", "h2", "h3", "h4"}:
            current = text[:100]
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(text)

    clean_sections = {
        heading: clean_whitespace("\n".join(parts))
        for heading, parts in sections.items()
        if clean_whitespace("\n".join(parts))
    }
    return clean_sections


def extract_page(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("h1") or soup.find("title")
    title = clean_whitespace(title_tag.get_text(" ", strip=True)) if title_tag else url
    sections = extract_sections(soup)
    full_text = clean_whitespace("\n\n".join([f"{k}\n{v}" for k, v in sections.items()]))

    price_match = re.search(r"EUR\s*([0-9]+(?:\.[0-9]+)?)", full_text, flags=re.I)
    price_eur = safe_float(price_match.group(1)) if price_match else None

    return {
        "url": url,
        "title": title,
        "page_type": infer_page_type(url),
        "price_eur": price_eur,
        "locations": infer_locations(f"{title}\n{full_text}", url),
        "activities": infer_activities(f"{title}\n{full_text}"),
        "sections": sections,
        "full_text": full_text,
        "text_length": len(full_text),
    }


def discover_and_scrape(config: ScrapeConfig) -> list[dict]:
    session = requests.Session()
    session.headers.update({"User-Agent": config.user_agent})
    robots = build_robots(config.base_url, config.user_agent)

    queue: deque[str] = deque(normalize_url(path, config.base_url) for path in SEED_PATHS)
    seen: set[str] = set()
    records: list[dict] = []

    with tqdm(total=config.max_pages, desc="Scraping pages") as pbar:
        while queue and len(records) < config.max_pages:
            url = queue.popleft()
            if url in seen:
                continue
            seen.add(url)
            if not is_internal_url(url, config.base_url) or not is_candidate_page(url):
                continue
           # if hasattr(robots, "can_fetch") and not robots.can_fetch(config.user_agent, url):
           #     continue

            try:
                response = session.get(url, timeout=25)
                response.raise_for_status()
                html = response.text
            except Exception as exc:
                print(f"[WARN] Could not fetch {url}: {exc}")
                continue

            record = extract_page(html, url)
            if record["text_length"] > 100:
                records.append(record)
                pbar.update(1)

            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                href = normalize_url(a["href"], config.base_url)
                if href not in seen and is_internal_url(href, config.base_url) and is_candidate_page(href):
                    queue.append(href)

            time.sleep(config.delay)

    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=120)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    config = ScrapeConfig(max_pages=args.max_pages, delay=args.delay, output=args.output)
    records = discover_and_scrape(config)
    write_jsonl(config.output, records)
    print(f"Saved {len(records)} records to {config.output}")


if __name__ == "__main__":
    main()
