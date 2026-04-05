"""
PyAgent 执行模块工具系统 - 离线地图工具

提供本地离线地图查询功能，支持 PMTiles 格式。
参考 Project N.O.M.A.D. 项目实现。
"""

import json
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass

from ..base import BaseTool, ToolCategory, ToolResult, ToolParameter, RiskLevel
from .geo_utils import GeoUtils, GeoPoint, GeoBounds


@dataclass
class POI:
    """兴趣点"""
    id: str
    name: str
    lat: float
    lon: float
    category: str = ""
    address: str = ""
    description: str = ""


@dataclass
class MapRegion:
    """地图区域"""
    id: str
    name: str
    version: str
    bounds: GeoBounds
    size_mb: float
    url: str = ""
    description: str = ""


class OfflineMapTool(BaseTool):
    """离线地图工具"""

    name = "offline_map"
    description = "离线地图查询工具，支持POI搜索、地理编码、距离计算等功能"
    category = ToolCategory.MAP
    risk_level = RiskLevel.SAFE

    DATA_DIR = Path("data/maps")
    PMTILES_DIR = DATA_DIR / "pmtiles"
    ASSETS_DIR = DATA_DIR / "assets"
    COLLECTIONS_DIR = Path("data/knowledge")

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._regions: dict[str, MapRegion] = {}
        self._pois: list[POI] = []
        self._load_collections()
        self._load_local_data()

        self._parameters = [
            ToolParameter(
                name="action",
                type="string",
                description="操作类型: search(搜索POI), reverse_geocode(逆地理编码), distance(距离计算), regions(列出区域), nearby(附近搜索)",
                required=True,
                enum=["search", "reverse_geocode", "distance", "regions", "nearby", "collections"]
            ),
            ToolParameter(
                name="query",
                type="string",
                description="搜索关键词或地址",
                required=False
            ),
            ToolParameter(
                name="lat",
                type="number",
                description="纬度",
                required=False
            ),
            ToolParameter(
                name="lon",
                type="number",
                description="经度",
                required=False
            ),
            ToolParameter(
                name="lat2",
                type="number",
                description="第二个点的纬度（距离计算用）",
                required=False
            ),
            ToolParameter(
                name="lon2",
                type="number",
                description="第二个点的经度（距离计算用）",
                required=False
            ),
            ToolParameter(
                name="radius",
                type="number",
                description="搜索半径（公里）",
                required=False,
                default=10
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="返回结果数量限制",
                required=False,
                default=10
            )
        ]

    def _load_collections(self):
        """加载地图收藏数据"""
        maps_path = self.COLLECTIONS_DIR / "maps.json"
        if maps_path.exists():
            try:
                with open(maps_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for collection in data.get("collections", []):
                        for resource in collection.get("resources", []):
                            region_id = resource.get("id", "")
                            self._regions[region_id] = MapRegion(
                                id=region_id,
                                name=resource.get("title", region_id),
                                version=resource.get("version", ""),
                                bounds=GeoBounds(-90, -180, 90, 180),
                                size_mb=resource.get("size_mb", 0),
                                url=resource.get("url", ""),
                                description=resource.get("description", "")
                            )
            except Exception:
                pass

    def _load_local_data(self):
        """加载本地地图数据"""
        if self.PMTILES_DIR.exists():
            for pmtiles_file in self.PMTILES_DIR.glob("*.pmtiles"):
                region_id = pmtiles_file.stem
                if region_id not in self._regions:
                    size_mb = pmtiles_file.stat().st_size / (1024 * 1024)
                    self._regions[region_id] = MapRegion(
                        id=region_id,
                        name=region_id.replace("_", " ").title(),
                        version="local",
                        bounds=GeoBounds(-90, -180, 90, 180),
                        size_mb=round(size_mb, 2)
                    )
        
        self._load_sample_pois()

    def _load_sample_pois(self):
        """加载示例POI数据"""
        sample_pois = [
            POI(id="bj_tiananmen", name="天安门", lat=39.9087, lon=116.3975, 
                category="landmark", address="北京市东城区东长安街"),
            POI(id="bj_forbidden", name="故宫", lat=39.9163, lon=116.3972,
                category="museum", address="北京市东城区景山前街4号"),
            POI(id="bj_summer", name="颐和园", lat=39.9999, lon=116.2755,
                category="park", address="北京市海淀区新建宫门路19号"),
            POI(id="sh_bund", name="外滩", lat=31.2400, lon=121.4900,
                category="landmark", address="上海市黄浦区中山东一路"),
            POI(id="sh_oriental", name="东方明珠", lat=31.2397, lon=121.4998,
                category="landmark", address="上海市浦东新区世纪大道1号"),
            POI(id="gz_canton", name="广州塔", lat=23.1066, lon=113.3245,
                category="landmark", address="广东省广州市海珠区阅江西路222号"),
            POI(id="sz_window", name="世界之窗", lat=22.5347, lon=113.9748,
                category="park", address="广东省深圳市南山区深南大道9037号"),
            POI(id="hz_westlake", name="西湖", lat=30.2500, lon=120.1500,
                category="park", address="浙江省杭州市西湖区"),
        ]
        self._pois = sample_pois

    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        action = kwargs.get("action", "regions")
        
        if action == "regions":
            return self._list_regions()
        elif action == "collections":
            return self._list_collections()
        elif action == "search":
            return self._search_poi(kwargs)
        elif action == "nearby":
            return self._nearby_search(kwargs)
        elif action == "reverse_geocode":
            return self._reverse_geocode(kwargs)
        elif action == "distance":
            return self._calculate_distance(kwargs)
        else:
            return ToolResult(success=False, error=f"未知操作: {action}")

    def _list_regions(self) -> ToolResult:
        """列出地图区域"""
        regions = []
        for region_id, region in self._regions.items():
            regions.append({
                "id": region.id,
                "name": region.name,
                "version": region.version,
                "size_mb": region.size_mb,
                "description": region.description,
                "url": region.url
            })
        
        return ToolResult(
            success=True,
            output=f"找到 {len(regions)} 个地图区域",
            data={"regions": regions}
        )

    def _list_collections(self) -> ToolResult:
        """列出地图收藏集"""
        maps_path = self.COLLECTIONS_DIR / "maps.json"
        collections = []
        
        if maps_path.exists():
            try:
                with open(maps_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for col in data.get("collections", []):
                        collections.append({
                            "name": col.get("name", ""),
                            "slug": col.get("slug", ""),
                            "description": col.get("description", ""),
                            "resource_count": len(col.get("resources", []))
                        })
            except Exception:
                pass
        
        return ToolResult(
            success=True,
            output=f"找到 {len(collections)} 个地图收藏集",
            data={"collections": collections}
        )

    def _search_poi(self, kwargs: dict) -> ToolResult:
        """搜索POI"""
        query = kwargs.get("query", "").lower()
        limit = kwargs.get("limit", 10)
        
        if not query:
            return ToolResult(success=False, error="请提供搜索关键词")
        
        results = []
        for poi in self._pois:
            if query in poi.name.lower() or query in poi.address.lower():
                results.append({
                    "id": poi.id,
                    "name": poi.name,
                    "lat": poi.lat,
                    "lon": poi.lon,
                    "category": poi.category,
                    "address": poi.address
                })
        
        return ToolResult(
            success=True,
            output=f"找到 {len(results)} 个匹配的POI",
            data={"results": results[:limit], "query": query}
        )

    def _nearby_search(self, kwargs: dict) -> ToolResult:
        """附近搜索"""
        try:
            lat = float(kwargs.get("lat", 0))
            lon = float(kwargs.get("lon", 0))
            radius = float(kwargs.get("radius", 10))
            limit = kwargs.get("limit", 10)
        except (ValueError, TypeError):
            return ToolResult(success=False, error="请提供有效的坐标")
        
        if lat == 0 and lon == 0:
            return ToolResult(success=False, error="请提供坐标 (lat, lon)")
        
        results = []
        for poi in self._pois:
            distance = GeoUtils.haversine_distance(lat, lon, poi.lat, poi.lon)
            if distance <= radius:
                results.append({
                    "id": poi.id,
                    "name": poi.name,
                    "lat": poi.lat,
                    "lon": poi.lon,
                    "category": poi.category,
                    "address": poi.address,
                    "distance_km": round(distance, 2)
                })
        
        results.sort(key=lambda x: x["distance_km"])
        
        return ToolResult(
            success=True,
            output=f"在 {radius} 公里范围内找到 {len(results)} 个POI",
            data={"results": results[:limit], "center": {"lat": lat, "lon": lon}, "radius": radius}
        )

    def _reverse_geocode(self, kwargs: dict) -> ToolResult:
        """逆地理编码"""
        try:
            lat = float(kwargs.get("lat", 0))
            lon = float(kwargs.get("lon", 0))
        except (ValueError, TypeError):
            return ToolResult(success=False, error="请提供有效的坐标")
        
        if lat == 0 and lon == 0:
            return ToolResult(success=False, error="请提供坐标 (lat, lon)")
        
        nearest = None
        min_distance = float("inf")
        
        for poi in self._pois:
            distance = GeoUtils.haversine_distance(lat, lon, poi.lat, poi.lon)
            if distance < min_distance:
                min_distance = distance
                nearest = poi
        
        coord_str = GeoUtils.format_coordinates(lat, lon, "dms")
        
        if nearest and min_distance < 50:
            return ToolResult(
                success=True,
                output=f"最近地点: {nearest.name} ({min_distance:.2f}公里)",
                data={
                    "formatted_address": nearest.address,
                    "nearest_poi": {
                        "name": nearest.name,
                        "lat": nearest.lat,
                        "lon": nearest.lon,
                        "distance_km": round(min_distance, 2)
                    },
                    "coordinates": {"lat": lat, "lon": lon},
                    "coordinates_formatted": coord_str
                }
            )
        
        return ToolResult(
            success=True,
            output=f"坐标: {coord_str}",
            data={
                "formatted_address": f"坐标位置 ({coord_str})",
                "coordinates": {"lat": lat, "lon": lon},
                "coordinates_formatted": coord_str
            }
        )

    def _calculate_distance(self, kwargs: dict) -> ToolResult:
        """计算距离"""
        try:
            lat1 = float(kwargs.get("lat", 0))
            lon1 = float(kwargs.get("lon", 0))
            lat2 = float(kwargs.get("lat2", 0))
            lon2 = float(kwargs.get("lon2", 0))
        except (ValueError, TypeError):
            return ToolResult(success=False, error="请提供有效的坐标")
        
        if lat1 == 0 and lon1 == 0:
            return ToolResult(success=False, error="请提供起点坐标 (lat, lon)")
        if lat2 == 0 and lon2 == 0:
            return ToolResult(success=False, error="请提供终点坐标 (lat2, lon2)")
        
        distance_km = GeoUtils.haversine_distance(lat1, lon1, lat2, lon2)
        distance_m = distance_km * 1000
        bearing = GeoUtils.bearing(lat1, lon1, lat2, lon2)
        
        direction = self._bearing_to_direction(bearing)
        
        return ToolResult(
            success=True,
            output=f"距离: {distance_km:.2f} 公里, 方向: {direction} ({bearing:.1f}°)",
            data={
                "distance_km": round(distance_km, 4),
                "distance_m": round(distance_m, 2),
                "bearing_degrees": round(bearing, 1),
                "direction": direction,
                "from": {"lat": lat1, "lon": lon1},
                "to": {"lat": lat2, "lon": lon2}
            }
        )

    def _bearing_to_direction(self, bearing: float) -> str:
        """将方位角转换为方向名称"""
        directions = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
        index = round(bearing / 45) % 8
        return directions[index]
