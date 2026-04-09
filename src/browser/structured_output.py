"""
PyAgent 浏览器自动化模块 - 结构化输出处理器

提供结构化数据提取、JSON Schema 验证和分页数据增量提取功能。
参考 browser-use 项目的结构化输出设计实现。
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


@dataclass
class ExtractedItem:
    """提取的数据项"""
    id: str
    data: dict[str, Any]
    source_url: str | None = None
    extracted_at: str | None = None
    hash: str | None = None


class ExtractionResult(BaseModel):
    """提取结果"""
    success: bool = True
    items: list[dict[str, Any]] = Field(default_factory=list)
    total_count: int = 0
    page_number: int = 1
    has_more: bool = False
    error: str | None = None
    schema_used: dict[str, Any] | None = None


class StructuredOutputProcessor:
    """结构化输出处理器"""

    def __init__(
        self,
        output_model: type[BaseModel] | None = None,
        dedup_enabled: bool = True,
        max_items: int = 1000,
    ):
        """
        初始化结构化输出处理器
        
        Args:
            output_model: 输出模型类
            dedup_enabled: 是否启用去重
            max_items: 最大提取项数
        """
        self._output_model = output_model
        self._dedup_enabled = dedup_enabled
        self._max_items = max_items
        self._extracted_hashes: set[str] = set()
        self._extracted_items: list[ExtractedItem] = []

    def set_output_model(self, model: type[BaseModel]) -> None:
        """设置输出模型"""
        self._output_model = model

    def _compute_hash(self, data: dict[str, Any]) -> str:
        """计算数据哈希"""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(json_str.encode()).hexdigest()

    def _is_duplicate(self, data: dict[str, Any]) -> bool:
        """检查是否重复"""
        if not self._dedup_enabled:
            return False

        data_hash = self._compute_hash(data)
        return data_hash in self._extracted_hashes

    def _add_to_extracted(self, data: dict[str, Any], source_url: str | None = None) -> ExtractedItem:
        """添加到已提取集合"""
        import datetime

        data_hash = self._compute_hash(data)

        item = ExtractedItem(
            id=data_hash[:8],
            data=data,
            source_url=source_url,
            extracted_at=datetime.datetime.now().isoformat(),
            hash=data_hash,
        )

        if self._dedup_enabled:
            self._extracted_hashes.add(data_hash)

        self._extracted_items.append(item)

        return item

    def validate_against_schema(
        self,
        data: dict[str, Any],
        schema: dict[str, Any] | None = None,
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """
        根据 Schema 验证数据
        
        Args:
            data: 要验证的数据
            schema: JSON Schema（可选，默认使用 output_model）
            
        Returns:
            (is_valid, validated_data, error_message)
        """
        if self._output_model is None and schema is None:
            return True, data, None

        try:
            if self._output_model:
                validated = self._output_model(**data)
                return True, validated.model_dump(), None

            return True, data, None

        except ValidationError as e:
            error_msg = str(e)
            logger.warning(f"Validation failed: {error_msg}")
            return False, None, error_msg
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Validation error: {error_msg}")
            return False, None, error_msg

    def extract_single(
        self,
        data: dict[str, Any],
        source_url: str | None = None,
        validate: bool = True,
    ) -> ExtractionResult:
        """
        提取单个数据项
        
        Args:
            data: 数据字典
            source_url: 来源 URL
            validate: 是否验证
            
        Returns:
            ExtractionResult: 提取结果
        """
        if len(self._extracted_items) >= self._max_items:
            return ExtractionResult(
                success=False,
                error=f"Maximum items ({self._max_items}) reached",
            )

        if self._is_duplicate(data):
            logger.debug("Skipping duplicate item")
            return ExtractionResult(
                success=True,
                items=[],
                total_count=len(self._extracted_items),
            )

        if validate:
            is_valid, validated_data, error = self.validate_against_schema(data)
            if not is_valid:
                return ExtractionResult(
                    success=False,
                    error=error,
                )
            data = validated_data or data

        item = self._add_to_extracted(data, source_url)

        return ExtractionResult(
            success=True,
            items=[data],
            total_count=len(self._extracted_items),
        )

    def extract_batch(
        self,
        data_list: list[dict[str, Any]],
        source_url: str | None = None,
        validate: bool = True,
    ) -> ExtractionResult:
        """
        批量提取数据
        
        Args:
            data_list: 数据列表
            source_url: 来源 URL
            validate: 是否验证
            
        Returns:
            ExtractionResult: 提取结果
        """
        extracted_items = []
        errors = []

        for data in data_list:
            if len(self._extracted_items) >= self._max_items:
                break

            result = self.extract_single(data, source_url, validate)

            if result.success and result.items:
                extracted_items.extend(result.items)
            elif not result.success:
                errors.append(result.error)

        return ExtractionResult(
            success=len(extracted_items) > 0,
            items=extracted_items,
            total_count=len(self._extracted_items),
            error="; ".join(errors) if errors else None,
        )

    async def extract_with_llm(
        self,
        llm_client: Any,
        content: str,
        extraction_prompt: str | None = None,
    ) -> ExtractionResult:
        """
        使用 LLM 提取结构化数据
        
        Args:
            llm_client: LLM 客户端
            content: 要提取的内容
            extraction_prompt: 提取提示词
            
        Returns:
            ExtractionResult: 提取结果
        """
        schema_description = ""
        if self._output_model:
            schema = self._output_model.model_json_schema()
            schema_description = f"\n\nOutput schema:\n{json.dumps(schema, indent=2)}"

        default_prompt = f"""Extract structured data from the following content.
{schema_description}

Return the extracted data as a JSON array. Each item should match the schema.
If no data can be extracted, return an empty array [].

Content:
{content}"""

        prompt = extraction_prompt or default_prompt

        try:
            response = await llm_client.chat.completions.create(
                model=llm_client.model,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.choices[0].message.content or "[]"

            import re
            json_match = re.search(r"\[[\s\S]*\]", content)
            if json_match:
                data_list = json.loads(json_match.group())
                return self.extract_batch(data_list)

            return ExtractionResult(
                success=False,
                error="No valid JSON array found in response",
            )

        except json.JSONDecodeError as e:
            return ExtractionResult(
                success=False,
                error=f"JSON parsing failed: {e}",
            )
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return ExtractionResult(
                success=False,
                error=str(e),
            )

    def get_all_extracted(self) -> list[dict[str, Any]]:
        """获取所有已提取的数据"""
        return [item.data for item in self._extracted_items]

    def get_extracted_items(self) -> list[ExtractedItem]:
        """获取所有已提取的数据项（含元数据）"""
        return self._extracted_items.copy()

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "total_items": len(self._extracted_items),
            "unique_hashes": len(self._extracted_hashes),
            "dedup_enabled": self._dedup_enabled,
            "max_items": self._max_items,
        }

    def clear(self) -> None:
        """清除所有已提取的数据"""
        self._extracted_hashes.clear()
        self._extracted_items.clear()
        logger.info("Extracted data cleared")

    def export_to_json(self, indent: int = 2) -> str:
        """导出为 JSON"""
        return json.dumps(
            self.get_all_extracted(),
            indent=indent,
            ensure_ascii=False,
            default=str,
        )

    def export_to_dict(self) -> dict[str, Any]:
        """导出为字典"""
        return {
            "items": self.get_all_extracted(),
            "statistics": self.get_statistics(),
        }
