from __future__ import annotations

import os

from app.config import Settings
from app.engine.mlx_engine import MLXEngine
from app.engine.base import GenerationParams


def main() -> None:
    model_path = os.environ.get("MODEL_PATH")
    if not model_path:
        raise SystemExit("MODEL_PATH is required")

    settings = Settings(model_id=os.environ.get("MODEL_ID", "local-mlx"), model_path=model_path)
    engine = MLXEngine(model_id=settings.model_id, model_path=settings.model_path)

    prompt = "user: say hello\nassistant:"
    params = GenerationParams(max_tokens=32, temperature=0.7, top_p=0.9)

    print("engine:", engine.__class__.__name__)
    print("prompt:", prompt)
    print("--- generate() ---")
    text = engine.generate(prompt, params)
    print(text)

    print("--- stream_generate() ---")
    out = []
    for s in engine.stream_generate(prompt, params):
        out.append(s)
    print("".join(out))


if __name__ == "__main__":
    main()

