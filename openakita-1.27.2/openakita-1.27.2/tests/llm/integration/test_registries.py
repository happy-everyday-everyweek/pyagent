"""
集成测试 - 服务商注册表 (8 个)

IT-R01 ~ IT-R08
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from openakita.llm.registries import (
    DashScopeRegistry,
    OpenRouterRegistry,
    SiliconFlowRegistry,
    AnthropicRegistry,
    get_registry,
    list_providers,
)
from openakita.llm.registries.base import ModelInfo


class TestDashScopeRegistry:
    """DashScope 注册表测试"""
    
    @pytest.fixture
    def registry(self):
        return DashScopeRegistry()
    
    @pytest.mark.asyncio
    async def test_it_r01_list_models(self, registry):
        """IT-R01: DashScope 模型列表"""
        mock_response = {
            "output": {
                "models": [
                    {"model_name": "qwen-max"},
                    {"model_name": "qwen-plus"},
                    {"model_name": "qwen-turbo"},
                ]
            }
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            mock_resp.raise_for_status = MagicMock()
            
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance
            
            models = await registry.list_models("test-api-key")
            
            assert len(models) == 3
            assert models[0].id == "qwen-max"
    
    @pytest.mark.asyncio
    async def test_it_r02_capability_completion(self, registry):
        """IT-R02: DashScope 能力补全"""
        mock_response = {
            "output": {
                "models": [
                    {"model_name": "qwen-plus"},
                ]
            }
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            mock_resp.raise_for_status = MagicMock()
            
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance
            
            models = await registry.list_models("test-api-key")
            
            # qwen-plus 应该有 thinking 能力
            assert models[0].capabilities.get("thinking") == True


class TestOpenRouterRegistry:
    """OpenRouter 注册表测试"""
    
    @pytest.fixture
    def registry(self):
        return OpenRouterRegistry()
    
    @pytest.mark.asyncio
    async def test_it_r03_list_models(self, registry):
        """IT-R03: OpenRouter 模型列表"""
        mock_response = {
            "data": [
                {
                    "id": "openai/gpt-4o",
                    "name": "GPT-4o",
                    "architecture": {
                        "input_modalities": ["text", "image"],
                        "supported_parameters": ["tools"]
                    }
                },
            ]
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            mock_resp.raise_for_status = MagicMock()
            
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance
            
            models = await registry.list_models("test-api-key")
            
            assert len(models) == 1
            assert models[0].id == "openai/gpt-4o"
    
    @pytest.mark.asyncio
    async def test_it_r04_capability_parsing(self, registry):
        """IT-R04: OpenRouter 能力解析"""
        mock_response = {
            "data": [
                {
                    "id": "test/vision-model",
                    "name": "Vision Model",
                    "architecture": {
                        "input_modalities": ["text", "image"],
                        "supported_parameters": ["tools", "function_call"]
                    }
                },
            ]
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            mock_resp.raise_for_status = MagicMock()
            
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance
            
            models = await registry.list_models("test-api-key")
            
            caps = models[0].capabilities
            assert caps["vision"] == True
            assert caps["tools"] == True


class TestSiliconFlowRegistry:
    """SiliconFlow 注册表测试"""
    
    @pytest.fixture
    def registry(self):
        return SiliconFlowRegistry()
    
    @pytest.mark.asyncio
    async def test_it_r05_list_models(self, registry):
        """IT-R05: SiliconFlow 模型列表"""
        mock_response = {
            "data": [
                {"id": "deepseek-ai/DeepSeek-V3"},
                {"id": "Qwen/Qwen2.5-72B-Instruct"},
                {"id": "text-embedding-model"},  # 应该被过滤
            ]
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            mock_resp.raise_for_status = MagicMock()
            
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance
            
            models = await registry.list_models("test-api-key")
            
            # 应该过滤掉 embedding 模型
            model_ids = [m.id for m in models]
            assert "text-embedding-model" not in model_ids


class TestAnthropicRegistry:
    """Anthropic 注册表测试"""
    
    @pytest.fixture
    def registry(self):
        return AnthropicRegistry()
    
    @pytest.mark.asyncio
    async def test_it_r06_list_models(self, registry):
        """IT-R06: Anthropic 模型列表"""
        mock_response = {
            "data": [
                {"id": "claude-3-opus-20240229", "display_name": "Claude 3 Opus"},
                {"id": "claude-3-sonnet-20240229", "display_name": "Claude 3 Sonnet"},
            ]
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response
            mock_resp.raise_for_status = MagicMock()
            
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance
            
            models = await registry.list_models("test-api-key")
            
            assert len(models) == 2


class TestErrorHandling:
    """错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_it_r07_invalid_api_key(self):
        """IT-R07: API Key 无效"""
        registry = DashScopeRegistry()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 401
            mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized", request=MagicMock(), response=mock_resp
            )
            
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_resp
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance
            
            # 应该返回预置模型列表而不是抛异常
            models = await registry.list_models("invalid-key")
            
            assert len(models) > 0  # 预置模型
    
    @pytest.mark.asyncio
    async def test_it_r08_network_timeout(self):
        """IT-R08: 网络超时"""
        registry = DashScopeRegistry()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = httpx.TimeoutException("Timeout")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance
            
            # 应该返回预置模型列表
            models = await registry.list_models("test-key")
            
            assert len(models) > 0


class TestHelperFunctions:
    """辅助函数测试"""
    
    def test_get_registry(self):
        """测试 get_registry"""
        registry = get_registry("dashscope")
        assert isinstance(registry, DashScopeRegistry)
        
        with pytest.raises(ValueError):
            get_registry("unknown-provider")
    
    def test_list_providers(self):
        """测试 list_providers"""
        providers = list_providers()
        
        assert len(providers) >= 5
        slugs = [p.slug for p in providers]
        assert "anthropic" in slugs
        assert "dashscope" in slugs
        assert "openrouter" in slugs
