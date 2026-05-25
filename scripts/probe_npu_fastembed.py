from __future__ import annotations

import os
import site
import sys
from pathlib import Path


MODEL_NAME = os.environ.get(
    "DOCMEMORY_NPU_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)
MODEL_CACHE = Path(__file__).resolve().parents[1] / ".models"
NPU_DEVICE = os.environ.get("DOCMEMORY_NPU_DEVICE", "NPU")
NPU_CACHE_DIR = Path(
    os.environ.get("DOCMEMORY_NPU_CACHE_DIR", str(MODEL_CACHE / "openvino-cache"))
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
            print("openvino libs:", candidate)
            return


def main() -> int:
    add_openvino_dll_dir()
    import fastembed
    import onnxruntime as ort
    from fastembed import TextEmbedding

    print("ort:", ort.__version__)
    print("ort providers:", ort.get_available_providers())
    print("fastembed:", getattr(fastembed, "__version__", "unknown"))
    print("target device:", NPU_DEVICE)
    print("openvino cache:", NPU_CACHE_DIR)
    print("precision:", NPU_PRECISION)

    supported_models = [item.get("model") for item in TextEmbedding.list_supported_models()]
    related_models = [
        model
        for model in supported_models
        if model and any(part in model.lower() for part in ("e5", "minilm", "mpnet"))
    ]
    print("related supported models:", related_models)
    print("target model supported:", MODEL_NAME in supported_models)
    print("cache:", MODEL_CACHE)

    if "OpenVINOExecutionProvider" not in ort.get_available_providers():
        print("")
        print("OpenVINOExecutionProvider is not available in this Python environment.")
        print("Install/run with: uv run --extra npu python scripts\\probe_npu_fastembed.py")
        return 2

    print("")
    print("Constructing TextEmbedding with OpenVINO NPU provider...")
    NPU_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("OV_CACHE_DIR", str(NPU_CACHE_DIR))
    emb = TextEmbedding(
        model_name=MODEL_NAME,
        cache_dir=str(MODEL_CACHE),
        providers=[
            (
                "OpenVINOExecutionProvider",
                {
                    "device_type": NPU_DEVICE,
                    "precision": NPU_PRECISION,
                    "cache_dir": str(NPU_CACHE_DIR),
                    "num_of_threads": NPU_THREADS,
                    "model_priority": NPU_MODEL_PRIORITY,
                    "disable_dynamic_shapes": NPU_DISABLE_DYNAMIC_SHAPES,
                },
            ),
            "CPUExecutionProvider",
        ],
    )

    providers = find_providers(emb)
    print("underlying session providers:", providers or "not found")
    if not providers or "OpenVINOExecutionProvider" not in providers:
        print("")
        print("OpenVINOExecutionProvider is not active. This would run on CPU, so stop here.")
        return 2

    print("")
    print("Running one tiny embed...")
    vectors = list(emb.embed(["query: payment retry design"]))
    print("vectors:", len(vectors))
    if vectors:
        print("dim:", len(vectors[0]))
    return 0


def find_providers(obj):
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
                return get_providers()
            except Exception:
                pass
        for name in ("model", "_model", "session", "ort_session", "_session"):
            child = getattr(item, name, None)
            if child is not None:
                stack.append(child)
    return None


if __name__ == "__main__":
    raise SystemExit(main())
