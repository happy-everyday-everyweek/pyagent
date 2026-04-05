"""
PyAgent 执行模块工具系统 - 地理计算工具

提供地理坐标计算功能。
"""

import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class GeoPoint:
    """地理坐标点"""
    lat: float
    lon: float
    name: str = ""
    address: str = ""


@dataclass
class GeoBounds:
    """地理边界"""
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float


class GeoUtils:
    """地理计算工具类"""

    EARTH_RADIUS_KM = 6371.0
    EARTH_RADIUS_M = 6371000.0

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        计算两点之间的球面距离（Haversine公式）
        
        Args:
            lat1, lon1: 第一个点的纬度和经度（度）
            lat2, lon2: 第二个点的纬度和经度（度）
        
        Returns:
            距离（公里）
        """
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return GeoUtils.EARTH_RADIUS_KM * c

    @staticmethod
    def distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算两点之间的距离（米）"""
        return GeoUtils.haversine_distance(lat1, lon1, lat2, lon2) * 1000

    @staticmethod
    def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        计算从点1到点2的方位角
        
        Returns:
            方位角（度），0-360
        """
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lon = math.radians(lon2 - lon1)

        x = math.sin(delta_lon) * math.cos(lat2_rad)
        y = (math.cos(lat1_rad) * math.sin(lat2_rad) -
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon))

        bearing = math.atan2(x, y)
        return (math.degrees(bearing) + 360) % 360

    @staticmethod
    def destination_point(lat: float, lon: float, 
                          bearing: float, distance_km: float) -> tuple[float, float]:
        """
        从起点沿方位角移动指定距离后的终点
        
        Args:
            lat, lon: 起点坐标
            bearing: 方位角（度）
            distance_km: 距离（公里）
        
        Returns:
            (终点纬度, 终点经度)
        """
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        bearing_rad = math.radians(bearing)

        angular_dist = distance_km / GeoUtils.EARTH_RADIUS_KM

        dest_lat = math.asin(
            math.sin(lat_rad) * math.cos(angular_dist) +
            math.cos(lat_rad) * math.sin(angular_dist) * math.cos(bearing_rad)
        )

        dest_lon = lon_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(angular_dist) * math.cos(lat_rad),
            math.cos(angular_dist) - math.sin(lat_rad) * math.sin(dest_lat)
        )

        return math.degrees(dest_lat), math.degrees(dest_lon)

    @staticmethod
    def is_point_in_bounds(lat: float, lon: float, bounds: GeoBounds) -> bool:
        """检查点是否在边界内"""
        return (bounds.min_lat <= lat <= bounds.max_lat and
                bounds.min_lon <= lon <= bounds.max_lon)

    @staticmethod
    def get_bounding_box(lat: float, lon: float, radius_km: float) -> GeoBounds:
        """
        获取以某点为中心、指定半径的边界框
        
        Args:
            lat, lon: 中心点坐标
            radius_km: 半径（公里）
        
        Returns:
            GeoBounds 边界框
        """
        lat_offset = radius_km / GeoUtils.EARTH_RADIUS_KM * (180 / math.pi)
        lon_offset = radius_km / (GeoUtils.EARTH_RADIUS_KM * math.cos(math.radians(lat))) * (180 / math.pi)

        return GeoBounds(
            min_lat=lat - lat_offset,
            max_lat=lat + lat_offset,
            min_lon=lon - lon_offset,
            max_lon=lon + lon_offset
        )

    @staticmethod
    def format_coordinates(lat: float, lon: float, format_type: str = "dms") -> str:
        """
        格式化坐标
        
        Args:
            lat, lon: 坐标
            format_type: dms(度分秒), decimal(小数), ddm(度分)
        """
        if format_type == "decimal":
            return f"{lat:.6f}, {lon:.6f}"
        
        def to_dms(decimal: float, is_lat: bool) -> str:
            direction = "N" if decimal >= 0 else "S" if is_lat else "E" if decimal >= 0 else "W"
            decimal = abs(decimal)
            degrees = int(decimal)
            minutes = int((decimal - degrees) * 60)
            seconds = (decimal - degrees - minutes / 60) * 3600
            return f"{degrees}°{minutes}'{seconds:.1f}\"{direction}"
        
        if format_type == "dms":
            return f"{to_dms(lat, True)}, {to_dms(lon, False)}"
        elif format_type == "ddm":
            def to_ddm(decimal: float, is_lat: bool) -> str:
                direction = "N" if decimal >= 0 else "S" if is_lat else "E" if decimal >= 0 else "W"
                decimal = abs(decimal)
                degrees = int(decimal)
                minutes = (decimal - degrees) * 60
                return f"{degrees}°{minutes:.3f}'{direction}"
            return f"{to_ddm(lat, True)}, {to_ddm(lon, False)}"
        
        return f"{lat:.6f}, {lon:.6f}"

    @staticmethod
    def parse_coordinates(coord_str: str) -> Optional[GeoPoint]:
        """
        解析坐标字符串
        
        支持格式:
        - "39.9042, 116.4074"
        - "39.9042 116.4074"
        - "39°54'15\"N, 116°24'27\"E"
        """
        coord_str = coord_str.strip()
        
        parts = coord_str.replace(",", " ").split()
        if len(parts) >= 2:
            try:
                lat = float(parts[0])
                lon = float(parts[1])
                return GeoPoint(lat=lat, lon=lon)
            except ValueError:
                pass
        
        import re
        dms_pattern = r"(\d+)°(\d+)'([\d.]+)\"([NSEW])"
        matches = re.findall(dms_pattern, coord_str)
        
        if len(matches) >= 2:
            def dms_to_decimal(d: str, m: str, s: str, direction: str) -> float:
                decimal = float(d) + float(m) / 60 + float(s) / 3600
                if direction in "SW":
                    decimal = -decimal
                return decimal
            
            lat = dms_to_decimal(*matches[0])
            lon = dms_to_decimal(*matches[1])
            return GeoPoint(lat=lat, lon=lon)
        
        return None
