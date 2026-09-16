from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request
from pathlib import Path

from ..config import DOWNLOADS_DIR
from .base import Tool, ToolResult


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"


def _open_url(url: str, timeout: int = 20) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def web_search(query: str, max_results: int = 5) -> ToolResult:
    max_results = max(1, min(int(max_results), 10))
    errors: list[str] = []
    for searcher in (_search_duckduckgo_lite, _search_duckduckgo_html, _search_bing):
        try:
            results = searcher(query, max_results)
            if results:
                return ToolResult(True, f"Encontré {len(results)} resultado(s).", {"results": results})
        except Exception as exc:
            errors.append(f"{searcher.__name__}: {exc}")
    detail = "; ".join(errors) if errors else "sin resultados parseables"
    return ToolResult(False, f"No pude obtener resultados ({detail}).")


def _clean_text(value: str) -> str:
    value = re.sub(r"<.*?>", "", value, flags=re.DOTALL)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def _dedupe(results: list[dict[str, str]], max_results: int) -> list[dict[str, str]]:
    seen = set()
    clean: list[dict[str, str]] = []
    for result in results:
        title = result.get("title", "").strip()
        url = result.get("url", "").strip()
        if not title or not url or url in seen or url.startswith("/"):
            continue
        seen.add(url)
        clean.append({"title": title, "url": url})
        if len(clean) >= max_results:
            break
    return clean


def _unwrap_duckduckgo_url(url: str) -> str:
    url = html.unescape(url)
    if url.startswith("//duckduckgo.com/l/?"):
        url = "https:" + url
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    if "uddg" in params:
        return params["uddg"][0]
    return url


def _search_duckduckgo_lite(query: str, max_results: int) -> list[dict[str, str]]:
    encoded = urllib.parse.urlencode({"q": query})
    page = _open_url(f"https://lite.duckduckgo.com/lite/?{encoded}").decode("utf-8", errors="replace")
    matches = re.findall(
        r'<a[^>]+class=["\']result-link["\'][^>]+href=["\'](.*?)["\'][^>]*>(.*?)</a>',
        page, flags=re.DOTALL | re.IGNORECASE,
    )
    return _dedupe([{"title": _clean_text(t), "url": _unwrap_duckduckgo_url(u)} for u, t in matches], max_results)


def _search_duckduckgo_html(query: str, max_results: int) -> list[dict[str, str]]:
    encoded = urllib.parse.urlencode({"q": query})
    page = _open_url(f"https://duckduckgo.com/html/?{encoded}").decode("utf-8", errors="replace")
    matches = re.findall(
        r'<a[^>]+class=["\']result__a["\'][^>]+href=["\'](.*?)["\'][^>]*>(.*?)</a>',
        page, flags=re.DOTALL | re.IGNORECASE,
    )
    return _dedupe([{"title": _clean_text(t), "url": _unwrap_duckduckgo_url(u)} for u, t in matches], max_results)


def _search_bing(query: str, max_results: int) -> list[dict[str, str]]:
    encoded = urllib.parse.urlencode({"q": query})
    page = _open_url(f"https://www.bing.com/search?{encoded}").decode("utf-8", errors="replace")
    blocks = re.findall(r'<li[^>]+class=["\']b_algo["\'][^>]*>(.*?)</li>', page, flags=re.DOTALL | re.IGNORECASE)
    results = []
    for block in blocks:
        match = re.search(
            r'<h2[^>]*>.*?<a[^>]+href=["\'](.*?)["\'][^>]*>(.*?)</a>',
            block, flags=re.DOTALL | re.IGNORECASE,
        )
        if match:
            results.append({"title": _clean_text(match.group(2)), "url": html.unescape(match.group(1))})
    return _dedupe(results, max_results)


def fetch_webpage(url: str, max_chars: int = 15000) -> ToolResult:
    try:
        data = _open_url(url, timeout=30)
        text = data.decode("utf-8", errors="replace")
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()[:max_chars]
        return ToolResult(True, f"Contenido de {url}", {"url": url, "text": text})
    except Exception as exc:
        return ToolResult(False, f"No pude obtener {url}: {exc}")


def download_file(url: str, filename: str | None = None) -> ToolResult:
    try:
        DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        parsed = urllib.parse.urlparse(url)
        inferred_name = Path(parsed.path).name or "descarga_bolt.bin"
        safe_name = filename or inferred_name
        target = DOWNLOADS_DIR / safe_name
        data = _open_url(url, timeout=60)
        target.write_bytes(data)
        return ToolResult(True, f"Descargué {target}", {"path": str(target), "bytes": len(data)})
    except Exception as exc:
        return ToolResult(False, f"No pude descargar {url}: {exc}")


def find_and_download_pdfs(query: str, max_results: int = 3) -> ToolResult:
    search = web_search(f"{query} filetype:pdf", max_results=max_results * 3)
    if not search.ok:
        return search
    downloaded = []
    for result in (search.data or {}).get("results", []):
        url = result.get("url", "")
        if ".pdf" not in url.lower():
            continue
        outcome = download_file(url)
        if outcome.ok:
            downloaded.append(outcome.data)
        if len(downloaded) >= max_results:
            break
    if not downloaded:
        return ToolResult(False, "No encontré PDFs descargables.", search.data)
    return ToolResult(True, f"Descargué {len(downloaded)} PDF(s).", {"downloads": downloaded})


def build_web_tools() -> list[Tool]:
    return [
        Tool(
            name="web_search",
            description="Busca en internet y devuelve titulos con URLs.",
            parameters={"query": "Consulta", "max_results": "Maximo opcional"},
            handler=web_search,
        ),
        Tool(
            name="fetch_webpage",
            description="Obtiene el contenido de texto de una pagina web.",
            parameters={"url": "URL a obtener", "max_chars": "Maximo de caracteres opcional"},
            handler=fetch_webpage,
        ),
        Tool(
            name="download_file",
            description="Descarga un archivo desde una URL.",
            parameters={"url": "URL directa", "filename": "Nombre opcional"},
            handler=download_file,
        ),
        Tool(
            name="find_and_download_pdfs",
            description="Busca y descarga PDFs de internet.",
            parameters={"query": "Tema o consulta", "max_results": "Cantidad maxima opcional"},
            handler=find_and_download_pdfs,
        ),
    ]
