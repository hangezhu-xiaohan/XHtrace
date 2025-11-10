import os
from PyQt5.QtCore import QCoreApplication, QTranslator, QLocale
from PyQt5.QtWidgets import QApplication

class LanguageManager:
    """多语言管理器，负责处理应用程序的语言切换"""
    
    def __init__(self):
        self.current_language = "zh_CN"  # 默认语言
        self.translator = QTranslator()
        self.available_languages = {
            "zh_CN": "简体中文",
            "en_US": "English"
        }
        
        # 确保语言目录存在
        self.lang_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lang")
        if not os.path.exists(self.lang_dir):
            os.makedirs(self.lang_dir)
            
        # 创建默认翻译文件
        self._create_default_translations()
    
    def _create_default_translations(self):
        """创建默认的翻译文件结构"""
        # 中文翻译
        cn_translations = {
            "XHtrace - 网络追踪工具": "XHtrace - 网络追踪工具",
            "目标地址:": "目标地址:",
            "追踪": "追踪",
            "MTR": "MTR",
            "清空": "清空",
            "高级设置": "高级设置",
            "最大跳数:": "最大跳数:",
            "超时 (毫秒):": "超时 (毫秒):",
            "数据包大小:": "数据包大小:",
            "DNS解析": "DNS解析",
            "启用反向DNS": "启用反向DNS",
            "协议": "协议",
            "ICMP": "ICMP",
            "UDP": "UDP",
            "TCP": "TCP",
            "隐藏本地路由": "隐藏本地路由",
            "结果": "结果",
            "原始输出": "原始输出",
            "可视化": "可视化",
            "就绪": "就绪",
            "正在追踪到 {0}...": "正在追踪到 {0}...",
            "追踪完成": "追踪完成",
            "警告": "警告",
            "请输入目标IP地址或域名": "请输入目标IP地址或域名",
            "停止MTR": "停止MTR",
            "正在执行MTR到 {0}...": "正在执行MTR到 {0}...",
            "跳数": "跳数",
            "IP地址": "IP地址",
            "主机名": "主机名",
            "地理位置": "地理位置",
            "ASN信息": "ASN信息",
            "延迟": "延迟",
            "首选项": "首选项",
            "帮助": "帮助",
            "关于": "关于",
            "文件": "文件",
            "导出": "导出",
            "设置": "设置",
            "退出": "退出",
            "XHtrace是一个网络追踪工具，可以帮助您分析网络连接路径和延迟。\n\n版本: 1.0.0\n作者: XHtrace开发团队": "XHtrace是一个网络追踪工具，可以帮助您分析网络连接路径和延迟。\n\n版本: 1.0.0\n作者: XHtrace开发团队",
            "成功": "成功",
            "失败": "失败",
            "保存设置": "保存设置",
            "取消": "取消",
            "重置": "重置",
            "界面设置": "界面设置",
            "网络设置": "网络设置",
            "地理位置数据库设置": "地理位置数据库设置",
            "结果设置": "结果设置",
            "显示高级选项": "显示高级选项",
            "应用语言": "应用语言",
            "默认协议": "默认协议",
            "默认最大跳数": "默认最大跳数",
            "默认超时时间 (秒)": "默认超时时间 (秒)",
            "默认数据包大小 (字节)": "默认数据包大小 (字节)",
            "默认启用反向DNS": "默认启用反向DNS",
            "每次ping数量": "每次ping数量",
            "MaxMind数据库路径": "MaxMind数据库路径",
            "浏览": "浏览",
            "启用在线API": "启用在线API",
            "自动保存结果": "自动保存结果",
            "结果保存路径": "结果保存路径",
            "导出为CSV": "导出为CSV",
            "导出为JSON": "导出为JSON",
            "导出为文本": "导出为文本",
            "请选择保存路径": "请选择保存路径",
            "保存文件": "保存文件",
            "CSV文件 (*.csv)": "CSV文件 (*.csv)",
            "JSON文件 (*.json)": "JSON文件 (*.json)",
            "文本文件 (*.txt)": "文本文件 (*.txt)",
            "导出成功": "导出成功",
            "导出失败: {0}": "导出失败: {0}"
        }
        
        # 英文翻译
        en_translations = {
            "XHtrace - 网络追踪工具": "XHtrace - Network Traceroute Tool",
            "目标设置": "Target Settings",
            "输入IP地址或域名": "Enter IP address or domain name",
            "开始追踪": "Start Trace",
            "停止追踪": "Stop Trace",
            "MTR模式": "MTR Mode",
            "高级设置": "Advanced Settings",
            "最大跳数": "Max Hops",
            "超时时间(ms)": "Timeout (ms)",
            "使用IPv6": "Use IPv6",
            "数据包大小(B)": "Packet Size (B)",
            "DNS解析": "DNS Resolution",
            "启用反向DNS": "Enable Reverse DNS",
            "隐私设置": "Privacy Settings",
            "隐藏前几跳": "Mask First Hops",
            "表格结果": "Table Results",
            "可视化": "Visualization",
            "Raw Output": "Raw Output",
            "跳数": "Hop",
            "IP地址": "IP Address",
            "主机名": "Hostname",
            "地理位置": "Location",
            "ASN信息": "ASN",
            "延迟(ms)": "Delay (ms)",
            "文件": "File",
            "导出结果": "Export Results",
            "清空结果": "Clear Results",
            "退出": "Exit",
            "设置": "Settings",
            "语言": "Language",
            "简体中文": "Simplified Chinese",
            "English": "English",
            "首选项": "Preferences",
            "帮助": "Help",
            "关于": "About",
            "目标地址:": "Target:",
            "追踪": "Trace",
            "MTR": "MTR",
            "清空": "Clear",
            "最大跳数:": "Max Hops:",
            "超时 (毫秒):": "Timeout (ms):",
            "数据包大小:": "Packet Size:",
            "协议": "Protocol",
            "ICMP": "ICMP",
            "UDP": "UDP",
            "TCP": "TCP",
            "隐藏本地路由": "Mask Local Routes",
            "结果": "Results",
            "原始输出": "Raw Output",
            "可视化": "Visualization",
            "就绪": "Ready",
            "正在追踪到 {0}...": "Tracing to {0}...",
            "追踪完成": "Trace Completed",
            "警告": "Warning",
            "请输入目标IP地址或域名": "Please enter target IP address or domain name",
            "停止MTR": "Stop MTR",
            "正在执行MTR到 {0}...": "Running MTR to {0}...",
            "XHtrace是一个网络追踪工具，可以帮助您分析网络连接路径和延迟。\n\n版本: 1.0.0\n作者: XHtrace开发团队": "XHtrace is a network traceroute tool that helps you analyze network connection paths and latency.\n\nVersion: 1.0.0\nAuthor: XHtrace Development Team",
            "成功": "Success",
            "失败": "Failure",
            "保存设置": "Save Settings",
            "取消": "Cancel",
            "重置": "Reset",
            "界面设置": "Interface Settings",
            "网络设置": "Network Settings",
            "地理位置数据库设置": "Geolocation Database Settings",
            "结果设置": "Result Settings",
            "显示高级选项": "Show Advanced Options",
            "应用语言": "Application Language",
            "默认协议": "Default Protocol",
            "默认最大跳数": "Default Max Hops",
            "默认超时时间 (秒)": "Default Timeout (seconds)",
            "默认数据包大小 (字节)": "Default Packet Size (bytes)",
            "默认启用反向DNS": "Default Enable Reverse DNS",
            "每次ping数量": "Pings per Hop",
            "MaxMind数据库路径": "MaxMind Database Path",
            "浏览": "Browse",
            "启用在线API": "Enable Online API",
            "自动保存结果": "Auto Save Results",
            "结果保存路径": "Results Save Path",
            "导出为CSV": "Export as CSV",
            "导出为JSON": "Export as JSON",
            "导出为文本": "Export as Text",
            "请选择保存路径": "Please select save path",
            "保存文件": "Save File",
            "CSV文件 (*.csv)": "CSV Files (*.csv)",
            "JSON文件 (*.json)": "JSON Files (*.json)",
            "文本文件 (*.txt)": "Text Files (*.txt)",
            "导出成功": "Export successful",
            "导出失败: {0}": "Export failed: {0}"
        }
        
        # 保存翻译字典到文件
        import json
        with open(os.path.join(self.lang_dir, "zh_CN.json"), "w", encoding="utf-8") as f:
            json.dump(cn_translations, f, ensure_ascii=False, indent=2)
        
        with open(os.path.join(self.lang_dir, "en_US.json"), "w", encoding="utf-8") as f:
            json.dump(en_translations, f, ensure_ascii=False, indent=2)
    
    def load_language(self, language_code):
        """加载指定语言的翻译"""
        if language_code not in self.available_languages:
            print(f"Language {language_code} not available")
            return False
        
        # 移除之前的翻译器
        if hasattr(self, 'translator') and self.translator:
            try:
                QCoreApplication.instance().removeTranslator(self.translator)
            except Exception:
                pass  # 如果翻译器未安装，忽略错误
        
        # 创建新的翻译器
        self.translator = QTranslator()
        
        # 尝试加载语言文件
        try:
            import json
            lang_file = os.path.join(self.lang_dir, f"{language_code}.json")
            
            if not os.path.exists(lang_file):
                print(f"Language file {lang_file} not found")
                # 创建默认翻译文件
                self._create_default_translations()
            
            # 加载翻译字典
            with open(lang_file, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
            
            # 安装翻译器到应用程序
            try:
                app = QCoreApplication.instance()
                if app:
                    app.installTranslator(self.translator)
                    print(f"Translator installed for language: {language_code}")
            except Exception as install_error:
                print(f"Failed to install translator: {install_error}")
            
            self.current_language = language_code
            print(f"Successfully loaded language: {language_code}")
            return True
        except Exception as e:
            print(f"Error loading language {language_code}: {e}")
            return False
    
    def translate(self, text, *args):
        """翻译文本，如果找不到对应的翻译则返回原文本"""
        # 首先尝试从我们的自定义翻译字典中获取
        if hasattr(self, 'translations') and text in self.translations:
            translated = self.translations[text]
            print(f"Custom translation: '{text}' -> '{translated}'")
        else:
            # 如果自定义字典中没有，则尝试使用Qt的翻译机制
            try:
                translated = QCoreApplication.translate("XHtrace", text)
                if translated == text:
                    # 如果Qt翻译没有改变文本，则记录下来
                    print(f"No translation found for: '{text}'")
            except Exception:
                translated = text
        
        # 如果有参数，格式化翻译后的文本
        if args:
            try:
                translated = translated.format(*args)
            except Exception as e:
                print(f"Error formatting translated text: {e}")
        
        return translated
    
    def get_available_languages(self):
        """获取可用的语言列表"""
        return self.available_languages
    
    def get_current_language(self):
        """获取当前语言代码"""
        return self.current_language
    
    def detect_system_language(self):
        """检测系统语言并返回最匹配的语言代码"""
        system_locale = QLocale.system().name()  # 获取系统区域设置
        
        # 简化语言代码（例如 "zh_CN" -> "zh"）
        lang_code = system_locale.split('_')[0]
        
        # 查找匹配的语言
        for code in self.available_languages:
            if code.startswith(lang_code):
                return code
        
        # 默认返回英文
        return "en_US"

# 创建单例实例
language_manager = None

def get_language_manager():
    """获取语言管理器的单例实例"""
    global language_manager
    if language_manager is None:
        language_manager = LanguageManager()
    return language_manager

def _translate(text, *args):
    """快捷翻译函数"""
    return get_language_manager().translate(text, *args)