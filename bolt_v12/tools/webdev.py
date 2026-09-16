from __future__ import annotations

import re
from pathlib import Path

from ..config import ROOT_DIR
from .base import Tool, ToolResult


def _slug(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return value or "sitio-bolt"


def create_static_website(title: str, brief: str, folder_name: str | None = None) -> ToolResult:
    slug = _slug(folder_name or title)
    target_dir = ROOT_DIR / "ThunderStudio" / "Sitios_Bolt" / slug
    target_dir.mkdir(parents=True, exist_ok=True)
    index_path = target_dir / "index.html"
    css_path = target_dir / "styles.css"

    html_content = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <nav class="topbar">
    <strong>{title}</strong>
    <div>
      <a href="#experiencia">Experiencia</a>
      <a href="#detalles">Detalles</a>
      <a href="#comprar">Comprar</a>
    </div>
  </nav>
  <main>
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Audio personal premium</p>
        <h1>{title}</h1>
        <p>{brief}</p>
        <div class="actions">
          <a class="primary" href="#comprar">Ver opciones</a>
          <a class="secondary" href="#detalles">Explorar detalles</a>
        </div>
      </div>
      <div class="product-stage">
        <div class="case"></div>
        <div class="bud bud-left"></div>
        <div class="bud bud-right"></div>
      </div>
    </section>
    <section id="experiencia" class="band">
      <h2>Diseñados para moverse contigo</h2>
      <div class="grid">
        <article><span>01</span><h3>Conexión inmediata</h3><p>Una experiencia clara y directa para escuchar, trabajar o crear sin fricción.</p></article>
        <article><span>02</span><h3>Sonido envolvente</h3><p>Una presentación inmersiva con foco en claridad y presencia.</p></article>
        <article><span>03</span><h3>Control intuitivo</h3><p>Interacciones simples, visuales limpias y jerarquía pensada para conversión.</p></article>
      </div>
    </section>
    <section id="detalles" class="split">
      <div><p class="eyebrow">Detalles</p><h2>Minimalismo técnico con carácter</h2></div>
      <p>Sitio web profesional generado por Bolt V12. Puede evolucionar con imágenes reales, animaciones y sección de compra.</p>
    </section>
    <section id="comprar" class="cta">
      <h2>Listos para una experiencia más limpia</h2>
      <a class="primary" href="#">Solicitar demo</a>
    </section>
  </main>
</body>
</html>"""

    css = """:root{color-scheme:dark;--bg:#05070a;--panel:#10141a;--text:#f5f7fb;--muted:#9aa4b2;--line:#252d38;--accent:#74d7ff;--warm:#f4b15d}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,system-ui,sans-serif}.topbar{position:sticky;top:0;z-index:5;display:flex;justify-content:space-between;align-items:center;padding:18px clamp(20px,5vw,72px);background:rgba(5,7,10,.82);backdrop-filter:blur(18px);border-bottom:1px solid var(--line)}.topbar a{color:var(--muted);text-decoration:none;margin-left:22px}.hero{min-height:88vh;display:grid;grid-template-columns:minmax(0,.95fr) minmax(320px,1.05fr);gap:40px;align-items:center;padding:clamp(48px,8vw,96px) clamp(20px,5vw,72px)}.hero h1{font-size:clamp(56px,9vw,124px);line-height:.9;margin:0 0 24px}.hero p,.split p{max-width:650px;color:var(--muted);font-size:clamp(17px,2vw,22px);line-height:1.55}.eyebrow{color:var(--accent);text-transform:uppercase;letter-spacing:.12em;font-size:13px!important;font-weight:700}.actions{display:flex;gap:14px;flex-wrap:wrap;margin-top:30px}.primary,.secondary{display:inline-flex;align-items:center;min-height:44px;padding:0 18px;border-radius:6px;text-decoration:none;font-weight:700}.primary{background:var(--text);color:var(--bg)}.secondary{color:var(--text);border:1px solid var(--line)}.product-stage{position:relative;min-height:460px;border-radius:8px;overflow:hidden;background:radial-gradient(circle at 50% 35%,rgba(116,215,255,.24),transparent 34%),linear-gradient(135deg,#111923,#07090d)}.case{position:absolute;left:50%;bottom:64px;width:300px;height:190px;transform:translateX(-50%);border-radius:58px;background:linear-gradient(145deg,#f7f8fb,#c9d0da);box-shadow:0 38px 90px rgba(0,0,0,.45)}.bud{position:absolute;top:92px;width:88px;height:170px;border-radius:48px 48px 38px 38px;background:linear-gradient(145deg,#fff,#cbd3df);box-shadow:0 24px 70px rgba(0,0,0,.38)}.bud::after{content:"";position:absolute;left:32px;bottom:-90px;width:24px;height:110px;border-radius:14px;background:linear-gradient(180deg,#eef2f7,#b5bfcb)}.bud-left{left:calc(50% - 150px);transform:rotate(-8deg)}.bud-right{right:calc(50% - 150px);transform:rotate(8deg)}.band,.split,.cta{padding:clamp(48px,7vw,88px) clamp(20px,5vw,72px);border-top:1px solid var(--line)}.band h2,.split h2,.cta h2{font-size:clamp(32px,5vw,64px);margin:0 0 28px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}article{border:1px solid var(--line);border-radius:8px;padding:24px;background:var(--panel)}article span{color:var(--warm);font-weight:800}article p{color:var(--muted);line-height:1.6}.split{display:grid;grid-template-columns:minmax(0,.8fr) minmax(0,1fr);gap:36px}.cta{min-height:320px;display:grid;place-items:center;text-align:center}@media(max-width:780px){.topbar div{display:none}.hero,.split,.grid{grid-template-columns:1fr}.product-stage{min-height:360px}}
"""

    index_path.write_text(html_content, encoding="utf-8")
    css_path.write_text(css, encoding="utf-8")
    return ToolResult(
        True,
        f"Sitio web creado en {target_dir}",
        {"folder": str(target_dir), "index": str(index_path), "css": str(css_path)},
    )


def build_webdev_tools() -> list[Tool]:
    return [
        Tool(
            name="create_static_website",
            description="Crea un sitio web estatico profesional con HTML y CSS.",
            parameters={"title": "Titulo del sitio", "brief": "Descripcion", "folder_name": "Carpeta opcional"},
            handler=create_static_website,
        ),
    ]
