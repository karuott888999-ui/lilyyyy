"""Persistent, bounded graph memory for the Paint canvas and local coordinator.

This is a user-authored memory graph, not a neural network. Graph traversal is
explainable, depth-limited, and returns source node IDs with every result.
"""
from __future__ import annotations

import json
import re
from typing import Any

from . import core

GRAPH_ID = "default"
MAX_GRAPH_BYTES = 900_000
MAX_LAYERS = 50
MAX_NODES = 300
MAX_EDGES = 1000
MAX_TEXT = 500


def init_graph_db() -> None:
    with core.connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS paint_graphs (
            graph_id TEXT PRIMARY KEY, title TEXT NOT NULL, graph_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""")


def _text(value: Any, label: str, maximum: int = MAX_TEXT, allow_empty: bool = True) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} peab olema tekst")
    value = value.strip()
    if len(value) > maximum or (not value and not allow_empty):
        raise ValueError(f"{label} on tühi või liiga pikk (max {maximum})")
    return value


def validate_graph(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Mõttekaart peab olema JSON-objekt")
    raw = json.dumps(value, ensure_ascii=False)
    if len(raw.encode("utf-8")) > MAX_GRAPH_BYTES:
        raise ValueError("Mõttekaart ületab suurusepiiri")
    title = _text(value.get("title", "Minu mõttekaart"), "Pealkiri", 100, False)
    layers = value.get("layers", [])
    nodes = value.get("nodes", [])
    edges = value.get("edges", [])
    if not all(isinstance(x, list) for x in (layers, nodes, edges)):
        raise ValueError("Kihid, sõlmed ja seosed peavad olema loendid")
    if len(layers) > MAX_LAYERS or len(nodes) > MAX_NODES or len(edges) > MAX_EDGES:
        raise ValueError("Mõttekaardil on liiga palju kihte, sõlmi või seoseid")
    clean_layers = []
    layer_ids = set()
    for layer in layers:
        if not isinstance(layer, dict): raise ValueError("Vigane kiht")
        layer_id = _text(layer.get("id"), "Kihi ID", 80, False)
        if layer_id in layer_ids: raise ValueError("Kihi ID peab olema unikaalne")
        layer_ids.add(layer_id)
        color = _text(layer.get("color", "#777777"), "Kihi värv", 20, False)
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", color): raise ValueError("Kihi värv peab olema HEX")
        clean_layers.append({"id": layer_id, "name": _text(layer.get("name", "Kiht"), "Kihi nimi", 50),
                             "color": color, "opacity": max(.1, min(1.0, float(layer.get("opacity", 1)))),
                             "visible": bool(layer.get("visible", True)), "locked": bool(layer.get("locked", False)),
                             "strokes": layer.get("strokes", []) if isinstance(layer.get("strokes", []), list) else []})
    clean_nodes = []
    node_ids = set()
    for node in nodes:
        if not isinstance(node, dict): raise ValueError("Vigane sõlm")
        node_id = _text(node.get("id"), "Sõlme ID", 80, False)
        if node_id in node_ids: raise ValueError("Sõlme ID peab olema unikaalne")
        node_ids.add(node_id)
        try: x, y = float(node.get("x", 0)), float(node.get("y", 0))
        except (TypeError, ValueError): raise ValueError("Sõlme koordinaadid peavad olema arvud")
        if not (0 <= x <= 1100 and 0 <= y <= 680): raise ValueError("Sõlm on lõuendist väljas")
        node_color = _text(node.get("color", "#777777"), "Sõlme värv", 20, False)
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", node_color): raise ValueError("Sõlme värv peab olema HEX")
        tags = node.get("tags", [])
        if not isinstance(tags, list) or len(tags) > 12 or any(not isinstance(t, str) for t in tags):
            raise ValueError("Sõlme sildid peavad olema kuni 12 tekstist koosnev loend")
        clean_nodes.append({"id": node_id, "label": _text(node.get("label", "Mõte"), "Sõlme nimi", 80, False),
                            "description": _text(node.get("description", ""), "Sõlme kirjeldus", 1000),
                            "topic": _text(node.get("topic", ""), "Teema", 80), "x": x, "y": y,
                            "color": node_color, "layer": _text(node.get("layer", ""), "Kihi ID", 80),
                            "tags": [t.strip()[:40] for t in tags if t.strip()]})
    clean_edges = []
    for edge in edges:
        if not isinstance(edge, dict): raise ValueError("Vigane seos")
        a, b = str(edge.get("a", "")), str(edge.get("b", ""))
        if a not in node_ids or b not in node_ids or a == b: raise ValueError("Seos peab ühendama kaht erinevat olemasolevat sõlme")
        clean_edges.append({"a": a, "b": b, "relation": _text(edge.get("relation", "associated"), "Seose tüüp", 40, False)})
    return {"title": title, "layers": clean_layers, "nodes": clean_nodes, "edges": clean_edges}


def save_graph(value: Any, graph_id: str = GRAPH_ID) -> dict[str, Any]:
    if graph_id != GRAPH_ID:
        raise ValueError("Selles lokaalses prototüübis on toetatud ainult vaikimisi lõuend")
    graph = validate_graph(value)
    stamp = core.now()
    with core.connect() as db:
        db.execute("INSERT INTO paint_graphs(graph_id,title,graph_json,updated_at) VALUES(?,?,?,?) "
                   "ON CONFLICT(graph_id) DO UPDATE SET title=excluded.title,graph_json=excluded.graph_json,updated_at=excluded.updated_at",
                   (graph_id, graph["title"], json.dumps(graph, ensure_ascii=False), stamp))
    return {"graph_id": graph_id, "title": graph["title"], "updated_at": stamp,
            "node_count": len(graph["nodes"]), "edge_count": len(graph["edges"])}


def load_graph(graph_id: str = GRAPH_ID) -> dict[str, Any] | None:
    with core.connect() as db:
        row = db.execute("SELECT graph_json,updated_at FROM paint_graphs WHERE graph_id=?", (graph_id,)).fetchone()
    if not row: return None
    result = json.loads(row["graph_json"])
    result["updated_at"] = row["updated_at"]
    return result


def _terms(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r"[\wõäöüšž]+", text) if len(w) > 2}


def coordinate(query: Any, graph_id: str = GRAPH_ID, max_depth: int = 2, limit: int = 10) -> dict[str, Any]:
    query = core.clean_text(query, core.MAX_PROMPT, "Otsing")
    if graph_id != GRAPH_ID: raise ValueError("Tundmatu mõttekaart")
    depth = max(0, min(int(max_depth), 2)); limit = max(1, min(int(limit), 10))
    graph = load_graph(graph_id)
    if not graph:
        return {"graph_id": graph_id, "query": query, "matches": [], "paths": [], "message": "Salvestatud mõttekaarti pole."}
    qterms = _terms(query)
    nodes = graph["nodes"]
    by_id = {n["id"]: n for n in nodes}
    scored = []
    for node in nodes:
        text = " ".join([node["label"], node["description"], node["topic"], *node["tags"]]).lower()
        overlap = sum(1 for term in qterms if term in text)
        exact = 5 if node["id"] == query.strip() else 0
        if overlap or exact: scored.append((exact + overlap, node))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["id"]))
    roots = [n for _, n in scored[:limit]]
    selected: dict[str, dict[str, Any]] = {n["id"]: n for n in roots}
    paths = []
    frontier = [(n["id"], [n["id"]], 0) for n in roots]
    seen_paths = set()
    for current, path, level in frontier:
        if level >= depth: continue
        for edge in graph["edges"]:
            other = edge["b"] if edge["a"] == current else edge["a"] if edge["b"] == current else None
            if not other or other in path or other not in by_id: continue
            next_path = path + [other]
            key = tuple(next_path)
            if key in seen_paths: continue
            seen_paths.add(key); selected.setdefault(other, by_id[other])
            paths.append({"node_ids": next_path, "relation": edge["relation"], "source": "user-authored canvas"})
            if len(selected) >= limit: break
            frontier.append((other, next_path, level + 1))
        if len(selected) >= limit: break
    return {"graph_id": graph_id, "title": graph["title"], "query": query,
            "matches": list(selected.values()), "paths": paths,
            "depth": depth, "source": "user-authored visual memory",
            "message": "Valitud on ainult märksõna/id vaste ja lubatud sügavusega seotud sõlmed; värv ise tähendust ei määra."}

init_graph_db()
