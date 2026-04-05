"""
单元测试 - STT 客户端 (6 个)

UT-S01 ~ UT-S06
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from openakita.llm.stt_client import STTClient
from openakita.llm.types import EndpointConfig


def _make_stt_endpoint(name: str, priority: int = 1) -> EndpointConfig:
    """创建测试用 STT 端点配置"""
    return EndpointConfig(
        name=name,
        provider="openai",
        api_type="openai",
        base_url="https://api.openai.com/v1",
        api_key_env="TEST_STT_KEY",
        model="whisper-1",
        priority=priority,
    )


class TestSTTAvailability:
    """STT 可用性测试"""

    def test_ut_s01_empty_endpoints_not_available(self):
        """UT-S01: 空端点 is_available == False"""
        client = STTClient(endpoints=None)
        assert client.is_available is False

        client2 = STTClient(endpoints=[])
        assert client2.is_available is False

    def test_ut_s02_with_endpoints_available(self):
        """UT-S02: 有端点 is_available == True"""
        ep = _make_stt_endpoint("stt-1")
        client = STTClient(endpoints=[ep])
        assert client.is_available is True
        assert len(client.endpoints) == 1


class TestSTTTranscription:
    """STT 转写测试"""

    @pytest.mark.asyncio
    async def test_ut_s03_transcribe_success(self, tmp_path):
        """UT-S03: transcribe 成功 — mock httpx → 返回转写文本"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        ep = _make_stt_endpoint("stt-ok")
        client = STTClient(endpoints=[ep])

        mock_response = MagicMock()
        mock_response.json.return_value = {"text": "你好世界"}
        mock_response.raise_for_status = MagicMock()

        mock_http_client = MagicMock()
        mock_http_client.__enter__ = MagicMock(return_value=mock_http_client)
        mock_http_client.__exit__ = MagicMock(return_value=False)
        mock_http_client.post.return_value = mock_response

        with (
            patch("httpx.Client", return_value=mock_http_client),
            patch.object(ep, "get_api_key", return_value="sk-test-key"),
        ):
            result = await client.transcribe(str(audio_file))

        assert result == "你好世界"

    @pytest.mark.asyncio
    async def test_ut_s04_transcribe_failover(self, tmp_path):
        """UT-S04: 第一个端点失败 → 自动 failover 到第二个"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        ep1 = _make_stt_endpoint("stt-bad", priority=1)
        ep2 = _make_stt_endpoint("stt-good", priority=2)
        client = STTClient(endpoints=[ep1, ep2])

        call_count = 0

        def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("First endpoint down")
            resp = MagicMock()
            resp.json.return_value = {"text": "Failover 成功"}
            resp.raise_for_status = MagicMock()
            return resp

        mock_http_client = MagicMock()
        mock_http_client.__enter__ = MagicMock(return_value=mock_http_client)
        mock_http_client.__exit__ = MagicMock(return_value=False)
        mock_http_client.post.side_effect = mock_post

        with (
            patch("httpx.Client", return_value=mock_http_client),
            patch.object(ep1, "get_api_key", return_value="sk-test-1"),
            patch.object(ep2, "get_api_key", return_value="sk-test-2"),
        ):
            result = await client.transcribe(str(audio_file))

        assert result == "Failover 成功"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_ut_s05_all_endpoints_failed(self, tmp_path):
        """UT-S05: 全部端点失败 → 返回 None"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        ep1 = _make_stt_endpoint("stt-fail-1", priority=1)
        ep2 = _make_stt_endpoint("stt-fail-2", priority=2)
        client = STTClient(endpoints=[ep1, ep2])

        mock_http_client = MagicMock()
        mock_http_client.__enter__ = MagicMock(return_value=mock_http_client)
        mock_http_client.__exit__ = MagicMock(return_value=False)
        mock_http_client.post.side_effect = ConnectionError("All down")

        with (
            patch("httpx.Client", return_value=mock_http_client),
            patch.object(ep1, "get_api_key", return_value="sk-test-1"),
            patch.object(ep2, "get_api_key", return_value="sk-test-2"),
        ):
            result = await client.transcribe(str(audio_file))

        assert result is None


class TestSTTReload:
    """STT 重载测试"""

    def test_ut_s06_reload_updates_endpoints(self):
        """UT-S06: 调用 reload 后端点列表更新"""
        ep1 = _make_stt_endpoint("stt-old", priority=1)
        client = STTClient(endpoints=[ep1])
        assert len(client.endpoints) == 1
        assert client.endpoints[0].name == "stt-old"

        # 重载为新端点
        ep2 = _make_stt_endpoint("stt-new-1", priority=2)
        ep3 = _make_stt_endpoint("stt-new-2", priority=1)
        client.reload(endpoints=[ep2, ep3])

        assert len(client.endpoints) == 2
        # 应该按 priority 排序
        assert client.endpoints[0].name == "stt-new-2"  # priority=1
        assert client.endpoints[1].name == "stt-new-1"  # priority=2

        # 重载为空
        client.reload(endpoints=[])
        assert client.is_available is False
        assert len(client.endpoints) == 0
