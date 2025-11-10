from PyQt5.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QPushButton, QFileDialog, QGroupBox, QGridLayout, QFrame,
    QMessageBox
)
from PyQt5.QtCore import Qt
import os
from config import get_config_manager, get_config, set_config, reset_config

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        """初始化设置对话框
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self.parent = parent
        self.config_manager = get_config_manager()
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和大小
        self.setWindowTitle("设置")
        self.resize(600, 450)
        
        # 创建选项卡控件
        self.tab_widget = QTabWidget()
        
        # 创建各个选项卡
        self.ui_tab = self.create_ui_tab()
        self.network_tab = self.create_network_tab()
        self.geoip_tab = self.create_geoip_tab()
        self.results_tab = self.create_results_tab()
        
        # 添加选项卡到选项卡控件
        self.tab_widget.addTab(self.ui_tab, "界面")
        self.tab_widget.addTab(self.network_tab, "网络")
        self.tab_widget.addTab(self.geoip_tab, "地理位置")
        self.tab_widget.addTab(self.results_tab, "结果")
        
        # 创建按钮布局
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # 重置按钮
        self.reset_button = QPushButton("重置为默认值")
        self.reset_button.clicked.connect(self.on_reset)
        buttons_layout.addWidget(self.reset_button)
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        # 确定按钮
        self.ok_button = QPushButton("确定")
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.on_ok)
        buttons_layout.addWidget(self.ok_button)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        main_layout.addLayout(buttons_layout)
        
        # 设置主布局
        self.setLayout(main_layout)
    
    def create_ui_tab(self):
        """创建界面设置选项卡
        
        Returns:
            QWidget: 界面设置选项卡
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 创建分组框
        general_group = QGroupBox("常规设置")
        general_layout = QGridLayout(general_group)
        
        # 主题设置
        general_layout.addWidget(QLabel("主题:"), 0, 0, 1, 1)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色"])
        general_layout.addWidget(self.theme_combo, 0, 1, 1, 2)
        
        # 字体大小设置
        general_layout.addWidget(QLabel("字体大小:"), 1, 0, 1, 1)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setSuffix(" pt")
        general_layout.addWidget(self.font_size_spin, 1, 1, 1, 1)
        general_layout.addWidget(QLabel("（重启应用后生效）"), 1, 2, 1, 1)
        
        # 语言设置
        general_layout.addWidget(QLabel("语言:"), 2, 0, 1, 1)
        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English"])
        general_layout.addWidget(self.language_combo, 2, 1, 1, 2)
        
        # 窗口设置分组框
        window_group = QGroupBox("窗口设置")
        window_layout = QVBoxLayout(window_group)
        
        # 显示高级选项
        self.show_advanced_check = QCheckBox("显示高级选项")
        window_layout.addWidget(self.show_advanced_check)
        
        # 添加分组框到布局
        layout.addWidget(general_group)
        layout.addWidget(window_group)
        layout.addStretch()
        
        return tab
    
    def create_network_tab(self):
        """创建网络设置选项卡
        
        Returns:
            QWidget: 网络设置选项卡
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 常规设置分组框
        general_group = QGroupBox("常规设置")
        general_layout = QGridLayout(general_group)
        
        # 超时设置
        general_layout.addWidget(QLabel("超时时间:"), 0, 0, 1, 1)
        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(0.5, 30)
        self.timeout_spin.setSingleStep(0.5)
        self.timeout_spin.setSuffix(" 秒")
        general_layout.addWidget(self.timeout_spin, 0, 1, 1, 1)
        
        # 最大跳数
        general_layout.addWidget(QLabel("最大跳数:"), 1, 0, 1, 1)
        self.max_hops_spin = QSpinBox()
        self.max_hops_spin.setRange(1, 100)
        general_layout.addWidget(self.max_hops_spin, 1, 1, 1, 1)
        
        # 数据包大小
        general_layout.addWidget(QLabel("数据包大小:"), 2, 0, 1, 1)
        self.packet_size_spin = QSpinBox()
        self.packet_size_spin.setRange(1, 65535)
        self.packet_size_spin.setSuffix(" 字节")
        general_layout.addWidget(self.packet_size_spin, 2, 1, 1, 1)
        
        # 解析主机名
        general_layout.addWidget(QLabel("解析主机名:"), 3, 0, 1, 1)
        self.resolve_hostnames_check = QCheckBox()
        general_layout.addWidget(self.resolve_hostnames_check, 3, 1, 1, 1)
        
        # 协议设置分组框
        protocol_group = QGroupBox("协议设置")
        protocol_layout = QGridLayout(protocol_group)
        
        # 协议选择
        protocol_layout.addWidget(QLabel("协议:"), 0, 0, 1, 1)
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["ICMP", "UDP", "TCP"])
        self.protocol_combo.currentIndexChanged.connect(self.on_protocol_changed)
        protocol_layout.addWidget(self.protocol_combo, 0, 1, 1, 2)
        
        # 端口设置
        protocol_layout.addWidget(QLabel("端口:"), 1, 0, 1, 1)
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setDisabled(True)  # 初始禁用，ICMP不需要端口
        protocol_layout.addWidget(self.port_spin, 1, 1, 1, 2)
        
        # IP版本设置
        protocol_layout.addWidget(QLabel("IP版本:"), 2, 0, 1, 1)
        self.ip_version_combo = QComboBox()
        self.ip_version_combo.addItems(["IPv4", "IPv6"])
        protocol_layout.addWidget(self.ip_version_combo, 2, 1, 1, 2)
        
        # MTR设置分组框
        mtr_group = QGroupBox("MTR设置")
        mtr_layout = QVBoxLayout(mtr_group)
        
        # ping次数
        mtr_ping_layout = QHBoxLayout()
        mtr_ping_layout.addWidget(QLabel("每跳ping次数:"))
        self.ping_count_spin = QSpinBox()
        self.ping_count_spin.setRange(1, 10)
        mtr_ping_layout.addWidget(self.ping_count_spin)
        mtr_ping_layout.addStretch()
        mtr_layout.addLayout(mtr_ping_layout)
        
        # 添加分组框到布局
        layout.addWidget(general_group)
        layout.addWidget(protocol_group)
        layout.addWidget(mtr_group)
        layout.addStretch()
        
        return tab
    
    def create_geoip_tab(self):
        """创建地理位置设置选项卡
        
        Returns:
            QWidget: 地理位置设置选项卡
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # MaxMind数据库设置分组框
        maxmind_group = QGroupBox("MaxMind GeoIP2 数据库设置")
        maxmind_layout = QVBoxLayout(maxmind_group)
        
        # 使用本地数据库
        self.use_local_db_check = QCheckBox("使用本地MaxMind GeoIP2数据库")
        self.use_local_db_check.stateChanged.connect(self.on_use_local_db_changed)
        maxmind_layout.addWidget(self.use_local_db_check)
        
        # 数据库路径
        db_path_layout = QHBoxLayout()
        self.db_path_label = QLabel("数据库路径:")
        db_path_layout.addWidget(self.db_path_label)
        
        self.db_path_edit = QLabel("未选择")
        self.db_path_edit.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.db_path_edit.setMinimumWidth(300)
        self.db_path_edit.setTextInteractionFlags(Qt.TextSelectableByMouse)
        db_path_layout.addWidget(self.db_path_edit)
        
        self.select_db_button = QPushButton("浏览...")
        self.select_db_button.clicked.connect(self.on_select_db)
        self.select_db_button.setEnabled(False)  # 初始禁用
        db_path_layout.addWidget(self.select_db_button)
        
        maxmind_layout.addLayout(db_path_layout)
        
        # 提示信息
        info_label = QLabel(
            "<font color='gray'>提示：使用本地MaxMind数据库可以提高查询速度并减少网络请求。</font><br/>"
            "<font color='gray'>您可以从 https://dev.maxmind.com/geoip/geolite2-free-geolocation-data 下载免费的GeoLite2数据库。</font>"
        )
        info_label.setWordWrap(True)
        maxmind_layout.addWidget(info_label)
        
        # 添加分组框到布局
        layout.addWidget(maxmind_group)
        layout.addStretch()
        
        return tab
    
    def create_results_tab(self):
        """创建结果设置选项卡
        
        Returns:
            QWidget: 结果设置选项卡
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 导出设置分组框
        export_group = QGroupBox("导出设置")
        export_layout = QVBoxLayout(export_group)
        
        # 自动导出
        self.auto_export_check = QCheckBox("自动导出结果")
        self.auto_export_check.stateChanged.connect(self.on_auto_export_changed)
        export_layout.addWidget(self.auto_export_check)
        
        # 导出格式和路径布局
        export_options_layout = QGridLayout()
        
        # 导出格式
        export_options_layout.addWidget(QLabel("导出格式:"), 0, 0, 1, 1)
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["JSON", "CSV", "文本"])
        self.export_format_combo.setEnabled(False)  # 初始禁用
        export_options_layout.addWidget(self.export_format_combo, 0, 1, 1, 1)
        
        # 导出路径
        export_options_layout.addWidget(QLabel("导出路径:"), 1, 0, 1, 1)
        path_layout = QHBoxLayout()
        self.export_path_edit = QLabel("未设置")
        self.export_path_edit.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.export_path_edit.setMinimumWidth(250)
        self.export_path_edit.setTextInteractionFlags(Qt.TextSelectableByMouse)
        path_layout.addWidget(self.export_path_edit)
        
        self.select_export_button = QPushButton("浏览...")
        self.select_export_button.clicked.connect(self.on_select_export_path)
        self.select_export_button.setEnabled(False)  # 初始禁用
        path_layout.addWidget(self.select_export_button)
        
        export_options_layout.addLayout(path_layout, 1, 1, 1, 2)
        export_layout.addLayout(export_options_layout)
        
        # 历史记录设置分组框
        history_group = QGroupBox("历史记录设置")
        history_layout = QVBoxLayout(history_group)
        
        # 保留历史记录
        self.keep_history_check = QCheckBox("保留历史记录")
        self.keep_history_check.stateChanged.connect(self.on_keep_history_changed)
        history_layout.addWidget(self.keep_history_check)
        
        # 最大历史记录数
        max_history_layout = QHBoxLayout()
        self.max_history_label = QLabel("最大历史记录数:")
        max_history_layout.addWidget(self.max_history_label)
        
        self.max_history_spin = QSpinBox()
        self.max_history_spin.setRange(1, 100)
        self.max_history_spin.setEnabled(False)  # 初始禁用
        max_history_layout.addWidget(self.max_history_spin)
        max_history_layout.addStretch()
        
        history_layout.addLayout(max_history_layout)
        
        # 视觉化设置分组框
        viz_group = QGroupBox("视觉化设置")
        viz_layout = QVBoxLayout(viz_group)
        
        # 显示地图
        self.show_map_check = QCheckBox("显示地理位置地图")
        viz_layout.addWidget(self.show_map_check)
        
        # 显示图表
        self.show_chart_check = QCheckBox("显示延迟图表")
        viz_layout.addWidget(self.show_chart_check)
        
        # 添加分组框到布局
        layout.addWidget(export_group)
        layout.addWidget(history_group)
        layout.addWidget(viz_group)
        layout.addStretch()
        
        return tab
    
    def on_protocol_changed(self, index):
        """处理协议变更事件
        
        Args:
            index: 协议下拉框的索引
        """
        # 如果选择的是ICMP，禁用端口设置
        self.port_spin.setEnabled(index != 0)
    
    def on_use_local_db_changed(self, state):
        """处理使用本地数据库复选框变更事件
        
        Args:
            state: 复选框的状态
        """
        enabled = state == Qt.Checked
        self.select_db_button.setEnabled(enabled)
        self.db_path_label.setEnabled(enabled)
    
    def on_auto_export_changed(self, state):
        """处理自动导出复选框变更事件
        
        Args:
            state: 复选框的状态
        """
        enabled = state == Qt.Checked
        self.export_format_combo.setEnabled(enabled)
        self.export_path_edit.setEnabled(enabled)
        self.select_export_button.setEnabled(enabled)
    
    def on_keep_history_changed(self, state):
        """处理保留历史记录复选框变更事件
        
        Args:
            state: 复选框的状态
        """
        enabled = state == Qt.Checked
        self.max_history_label.setEnabled(enabled)
        self.max_history_spin.setEnabled(enabled)
    
    def on_select_db(self):
        """处理选择数据库文件按钮点击事件"""
        # 打开文件对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择MaxMind GeoIP2数据库文件", "", "数据库文件 (*.mmdb)"
        )
        
        if file_path:
            self.db_path_edit.setText(file_path)
    
    def on_select_export_path(self):
        """处理选择导出路径按钮点击事件"""
        # 打开目录对话框
        directory = QFileDialog.getExistingDirectory(
            self, "选择导出目录", ""
        )
        
        if directory:
            self.export_path_edit.setText(directory)
    
    def on_reset(self):
        """处理重置按钮点击事件"""
        # 确认重置
        reply = QMessageBox.question(
            self, "确认重置", "确定要将所有设置恢复为默认值吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 重置配置
            if reset_config():
                self.load_settings()
                QMessageBox.information(self, "成功", "设置已重置为默认值")
            else:
                QMessageBox.warning(self, "错误", "重置设置失败")
    
    def on_ok(self):
        """处理确定按钮点击事件"""
        # 保存设置
        if self.save_settings():
            self.accept()
        else:
            QMessageBox.warning(self, "错误", "保存设置失败")
    
    def load_settings(self):
        """从配置中加载设置到界面控件"""
        # UI设置
        theme = get_config('ui.theme')
        self.theme_combo.setCurrentIndex(1 if theme == 'dark' else 0)
        
        font_size = get_config('ui.font_size')
        self.font_size_spin.setValue(font_size)
        
        language = get_config('ui.language')
        self.language_combo.setCurrentIndex(1 if language == 'en_US' else 0)
        
        show_advanced = get_config('ui.show_advanced_options')
        self.show_advanced_check.setChecked(show_advanced)
        
        # 网络设置
        timeout = get_config('network.timeout')
        self.timeout_spin.setValue(timeout)
        
        max_hops = get_config('network.max_hops')
        self.max_hops_spin.setValue(max_hops)
        
        packet_size = get_config('network.packet_size')
        self.packet_size_spin.setValue(packet_size)
        
        protocol = get_config('network.protocol')
        protocol_index = 0  # 默认ICMP
        if protocol == 'udp':
            protocol_index = 1
        elif protocol == 'tcp':
            protocol_index = 2
        self.protocol_combo.setCurrentIndex(protocol_index)
        
        port = get_config('network.port')
        self.port_spin.setValue(port)
        
        # 处理端口是否启用
        self.port_spin.setEnabled(protocol_index != 0)
        
        # IP版本设置
        use_ipv6 = get_config('network.use_ipv6', False)
        self.ip_version_combo.setCurrentIndex(1 if use_ipv6 else 0)
        
        ping_count = get_config('network.ping_count')
        self.ping_count_spin.setValue(ping_count)
        
        resolve_hostnames = get_config('network.resolve_hostnames')
        self.resolve_hostnames_check.setChecked(resolve_hostnames)
        
        # 地理位置设置
        use_local_db = get_config('maxmind.enabled')
        self.use_local_db_check.setChecked(use_local_db)
        
        db_path = get_config('maxmind.db_path')
        self.db_path_edit.setText(db_path if db_path else "未选择")
        
        # 处理数据库按钮是否启用
        self.select_db_button.setEnabled(use_local_db)
        self.db_path_label.setEnabled(use_local_db)
        
        # 结果设置
        auto_export = get_config('results.auto_export')
        self.auto_export_check.setChecked(auto_export)
        
        export_format = get_config('results.export_format')
        format_index = 0  # 默认JSON
        if export_format == 'csv':
            format_index = 1
        elif export_format == 'txt':
            format_index = 2
        self.export_format_combo.setCurrentIndex(format_index)
        
        export_path = get_config('results.export_path')
        self.export_path_edit.setText(export_path if export_path else "未设置")
        
        # 处理导出选项是否启用
        self.export_format_combo.setEnabled(auto_export)
        self.export_path_edit.setEnabled(auto_export)
        self.select_export_button.setEnabled(auto_export)
        
        keep_history = get_config('results.keep_history')
        self.keep_history_check.setChecked(keep_history)
        
        max_history_items = get_config('results.max_history_items')
        self.max_history_spin.setValue(max_history_items)
        
        # 处理历史记录选项是否启用
        self.max_history_label.setEnabled(keep_history)
        self.max_history_spin.setEnabled(keep_history)
        
        # 视觉化设置
        show_map = get_config('visualization.show_map')
        self.show_map_check.setChecked(show_map)
        
        show_chart = get_config('visualization.show_chart')
        self.show_chart_check.setChecked(show_chart)
    
    def save_settings(self) -> bool:
        """保存界面设置到配置
        
        Returns:
            是否保存成功
        """
        try:
            # UI设置
            theme = 'dark' if self.theme_combo.currentIndex() == 1 else 'light'
            set_config('ui.theme', theme)
            
            set_config('ui.font_size', self.font_size_spin.value())
            
            language = 'en_US' if self.language_combo.currentIndex() == 1 else 'zh_CN'
            set_config('ui.language', language)
            
            set_config('ui.show_advanced_options', self.show_advanced_check.isChecked())
            
            # 网络设置
            set_config('network.timeout', self.timeout_spin.value())
            set_config('network.max_hops', self.max_hops_spin.value())
            set_config('network.packet_size', self.packet_size_spin.value())
            
            protocol = 'icmp'  # 默认ICMP
            if self.protocol_combo.currentIndex() == 1:
                protocol = 'udp'
            elif self.protocol_combo.currentIndex() == 2:
                protocol = 'tcp'
            set_config('network.protocol', protocol)
            
            if protocol != 'icmp':
                set_config('network.port', self.port_spin.value())
            
            # 保存IP版本设置
            set_config('network.use_ipv6', self.ip_version_combo.currentIndex() == 1)
            
            set_config('network.ping_count', self.ping_count_spin.value())
            set_config('network.resolve_hostnames', self.resolve_hostnames_check.isChecked())
            
            # 地理位置设置
            use_local_db = self.use_local_db_check.isChecked()
            set_config('maxmind.enabled', use_local_db)
            
            if use_local_db:
                db_path = self.db_path_edit.text()
                if db_path and db_path != "未选择" and os.path.exists(db_path):
                    set_config('maxmind.db_path', db_path)
                else:
                    QMessageBox.warning(self, "警告", "请选择有效的MaxMind数据库文件")
                    return False
            
            # 结果设置
            auto_export = self.auto_export_check.isChecked()
            set_config('results.auto_export', auto_export)
            
            if auto_export:
                export_format = 'json'  # 默认JSON
                if self.export_format_combo.currentIndex() == 1:
                    export_format = 'csv'
                elif self.export_format_combo.currentIndex() == 2:
                    export_format = 'txt'
                set_config('results.export_format', export_format)
                
                export_path = self.export_path_edit.text()
                if export_path and export_path != "未设置" and os.path.exists(export_path):
                    set_config('results.export_path', export_path)
                else:
                    QMessageBox.warning(self, "警告", "请选择有效的导出目录")
                    return False
            
            keep_history = self.keep_history_check.isChecked()
            set_config('results.keep_history', keep_history)
            
            if keep_history:
                set_config('results.max_history_items', self.max_history_spin.value())
            
            # 视觉化设置
            set_config('visualization.show_map', self.show_map_check.isChecked())
            set_config('visualization.show_chart', self.show_chart_check.isChecked())
            
            # 验证配置
            self.config_manager.validate_config()
            
            # 如果父窗口存在，通知父窗口配置已更改
            if self.parent:
                self.parent.on_config_changed()
            
            return True
        except Exception as e:
            print(f"保存设置时出错: {str(e)}")
            return False