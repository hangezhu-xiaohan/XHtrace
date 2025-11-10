import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QTabWidget, QLabel, QGroupBox,
    QSpinBox, QCheckBox, QComboBox, QMessageBox, QSplitter, QProgressBar,
    QMenuBar, QMenu, QAction, QStatusBar, QFileDialog, QFrame, QInputDialog,
    QStyle, QHeaderView, QToolBar
)
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QPen, QBrush
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint, QRect
import platform
import socket
# 导入我们的模块
from traceroute import traceroute, mtr
from settings import SettingsDialog
from config import get_config_manager, get_config, set_config
from ip_geo import update_traceroute_with_geo_info
from language import get_language_manager, _translate
from visualization import TracerouteVisualizer
from exporter import ResultExporter
from mtr_thread import MTRThread

class XHtraceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # 加载语言管理器
        self.lang_manager = get_language_manager()
        
        # 加载配置
        self.config_manager = get_config_manager()
        # 验证配置
        self.config_manager.validate_config()
        
        # 从配置加载语言
        language = get_config('ui.language', 'zh_CN')
        self.lang_manager.load_language(language)
        
        self.init_ui()
        self.traceroute_thread = None
        self.mtr_thread = None
        # 加载保存的设置到UI
        self.load_config_to_ui()
        
        # 存储当前追踪结果
        self.current_hops_data = []
        self.current_raw_output = ""
        
    def change_language(self, language_code):
        """更改应用程序语言"""
        print(f"Changing language to: {language_code}")
        if self.lang_manager.load_language(language_code):
            # 保存到配置
            set_config('ui.language', language_code)
            # 重新初始化UI以应用新语言
            self.reinit_ui()
            # 显示状态消息
            self.statusBar.showMessage(f"语言已切换为 {self.lang_manager.available_languages[language_code]}")
            return True
        else:
            print(f"Failed to load language: {language_code}")
            return False
    
    def reinit_ui(self):
        """重新初始化UI以应用语言更改"""
        # 完全清除所有现有部件
        
        # 清除菜单栏 - 确保正确清除所有菜单
        menubar = self.menuBar()
        menubar.clear()
        
        # 清除工具栏和状态栏
        for toolbar in self.findChildren(QToolBar):
            self.removeToolBar(toolbar)
        
        self.statusBar.clearMessage()
        
        # 清除中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 重新设置窗口标题
        self.setWindowTitle(_translate("XHtrace - 网络追踪工具"))
        
        # 重新创建所有UI元素
        self.create_menu_bar()
        self.init_ui()
        self.load_config_to_ui()
        
        print(f"UI successfully reinitialized with language: {self.lang_manager.get_current_language()}")
        
    def init_ui(self):
        # 设置窗口基本属性
        self.setWindowTitle(_translate("XHtrace - 网络追踪工具"))
        
        # 尝试从配置中加载窗口大小和位置
        window_size = get_config('ui.window_size', [1000, 700])
        window_pos = get_config('ui.window_position', [100, 100])
        
        self.setGeometry(window_pos[0], window_pos[1], window_size[0], window_size[1])
        self.setMinimumSize(800, 600)
        
        # 设置中文字体支持
        font = QFont("SimHei", 9)
        QApplication.setFont(font)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建输入区域
        input_group = QGroupBox(_translate("目标设置"))
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText(_translate("输入IP地址或域名"))
        self.target_input.setMinimumWidth(300)
        
        self.trace_button = QPushButton(_translate("开始追踪"))
        self.trace_button.setMinimumHeight(30)
        self.trace_button.clicked.connect(self.start_traceroute)
        
        self.stop_button = QPushButton(_translate("停止追踪"))
        self.stop_button.setMinimumHeight(30)
        self.stop_button.clicked.connect(self.stop_tracing)
        self.stop_button.setEnabled(False)  # 初始禁用
        
        self.mtr_button = QPushButton(_translate("MTR模式"))
        self.mtr_button.setMinimumHeight(30)
        self.mtr_button.clicked.connect(self.start_mtr)
        
        input_layout.addWidget(self.target_input)
        input_layout.addWidget(self.trace_button)
        input_layout.addWidget(self.stop_button)
        input_layout.addWidget(self.mtr_button)
        input_group.setLayout(input_layout)
        
        # 创建配置区域
        config_group = QGroupBox(_translate("高级设置"))
        config_layout = QHBoxLayout()
        config_layout.setContentsMargins(10, 10, 10, 10)
        
        # 最大跳数设置
        max_hops_layout = QVBoxLayout()
        max_hops_layout.addWidget(QLabel(_translate("最大跳数")))
        self.max_hops = QSpinBox()
        self.max_hops.setRange(1, 30)
        self.max_hops.setValue(30)
        max_hops_layout.addWidget(self.max_hops)
        config_layout.addLayout(max_hops_layout)
        
        # 超时设置
        timeout_layout = QVBoxLayout()
        timeout_layout.addWidget(QLabel(_translate("超时时间(ms)")))
        self.timeout = QSpinBox()
        self.timeout.setRange(100, 5000)
        self.timeout.setValue(1000)
        self.timeout.setSuffix(" ms")
        timeout_layout.addWidget(self.timeout)
        config_layout.addLayout(timeout_layout)
        
        # IP版本选择
        ip_version_layout = QVBoxLayout()
        self.ipv6_checkbox = QCheckBox(_translate("使用IPv6"))
        self.ipv6_checkbox.setChecked(False)  # 默认使用IPv4
        ip_version_layout.addWidget(self.ipv6_checkbox)
        config_layout.addLayout(ip_version_layout)
        
        # 包大小设置
        packet_size_layout = QVBoxLayout()
        packet_size_layout.addWidget(QLabel(_translate("数据包大小(B)")))
        self.packet_size = QSpinBox()
        self.packet_size.setRange(32, 1500)
        self.packet_size.setValue(64)
        self.packet_size.setSuffix(" B")
        packet_size_layout.addWidget(self.packet_size)
        config_layout.addLayout(packet_size_layout)
        
        # DNS选项
        dns_layout = QVBoxLayout()
        dns_layout.addWidget(QLabel(_translate("DNS解析")))
        self.resolve_dns = QCheckBox(_translate("启用反向DNS"))
        self.resolve_dns.setChecked(True)
        dns_layout.addWidget(self.resolve_dns)
        config_layout.addLayout(dns_layout)
        
        # 隐私选项
        privacy_layout = QVBoxLayout()
        privacy_layout.addWidget(QLabel(_translate("隐私设置")))
        self.mask_first_hops = QCheckBox(_translate("隐藏前几跳"))
        privacy_layout.addWidget(self.mask_first_hops)
        config_layout.addLayout(privacy_layout)
        
        config_group.setLayout(config_layout)
        
        # 创建结果选项卡
        self.tab_widget = QTabWidget()
        
        # 创建表格结果标签
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(6)
        self.result_table.setHorizontalHeaderLabels([_translate("跳数"), _translate("IP地址"), _translate("主机名"), _translate("地理位置"), _translate("ASN信息"), _translate("延迟(ms)")])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        # 设置表格拉伸策略，使其铺满页面
        self.result_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # 设置第2、3、4、5列自动拉伸
        for i in range(1, 5):
            self.result_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        # 设置最小列宽
        self.result_table.setColumnWidth(0, 50)  # 跳数列
        self.result_table.setColumnWidth(5, 100)  # 延迟列
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 创建图表标签（占位）
        self.chart_widget = QWidget()
        chart_layout = QVBoxLayout(self.chart_widget)
        
        # 创建控制面板
        control_layout = QHBoxLayout()
        chart_layout.addLayout(control_layout)
        
        # 导出按钮
        self.export_btn = QPushButton(_translate("导出结果"))
        self.export_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.export_btn.clicked.connect(self.export_current_results)
        control_layout.addWidget(self.export_btn)
        
        # 导出截图按钮
        self.export_screenshot_btn = QPushButton(_translate("导出截图"))
        self.export_screenshot_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.export_screenshot_btn.clicked.connect(self.export_current_screenshot)
        control_layout.addWidget(self.export_screenshot_btn)
        
        control_layout.addStretch()
        
        # 创建可视化组件
        self.traceroute_visualizer = TracerouteVisualizer()
        chart_layout.addWidget(self.traceroute_visualizer)
        
        # 存储当前追踪结果
        self.current_hops_data = []
        self.current_raw_output = ""
        
        # 创建原始输出标签
        self.raw_output = QTableWidget()
        self.raw_output.setColumnCount(1)
        self.raw_output.setHorizontalHeaderLabels([_translate("原始输出")])
        self.raw_output.horizontalHeader().setStretchLastSection(True)
        self.raw_output.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 添加标签页
        self.tab_widget.addTab(self.result_table, _translate("表格结果"))
        self.tab_widget.addTab(self.chart_widget, _translate("可视化"))
        self.tab_widget.addTab(self.raw_output, _translate("原始输出"))
        
        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # 创建状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage(_translate("就绪"))
        
        # 将所有部件添加到主布局
        main_layout.addWidget(input_group)
        main_layout.addWidget(config_group)
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(self.progress_bar)
        
        # 美化界面
        self.style_ui()
    
    def create_menu_bar(self):
        # 确保先清除现有的菜单栏内容
        menubar = self.menuBar()
        menubar.clear()
        
        # 文件菜单
        file_menu = menubar.addMenu(_translate("文件"))
        
        export_action = QAction(_translate("导出结果"), self)
        export_action.triggered.connect(self.export_results)
        file_menu.addAction(export_action)
        
        clear_action = QAction(_translate("清空结果"), self)
        clear_action.triggered.connect(self.clear_results)
        file_menu.addAction(clear_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(_translate("退出"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 设置菜单
        settings_menu = menubar.addMenu(_translate("设置"))
        
        # 语言子菜单
        lang_menu = QMenu(_translate("语言"), self)
        settings_menu.addMenu(lang_menu)
        
        zh_cn_action = QAction(_translate("简体中文"), self)
        zh_cn_action.triggered.connect(lambda: self.change_language('zh_CN'))
        lang_menu.addAction(zh_cn_action)
        
        en_us_action = QAction(_translate("English"), self)
        en_us_action.triggered.connect(lambda: self.change_language('en_US'))
        lang_menu.addAction(en_us_action)
        
        settings_menu.addSeparator()
        
        preferences_action = QAction(_translate("首选项"), self)
        preferences_action.triggered.connect(self.show_preferences)
        settings_menu.addAction(preferences_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu(_translate("帮助"))
        
        about_action = QAction(_translate("关于"), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def style_ui(self):
        # 设置样式表
        self.setStyleSheet(""
            "QMainWindow {background-color: #f5f5f5;}"
            "QGroupBox {border: 1px solid #ccc; border-radius: 6px; margin-top: 10px;}"
            "QGroupBox::title {subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px;}"
            "QPushButton {background-color: #4CAF50; color: white; border: none; border-radius: 4px; padding: 6px 12px;}"
            "QPushButton:hover {background-color: #45a049;}"
            "QPushButton:pressed {background-color: #3e8e41;}"
            "QPushButton#mtr_button {background-color: #2196F3;}"
            "QPushButton#mtr_button:hover {background-color: #0b7dda;}"
            "QLineEdit {padding: 5px; border: 1px solid #ccc; border-radius: 4px;}"
            "QTableWidget {alternate-background-color: #f0f0f0; border: 1px solid #ccc;}"
            "QHeaderView::section {background-color: #e0e0e0; padding: 5px; border: 1px solid #ccc;}"
            "QTabWidget::pane {border: 1px solid #ccc; border-radius: 4px;}"
            "QTabBar::tab {padding: 6px 12px; border: 1px solid #ccc; margin-right: 2px; border-bottom-left-radius: 4px; border-bottom-right-radius: 4px;}"
            "QTabBar::tab:selected {background-color: #ffffff; border-bottom-color: #ffffff;}"
        )
    
    def start_traceroute(self):
        target = self.target_input.text().strip()
        if not target:
            QMessageBox.warning(self, _translate("警告"), _translate("请输入目标IP地址或域名"))
            return
        
        # 更新状态栏
        self.statusBar.showMessage(_translate("正在追踪到 {0}...", target))
        
        # 清空之前的结果
        self.clear_results()
        
        # 设置进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 获取配置值
        max_hops = get_config('network.max_hops', self.max_hops.value())
        timeout = get_config('network.timeout', self.timeout.value() / 1000.0)  # 转换为秒
        packet_size = get_config('network.packet_size', self.packet_size.value())
        resolve_dns = get_config('network.resolve_hostnames', self.resolve_dns.isChecked())
        protocol = get_config('network.protocol', 'icmp')
        
        # 启动追踪线程
        self.traceroute_thread = TracerouteThread(
            target=target,
            max_hops=max_hops,
            timeout=timeout,
            packet_size=packet_size,
            resolve_dns=resolve_dns,
            mask_first_hops=self.mask_first_hops.isChecked(),
            protocol=protocol,
            debug_mode=False,  # 使用真实数据解析IP地址
            ipv6=self.ipv6_checkbox.isChecked()
        )
        self.traceroute_thread.update_signal.connect(self.update_result)
        self.traceroute_thread.progress_signal.connect(self.update_progress)
        self.traceroute_thread.finished_signal.connect(self.trace_finished)
        self.traceroute_thread.start()
        
        # 禁用相关按钮
        self.trace_button.setEnabled(False)
        self.mtr_button.setEnabled(False)
        self.target_input.setEnabled(False)
        self.stop_button.setEnabled(True)
    
    def start_mtr(self):
        target = self.target_input.text().strip()
        if not target:
            QMessageBox.warning(self, _translate("警告"), _translate("请输入目标IP地址或域名"))
            return
        
        # 更新状态栏
        self.statusBar.showMessage(_translate("正在执行MTR到 {0}...", target))
        
        # 清空结果
        self.clear_results()
        
        # 获取配置值
        max_hops = get_config('network.max_hops', self.max_hops.value())
        packet_size = get_config('network.packet_size', self.packet_size.value())
        resolve_dns = get_config('network.resolve_hostnames', self.resolve_dns.isChecked())
        ping_count = get_config('network.ping_count', 3)
        
        # 启动MTR线程
        self.mtr_thread = MTRThread(
            target=target,
            max_hops=max_hops,
            packet_size=packet_size,
            resolve_dns=resolve_dns,
            mask_first_hops=self.mask_first_hops.isChecked(),
            ping_count=ping_count,
            ipv6=self.ipv6_checkbox.isChecked()
        )
        self.mtr_thread.update_signal.connect(self.update_mtr_result)
        self.mtr_thread.finished_signal.connect(self.mtr_finished)
        self.mtr_thread.start()
        
        # 禁用相关按钮
        self.trace_button.setEnabled(False)
        self.mtr_button.setEnabled(False)
        self.target_input.setEnabled(False)
        self.stop_button.setEnabled(True)
    
    def update_result(self, hop_info):
        # 使用IP地理位置功能更新结果
        updated_hop_info = update_traceroute_with_geo_info(hop_info)
        
        # 在表格中添加一行
        row_position = self.result_table.rowCount()
        self.result_table.insertRow(row_position)
        
        # 跳数
        hop_item = QTableWidgetItem(str(updated_hop_info.get('hop', '-')))
        hop_item.setTextAlignment(Qt.AlignCenter)
        self.result_table.setItem(row_position, 0, hop_item)
        
        # IP地址
        ip_item = QTableWidgetItem(updated_hop_info.get('ip', '-'))
        self.result_table.setItem(row_position, 1, ip_item)
        
        # 主机名
        hostname_item = QTableWidgetItem(updated_hop_info.get('hostname', '-'))
        self.result_table.setItem(row_position, 2, hostname_item)
        
        # 地理位置
        location_item = QTableWidgetItem(updated_hop_info.get('location', '-'))
        self.result_table.setItem(row_position, 3, location_item)
        
        # ASN信息
        asn_item = QTableWidgetItem(updated_hop_info.get('asn', '-'))
        self.result_table.setItem(row_position, 4, asn_item)
        
        # 延迟
        delay_item = QTableWidgetItem(updated_hop_info.get('delay', '-'))
        delay_item.setTextAlignment(Qt.AlignCenter)
        self.result_table.setItem(row_position, 5, delay_item)
        
        # 在原始输出中添加
        raw_text = f"{updated_hop_info.get('hop', '-')}. {updated_hop_info.get('ip', '-')} {updated_hop_info.get('hostname', '-')} {updated_hop_info.get('delay', '-')}"
        if updated_hop_info.get('location'):
            raw_text += f" [{updated_hop_info.get('location')}]"
        if updated_hop_info.get('asn'):
            raw_text += f" [{updated_hop_info.get('asn')}]"
        
        raw_row = self.raw_output.rowCount()
        self.raw_output.insertRow(raw_row)
        self.raw_output.setItem(raw_row, 0, QTableWidgetItem(raw_text))
        
        # 保存当前结果
        self.current_raw_output += raw_text + "\n"
        
        # 更新可视化
        if hasattr(self, 'traceroute_visualizer'):
            # 收集当前所有结果
            current_hops = []
            for row in range(self.result_table.rowCount()):
                hop = {
                    'hop': int(self.result_table.item(row, 0).text()) if self.result_table.item(row, 0) else None,
                    'ip': self.result_table.item(row, 1).text() if self.result_table.item(row, 1) else '',
                    'hostname': self.result_table.item(row, 2).text() if self.result_table.item(row, 2) else '',
                    'location': self.result_table.item(row, 3).text() if self.result_table.item(row, 3) else '',
                    'asn': self.result_table.item(row, 4).text() if self.result_table.item(row, 4) else '',
                    'delay': self.result_table.item(row, 5).text() if self.result_table.item(row, 5) else ''
                }
                current_hops.append(hop)
            
            self.current_hops_data = current_hops
            self.traceroute_visualizer.update_data(current_hops)
        
        # 自动调整列宽
        self.result_table.resizeColumnsToContents()
        self.raw_output.resizeColumnsToContents()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def export_current_results(self):
        """导出当前结果"""
        if not self.current_hops_data:
            QMessageBox.information(self, _translate("无法导出"), _translate("没有可导出的结果"))
            return
        
        target = self.target_input.text()
        success = ResultExporter.export_results(self, self.current_hops_data, self.current_raw_output, target)
        
        if success:
            QMessageBox.information(self, _translate("导出成功"), _translate("结果已成功导出"))
    
    def export_results(self):
        """从菜单导出结果的方法"""
        if self.result_table.rowCount() == 0:
            QMessageBox.warning(self, _translate("警告"), _translate("没有可导出的结果"))
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出结果", "", "文本文件 (*.txt);;CSV文件 (*.csv);;所有文件 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    # 写入表头
                    headers = [self.result_table.horizontalHeaderItem(i).text() for i in range(self.result_table.columnCount())]
                    f.write('\t'.join(headers) + '\n')
                    
                    # 写入数据
                    for row in range(self.result_table.rowCount()):
                        row_data = []
                        for col in range(self.result_table.columnCount()):
                            item = self.result_table.item(row, col)
                            row_data.append(item.text() if item else '')
                        f.write('\t'.join(row_data) + '\n')
                
                QMessageBox.information(self, "成功", f"结果已导出到 {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
                
    def clear_results(self):
        """清空结果表格"""
        self.result_table.setRowCount(0)
        self.raw_output.setRowCount(0)
        
    def show_preferences(self):
        """显示首选项设置对话框"""
        dialog = SettingsDialog(self)
        if dialog.exec_():
            # 设置已保存，重新加载配置到UI
            self.load_config_to_ui()
            
    def load_config_to_ui(self):
        """从配置加载设置到UI控件"""
        # 网络设置
        self.max_hops.setValue(get_config('network.max_hops', 30))
        self.timeout.setValue(int(get_config('network.timeout', 1.0) * 1000))  # 转换为毫秒
        self.packet_size.setValue(get_config('network.packet_size', 64))
        self.resolve_dns.setChecked(get_config('network.resolve_hostnames', True))
        self.mask_first_hops.setChecked(get_config('network.mask_first_hops', False))
        
        # 获取协议配置并设置到下拉框
        protocol = get_config('network.protocol', 'icmp')
        protocol_index = 0  # 默认ICMP
        if hasattr(self, 'protocol_combo'):
            protocol_index = self.protocol_combo.findText(protocol.upper())
            if protocol_index >= 0:
                self.protocol_combo.setCurrentIndex(protocol_index)
        
        # 界面设置
        show_advanced = get_config('ui.show_advanced_options', True)
        if hasattr(self, 'centralWidget') and self.centralWidget() and hasattr(self.centralWidget(), 'layout'):
            config_group = self.centralWidget().layout().itemAt(1).widget()
            config_group.setVisible(show_advanced)
    
    def export_current_screenshot(self):
        """导出当前截图"""
        # 询问用户要截取哪个部分
        options = [_translate("整个窗口"), _translate("结果表格"), _translate("可视化"), _translate("原始输出")]
        choice, ok = QInputDialog.getItem(self, _translate("选择截图范围"), 
                                         _translate("请选择要截取的部分:"), options, 0, False)
        
        if ok:
            if choice == options[0]:
                # 整个窗口
                widget = self
            elif choice == options[1]:
                # 结果表格
                widget = self.result_table
            elif choice == options[2]:
                # 可视化
                widget = self.traceroute_visualizer
            else:
                # 原始输出
                widget = self.raw_output
            
            success = ResultExporter.export_screenshot(self, widget)
            
            if success:
                QMessageBox.information(self, _translate("导出成功"), _translate("截图已成功导出"))
                
    def stop_tracing(self):
        """停止当前的路由追踪"""
        # 停止traceroute线程
        if hasattr(self, 'traceroute_thread') and self.traceroute_thread and self.traceroute_thread.isRunning():
            print("正在停止路由追踪...")
            self.traceroute_thread.stop()
            self.statusBar.showMessage(_translate("路由追踪已停止"))
        # 停止MTR线程
        elif hasattr(self, 'mtr_thread') and self.mtr_thread and self.mtr_thread.isRunning():
            print("正在停止MTR...")
            self.mtr_thread.stop()
            self.statusBar.showMessage(_translate("MTR已停止"))
        
        # 重置UI状态
        self.reset_ui_state()
    
    def reset_ui_state(self):
        """重置UI状态"""
        self.trace_button.setEnabled(True)
        self.mtr_button.setEnabled(True)
        self.target_input.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
    
    def trace_finished(self, success):
        # 重置UI状态
        self.reset_ui_state()
        
        if success:
            self.statusBar.showMessage(_translate("追踪完成"))
        else:
            self.statusBar.showMessage(_translate("追踪失败"))
            
    def update_mtr_result(self, hops_data):
        # 清空表格但保持表头
        self.result_table.setRowCount(0)
        
        # 更新表格
        for hop_info in hops_data:
            # 使用IP地理位置功能更新结果
            updated_hop_info = update_traceroute_with_geo_info(hop_info)
            
            row_position = self.result_table.rowCount()
            self.result_table.insertRow(row_position)
            
            # 跳数
            hop_item = QTableWidgetItem(str(updated_hop_info.get('hop', '-')))
            hop_item.setTextAlignment(Qt.AlignCenter)
            self.result_table.setItem(row_position, 0, hop_item)
            
            # IP地址
            ip_item = QTableWidgetItem(updated_hop_info.get('ip', '-'))
            self.result_table.setItem(row_position, 1, ip_item)
            
            # 主机名
            hostname_item = QTableWidgetItem(updated_hop_info.get('hostname', '-'))
            self.result_table.setItem(row_position, 2, hostname_item)
            
            # 地理位置
            location_item = QTableWidgetItem(updated_hop_info.get('location', '-'))
            self.result_table.setItem(row_position, 3, location_item)
            
            # ASN信息
            asn_item = QTableWidgetItem(updated_hop_info.get('asn', '-'))
            self.result_table.setItem(row_position, 4, asn_item)
            
            # 延迟
            delay_text = "-"
            if 'min_delay' in updated_hop_info and 'avg_delay' in updated_hop_info and 'max_delay' in updated_hop_info:
                delay_text = f"{updated_hop_info['min_delay']} / {updated_hop_info['avg_delay']} / {updated_hop_info['max_delay']}"
            elif 'avg_delay' in updated_hop_info:
                delay_text = updated_hop_info['avg_delay']
            
            delay_item = QTableWidgetItem(delay_text)
            delay_item.setTextAlignment(Qt.AlignCenter)
            self.result_table.setItem(row_position, 5, delay_item)
        
        # 保存当前结果
        self.current_hops_data = hops_data
        
        # 更新可视化
        if hasattr(self, 'traceroute_visualizer'):
            self.traceroute_visualizer.update_data(hops_data)
        
        # 自动调整列宽
        self.result_table.resizeColumnsToContents()
            
    def mtr_finished(self, success):
        # 重置UI状态
        self.reset_ui_state()
        
        if success:
            self.statusBar.showMessage(_translate("MTR已停止"))
        else:
            self.statusBar.showMessage(_translate("MTR执行出错"))
            
    def on_config_changed(self):
        """配置更改时调用此方法"""
        self.load_config_to_ui()
        
    def closeEvent(self, event):
        """窗口关闭时保存设置"""
        # 保存窗口大小和位置
        window_size = [self.size().width(), self.size().height()]
        window_pos = [self.pos().x(), self.pos().y()]
        
        from config import set_config
        set_config('ui.window_size', window_size)
        set_config('ui.window_position', window_pos)
        
        # 确保线程停止
        if hasattr(self, 'traceroute_thread') and self.traceroute_thread and self.traceroute_thread.isRunning():
            self.traceroute_thread.terminate()
        if hasattr(self, 'mtr_thread') and self.mtr_thread and self.mtr_thread.isRunning():
            self.mtr_thread.stop()
        
        event.accept()
    
    def show_about(self):
        QMessageBox.about(self,
            _translate("关于XHtrace"),
            _translate("XHtrace v1.0\n\n"
            "一个现代化的网络追踪工具，基于Python和PyQt5开发。\n\n"
            "灵感来自OpenTrace项目\n\n"
            "© 2024 XHtrace Team")
        )
            


class TracerouteThread(QThread):
    update_signal = pyqtSignal(dict)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, target, max_hops=30, timeout=1.0, packet_size=64, resolve_dns=True, mask_first_hops=False, protocol='icmp', debug_mode=False, ipv6=False):
        super().__init__()
        self.target = target
        self.max_hops = max_hops
        self.timeout = timeout  # 已经是秒
        self.packet_size = packet_size
        self.resolve_dns = resolve_dns
        self.mask_first_hops = mask_first_hops
        self.protocol = protocol
        self.debug_mode = debug_mode
        self.ipv6 = ipv6
        self.running = True
        
    def stop(self):
        """停止追踪线程"""
        self.running = False
        # 如果线程正在运行，尝试终止
        if self.isRunning():
            self.wait(1000)  # 等待1秒让线程自行终止
            if self.isRunning():
                print("强制终止追踪线程")
                # 在Python中，我们不能强制终止线程，但可以设置标志让线程自行退出
        
    def run(self):
        try:
            # 使用traceroute模块执行真实的traceroute
            # 确保参数名与traceroute函数定义匹配
            # 设置max_retries为5以增加成功率
            for hop_info, progress, is_destination in traceroute(
                self.target, 
                max_hops=self.max_hops,
                timeout=self.timeout,
                packet_size=self.packet_size,
                resolve_dns=self.resolve_dns,
                protocol=self.protocol,
                max_retries=5,
                debug_mode=self.debug_mode
            ):
                # 检查是否需要停止
                if not self.running:
                    print("追踪已停止")
                    self.finished_signal.emit(False)
                    return
                
                # 检查是否有错误
                if "error" in hop_info:
                    # 显示错误信息
                    self.update_signal.emit({
                        'hop': 0,
                        'ip': '错误',
                        'hostname': hop_info['error'],
                        'location': '',
                        'asn': '',
                        'delay': ''
                    })
                    self.progress_signal.emit(100)
                    self.finished_signal.emit(False)
                    return
                
                # 添加位置和ASN信息（如果没有）
                if 'location' not in hop_info or not hop_info['location']:
                    hop_info['location'] = "未知位置"
                if 'asn' not in hop_info or not hop_info['asn']:
                    hop_info['asn'] = "未知ASN"
                
                # 隐私打码
                if self.mask_first_hops and hop_info['hop'] <= 3:
                    hop_info['ip'] = "***.***.***.***"
                    hop_info['hostname'] = "***"
                    hop_info['location'] = "***"
                
                # 发送更新信号
                self.update_signal.emit(hop_info)
                self.progress_signal.emit(progress)
                
                # 检查是否达到目标
                if is_destination:
                    break
            
            self.finished_signal.emit(True)
        except Exception as e:
            print(f"Traceroute error: {e}")
            # 显示错误信息给用户
            self.update_signal.emit({
                'hop': 0,
                'ip': '错误',
                'hostname': str(e),
                'location': '',
                'asn': '',
                'delay': ''
            })
            self.progress_signal.emit(100)
            self.finished_signal.emit(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 设置应用图标（可以后续添加）
    # app.setWindowIcon(QIcon("icon.ico"))
    
    # 启用高DPI支持
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    window = XHtraceApp()
    window.show()
    sys.exit(app.exec_())