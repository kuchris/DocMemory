from __future__ import annotations

import os
import site
import sys
from pathlib import Path

from . import cli


NPU_VECTOR_MODEL = os.environ.get(
    "DOCMEMORY_NPU_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)
NPU_BATCH_SIZE = int(os.environ.get("DOCMEMORY_NPU_BATCH_SIZE", "32"))
NPU_PARALLEL = int(os.environ.get("DOCMEMORY_NPU_PARALLEL", "2"))
NPU_MAX_CHARS = int(os.environ.get("DOCMEMORY_NPU_MAX_CHARS", "600"))
NPU_DEVICE = os.environ.get("DOCMEMORY_NPU_DEVICE", "NPU")
NPU_CACHE_DIR = Path(
    os.environ.get("DOCMEMORY_NPU_CACHE_DIR", str(cli.MODEL_CACHE_DIR / "openvino-cache"))
).resolve()
NPU_PRECISION = os.environ.get("DOCMEMORY_NPU_PRECISION", "FP16")
NPU_THREADS = os.environ.get("DOCMEMORY_NPU_THREADS", "4")
NPU_MODEL_PRIORITY = os.environ.get("DOCMEMORY_NPU_MODEL_PRIORITY", "HIGH")
NPU_DISABLE_DYNAMIC_SHAPES = os.environ.get("DOCMEMORY_NPU_DISABLE_DYNAMIC_SHAPES", "True")


def add_openvino_dll_dir() -> None:
    search_roots = [Path(item) for item in site.getsitepackages()]
    search_roots.extend(Path(item) for item in sys.path if item)
    for root in search_roots:
        candidate = root / "openvino" / "libs"
        if (candidate / "openvino.dll").exists():
            os.environ["PATH"] = str(candidate) + os.pathsep + os.environ.get("PATH", "")
            add_dll_directory = getattr(os, "add_dll_directory", None)
            if add_dll_directory is not None:
                add_dll_directory(str(candidate))
            return


def make_npu_embedding_model(TextEmbedding, model_name: str):
    cache_dir = Path(os.environ.get("DOCMEMORY_MODEL_DIR", str(cli.MODEL_CACHE_DIR))).resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)
    NPU_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("OV_CACHE_DIR", str(NPU_CACHE_DIR))
    provider_options = {
        "device_type": NPU_DEVICE,
        "precision": NPU_PRECISION,
        "cache_dir": str(NPU_CACHE_DIR),
        "num_of_threads": NPU_THREADS,
        "model_priority": NPU_MODEL_PRIORITY,
        "disable_dynamic_shapes": NPU_DISABLE_DYNAMIC_SHAPES,
    }
    model = TextEmbedding(
        model_name=model_name,
        cache_dir=str(cache_dir),
        providers=[("OpenVINOExecutionProvider", provider_options), "CPUExecutionProvider"],
    )
    providers = find_providers(model)
    if "OpenVINOExecutionProvider" not in providers:
        raise cli.DocMemoryError(
            f"OpenVINOExecutionProvider is not active; providers={providers or ['unknown']}"
        )
    return model


def find_providers(obj) -> list[str]:
    seen: set[int] = set()
    stack = [obj]
    while stack:
        item = stack.pop()
        item_id = id(item)
        if item_id in seen:
            continue
        seen.add(item_id)
        get_providers = getattr(item, "get_providers", None)
        if callable(get_providers):
            try:
                return list(get_providers())
            except Exception:
                pass
        for name in ("model", "_model", "session", "ort_session", "_session"):
            child = getattr(item, name, None)
            if child is not None:
                stack.append(child)
    return []


def main(argv: list[str] | None = None) -> int:
    add_openvino_dll_dir()
    cli.DEFAULT_VECTOR_MODEL = NPU_VECTOR_MODEL
    cli.VECTOR_BATCH_SIZE = NPU_BATCH_SIZE
    cli.VECTOR_PARALLEL = NPU_PARALLEL
    cli.VECTOR_MAX_CHARS = NPU_MAX_CHARS
    cli.make_embedding_model = make_npu_embedding_model
    return cli.main(argv)
