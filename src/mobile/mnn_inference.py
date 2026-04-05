"""
PyAgent 移动端模块 - MNN本地推理

提供基于MNN的本地模型推理能力，支持在移动设备上运行AI模型。
v0.8.0: 新增MNN本地推理支持

参考: Operit项目 MNN模块
"""

import json
import logging
import os
import platform
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MNNBackend(Enum):
    CPU = "cpu"
    OPENCL = "opencl"
    METAL = "metal"
    VULKAN = "vulkan"
    OPENGL = "opengl"


class MNNPrecision(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class MNNMemory(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class MNNModelStatus(Enum):
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class MNNModelInfo:
    name: str
    path: str
    model_type: str = "llm"
    size_mb: float = 0.0
    quantization: str = "q4"
    context_length: int = 2048
    description: str = ""
    supported_backends: list[MNNBackend] = field(default_factory=lambda: [MNNBackend.CPU])


@dataclass
class MNNInferenceConfig:
    backend: MNNBackend = MNNBackend.CPU
    thread_num: int = 4
    precision: MNNPrecision = MNNPrecision.LOW
    memory: MNNMemory = MNNMemory.LOW
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    cache_dir: str = "data/mobile/mnn_cache"
    model_dir: str = "data/mobile/models"


@dataclass
class MNNMemoryUsage:
    total_mb: float = 0.0
    used_mb: float = 0.0
    available_mb: float = 0.0
    model_mb: float = 0.0
    cache_mb: float = 0.0


@dataclass
class MNNInferenceResult:
    success: bool
    text: str = ""
    tokens_generated: int = 0
    inference_time_ms: float = 0.0
    tokens_per_second: float = 0.0
    error: str = ""


class MNNInference:
    _instance: Optional["MNNInference"] = None
    _lock = threading.Lock()

    def __new__(cls, config: MNNInferenceConfig | None = None) -> "MNNInference":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: MNNInferenceConfig | None = None):
        if self._initialized:
            return

        self._config = config or MNNInferenceConfig()
        self._model_status: dict[str, MNNModelStatus] = {}
        self._loaded_models: dict[str, Any] = {}
        self._model_info: dict[str, MNNModelInfo] = {}
        self._mnn_available: bool = False
        self._mnn_lib_path: str = ""
        self._session: Any = None
        self._current_model: str | None = None
        self._callbacks: list[Callable[[str], None]] = []
        self._init_lock = threading.Lock()
        self._initialized = True

        self._detect_mnn()

    def _detect_mnn(self) -> bool:
        try:
            system = platform.system().lower()

            if system == "linux":
                if "android" in platform.platform().lower():
                    lib_paths = [
                        "/system/lib/libMNN.so",
                        "/system/lib64/libMNN.so",
                        "/vendor/lib/libMNN.so",
                        "/data/local/tmp/libMNN.so",
                    ]
                else:
                    lib_paths = [
                        "/usr/lib/libMNN.so",
                        "/usr/local/lib/libMNN.so",
                        "/usr/lib/x86_64-linux-gnu/libMNN.so",
                    ]
            elif system == "darwin":
                lib_paths = [
                    "/usr/lib/libMNN.dylib",
                    "/usr/local/lib/libMNN.dylib",
                ]
            elif system == "windows":
                lib_paths = [
                    "C:\\Windows\\System32\\MNN.dll",
                    os.path.join(os.path.dirname(sys.executable), "MNN.dll"),
                ]
            else:
                lib_paths = []

            for path in lib_paths:
                if os.path.exists(path):
                    self._mnn_lib_path = path
                    self._mnn_available = True
                    logger.info(f"MNN library found at: {path}")
                    break

            if not self._mnn_available:
                logger.warning("MNN library not found, using fallback mode")

            return self._mnn_available

        except Exception as e:
            logger.error(f"Error detecting MNN: {e}")
            self._mnn_available = False
            return False

    @property
    def is_available(self) -> bool:
        return self._mnn_available

    @property
    def current_model(self) -> str | None:
        return self._current_model

    @property
    def config(self) -> MNNInferenceConfig:
        return self._config

    def initialize(self, model_path: str) -> bool:
        with self._init_lock:
            try:
                if not os.path.exists(model_path):
                    logger.error(f"Model path not found: {model_path}")
                    return False

                config_file = Path(model_path) / "llm_config.json"
                if not config_file.exists():
                    config_file = Path(model_path) / "config.json"

                if not config_file.exists():
                    logger.error(f"Config file not found in: {model_path}")
                    return False

                cache_dir = Path(self._config.cache_dir)
                cache_dir.mkdir(parents=True, exist_ok=True)

                model_name = Path(model_path).name
                self._model_status[model_name] = MNNModelStatus.LOADING

                if self._mnn_available:
                    try:

                        if not self._load_mnn_library():
                            logger.warning("Failed to load MNN library, using simulation mode")
                            self._model_status[model_name] = MNNModelStatus.LOADED
                            self._current_model = model_name
                            return True

                        self._session = self._create_mnn_session(str(config_file))
                        if self._session:
                            self._model_status[model_name] = MNNModelStatus.LOADED
                            self._current_model = model_name
                            logger.info(f"MNN session created for: {model_name}")
                            return True
                        else:
                            self._model_status[model_name] = MNNModelStatus.ERROR
                            return False

                    except Exception as e:
                        logger.error(f"Error creating MNN session: {e}")
                        self._model_status[model_name] = MNNModelStatus.ERROR
                        return False
                else:
                    self._model_status[model_name] = MNNModelStatus.LOADED
                    self._current_model = model_name
                    logger.info(f"Model loaded in simulation mode: {model_name}")
                    return True

            except Exception as e:
                logger.error(f"Failed to initialize MNN: {e}")
                if model_name in self._model_status:
                    self._model_status[model_name] = MNNModelStatus.ERROR
                return False

    def _load_mnn_library(self) -> bool:
        if not self._mnn_lib_path:
            return False

        try:
            import ctypes

            self._mnn_lib = ctypes.CDLL(self._mnn_lib_path)
            return True
        except Exception as e:
            logger.error(f"Failed to load MNN library: {e}")
            return False

    def _create_mnn_session(self, config_path: str) -> Any:
        if not self._mnn_available:
            return None

        try:
            import ctypes

            create_fn = self._mnn_lib.MNNCreateLlm
            create_fn.argtypes = [ctypes.c_char_p]
            create_fn.restype = ctypes.c_void_p

            session_ptr = create_fn(config_path.encode())
            if session_ptr:
                return session_ptr
            return None

        except Exception as e:
            logger.error(f"Error creating MNN session: {e}")
            return None

    def load_model(self, model_name: str) -> bool:
        model_path = os.path.join(self._config.model_dir, model_name)
        if not os.path.exists(model_path):
            model_path = model_name

        return self.initialize(model_path)

    def unload_model(self) -> bool:
        try:
            if self._session and self._mnn_available:
                try:
                    import ctypes

                    release_fn = self._mnn_lib.MNNReleaseLlm
                    release_fn.argtypes = [ctypes.c_void_p]
                    release_fn(self._session)
                except Exception:
                    pass

            self._session = None
            if self._current_model:
                self._model_status[self._current_model] = MNNModelStatus.UNLOADED
            self._current_model = None

            logger.info("Model unloaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to unload model: {e}")
            return False

    def run_inference(
        self,
        input_data: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        stream: bool = False,
        callback: Callable[[str], bool] | None = None,
    ) -> MNNInferenceResult:
        if not self._current_model:
            return MNNInferenceResult(
                success=False,
                error="No model loaded. Call load_model() first.",
            )

        model_status = self._model_status.get(self._current_model)
        if model_status != MNNModelStatus.LOADED:
            return MNNInferenceResult(
                success=False,
                error=f"Model not ready. Status: {model_status}",
            )

        start_time = time.time()
        max_tokens = max_tokens or self._config.max_tokens
        temperature = temperature or self._config.temperature

        try:
            self._model_status[self._current_model] = MNNModelStatus.RUNNING

            if self._mnn_available and self._session:
                result = self._run_mnn_inference(
                    input_data, max_tokens, temperature, stream, callback
                )
            else:
                result = self._run_simulation_inference(
                    input_data, max_tokens, stream, callback
                )

            inference_time = (time.time() - start_time) * 1000

            if result.success:
                tokens_per_second = (
                    result.tokens_generated / (inference_time / 1000)
                    if inference_time > 0
                    else 0
                )
                result.inference_time_ms = inference_time
                result.tokens_per_second = tokens_per_second

            self._model_status[self._current_model] = MNNModelStatus.LOADED
            return result

        except Exception as e:
            self._model_status[self._current_model] = MNNModelStatus.ERROR
            return MNNInferenceResult(
                success=False,
                error=f"Inference error: {str(e)}",
            )

    def _run_mnn_inference(
        self,
        input_data: str,
        max_tokens: int,
        temperature: float,
        stream: bool,
        callback: Callable[[str], bool] | None,
    ) -> MNNInferenceResult:
        try:
            import ctypes

            if stream and callback:
                result = self._run_streaming_mnn(
                    input_data, max_tokens, callback
                )
                return result

            generate_fn = self._mnn_lib.MNNGenerate
            generate_fn.argtypes = [
                ctypes.c_void_p,
                ctypes.c_char_p,
                ctypes.c_int,
            ]
            generate_fn.restype = ctypes.c_char_p

            output = generate_fn(
                self._session,
                input_data.encode(),
                max_tokens,
            )

            if output:
                generated = output.decode()
                return MNNInferenceResult(
                    success=True,
                    text=generated,
                    tokens_generated=len(generated.split()),
                )

            return MNNInferenceResult(
                success=False,
                error="MNN generation returned empty result",
            )

        except Exception as e:
            return MNNInferenceResult(
                success=False,
                error=f"MNN inference error: {str(e)}",
            )

    def _run_streaming_mnn(
        self,
        input_data: str,
        max_tokens: int,
        callback: Callable[[str], bool],
    ) -> MNNInferenceResult:
        generated_text = []
        token_count = 0

        try:
            import ctypes

            callback_func = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_char_p)

            def internal_callback(token: bytes) -> bool:
                nonlocal token_count
                token_str = token.decode()
                generated_text.append(token_str)
                token_count += 1
                return callback(token_str)

            callback_ptr = callback_func(internal_callback)

            stream_fn = self._mnn_lib.MNNGenerateStream
            stream_fn.argtypes = [
                ctypes.c_void_p,
                ctypes.c_char_p,
                ctypes.c_int,
                callback_func,
            ]
            stream_fn.restype = ctypes.c_bool

            success = stream_fn(
                self._session,
                input_data.encode(),
                max_tokens,
                callback_ptr,
            )

            return MNNInferenceResult(
                success=success,
                text="".join(generated_text),
                tokens_generated=token_count,
            )

        except Exception as e:
            return MNNInferenceResult(
                success=False,
                error=f"Streaming error: {str(e)}",
            )

    def _run_simulation_inference(
        self,
        input_data: str,
        max_tokens: int,
        stream: bool,
        callback: Callable[[str], bool] | None,
    ) -> MNNInferenceResult:
        response = f"[MNN Simulation] Processed: {input_data[:100]}..."
        tokens = response.split()
        token_count = len(tokens)

        if stream and callback:
            for token in tokens:
                if not callback(token + " "):
                    break
                time.sleep(0.01)

        return MNNInferenceResult(
            success=True,
            text=response,
            tokens_generated=token_count,
        )

    def get_supported_models(self) -> list[MNNModelInfo]:
        models = []

        model_dir = Path(self._config.model_dir)
        if model_dir.exists():
            for model_path in model_dir.iterdir():
                if model_path.is_dir():
                    config_file = model_path / "llm_config.json"
                    if config_file.exists():
                        try:
                            with open(config_file, encoding="utf-8") as f:
                                config = json.load(f)

                            model_info = MNNModelInfo(
                                name=model_path.name,
                                path=str(model_path),
                                model_type=config.get("model_type", "llm"),
                                context_length=config.get("context_length", 2048),
                                description=config.get("description", ""),
                            )

                            model_size = sum(
                                f.stat().st_size
                                for f in model_path.rglob("*")
                                if f.is_file()
                            )
                            model_info.size_mb = model_size / (1024 * 1024)

                            models.append(model_info)

                        except Exception as e:
                            logger.warning(
                                f"Failed to load model config: {model_path}, error: {e}"
                            )

        default_models = [
            MNNModelInfo(
                name="qwen-1.8b-chat",
                path="data/mobile/models/qwen-1.8b-chat",
                model_type="llm",
                size_mb=1800,
                quantization="q4",
                context_length=8192,
                description="Qwen 1.8B Chat model for mobile devices",
            ),
            MNNModelInfo(
                name="tiny-llama-1.1b",
                path="data/mobile/models/tiny-llama-1.1b",
                model_type="llm",
                size_mb=1100,
                quantization="q4",
                context_length=2048,
                description="TinyLlama 1.1B model optimized for mobile",
            ),
        ]

        existing_names = {m.name for m in models}
        for default in default_models:
            if default.name not in existing_names:
                models.append(default)

        return models

    def get_memory_usage(self) -> MNNMemoryUsage:
        try:
            if platform.system().lower() == "linux":
                meminfo_path = "/proc/meminfo"
                if os.path.exists(meminfo_path):
                    with open(meminfo_path, encoding="utf-8") as f:
                        meminfo = {}
                        for line in f:
                            parts = line.split(":")
                            if len(parts) == 2:
                                key = parts[0].strip()
                                value = parts[1].strip().split()[0]
                                meminfo[key] = int(value)

                    total_kb = meminfo.get("MemTotal", 0)
                    available_kb = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))
                    used_kb = total_kb - available_kb

                    model_mb = 0.0
                    if self._current_model:
                        model_info = self._model_info.get(self._current_model)
                        if model_info:
                            model_mb = model_info.size_mb

                    cache_mb = 0.0
                    cache_dir = Path(self._config.cache_dir)
                    if cache_dir.exists():
                        cache_mb = sum(
                            f.stat().st_size
                            for f in cache_dir.rglob("*")
                            if f.is_file()
                        ) / (1024 * 1024)

                    return MNNMemoryUsage(
                        total_mb=total_kb / 1024,
                        used_mb=used_kb / 1024,
                        available_mb=available_kb / 1024,
                        model_mb=model_mb,
                        cache_mb=cache_mb,
                    )

            import psutil

            memory = psutil.virtual_memory()
            return MNNMemoryUsage(
                total_mb=memory.total / (1024 * 1024),
                used_mb=memory.used / (1024 * 1024),
                available_mb=memory.available / (1024 * 1024),
            )

        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            return MNNMemoryUsage()

    def get_model_status(self, model_name: str | None = None) -> MNNModelStatus:
        model_name = model_name or self._current_model
        if model_name:
            return self._model_status.get(model_name, MNNModelStatus.UNLOADED)
        return MNNModelStatus.UNLOADED

    def reset_session(self) -> bool:
        try:
            if self._session and self._mnn_available:
                try:
                    import ctypes

                    reset_fn = self._mnn_lib.MNNReset
                    reset_fn.argtypes = [ctypes.c_void_p]
                    reset_fn(self._session)
                except Exception:
                    pass

            logger.info("Session reset successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to reset session: {e}")
            return False

    def cancel_generation(self) -> bool:
        try:
            if self._session and self._mnn_available:
                try:
                    import ctypes

                    cancel_fn = self._mnn_lib.MNNCancel
                    cancel_fn.argtypes = [ctypes.c_void_p]
                    cancel_fn(self._session)
                except Exception:
                    pass

            logger.info("Generation cancelled")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel generation: {e}")
            return False

    def set_config(self, **kwargs) -> bool:
        try:
            if "max_tokens" in kwargs:
                self._config.max_tokens = kwargs["max_tokens"]
            if "temperature" in kwargs:
                self._config.temperature = kwargs["temperature"]
            if "top_p" in kwargs:
                self._config.top_p = kwargs["top_p"]
            if "thread_num" in kwargs:
                self._config.thread_num = kwargs["thread_num"]
            if "precision" in kwargs:
                if isinstance(kwargs["precision"], str):
                    self._config.precision = MNNPrecision(kwargs["precision"])
                else:
                    self._config.precision = kwargs["precision"]
            if "memory" in kwargs:
                if isinstance(kwargs["memory"], str):
                    self._config.memory = MNNMemory(kwargs["memory"])
                else:
                    self._config.memory = kwargs["memory"]

            if self._session and self._mnn_available:
                config_json = json.dumps(kwargs)
                try:
                    import ctypes

                    set_config_fn = self._mnn_lib.MNNSetConfig
                    set_config_fn.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
                    set_config_fn.restype = ctypes.c_bool

                    return set_config_fn(self._session, config_json.encode())
                except Exception:
                    pass

            return True

        except Exception as e:
            logger.error(f"Failed to set config: {e}")
            return False

    def cleanup(self) -> None:
        self.unload_model()
        self._model_status.clear()
        self._model_info.clear()
        self._callbacks.clear()

    @classmethod
    def reset_instance(cls) -> None:
        if cls._instance:
            cls._instance.cleanup()
            cls._instance = None


mnn_inference = MNNInference()
