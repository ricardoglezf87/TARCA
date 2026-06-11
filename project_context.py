# -*- coding: utf-8 -*-
import json
import os
import re
import unicodedata
from pathlib import Path


DEFAULT_CONTEXT_DIR = "InformacionPrevia"
DEFAULT_CACHE_PATH = ".tarca_cache/project_context.json"
DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_MAX_CHUNKS = 5


def _env_int(nombre, default):
    valor = os.getenv(nombre)
    if not valor:
        return default
    try:
        return int(valor)
    except ValueError:
        print(f"Valor invalido para {nombre}: {valor}. Se usa {default}.")
        return default


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    return texto


def _tokens(texto):
    normalizado = _normalizar(texto)
    return {
        token
        for token in re.findall(r"[a-z0-9_]{3,}", normalizado)
        if token not in {"the", "and", "que", "para", "por", "con", "una", "las", "los", "del"}
    }


def _firma_pdf(ruta):
    stat = ruta.stat()
    return {
        "path": str(ruta),
        "size": stat.st_size,
        "mtime": stat.st_mtime,
    }


def _descubrir_pdfs(carpeta):
    base = Path(carpeta)
    if not base.exists():
        return []
    return sorted(base.rglob("*.pdf"))


def _extraer_paginas_pdf(ruta):
    import fitz

    paginas = []
    with fitz.open(ruta) as documento:
        for indice, pagina in enumerate(documento, start=1):
            texto = pagina.get_text("text").strip()
            if texto:
                paginas.append({"page": indice, "text": texto})
    return paginas


def _crear_chunks(texto, chunk_size, overlap):
    texto = re.sub(r"\s+", " ", texto).strip()
    if not texto:
        return []

    chunks = []
    inicio = 0
    while inicio < len(texto):
        fin = min(len(texto), inicio + chunk_size)
        chunks.append(texto[inicio:fin].strip())
        if fin == len(texto):
            break
        inicio = max(0, fin - overlap)
    return chunks


def _construir_indice(carpeta):
    chunk_size = _env_int("PROJECT_CONTEXT_CHUNK_SIZE", DEFAULT_CHUNK_SIZE)
    overlap = _env_int("PROJECT_CONTEXT_CHUNK_OVERLAP", DEFAULT_CHUNK_OVERLAP)
    pdfs = _descubrir_pdfs(carpeta)
    chunks = []

    for ruta in pdfs:
        try:
            for pagina in _extraer_paginas_pdf(ruta):
                for chunk in _crear_chunks(pagina["text"], chunk_size, overlap):
                    chunks.append(
                        {
                            "source": str(ruta),
                            "name": ruta.name,
                            "page": pagina["page"],
                            "text": chunk,
                            "tokens": sorted(_tokens(chunk)),
                        }
                    )
        except Exception as exc:
            print(f"No se pudo indexar {ruta}: {exc}")

    return {
        "signatures": [_firma_pdf(ruta) for ruta in pdfs],
        "chunks": chunks,
    }


def _cargar_o_crear_indice():
    carpeta = os.getenv("PROJECT_CONTEXT_DIR", DEFAULT_CONTEXT_DIR)
    cache_path = Path(os.getenv("PROJECT_CONTEXT_CACHE", DEFAULT_CACHE_PATH))
    pdfs = _descubrir_pdfs(carpeta)
    firmas = [_firma_pdf(ruta) for ruta in pdfs]

    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            if cache.get("signatures") == firmas:
                return cache
        except (OSError, json.JSONDecodeError):
            pass

    indice = _construir_indice(carpeta)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(indice, ensure_ascii=False), encoding="utf-8")
    print(f"Indice local creado: {len(indice['chunks'])} fragmentos de {len(pdfs)} PDFs.")
    return indice


def buscar_contexto_proyecto(consulta):
    if not consulta:
        return ""

    indice = _cargar_o_crear_indice()
    consulta_tokens = _tokens(consulta)
    if not consulta_tokens:
        return ""

    puntuados = []
    consulta_normalizada = _normalizar(consulta)
    for chunk in indice.get("chunks", []):
        chunk_tokens = set(chunk.get("tokens", []))
        interseccion = consulta_tokens & chunk_tokens
        if not interseccion:
            continue

        score = len(interseccion)
        texto_normalizado = _normalizar(chunk["text"])
        for token in consulta_tokens:
            if token in texto_normalizado:
                score += 0.25
        if consulta_normalizada[:80] and consulta_normalizada[:80] in texto_normalizado:
            score += 5

        puntuados.append((score, chunk))

    puntuados.sort(key=lambda item: item[0], reverse=True)
    max_chunks = _env_int("PROJECT_CONTEXT_MAX_CHUNKS", DEFAULT_MAX_CHUNKS)
    seleccionados = [chunk for _score, chunk in puntuados[:max_chunks]]
    if not seleccionados:
        return ""

    partes = []
    for chunk in seleccionados:
        partes.append(
            f"[{chunk['name']} - pagina {chunk['page']}]\n{chunk['text']}"
        )
    return "\n\n---\n\n".join(partes)
