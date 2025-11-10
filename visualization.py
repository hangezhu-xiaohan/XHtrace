from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, 
                            QHBoxLayout, QGroupBox, QMessageBox)
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QFontMetrics
from PyQt5.QtCore import Qt, QRect, QSize
import math
from language import _translate

class TracerouteVisualizer(QWidget):
    """网络追踪结果可视化组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hops_data = []
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(_translate("网络路径可视化"))
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 可视化组件
        self.visual_widget = QWidget()
        self.visual_layout = QVBoxLayout(self.visual_widget)
        self.visual_layout.setAlignment(Qt.AlignTop)
        
        self.scroll_area.setWidget(self.visual_widget)
        layout.addWidget(self.scroll_area)
        
        # 初始提示
        self.placeholder = QLabel(_translate("执行追踪后将显示可视化结果"))
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("color: #888; font-style: italic;")
        self.visual_layout.addWidget(self.placeholder)
    
    def update_data(self, hops_data):
        """更新可视化数据"""
        self.hops_data = hops_data
        self.render_visualization()
    
    def render_visualization(self):
        """渲染可视化结果"""
        # 清除现有内容
        self.clear_visualization()
        
        if not self.hops_data:
            self.visual_layout.addWidget(self.placeholder)
            return
        
        # 创建路径图表
        path_widget = NetworkPathWidget(self.hops_data)
        self.visual_layout.addWidget(path_widget)
        
        # 创建统计信息
        stats_widget = self.create_statistics()
        self.visual_layout.addWidget(stats_widget)
    
    def clear_visualization(self):
        """清除可视化内容"""
        # 移除所有子部件
        while self.visual_layout.count():
            item = self.visual_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def create_statistics(self):
        """创建统计信息面板"""
        stats_group = QGroupBox(_translate("追踪统计"))
        stats_layout = QVBoxLayout(stats_group)
        
        # 计算统计信息
        total_hops = len(self.hops_data)
        total_delay = 0
        last_delay = 0
        successful_hops = 0
        failed_hops = 0
        
        for hop in self.hops_data:
            if 'delay' in hop and hop['delay'] != '-':
                try:
                    delay = float(hop['delay'].split(' ms')[0])
                    total_delay += delay
                    last_delay = delay
                    successful_hops += 1
                except (ValueError, IndexError):
                    failed_hops += 1
            else:
                failed_hops += 1
        
        avg_delay = total_delay / successful_hops if successful_hops > 0 else 0
        
        # 添加统计信息标签
        stats_layout.addWidget(QLabel(f"{_translate('总跳数')}: {total_hops}"))
        stats_layout.addWidget(QLabel(f"{_translate('成功跳数')}: {successful_hops}"))
        stats_layout.addWidget(QLabel(f"{_translate('失败跳数')}: {failed_hops}"))
        stats_layout.addWidget(QLabel(f"{_translate('平均延迟')}: {avg_delay:.2f} ms"))
        stats_layout.addWidget(QLabel(f"{_translate('最终延迟')}: {last_delay} ms"))
        
        return stats_group

class NetworkPathWidget(QWidget):
    """网络路径可视化组件"""
    def __init__(self, hops_data, parent=None):
        super().__init__(parent)
        self.hops_data = hops_data
        self.setMinimumHeight(max(300, len(hops_data) * 80))
        self.setMinimumWidth(800)
    
    def paintEvent(self, event):
        """绘制网络路径"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # 绘制背景
        painter.fillRect(event.rect(), QBrush(QColor(240, 240, 240)))
        
        if not self.hops_data:
            return
        
        # 计算节点位置
        node_width = 150
        node_height = 60
        vertical_spacing = 20
        
        # 绘制每个节点和连接线
        for i, hop in enumerate(self.hops_data):
            # 节点位置
            x = (width - node_width) // 2
            y = 50 + i * (node_height + vertical_spacing)
            
            # 绘制连接线（除了第一个节点）
            if i > 0:
                prev_y = 50 + (i - 1) * (node_height + vertical_spacing)
                painter.setPen(QPen(QColor(100, 181, 246), 2))
                painter.drawLine(
                    x + node_width // 2, prev_y + node_height,  # 上一节点底部
                    x + node_width // 2, y                    # 当前节点顶部
                )
            
            # 确定节点颜色
            if i == len(self.hops_data) - 1:
                # 目标节点
                color = QColor(76, 175, 80)
            elif 'delay' not in hop or hop['delay'] == '-':
                # 失败节点
                color = QColor(244, 67, 54)
            else:
                # 普通节点
                color = QColor(33, 150, 243)
            
            # 绘制节点背景
            painter.setPen(QPen(color.darker(120), 2))
            painter.setBrush(QBrush(color.lighter(130)))
            painter.drawRoundedRect(x, y, node_width, node_height, 8, 8)
            
            # 绘制节点内容
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QPen(Qt.black))
            
            # 跳数
            hop_text = f"{_translate('跳数')}: {hop.get('hop', '-')}"
            painter.drawText(x + 10, y + 20, hop_text)
            
            # IP地址和主机名
            font.setBold(False)
            painter.setFont(font)
            
            ip_text = hop.get('ip', '-')
            painter.drawText(x + 10, y + 40, ip_text)
            
            # 延迟
            delay_text = hop.get('delay', '-')
            painter.drawText(x + 10, y + 55, delay_text)

class DelayChartWidget(QWidget):
    """延迟图表组件"""
    def __init__(self, hops_data, parent=None):
        super().__init__(parent)
        self.hops_data = hops_data
        self.setMinimumHeight(300)
        self.setMinimumWidth(800)
    
    def paintEvent(self, event):
        """绘制延迟图表"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # 绘制背景
        painter.fillRect(event.rect(), QBrush(QColor(240, 240, 240)))
        
        if not self.hops_data:
            return
        
        # 提取延迟数据
        delays = []
        for hop in self.hops_data:
            if 'delay' in hop and hop['delay'] != '-':
                try:
                    delay = float(hop['delay'].split(' ms')[0])
                    delays.append(delay)
                except (ValueError, IndexError):
                    delays.append(0)
            else:
                delays.append(0)
        
        if not delays:
            return
        
        # 计算最大值和比例
        max_delay = max(delays) if delays else 1
        if max_delay == 0:
            max_delay = 1
        
        # 绘制坐标轴
        margin = 50
        chart_width = width - 2 * margin
        chart_height = height - 2 * margin
        
        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(margin, margin, margin, height - margin)  # Y轴
        painter.drawLine(margin, height - margin, width - margin, height - margin)  # X轴
        
        # 绘制Y轴刻度
        num_ticks = 5
        for i in range(num_ticks + 1):
            y = height - margin - (i * chart_height / num_ticks)
            painter.drawLine(margin - 5, y, margin, y)
            
            # 刻度标签
            value = (max_delay * i / num_ticks)
            painter.drawText(margin - 40, y + 5, f"{value:.0f}")
        
        # 绘制Y轴标签
        painter.rotate(-90)
        painter.drawText(-(height // 2 + 30), margin - 20, _translate("延迟 (ms)"))
        painter.rotate(90)
        
        # 绘制X轴标签
        painter.drawText(width // 2 - 30, height - 10, _translate("跳数"))
        
        # 绘制柱状图
        bar_width = chart_width / len(delays) * 0.6
        spacing = chart_width / len(delays) * 0.4 / 2
        
        for i, delay in enumerate(delays):
            bar_height = (delay / max_delay) * chart_height
            x = margin + spacing + i * (bar_width + 2 * spacing)
            y = height - margin - bar_height
            
            # 根据延迟设置颜色
            if delay > max_delay * 0.7:
                color = QColor(244, 67, 54)
            elif delay > max_delay * 0.4:
                color = QColor(255, 193, 7)
            else:
                color = QColor(76, 175, 80)
            
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(120), 1))
            painter.drawRect(x, y, bar_width, bar_height)
            
            # 添加跳数标签
            painter.setPen(QPen(Qt.black))
            painter.drawText(x + bar_width // 2 - 10, height - margin + 20, f"{i+1}")

# 测试代码
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow
    
    app = QApplication(sys.argv)
    window = QMainWindow()
    
    # 测试数据
    test_hops = [
        {'hop': 1, 'ip': '192.168.1.1', 'hostname': 'router.local', 'delay': '1.2 ms'},
        {'hop': 2, 'ip': '10.0.0.1', 'hostname': 'isp-gateway', 'delay': '5.4 ms'},
        {'hop': 3, 'ip': '202.100.1.1', 'hostname': 'isp-backbone', 'delay': '10.8 ms'},
        {'hop': 4, 'ip': '1.1.1.1', 'hostname': 'cloudflare-dns', 'delay': '20.3 ms'}
    ]
    
    visualizer = TracerouteVisualizer()
    visualizer.update_data(test_hops)
    
    window.setCentralWidget(visualizer)
    window.setWindowTitle("网络追踪可视化测试")
    window.resize(900, 600)
    window.show()
    
    sys.exit(app.exec_())
