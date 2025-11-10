import json
import os
import platform
from typing import Dict, Any

class ConfigManager:
    def __init__(self):
        """初始化配置管理器"""
        self.config_path = self._get_config_path()
        self.default_config = self._get_default_config()
        self.config = self.load_config()
    
    def _get_config_path(self) -> str:
        """获取配置文件的路径
        
        根据操作系统确定配置文件的存储位置
        
        Returns:
            配置文件的绝对路径
        """
        system = platform.system()
        
        if system == 'Windows':
            # Windows系统使用AppData目录
            appdata = os.getenv('APPDATA')
            config_dir = os.path.join(appdata, 'XHtrace')
        elif system == 'Darwin':  # macOS
            # macOS使用Library/Application Support目录
            home = os.path.expanduser('~')
            config_dir = os.path.join(home, 'Library', 'Application Support', 'XHtrace')
        else:  # Linux和其他系统
            # Linux使用~/.config目录
            home = os.path.expanduser('~')
            config_dir = os.path.join(home, '.config', 'XHtrace')
        
        # 确保配置目录存在
        os.makedirs(config_dir, exist_ok=True)
        
        # 返回配置文件路径
        return os.path.join(config_dir, 'config.json')
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置
        
        Returns:
            默认配置字典
        """
        return {
            # 界面设置
            'ui': {
                'theme': 'light',  # 'light' 或 'dark'
                'font_size': 10,  # 默认字体大小
                'language': 'zh_CN',  # 默认语言
                'window_size': [1024, 768],  # 默认窗口大小
                'window_position': [100, 100],  # 默认窗口位置
                'show_advanced_options': True  # 是否显示高级选项
            },
            
            # 网络设置
            'network': {
                'timeout': 3,  # 超时时间（秒）
                'max_hops': 30,  # 最大跳数
                'packet_size': 64,  # 数据包大小（字节）
                'protocol': 'icmp',  # 'icmp', 'udp', 或 'tcp'
                'port': 33434,  # UDP/TCP默认端口
                'ping_count': 3,  # MTR模式下的ping次数
                'resolve_hostnames': True  # 是否解析主机名
            },
            
            # MaxMind数据库设置
            'maxmind': {
                'enabled': False,  # 是否启用本地数据库
                'db_path': ''  # 数据库文件路径
            },
            
            # 结果设置
            'results': {
                'auto_export': False,  # 是否自动导出结果
                'export_format': 'json',  # 'json', 'csv', 'txt'
                'export_path': '',  # 导出路径
                'keep_history': True,  # 是否保留历史记录
                'max_history_items': 10  # 最大历史记录数
            },
            
            # 视觉化设置
            'visualization': {
                'show_map': True,  # 是否显示地图
                'show_chart': True,  # 是否显示图表
                'color_scheme': 'default'  # 颜色方案
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件
        
        如果配置文件不存在或格式错误，返回默认配置
        
        Returns:
            配置字典
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并用户配置和默认配置，保留用户配置中的键值对，补充缺失的默认值
                    return self._merge_configs(self.default_config, user_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载配置文件失败: {str(e)}")
        
        # 如果加载失败，返回默认配置
        return self.default_config.copy()
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """递归合并配置字典
        
        Args:
            default: 默认配置字典
            user: 用户配置字典
            
        Returns:
            合并后的配置字典
        """
        merged = default.copy()
        
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # 如果是嵌套字典，递归合并
                merged[key] = self._merge_configs(merged[key], value)
            else:
                # 否则直接覆盖
                merged[key] = value
        
        return merged
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """保存配置到文件
        
        Args:
            config: 要保存的配置字典，如果为None则保存当前配置
            
        Returns:
            是否保存成功
        """
        try:
            config_to_save = config if config is not None else self.config
            
            # 确保父目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, ensure_ascii=False, indent=4)
            
            # 如果保存的是新配置，更新当前配置
            if config is not None:
                self.config = config
            
            return True
        except Exception as e:
            print(f"保存配置文件失败: {str(e)}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """获取配置值
        
        支持通过点表示法访问嵌套配置，例如 'network.timeout'
        
        Args:
            key_path: 配置键路径
            default: 默认值，如果配置不存在
            
        Returns:
            配置值或默认值
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """设置配置值
        
        支持通过点表示法设置嵌套配置，例如 'network.timeout'
        
        Args:
            key_path: 配置键路径
            value: 新的配置值
            
        Returns:
            是否设置成功
        """
        keys = key_path.split('.')
        config = self.config
        
        # 导航到目标配置项的父级
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # 设置值
        config[keys[-1]] = value
        
        # 保存配置
        return self.save_config()
    
    def reset_config(self) -> bool:
        """重置配置为默认值
        
        Returns:
            是否重置成功
        """
        self.config = self.default_config.copy()
        return self.save_config()
    
    def validate_config(self) -> bool:
        """验证配置的有效性
        
        Returns:
            配置是否有效
        """
        # 验证UI主题
        theme = self.get('ui.theme')
        if theme not in ['light', 'dark']:
            self.set('ui.theme', 'light')
        
        # 验证网络超时，必须为正数
        timeout = self.get('network.timeout')
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            self.set('network.timeout', 3)
        
        # 验证最大跳数，必须在合理范围内
        max_hops = self.get('network.max_hops')
        if not isinstance(max_hops, int) or max_hops < 1 or max_hops > 100:
            self.set('network.max_hops', 30)
        
        # 验证数据包大小，必须在合理范围内
        packet_size = self.get('network.packet_size')
        if not isinstance(packet_size, int) or packet_size < 1 or packet_size > 65535:
            self.set('network.packet_size', 64)
        
        # 验证协议类型
        protocol = self.get('network.protocol')
        if protocol not in ['icmp', 'udp', 'tcp']:
            self.set('network.protocol', 'icmp')
        
        # 验证MaxMind数据库路径
        if self.get('maxmind.enabled'):
            db_path = self.get('maxmind.db_path')
            if not db_path or not os.path.exists(db_path):
                self.set('maxmind.enabled', False)
        
        # 验证后保存配置
        return self.save_config()

# 全局配置管理器实例
_config_manager = None

def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例
    
    Returns:
        ConfigManager实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_config(key_path: str, default: Any = None) -> Any:
    """获取配置值的便捷函数
    
    Args:
        key_path: 配置键路径
        default: 默认值
        
    Returns:
        配置值或默认值
    """
    manager = get_config_manager()
    return manager.get(key_path, default)

def set_config(key_path: str, value: Any) -> bool:
    """设置配置值的便捷函数
    
    Args:
        key_path: 配置键路径
        value: 新的配置值
        
    Returns:
        是否设置成功
    """
    manager = get_config_manager()
    return manager.set(key_path, value)

def reset_config() -> bool:
    """重置配置为默认值的便捷函数
    
    Returns:
        是否重置成功
    """
    manager = get_config_manager()
    return manager.reset_config()

if __name__ == "__main__":
    # 测试配置管理器
    print("测试配置管理器功能")
    
    # 创建配置管理器
    config_manager = get_config_manager()
    
    # 打印配置路径
    print(f"配置文件路径: {config_manager.config_path}")
    
    # 获取和设置配置
    print(f"当前网络超时设置: {get_config('network.timeout')}秒")
    set_config('network.timeout', 5)
    print(f"更新后的网络超时设置: {get_config('network.timeout')}秒")
    
    # 测试嵌套配置
    print(f"UI主题: {get_config('ui.theme')}")
    set_config('ui.theme', 'dark')
    print(f"更新后的UI主题: {get_config('ui.theme')}")
    
    # 测试默认值
    print(f"不存在的配置项: {get_config('nonexistent.key', '默认值')}")
    
    # 测试配置验证
    print("验证配置...")
    config_manager.set('network.max_hops', 200)  # 设置一个无效的值
    print(f"验证前最大跳数: {get_config('network.max_hops')}")
    config_manager.validate_config()
    print(f"验证后最大跳数: {get_config('network.max_hops')}")
    
    # 恢复默认超时设置
    set_config('network.timeout', 3)
    print("测试完成")