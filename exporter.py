import csv
import json
import os
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from PyQt5.QtCore import Qt
from language import _translate

class ResultExporter:
    """追踪结果导出工具类"""
    
    @staticmethod
    def export_results(parent, hops_data, raw_output, target=None):
        """导出结果主方法"""
        # 显示文件对话框，让用户选择保存位置和格式
        formats = [
            _translate("文本文件 (*.txt)"),
            _translate("CSV文件 (*.csv)"),
            _translate("JSON文件 (*.json)")
        ]
        
        file_name = f"trace_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        default_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        
        file_path, file_filter = QFileDialog.getSaveFileName(
            parent, 
            _translate("导出结果"), 
            os.path.join(default_dir, file_name),
            f"{formats[0]};;{formats[1]};;{formats[2]}"
        )
        
        if not file_path:
            return False
        
        try:
            # 根据选择的格式导出
            if formats[0] in file_filter:
                if not file_path.endswith('.txt'):
                    file_path += '.txt'
                return ResultExporter._export_as_text(file_path, hops_data, raw_output, target)
            elif formats[1] in file_filter:
                if not file_path.endswith('.csv'):
                    file_path += '.csv'
                return ResultExporter._export_as_csv(file_path, hops_data)
            elif formats[2] in file_filter:
                if not file_path.endswith('.json'):
                    file_path += '.json'
                return ResultExporter._export_as_json(file_path, hops_data, raw_output, target)
            
            return False
        
        except Exception as e:
            QMessageBox.critical(parent, 
                                _translate("导出失败"), 
                                _translate("导出文件时发生错误") + f": {str(e)}")
            return False
    
    @staticmethod
    def _export_as_text(file_path, hops_data, raw_output, target=None):
        """导出为文本文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            # 添加头部信息
            f.write(_translate("网络追踪结果") + "\n")
            f.write("="*60 + "\n\n")
            
            if target:
                f.write(f"{_translate('目标')}: {target}\n")
            f.write(f"{_translate('执行时间')}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 添加表格结果
            f.write(_translate("追踪结果摘要") + "\n")
            f.write("-"*60 + "\n")
            
            # 表头
            headers = [_translate("跳数"), _translate("IP地址"), _translate("主机名"), _translate("地理位置"), _translate("延迟")]
            f.write(f"{headers[0]:<6} {headers[1]:<20} {headers[2]:<30} {headers[3]:<30} {headers[4]:<10}\n")
            f.write("-"*60 + "\n")
            
            # 数据行
            for hop in hops_data:
                hop_num = str(hop.get('hop', '-'))
                ip = hop.get('ip', '-')
                hostname = hop.get('hostname', '-')[:27]  # 限制长度
                location = hop.get('location', '-')[:27]  # 限制长度
                delay = hop.get('delay', '-')
                
                f.write(f"{hop_num:<6} {ip:<20} {hostname:<30} {location:<30} {delay:<10}\n")
            
            # 添加原始输出
            f.write("\n\n" + _translate("原始输出") + "\n")
            f.write("="*60 + "\n")
            f.write(raw_output)
        
        return True
    
    @staticmethod
    def _export_as_csv(file_path, hops_data):
        """导出为CSV文件"""
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:  # utf-8-sig 支持Excel打开时正确显示中文
            fieldnames = ['hop', 'ip', 'hostname', 'location', 'country', 'asn', 'isp', 'delay']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # 写入表头（使用翻译后的字段名）
            header_mapping = {
                'hop': _translate("跳数"),
                'ip': _translate("IP地址"),
                'hostname': _translate("主机名"),
                'location': _translate("地理位置"),
                'country': _translate("国家"),
                'asn': _translate("ASN"),
                'isp': _translate("ISP"),
                'delay': _translate("延迟")
            }
            writer.writerow(header_mapping)
            
            # 写入数据行
            for hop in hops_data:
                row = {
                    'hop': hop.get('hop', ''),
                    'ip': hop.get('ip', ''),
                    'hostname': hop.get('hostname', ''),
                    'location': hop.get('location', ''),
                    'country': hop.get('country', ''),
                    'asn': hop.get('asn', ''),
                    'isp': hop.get('isp', ''),
                    'delay': hop.get('delay', '')
                }
                writer.writerow(row)
        
        return True
    
    @staticmethod
    def _export_as_json(file_path, hops_data, raw_output, target=None):
        """导出为JSON文件"""
        data = {
            'metadata': {
                'target': target,
                'timestamp': datetime.now().isoformat(),
                'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_hops': len(hops_data)
            },
            'raw_output': raw_output,
            'hops': hops_data
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True

    @staticmethod
    def export_screenshot(parent, widget):
        """导出截图"""
        # 显示文件对话框
        file_name = f"trace_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        default_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        
        file_path, _ = QFileDialog.getSaveFileName(
            parent, 
            _translate("导出截图"), 
            os.path.join(default_dir, file_name),
            _translate("PNG图片 (*.png)")
        )
        
        if not file_path:
            return False
        
        try:
            # 如果用户没有指定扩展名，添加.png
            if not file_path.endswith('.png'):
                file_path += '.png'
            
            # 截取组件的完整内容
            pixmap = widget.grab()
            success = pixmap.save(file_path, 'PNG')
            
            if success:
                return True
            else:
                raise Exception(_translate("截图保存失败"))
                
        except Exception as e:
            QMessageBox.critical(parent, 
                                _translate("导出失败"), 
                                _translate("导出截图时发生错误") + f": {str(e)}")
            return False
