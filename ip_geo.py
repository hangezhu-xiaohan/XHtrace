import requests
import json
import os
import geoip2.database
import socket
import ipaddress
from typing import Dict, Optional, Tuple

class IPGeoLocator:
    def __init__(self, config=None):
        """初始化IP地理位置查询器
        
        Args:
            config: 配置字典，包含API密钥、数据库路径等
        """
        self.config = config or {}
        self.maxmind_reader = None
        
        # 尝试加载本地MaxMind数据库
        if 'maxmind_db_path' in self.config:
            self._load_maxmind_database(self.config['maxmind_db_path'])
    
    def _load_maxmind_database(self, db_path: str) -> bool:
        """加载MaxMind GeoIP2数据库
        
        Args:
            db_path: 数据库文件路径
            
        Returns:
            是否成功加载
        """
        try:
            if os.path.exists(db_path):
                self.maxmind_reader = geoip2.database.Reader(db_path)
                return True
            return False
        except Exception as e:
            print(f"加载MaxMind数据库失败: {str(e)}")
            self.maxmind_reader = None
            return False
    
    def is_private_ip(self, ip: str) -> bool:
        """检查IP是否为私有IP地址
        
        Args:
            ip: IP地址字符串
            
        Returns:
            是否为私有IP
        """
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except ValueError:
            return False
    
    def get_location_from_maxmind(self, ip: str) -> Dict[str, str]:
        """从本地MaxMind数据库获取IP位置信息
        
        Args:
            ip: IP地址字符串
            
        Returns:
            包含位置信息的字典
        """
        if not self.maxmind_reader:
            return {}
        
        try:
            response = self.maxmind_reader.city(ip)
            
            location = []
            if response.country.name:
                location.append(response.country.name)
            if response.subdivisions.most_specific.name:
                location.append(response.subdivisions.most_specific.name)
            if response.city.name:
                location.append(response.city.name)
            
            # 尝试获取ASN信息
            asn_info = ""
            try:
                asn_response = self.maxmind_reader.asn(ip)
                if asn_response.autonomous_system_organization:
                    asn_info = f"AS{asn_response.autonomous_system_number} {asn_response.autonomous_system_organization}"
            except:
                pass
            
            return {
                'location': ", ".join(location) if location else "未知位置",
                'asn': asn_info if asn_info else "未知ASN",
                'latitude': str(response.location.latitude) if response.location.latitude else None,
                'longitude': str(response.location.longitude) if response.location.longitude else None
            }
        except Exception as e:
            print(f"MaxMind查询失败: {str(e)}")
            return {}
    
    def get_location_from_ipapi(self, ip: str) -> Dict[str, str]:
        """从ip-api.com获取IP位置信息（免费API）
        
        Args:
            ip: IP地址字符串
            
        Returns:
            包含位置信息的字典
        """
        try:
            # 使用ip-api.com的免费API
            # 注意：免费版有速率限制
            url = f"http://ip-api.com/json/{ip}?fields=country,regionName,city,isp,as,org,asname,lat,lon,status"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    location = []
                    if data.get('country'):
                        location.append(data['country'])
                    if data.get('regionName'):
                        location.append(data['regionName'])
                    if data.get('city'):
                        location.append(data['city'])
                    
                    # 构建ASN信息
                    asn_info = ""
                    if data.get('as'):
                        asn_info = data['as']
                    elif data.get('asname') and data.get('org'):
                        asn_info = f"{data['asname']} {data['org']}"
                    elif data.get('isp'):
                        asn_info = data['isp']
                    
                    return {
                        'location': ", ".join(location) if location else "未知位置",
                        'asn': asn_info if asn_info else "未知ASN",
                        'latitude': str(data.get('lat')) if data.get('lat') else None,
                        'longitude': str(data.get('lon')) if data.get('lon') else None
                    }
        except Exception as e:
            print(f"ip-api.com查询失败: {str(e)}")
        
        return {}
    
    def get_location_from_geoip_lookup(self, ip: str) -> Dict[str, str]:
        """从geoip-lookup.com获取IP位置信息（备用API）
        
        Args:
            ip: IP地址字符串
            
        Returns:
            包含位置信息的字典
        """
        try:
            url = f"https://json.geoiplookup.io/{ip}"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                
                location = []
                if data.get('country_name'):
                    location.append(data['country_name'])
                if data.get('region'):
                    location.append(data['region'])
                if data.get('city'):
                    location.append(data['city'])
                
                # 构建ASN信息
                asn_info = ""
                if data.get('asn'):
                    asn_info = f"AS{data['asn']} {data.get('isp', '')}"
                elif data.get('isp'):
                    asn_info = data['isp']
                
                return {
                    'location': ", ".join(location) if location else "未知位置",
                    'asn': asn_info if asn_info else "未知ASN",
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude')
                }
        except Exception as e:
            print(f"geoip-lookup.com查询失败: {str(e)}")
        
        return {}
    
    def get_location(self, ip: str) -> Tuple[str, str]:
        """获取IP的地理位置和ASN信息
        
        尝试按以下顺序获取信息：
        1. 本地MaxMind数据库
        2. ip-api.com
        3. geoip-lookup.com
        
        Args:
            ip: IP地址字符串
            
        Returns:
            (location, asn) 元组
        """
        # 检查是否为私有IP
        if self.is_private_ip(ip):
            return "私有IP", "内部网络"
        
        # 尝试本地数据库
        if self.maxmind_reader:
            location_data = self.get_location_from_maxmind(ip)
            if location_data and location_data.get('location') != "未知位置":
                return location_data.get('location', "未知位置"), location_data.get('asn', "未知ASN")
        
        # 尝试ip-api.com
        location_data = self.get_location_from_ipapi(ip)
        if location_data and location_data.get('location') != "未知位置":
            return location_data.get('location', "未知位置"), location_data.get('asn', "未知ASN")
        
        # 尝试geoip-lookup.com
        location_data = self.get_location_from_geoip_lookup(ip)
        if location_data and location_data.get('location') != "未知位置":
            return location_data.get('location', "未知位置"), location_data.get('asn', "未知ASN")
        
        # 所有方法都失败
        return "未知位置", "未知ASN"
    
    def batch_get_locations(self, ip_list: list) -> Dict[str, Tuple[str, str]]:
        """批量获取多个IP的地理位置信息
        
        Args:
            ip_list: IP地址列表
            
        Returns:
            {ip: (location, asn)} 字典
        """
        results = {}
        
        for ip in ip_list:
            # 跳过已查询过的IP
            if ip in results:
                continue
            
            location, asn = self.get_location(ip)
            results[ip] = (location, asn)
        
        return results
    
    def close(self):
        """关闭资源，如数据库连接"""
        if self.maxmind_reader:
            try:
                self.maxmind_reader.close()
            except:
                pass
            self.maxmind_reader = None
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        self.close()

# 全局地理位置查询器实例
_geo_locator = None

def get_geo_locator(config=None) -> IPGeoLocator:
    """获取全局地理位置查询器实例
    
    Args:
        config: 配置字典
        
    Returns:
        IPGeoLocator实例
    """
    global _geo_locator
    if _geo_locator is None:
        _geo_locator = IPGeoLocator(config)
    elif config:
        # 如果提供了新配置，更新配置
        _geo_locator.config.update(config)
        # 如果配置了新的数据库路径，重新加载
        if 'maxmind_db_path' in config:
            _geo_locator._load_maxmind_database(config['maxmind_db_path'])
    return _geo_locator

def get_ip_location(ip: str) -> Tuple[str, str]:
    """获取IP的地理位置和ASN信息的便捷函数
    
    Args:
        ip: IP地址字符串
        
    Returns:
        (location, asn) 元组
    """
    locator = get_geo_locator()
    return locator.get_location(ip)

def update_traceroute_with_geo_info(hop_info: Dict) -> Dict:
    """更新traceroute结果中的地理位置信息
    
    Args:
        hop_info: traceroute跳数信息字典
        
    Returns:
        更新后的字典
    """
    # 只处理有效的IP地址
    ip = hop_info.get('ip')
    if ip and ip != '*' and ip != '***.***.***.***':
        try:
            # 验证IP地址格式
            socket.inet_aton(ip)
            # 获取地理位置信息
            location, asn = get_ip_location(ip)
            # 更新字典
            hop_info['location'] = location
            hop_info['asn'] = asn
        except (socket.error, ValueError):
            # 不是有效的IP地址格式
            pass
    return hop_info

if __name__ == "__main__":
    # 示例用法
    print("测试IP地理位置查询功能")
    
    # 测试几个IP地址
    test_ips = [
        "8.8.8.8",  # Google DNS
        "1.1.1.1",  # Cloudflare DNS
        "192.168.1.1",  # 私有IP
        "202.108.22.5"  # 百度IP
    ]
    
    locator = IPGeoLocator()
    
    for ip in test_ips:
        location, asn = locator.get_location(ip)
        print(f"IP: {ip}")
        print(f"位置: {location}")
        print(f"ASN: {asn}")
        print("-" * 40)
    
    # 测试批量查询
    print("\n批量查询结果:")
    results = locator.batch_get_locations(test_ips)
    for ip, (location, asn) in results.items():
        print(f"{ip}: {location} | {asn}")
    
    # 测试traceroute结果更新
    print("\n更新traceroute结果:")
    test_hop = {
        'hop': 1,
        'ip': '8.8.8.8',
        'hostname': 'dns.google',
        'location': '',
        'asn': '',
        'delay': '10.5 ms'
    }
    updated_hop = update_traceroute_with_geo_info(test_hop)
    print(updated_hop)