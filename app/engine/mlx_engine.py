from __future__ import annotations

import importlib.util
from collections.abc import Iterable
from typing import Sequence

from .base import ChatMessageLike, GenerationParams, LLMEngine


class MLXEngine(LLMEngine):
    """MLX engine via `mlx-lm`.

    `mlx_lm.stream_generate(..., **kwargs)` forwards kwargs to an internal
    `generate_step()` which may differ across builds. Some installs reject
    keys like `top_p` and/or `temperature`.

    We therefore probe supported kwargs once (best-effort) and cache the result.
    """

    def __init__(self, model_id: str, model_path: str | None) -> None:
        self.model_id = model_id
        self.model_path = model_path

        spec = importlib.util.find_spec("mlx_lm")
        if spec is None:
            raise RuntimeError(
                "MLX generation requires the optional 'mlx-lm' package. "
                "Install it with: uv add mlx-lm"
            )

        from mlx_lm import load  # type: ignore

        path = model_path or model_id
        self._model, self._tokenizer = load(path)

        # Cached supported kwargs for this environment.
        self._supported: set[str] | None = None
        self._temp_kw: str | None = None

    def _probe_supported_kwargs(self) -> None:
        """Probe which kwargs are accepted by the internal generate_step.

        We do one tiny generation (max_tokens=1) with different kwargs.
        On unexpected keyword errors, we drop that key.
        """
        if self._supported is not None:
            return

        from mlx_lm import stream_generate  # type: ignore

        supported = {"temp", "temperature", "top_p"}

        # Use a tiny prompt and minimal generation.
        prompt = "hello"

        # We'll try multiple times, dropping keys that fail.
        def _try(kwargs: dict) -> Exception | None:
            try:
                it = stream_generate(
                    self._model,
                    self._tokenizer,
                    prompt,
                    max_tokens=1,
                    **kwargs,
                )
                next(iter(it))
                return None
            except Exception as e:
                return e

        # First, try all.
        kwargs = {"temp": 0.0, "temperature": 0.0, "top_p": 1.0}
        err = _try({k: v for k, v in kwargs.items() if k in supported})
        if err is not None:
            msg = str(err)
            # Repeatedly remove the offending key if it's an unexpected keyword.
            while "unexpected keyword argument" in msg:
                # Extract key name between quotes if possible.
                bad = None
                for key in list(supported):
                    if f"'{key}'" in msg or f'"{key}"' in msg:
                        bad = key
                        break
                if bad is None:
                    break
                supported.discard(bad)
                err = _try({k: v for k, v in kwargs.items() if k in supported})
                if err is None:
                    break
                msg = str(err)

        # Decide temp kw preference.
        if "temperature" in supported:
            temp_kw = "temperature"
        elif "temp" in supported:
            temp_kw = "temp"
        else:
            temp_kw = None

        self._supported = supported
        self._temp_kw = temp_kw

        print(f"[mlx] supported_kwargs={sorted(supported)} temp_kw={temp_kw}")

    def _mlx_lm_kwargs(self, params: GenerationParams) -> dict:
        self._probe_supported_kwargs()

        kwargs: dict = {}
        assert self._supported is not None

        if self._temp_kw is not None and self._temp_kw in self._supported:
            kwargs[self._temp_kw] = float(params.temperature)
        if "top_p" in self._supported:
            kwargs["top_p"] = float(params.top_p)

        return kwargs

    def generate(self, prompt: str, params: GenerationParams) -> str:
        from mlx_lm import stream_generate  # type: ignore

        pieces: list[str] = []
        for resp in stream_generate(
            self._model,
            self._tokenizer,
            prompt,
            max_tokens=int(params.max_tokens),
            **self._mlx_lm_kwargs(params),
        ):
            text = getattr(resp, "text", None)
            if text is None:
                text = str(resp)
            pieces.append(str(text))
        return "".join(pieces)

    def stream_generate(self, prompt: str, params: GenerationParams) -> Iterable[str]:
        from mlx_lm import stream_generate  # type: ignore

        for resp in stream_generate(
            self._model,
            self._tokenizer,
            prompt,
            max_tokens=int(params.max_tokens),
            **self._mlx_lm_kwargs(params),
        ):
            text = getattr(resp, "text", None)
            if text is None:
                yield str(resp)
            else:
                yield str(text)

    @staticmethod
    def _render_fallback_chat(messages: Sequence[ChatMessageLike]) -> str:
        parts: list[str] = []
        for m in messages:
            if getattr(m, "content", None) is None:
                continue
            parts.append(f"{m.role}: {m.content}")
        parts.append("assistant:")
        return "\n".join(parts)

    def _render_chat(self, messages: Sequence[ChatMessageLike]) -> str:
        tok = self._tokenizer
        # Many HF tokenizers expose apply_chat_template.
        apply = getattr(tok, "apply_chat_template", None)
        if callable(apply):
            try:
                chat = [{"role": m.role, "content": m.content or ""} for m in messages]
                return apply(chat, tokenize=False, add_generation_prompt=True)
            except Exception:
                pass
        return self._render_fallback_chat(messages)

    @staticmethod
    def _post_process(prompt: str, generated: str) -> str:
        # 1) If the model echoed the prompt, strip it.
        if generated.startswith(prompt):
            generated = generated[len(prompt) :]

        # 2) If the model starts repeating the conversation, cut when a new user/system turn appears.
        cut_markers = ["\nuser:", "\nsystem:", "\nUser:", "\nSystem:"]
        cut_at = None
        for m in cut_markers:
            idx = generated.find(m)
            if idx != -1:
                cut_at = idx if cut_at is None else min(cut_at, idx)
        if cut_at is not None:
            generated = generated[:cut_at]

        return generated.lstrip("\n")

    def generate_chat(self, messages: Sequence[ChatMessageLike], params: GenerationParams) -> str:
        prompt = self._render_chat(messages)
        text = self.generate(prompt, params)
        return self._post_process(prompt, text)

    def stream_generate_chat(
        self, messages: Sequence[ChatMessageLike], params: GenerationParams
    ) -> Iterable[str]:
        # We produce incremental chunks after post-processing by keeping a rolling buffer.
        prompt = self._render_chat(messages)
        buf = ""
        emitted = 0
        for chunk in self.stream_generate(prompt, params):
            buf += chunk
            processed = self._post_process(prompt, buf)
            if len(processed) > emitted:
                yield processed[emitted:]
                emitted = len(processed)

