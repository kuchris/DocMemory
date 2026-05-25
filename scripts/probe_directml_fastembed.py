from __future__ import annotations

import os
from pathlib import Path


MODEL_NAME = os.environ.get(
    "DOCMEMORY_DML_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)
MODEL_CACHE = Path(__file__).resolve().parents[1] / ".models"


def main() -> int:
    import fastembed
    import onnxruntime as ort
    from fastembed import TextEmbedding

    print("ort:", ort.__version__)
    print("ort providers:", ort.get_available_providers())
    print("fastembed:", getattr(fastembed, "__version__", "unknown"))

    supported_models = [item.get("model") for item in TextEmbedding.list_supported_models()]
    related_models = [
        model
        for model in supported_models
        if model and any(part in model.lower() for part in ("e5", "minilm", "mpnet"))
    ]
    print("related supported models:", related_models)
    print("target model supported:", MODEL_NAME in supported_models)
    print("cache:", MODEL_CACHE)
    print("ORT_LOGGING_LEVEL:", os.environ.get("ORT_LOGGING_LEVEL", "not set"))

    print("")
    print("Constructing TextEmbedding with DirectML providers...")
    emb = TextEmbedding(
        model_name=MODEL_NAME,
        cache_dir=str(MODEL_CACHE),
        providers=["DmlExecutionProvider", "CPUExecutionProvider"],
    )

    providers = find_providers(emb)
    print("underlying session providers:", providers or "not found")

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
