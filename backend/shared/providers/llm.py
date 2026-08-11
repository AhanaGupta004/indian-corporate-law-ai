from typing import Protocol, Optional
import ollama
import asyncio
import re
import logging
from shared.config.settings import get_settings

logger = logging.getLogger(__name__)

class LLMProvider(Protocol):
    async def generate(self, prompt: str, timeout: int) -> Optional[str]:
        ...

class OllamaProvider:
    def __init__(self):
        self.settings = get_settings()
        self.model = self.settings.OLLAMA_MODEL
        self._semaphore = asyncio.Semaphore(5)

    async def generate(self, prompt: str, timeout: int) -> Optional[str]:
        logger.info(f"[LLM] Calling {self.model} (timeout={timeout}s, prompt={len(prompt)} chars)...")

        def _sync():
            return ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=False,
                options={
                    "num_predict":    1500,
                    "temperature":    0.15,
                    "top_k":          30,
                    "top_p":          0.90,
                    "repeat_penalty": 1.15,
                    "stop": ["Output:", "Note:", "I hope"],
                },
            )

        try:
            loop = asyncio.get_event_loop()
            async with self._semaphore:
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, _sync),
                    timeout=timeout,
                )
            raw = result.get("message", {}).get("content", "").strip()

            # Strip thinking blocks (Qwen3 / DeepSeek)
            raw = re.sub(r"<think>[\s\S]*?</think>", "", raw, flags=re.DOTALL).strip()
            raw = re.sub(r"<thinking>[\s\S]*?</thinking>", "", raw, flags=re.DOTALL).strip()

            # Strip markdown code fences
            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE).strip()
            raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE).strip()

            # Strip escaped quotes
            if raw.startswith('"') and raw.endswith('"'):
                raw = raw[1:-1].replace('\\"', '"')

            logger.info(f"[LLM] Response received: {len(raw)} chars")
            return raw

        except asyncio.TimeoutError:
            logger.error(f"[TIMEOUT] LLM timed out after {timeout}s")
            return None
        except Exception as exc:
            logger.error(f"[FAIL] LLM error: {exc}", exc_info=True)
            return None
