"""
PyAgent 地图工具测试
"""

import pytest
import asyncio

from src.execution.tools.map import OfflineMapTool, GeoUtils, GeoPoint, GeoBounds
from src.execution.tools.base import ToolCategory, RiskLevel


class TestOfflineMapTool:
    """离线地图工具测试"""

    def test_tool_properties(self):
        """测试工具属性"""
        tool = OfflineMapTool()
        
        assert tool.name == "offline_map"
        assert tool.category == ToolCategory.MAP
        assert tool.risk_level == RiskLevel.SAFE
        assert "地图" in tool.description

    def test_list_regions(self):
        """测试列出区域"""
        tool = OfflineMapTool()
        result = asyncio.run(tool.execute(action="regions"))
        
        assert result.success is True
        assert "regions" in result.data

    def test_list_collections(self):
        """测试列出收藏集"""
        tool = OfflineMapTool()
        result = asyncio.run(tool.execute(action="collections"))
        
        assert result.success is True
        assert "collections" in result.data

    def test_search_poi(self):
        """测试POI搜索"""
        tool = OfflineMapTool()
        result = asyncio.run(tool.execute(action="search", query="天安门"))
        
        assert result.success is True
        assert "results" in result.data

    def test_search_poi_without_query(self):
        """测试无关键词POI搜索"""
        tool = OfflineMapTool()
        result = asyncio.run(tool.execute(action="search"))
        
        assert result.success is False

    def test_nearby_search(self):
        """测试附近搜索"""
        tool = OfflineMapTool()
        result = asyncio.run(tool.execute(
            action="nearby",
            lat=39.9042,
            lon=116.4074,
            radius=50
        ))
        
        assert result.success is True
        assert "results" in result.data

    def test_nearby_search_without_coords(self):
        """测试无坐标附近搜索"""
        tool = OfflineMapTool()
        result = asyncio.run(tool.execute(action="nearby"))
        
        assert result.success is False

    def test_reverse_geocode(self):
        """测试逆地理编码"""
        tool = OfflineMapTool()
        result = asyncio.run(tool.execute(
            action="reverse_geocode",
            lat=39.9042,
            lon=116.4074
        ))
        
        assert result.success is True
        assert "coordinates" in result.data

    def test_calculate_distance(self):
        """测试距离计算"""
        tool = OfflineMapTool()
        result = asyncio.run(tool.execute(
            action="distance",
            lat=39.9042,
            lon=116.4074,
            lat2=31.2304,
            lon2=121.4737
        ))
        
        assert result.success is True
        assert "distance_km" in result.data
        assert result.data["distance_km"] > 1000


class TestGeoUtils:
    """地理计算工具测试"""

    def test_haversine_distance(self):
        """测试Haversine距离计算"""
        distance = GeoUtils.haversine_distance(
            39.9042, 116.4074,
            31.2304, 121.4737
        )
        
        assert 1000 < distance < 1500

    def test_distance_same_point(self):
        """测试相同点距离"""
        distance = GeoUtils.haversine_distance(
            39.9042, 116.4074,
            39.9042, 116.4074
        )
        
        assert distance == 0

    def test_bearing(self):
        """测试方位角计算"""
        bearing = GeoUtils.bearing(
            39.9042, 116.4074,
            31.2304, 121.4737
        )
        
        assert 0 <= bearing <= 360

    def test_is_point_in_bounds(self):
        """测试点是否在边界内"""
        bounds = GeoBounds(30, 100, 40, 120)
        
        assert GeoUtils.is_point_in_bounds(35, 110, bounds) is True
        assert GeoUtils.is_point_in_bounds(25, 110, bounds) is False
        assert GeoUtils.is_point_in_bounds(35, 130, bounds) is False

    def test_get_bounding_box(self):
        """测试获取边界框"""
        bounds = GeoUtils.get_bounding_box(39.9042, 116.4074, 10)
        
        assert bounds.min_lat < 39.9042 < bounds.max_lat
        assert bounds.min_lon < 116.4074 < bounds.max_lon

    def test_format_coordinates_decimal(self):
        """测试坐标格式化（小数）"""
        result = GeoUtils.format_coordinates(39.9042, 116.4074, "decimal")
        
        assert "39.9042" in result
        assert "116.4074" in result

    def test_format_coordinates_dms(self):
        """测试坐标格式化（度分秒）"""
        result = GeoUtils.format_coordinates(39.9042, 116.4074, "dms")
        
        assert "°" in result
        assert "'" in result
        assert '"' in result

    def test_parse_coordinates_decimal(self):
        """测试解析小数坐标"""
        point = GeoUtils.parse_coordinates("39.9042, 116.4074")
        
        assert point is not None
        assert abs(point.lat - 39.9042) < 0.001
        assert abs(point.lon - 116.4074) < 0.001

    def test_parse_coordinates_space(self):
        """测试解析空格分隔坐标"""
        point = GeoUtils.parse_coordinates("39.9042 116.4074")
        
        assert point is not None
        assert abs(point.lat - 39.9042) < 0.001


class TestOfflineMapToolParameters:
    """地图工具参数测试"""

    def test_parameter_schema(self):
        """测试参数Schema"""
        tool = OfflineMapTool()
        schema = tool.get_parameter_schema()
        
        assert "properties" in schema
        assert "action" in schema["properties"]
        assert "lat" in schema["properties"]
        assert "lon" in schema["properties"]

    def test_get_info(self):
        """测试获取工具信息"""
        tool = OfflineMapTool()
        info = tool.get_info()
        
        assert info["name"] == "offline_map"
        assert info["category"] == "map"
        assert info["risk_level"] == "safe"
