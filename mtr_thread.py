#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QThread, pyqtSignal
from traceroute import mtr

class MTRThread(QThread):
    update_signal = pyqtSignal(list)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, target, max_hops=30, packet_size=64, resolve_dns=True, mask_first_hops=False, ping_count=3, ipv6=False):
        super().__init__()
        self.target = target
        self.max_hops = max_hops
        self.packet_size = packet_size
        self.resolve_dns = resolve_dns
        self.mask_first_hops = mask_first_hops
        self.ping_count = ping_count
        self.ipv6 = ipv6
        self.running = True
    
    def stop(self):
        """停止MTR线程"""
        self.running = False
        # 如果线程正在运行，尝试终止
        if self.isRunning():
            self.wait(1000)  # 等待1秒让线程自行终止
            if self.isRunning():
                print("强制终止MTR线程")
                # 在Python中，我们不能强制终止线程，但可以设置标志让线程自行退出
    
    def run(self):
        try:
            # 使用mtr模块执行MTR
            for summary, progress, all_hops_data in mtr(
                self.target,
                count=self.ping_count,  # 将ping_count改为count
                max_hops=self.max_hops,
                packet_size=self.packet_size,
                resolve_dns=self.resolve_dns,
                ipv6=self.ipv6
            ):
                # 检查是否需要停止
                if not self.running:
                    print("MTR已停止")
                    self.finished_signal.emit(False)
                    return
                
                # 隐私打码
                if self.mask_first_hops:
                    for hop_info in all_hops_data:
                        if hop_info['hop'] <= 3:
                            hop_info['ip'] = "***.***.***.***"
                            hop_info['hostname'] = "***"
                            hop_info['location'] = "***" if 'location' in hop_info else "***"
                
                # 发送更新信号到UI
                self.update_signal.emit(all_hops_data)
                
            # 完成执行
            self.finished_signal.emit(True)
            
        except Exception as e:
            print(f"MTR错误: {str(e)}")
            self.update_signal.emit([{"error": str(e)}])
            self.finished_signal.emit(False)
