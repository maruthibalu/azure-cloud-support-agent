import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

DEFAULT_SOURCES_FILE = Path("config/azure_kb_sources.json")
DEFAULT_KB_FILE = Path("config/kb_data.json")
SUPPORTED_CATEGORIES = {
    "compute",
    "networking",
    "storage",
    "identity",
    "aks",
    "billing",
    "monitoring",
    "deployment",
    "other",
}

SERVICE_KEYWORDS = {
    "virtual machine": ["vm", "virtual machine", "boot", "compute"],
    "network": ["nsg", "network", "vnet", "subnet", "connectivity", "dns"],
    "storage": ["storage", "blob", "file", "sas", "firewall", "403"],
    "identity": ["entra", "rbac", "managed identity", "role", "permission"],
    "aks": ["aks", "kubernetes", "pod", "node", "crashloopbackoff"],
    "monitor": ["monitor", "alert", "log analytics", "application insights"],
    "deploy": ["arm", "bicep", "template", "deployment", "pipeline"],
    "billing": ["cost", "billing", "invoice", "budget", "charge"],
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
        file.write("\n")


def strip_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def infer_category(url: str, title: str, fallback: str = "other") -> str:
    text = f"{url} {title}".lower()
    rules = [
        ("aks", ["aks", "kubernetes"]),
        ("compute", ["virtual-machine", "vm", "compute"]),
        ("networking", ["network", "nsg", "vnet", "subnet", "dns", "load-balancer"]),
        ("storage", ["storage", "blob", "file-share", "sas"]),
        ("identity", ["identity", "entra", "rbac", "key-vault", "permission"]),
        ("monitoring", ["monitor", "alert", "log-analytics", "application-insights"]),
        ("deployment", ["arm", "bicep", "deployment", "template", "devops", "pipeline"]),
        ("billing", ["billing", "cost", "invoice", "finops", "charge"]),
    ]

    for category, markers in rules:
        if any(marker in text for marker in markers):
            return category

    return fallback if fallback in SUPPORTED_CATEGORIES else "other"


def extract_keywords(title: str, text_blob: str) -> list[str]:
    combined = f"{title.lower()} {text_blob.lower()}"
    keywords = set()

    for _, candidates in SERVICE_KEYWORDS.items():
        for keyword in candidates:
            if keyword in combined:
                keywords.add(keyword)

    title_tokens = [token for token in re.findall(r"[a-zA-Z0-9-]+", title.lower()) if len(token) > 3]
    for token in title_tokens:
        keywords.add(token)

    return sorted(list(keywords))[:15]


def build_steps_from_page(soup: BeautifulSoup) -> list[str]:
    steps = []

    # Prefer ordered/unordered lists inside article content.
    for item in soup.select("main li")[:12]:
        text = strip_text(item.get_text(" ", strip=True))
        if 20 <= len(text) <= 220:
            steps.append(text)

    deduped = []
    seen = set()
    for step in steps:
        key = step.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(step)

    return deduped[:6]


def build_summary(soup: BeautifulSoup) -> str:
    paragraphs = [strip_text(p.get_text(" ", strip=True)) for p in soup.select("main p")]
    paragraphs = [p for p in paragraphs if len(p) > 50]
    if paragraphs:
        return paragraphs[0][:240]
    return "Troubleshooting guidance sourced from Microsoft Learn."


def fetch_article(url: str, timeout: int) -> tuple[str, str, list[str], list[str]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    response = requests.get(url, timeout=timeout, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    title = strip_text(soup.title.get_text(" ", strip=True)) if soup.title else "Azure Troubleshooting Article"
    summary = build_summary(soup)

    blocked_markers = [
        "access to this page requires authorization",
        "signing in or changing directories",
    ]
    if any(marker in summary.lower() for marker in blocked_markers):
        raise ValueError(f"Blocked source page: {url}")

    steps = build_steps_from_page(soup)
    prerequisites = [
        "Access to Azure Portal and target subscription",
        "Permission to read Activity Log and resource configuration",
    ]

    return title, summary, steps, prerequisites


def next_article_id(existing_ids: set[str]) -> str:
    prefix = "AZDOC"
    highest = 0
    for article_id in existing_ids:
        if article_id.startswith(prefix):
            suffix = article_id.replace(prefix, "")
            if suffix.isdigit():
                highest = max(highest, int(suffix))
    return f"{prefix}{highest + 1:03d}"


def ingest(sources_file: Path, kb_file: Path, mode: str, timeout: int) -> dict[str, int]:
    sources_data = load_json(sources_file)
    kb_data = load_json(kb_file)

    existing_articles = kb_data.get("articles", [])
    if mode == "replace":
        existing_articles = []

    source_url_index = {article.get("source_url"): article for article in existing_articles if article.get("source_url")}
    existing_ids = {article.get("article_id", "") for article in existing_articles}

    inserted = 0
    updated = 0
    failed = 0

    for source in sources_data.get("sources", []):
        url = source.get("url", "").strip()
        if not url:
            continue

        try:
            title, summary, steps, prerequisites = fetch_article(url, timeout=timeout)
            category = infer_category(url, title, source.get("category", "other"))
            service = source.get("service", "azure")
            severity_hint = source.get("severity_hint", "medium")
            status = source.get("status", "draft")

            text_blob = f"{summary} {' '.join(steps)}"
            keywords = extract_keywords(title, text_blob)

            article = {
                "article_id": next_article_id(existing_ids),
                "title": title,
                "category": category,
                "keywords": keywords,
                "solution_summary": summary,
                "steps": steps,
                "prerequisites": prerequisites,
                "source_url": url,
                "source_type": "microsoft_learn",
                "service": service,
                "severity_hint": severity_hint,
                "status": status,
                "last_verified_utc": datetime.now(timezone.utc).isoformat(),
            }

            if url in source_url_index:
                existing = source_url_index[url]
                existing.update(article)
                updated += 1
            else:
                existing_ids.add(article["article_id"])
                existing_articles.append(article)
                source_url_index[url] = article
                inserted += 1
        except Exception:
            failed += 1

    kb_data["articles"] = existing_articles
    save_json(kb_file, kb_data)

    return {
        "inserted": inserted,
        "updated": updated,
        "failed": failed,
        "total": len(existing_articles),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest Microsoft Azure KB articles into local kb_data.json")
    parser.add_argument("--sources", default=str(DEFAULT_SOURCES_FILE), help="Path to source URL list JSON")
    parser.add_argument("--kb", default=str(DEFAULT_KB_FILE), help="Path to destination KB JSON")
    parser.add_argument(
        "--mode",
        choices=["append", "replace"],
        default="append",
        help="append: merge into existing KB, replace: overwrite all local articles",
    )
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = ingest(Path(args.sources), Path(args.kb), args.mode, args.timeout)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
