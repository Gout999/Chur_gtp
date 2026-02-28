"""
ingest_material: parse and index educational material into knowledge graph.
PRD section 2.1.2; Phase 2 (Engineer A).
"""
from pathlib import Path
from typing import Any, Dict, Literal, Optional
from uuid import uuid4


def ingest_material(
    file_path: str,
    source_type: Literal["teacher_upload", "reference", "supplementary"],
    auto_chunk: bool = True,
    custom_chunk_size: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Parse and index material.

    This MVP implementation returns deterministic metadata so graph/agent flows
    can run before heavy parsing/indexing infrastructure is wired.
    """
    path = Path(file_path)
    exists = path.exists()
    inferred_name = path.stem or "material"
    chunk_size = custom_chunk_size or 1000
    chunk_count = 1 if exists else 0

    warnings = []
    if not exists:
        warnings.append("file_not_found")
    if not auto_chunk and custom_chunk_size is None:
        warnings.append("auto_chunk_disabled_without_custom_size")

    knowledge_nodes = [
        {
            "node_id": f"kn_{uuid4().hex[:10]}",
            "title": inferred_name,
            "source_type": source_type,
            "chunk_size": chunk_size,
        }
    ]

    return {
        "material_id": f"mat_{uuid4().hex[:12]}",
        "knowledge_nodes": knowledge_nodes,
        "chunk_count": chunk_count,
        "indexing_status": "success" if exists else "partial",
        "warnings": warnings,
    }
