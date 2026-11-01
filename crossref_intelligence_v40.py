"""Crossref metadata verification utilities for Research Analyzer Professional v4.0.

Uses the public Crossref REST API. Network calls are explicit, rate-limited by
caller pacing, and never happen during import. A Crossref match is metadata
corroboration, not a judgement of source quality or peer-review status.
"""
from __future__ import annotations
import json, re, time, urllib.parse, urllib.request, urllib.error
from typing import Callable

BASE_URL = "https://api.crossref.org"
USER_AGENT = "ResearchAnalyzerProfessional/4.0 (academic metadata verification)"
DOI_RE = re.compile(r"(?:https?://(?:dx\.)?doi\.org/)?(10\.\d{4,9}/[^\s<>\"']+)", re.I)


def normalize_doi(value: str) -> str:
    raw = str(value or "").strip()
    m = DOI_RE.search(raw)
    if not m:
        return ""
    return m.group(1).rstrip(".,;:)]}").lower()


def _first(value):
    return value[0] if isinstance(value, list) and value else value


def normalize_work(item: dict) -> dict:
    authors = item.get("author") or []
    author_names = []
    for a in authors[:20]:
        name = " ".join(x for x in [a.get("given", ""), a.get("family", "")] if x).strip()
        if name: author_names.append(name)
    date = item.get("published-print") or item.get("published-online") or item.get("created") or {}
    parts = (date or {}).get("date-parts", [[]])
    year = parts[0][0] if parts and parts[0] else ""
    return {
        "doi": normalize_doi(item.get("DOI", "")),
        "title": str(_first(item.get("title")) or ""),
        "authors": "; ".join(author_names),
        "year": year,
        "container_title": str(_first(item.get("container-title")) or ""),
        "volume": str(item.get("volume") or ""),
        "issue": str(item.get("issue") or ""),
        "page": str(item.get("page") or item.get("article-number") or ""),
        "publisher": str(item.get("publisher") or ""),
        "type": str(item.get("type") or ""),
        "url": str(item.get("URL") or ("https://doi.org/" + normalize_doi(item.get("DOI", "")) if item.get("DOI") else "")),
        "indexed_date": str(((item.get("indexed") or {}).get("date-time")) or ""),
    }


def _request_json(url: str, timeout: int = 25, opener: Callable = urllib.request.urlopen) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with opener(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"not_found": True}
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Crossref HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Koneksi Crossref gagal: {exc.reason}") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RuntimeError("Respons Crossref bukan JSON yang valid.") from exc
    return payload


def lookup_doi(doi: str, timeout: int = 25, opener: Callable = urllib.request.urlopen) -> dict:
    clean = normalize_doi(doi)
    if not clean:
        raise ValueError("DOI tidak dikenali. Masukkan DOI atau URL doi.org yang valid.")
    url = BASE_URL + "/works/" + urllib.parse.quote(clean, safe="/")
    payload = _request_json(url, timeout, opener)
    if payload.get("not_found"):
        return {"match_status": "not_found", "input_doi": clean}
    msg = payload.get("message") or {}
    normalized = normalize_work(msg)
    normalized["input_doi"] = clean
    normalized["match_status"] = "matched" if normalized["doi"] else "incomplete_metadata"
    normalized["doi_matches_input"] = normalized["doi"] == clean
    return normalized


def search_title(title: str, rows: int = 5, timeout: int = 25, opener: Callable = urllib.request.urlopen) -> list[dict]:
    query = str(title or "").strip()
    if len(query) < 4:
        raise ValueError("Judul minimal 4 karakter untuk pencarian Crossref.")
    if not 1 <= int(rows) <= 20:
        raise ValueError("Jumlah hasil harus antara 1 dan 20.")
    params = urllib.parse.urlencode({"query.title": query, "rows": int(rows), "select": "DOI,title,author,published-print,published-online,created,container-title,volume,issue,page,article-number,publisher,type,URL,indexed"})
    payload = _request_json(BASE_URL + "/works?" + params, timeout, opener)
    items = ((payload.get("message") or {}).get("items") or [])
    return [normalize_work(x) for x in items]


def verify_reference_rows(rows: list[dict], pause_seconds: float = 0.1,
                          lookup: Callable = lookup_doi) -> list[dict]:
    """Verify supplied rows containing optional doi/title fields against Crossref."""
    results=[]
    for index, row in enumerate(rows, start=1):
        doi = normalize_doi(row.get("doi", ""))
        title = str(row.get("title", "") or "").strip()
        try:
            if doi:
                found = lookup(doi)
                results.append({"row": index, "input_title": title, **found,
                                "verification_method": "DOI"})
            elif title:
                matches = search_title(title, rows=3)
                best = matches[0] if matches else {}
                results.append({"row": index, "input_title": title, **best,
                                "match_status": "title_candidates" if matches else "not_found",
                                "candidate_count": len(matches), "verification_method": "title search"})
            else:
                results.append({"row": index, "input_title": "", "match_status": "missing_identifier",
                                "verification_method": "none"})
        except Exception as exc:
            results.append({"row": index, "input_title": title, "match_status": "error",
                            "error": str(exc), "verification_method": "DOI" if doi else "title search"})
        if pause_seconds and index < len(rows): time.sleep(max(0.0, float(pause_seconds)))
    return results


def compare_metadata(input_row: dict, crossref_row: dict) -> dict:
    """Report differences without silently overwriting researcher-supplied data."""
    fields = ("title", "year", "authors", "container_title", "volume", "issue", "page")
    differences=[]
    for field in fields:
        supplied = str(input_row.get(field, "") or "").strip()
        verified = str(crossref_row.get(field, "") or "").strip()
        if supplied and verified and supplied.casefold() != verified.casefold():
            differences.append({"field": field, "supplied": supplied, "crossref": verified})
    return {"differences": differences, "difference_count": len(differences),
            "decision": "review_required" if differences else "no_detected_difference",
            "note": "Metadata Crossref adalah pembanding; koreksi akhir harus diperiksa pada sumber penerbit."}
