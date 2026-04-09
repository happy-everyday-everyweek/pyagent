"""Local model support for offline inference."""

import asyncio
import json
import logging
import subprocess
from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    name: str
    path: str
    model_type: str
    context_length: int = 4096
    gpu_layers: int = 35
    threads: int = 4
    temperature: float = 0.7
    max_tokens: int = 2048


@dataclass
class GenerationResult:
    text: str
    tokens_generated: int
    time_taken: float
    tokens_per_second: float


class BaseModelBackend(ABC):
    @abstractmethod
    def load_model(self, config: ModelConfig) -> bool:
        pass

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> GenerationResult:
        pass

    @abstractmethod
    def generate_stream(self, prompt: str, **kwargs: Any) -> Generator[str, None, None]:
        pass

    @abstractmethod
    def unload_model(self) -> None:
        pass


class LlamaCppBackend(BaseModelBackend):
    """Backend for llama.cpp based models (GGUF format)."""

    def __init__(self, llama_cpp_path: str = "llama.cpp"):
        self._llama_cpp_path = Path(llama_cpp_path)
        self._model_path: Path | None = None
        self._config: ModelConfig | None = None
        self._process: subprocess.Popen | None = None

    def load_model(self, config: ModelConfig) -> bool:
        try:
            self._model_path = Path(config.path)
            self._config = config
            if not self._model_path.exists():
                logger.error("Model file not found: %s", config.path)
                return False
            logger.info("Loaded model: %s", config.name)
            return True
        except Exception as e:
            logger.error("Failed to load model: %s", e)
            return False

    def generate(self, prompt: str, **kwargs: Any) -> GenerationResult:
        import time

        if not self._model_path or not self._config:
            raise RuntimeError("Model not loaded")

        start_time = time.time()
        result_text = ""
        tokens_generated = 0

        try:
            cmd = [
                str(self._llama_cpp_path / "main"),
                "-m",
                str(self._model_path),
                "-p",
                prompt,
                "-n",
                str(kwargs.get("max_tokens", self._config.max_tokens)),
                "--temp",
                str(kwargs.get("temperature", self._config.temperature)),
                "-t",
                str(self._config.threads),
                "-ngl",
                str(self._config.gpu_layers),
                "--no-display-prompt",
            ]

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            result_text = proc.stdout.strip()
            tokens_generated = len(result_text.split())

        except subprocess.TimeoutExpired:
            logger.error("Generation timed out")
        except Exception as e:
            logger.error("Generation failed: %s", e)

        time_taken = time.time() - start_time
        return GenerationResult(
            text=result_text,
            tokens_generated=tokens_generated,
            time_taken=time_taken,
            tokens_per_second=tokens_generated / time_taken if time_taken > 0 else 0,
        )

    def generate_stream(self, prompt: str, **kwargs: Any) -> Generator[str, None, None]:
        if not self._model_path or not self._config:
            raise RuntimeError("Model not loaded")

        cmd = [
            str(self._llama_cpp_path / "main"),
            "-m",
            str(self._model_path),
            "-p",
            prompt,
            "-n",
            str(kwargs.get("max_tokens", self._config.max_tokens)),
            "--temp",
            str(kwargs.get("temperature", self._config.temperature)),
            "-t",
            str(self._config.threads),
            "-ngl",
            str(self._config.gpu_layers),
            "--no-display-prompt",
            "-r",
            "User:",
        ]

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            for line in proc.stdout:
                yield line
        finally:
            proc.terminate()

    def unload_model(self) -> None:
        self._model_path = None
        self._config = None
        if self._process:
            self._process.terminate()
            self._process = None


class MNNBackend(BaseModelBackend):
    """Backend for MNN (Mobile Neural Network) models."""

    def __init__(self, mnn_path: str = "mnn"):
        self._mnn_path = Path(mnn_path)
        self._model_path: Path | None = None
        self._config: ModelConfig | None = None

    def load_model(self, config: ModelConfig) -> bool:
        try:
            self._model_path = Path(config.path)
            self._config = config
            if not self._model_path.exists():
                logger.error("Model file not found: %s", config.path)
                return False
            logger.info("Loaded MNN model: %s", config.name)
            return True
        except Exception as e:
            logger.error("Failed to load MNN model: %s", e)
            return False

    def generate(self, prompt: str, **kwargs: Any) -> GenerationResult:
        import time

        if not self._model_path or not self._config:
            raise RuntimeError("Model not loaded")

        start_time = time.time()
        result_text = ""
        tokens_generated = 0

        try:
            cmd = [
                str(self._mnn_path / "llm_demo"),
                str(self._model_path),
                prompt,
                str(kwargs.get("max_tokens", self._config.max_tokens)),
            ]

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            result_text = proc.stdout.strip()
            tokens_generated = len(result_text.split())

        except Exception as e:
            logger.error("MNN generation failed: %s", e)

        time_taken = time.time() - start_time
        return GenerationResult(
            text=result_text,
            tokens_generated=tokens_generated,
            time_taken=time_taken,
            tokens_per_second=tokens_generated / time_taken if time_taken > 0 else 0,
        )

    def generate_stream(self, prompt: str, **kwargs: Any) -> Generator[str, None, None]:
        result = self.generate(prompt, **kwargs)
        for word in result.text.split():
            yield word + " "

    def unload_model(self) -> None:
        self._model_path = None
        self._config = None


class LocalModelManager:
    """Manager for local model backends."""

    def __init__(self, models_dir: str = "data/models"):
        self._models_dir = Path(models_dir)
        self._models_dir.mkdir(parents=True, exist_ok=True)
        self._backends: dict[str, BaseModelBackend] = {}
        self._models: dict[str, ModelConfig] = {}
        self._current_model: str | None = None

    def register_backend(self, name: str, backend: BaseModelBackend) -> None:
        self._backends[name] = backend

    def get_backend(self, name: str) -> BaseModelBackend | None:
        return self._backends.get(name)

    def list_models(self) -> list[ModelConfig]:
        return list(self._models.values())

    def load_model(self, config: ModelConfig, backend_name: str = "llama.cpp") -> bool:
        backend = self._backends.get(backend_name)
        if not backend:
            if backend_name == "llama.cpp":
                backend = LlamaCppBackend()
            elif backend_name == "mnn":
                backend = MNNBackend()
            else:
                logger.error("Unknown backend: %s", backend_name)
                return False
            self._backends[backend_name] = backend

        if backend.load_model(config):
            self._models[config.name] = config
            self._current_model = config.name
            return True
        return False

    def unload_model(self, model_name: str) -> bool:
        config = self._models.get(model_name)
        if not config:
            return False

        for backend in self._backends.values():
            backend.unload_model()

        del self._models[model_name]
        if self._current_model == model_name:
            self._current_model = None
        return True

    def generate(self, prompt: str, model_name: str | None = None, **kwargs: Any) -> GenerationResult:
        name = model_name or self._current_model
        if not name:
            raise RuntimeError("No model loaded")

        config = self._models.get(name)
        if not config:
            raise RuntimeError(f"Model not found: {name}")

        backend = self._backends.get("llama.cpp")
        if not backend:
            raise RuntimeError("No backend available")

        return backend.generate(prompt, **kwargs)

    def generate_stream(
        self, prompt: str, model_name: str | None = None, **kwargs: Any
    ) -> Generator[str, None, None]:
        name = model_name or self._current_model
        if not name:
            raise RuntimeError("No model loaded")

        config = self._models.get(name)
        if not config:
            raise RuntimeError(f"Model not found: {name}")

        backend = self._backends.get("llama.cpp")
        if not backend:
            raise RuntimeError("No backend available")

        yield from backend.generate_stream(prompt, **kwargs)


_local_model_manager: LocalModelManager | None = None


def get_local_model_manager() -> LocalModelManager:
    global _local_model_manager
    if _local_model_manager is None:
        _local_model_manager = LocalModelManager()
    return _local_model_manager
