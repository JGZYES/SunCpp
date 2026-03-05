import json
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QKeySequenceEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QKeyCombination
from PyQt6.QtGui import QKeySequence


class KeyBindingManager:
    """快捷键管理器"""
    
    DEFAULT_BINDINGS = {
        'new_file': {'name': '新建文件', 'shortcut': 'Ctrl+N'},
        'open_file': {'name': '打开文件', 'shortcut': 'Ctrl+O'},
        'save_file': {'name': '保存文件', 'shortcut': 'Ctrl+S'},
        'save_as': {'name': '另存为', 'shortcut': 'Ctrl+Shift+S'},
        'close_tab': {'name': '关闭标签页', 'shortcut': 'Ctrl+W'},
        'quit': {'name': '退出', 'shortcut': 'Ctrl+Q'},
        'undo': {'name': '撤销', 'shortcut': 'Ctrl+Z'},
        'redo': {'name': '重做', 'shortcut': 'Ctrl+Y'},
        'cut': {'name': '剪切', 'shortcut': 'Ctrl+X'},
        'copy': {'name': '复制', 'shortcut': 'Ctrl+C'},
        'paste': {'name': '粘贴', 'shortcut': 'Ctrl+V'},
        'select_all': {'name': '全选', 'shortcut': 'Ctrl+A'},
        'find': {'name': '查找', 'shortcut': 'Ctrl+F'},
        'replace': {'name': '替换', 'shortcut': 'Ctrl+H'},
        'goto_line': {'name': '跳转到行', 'shortcut': 'Ctrl+G'},
        'comment_line': {'name': '注释/取消注释', 'shortcut': 'Ctrl+/'},
        'fold_region': {'name': '折叠代码', 'shortcut': 'Ctrl+Shift+['},
        'unfold_region': {'name': '展开代码', 'shortcut': 'Ctrl+Shift+]'},
        'unfold_all': {'name': '展开所有', 'shortcut': 'Ctrl+K Ctrl+J'},
        'compile': {'name': '编译', 'shortcut': 'F5'},
        'run': {'name': '运行', 'shortcut': 'F6'},
        'compile_run': {'name': '编译并运行', 'shortcut': 'F7'},
    }
    
    def __init__(self):
        self.bindings = {}
        self.load_bindings()
    
    def get_config_path(self):
        """获取配置文件路径"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, 'keybindings.json')
    
    def load_bindings(self):
        """加载快捷键配置"""
        config_path = self.get_config_path()
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.bindings = json.load(f)
            except Exception as e:
                print(f'加载快捷键配置失败: {e}')
                self.bindings = self.DEFAULT_BINDINGS.copy()
        else:
            self.bindings = self.DEFAULT_BINDINGS.copy()
            self.save_bindings()
    
    def save_bindings(self):
        """保存快捷键配置"""
        config_path = self.get_config_path()
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.bindings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f'保存快捷键配置失败: {e}')
    
    def get_shortcut(self, action_id):
        """获取快捷键"""
        if action_id in self.bindings:
            return self.bindings[action_id]['shortcut']
        return None
    
    def set_shortcut(self, action_id, shortcut):
        """设置快捷键"""
        if action_id in self.bindings:
            self.bindings[action_id]['shortcut'] = shortcut
            self.save_bindings()
            return True
        return False
    
    def reset_to_default(self):
        """重置为默认快捷键"""
        self.bindings = self.DEFAULT_BINDINGS.copy()
        self.save_bindings()


class KeyBindingDialog(QDialog):
    """快捷键设置对话框"""
    
    def __init__(self, key_manager, parent=None):
        super().__init__(parent)
        self.key_manager = key_manager
        self.current_editing = None
        self.init_ui()
        self.setStyleSheet('''
            QDialog {
                background-color: #1e1e1e;
            }
            QTableWidget {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                gridline-color: #3c3c3c;
            }
            QTableWidget::item:selected {
                background-color: #094771;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #333333;
                color: #d4d4d4;
                padding: 5px;
                border: 1px solid #3c3c3c;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #094771;
            }
            QLabel {
                color: #d4d4d4;
            }
            QLineEdit {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
        ''')
    
    def init_ui(self):
        self.setWindowTitle('快捷键设置')
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel('搜索:'))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('输入命令名称搜索...')
        self.search_input.textChanged.connect(self.filter_bindings)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # 快捷键表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['命令', '快捷键', '操作'])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.load_bindings_to_table()
        layout.addWidget(self.table)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        reset_btn = QPushButton('恢复默认')
        reset_btn.clicked.connect(self.reset_bindings)
        btn_layout.addWidget(reset_btn)
        
        btn_layout.addStretch()
        
        ok_btn = QPushButton('确定')
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def load_bindings_to_table(self):
        """加载快捷键到表格"""
        bindings = self.key_manager.bindings
        self.table.setRowCount(len(bindings))
        
        for i, (action_id, info) in enumerate(bindings.items()):
            # 命令名称
            name_item = QTableWidgetItem(info['name'])
            self.table.setItem(i, 0, name_item)
            
            # 快捷键
            shortcut_item = QTableWidgetItem(info['shortcut'])
            self.table.setItem(i, 1, shortcut_item)
            
            # 编辑按钮
            edit_btn = QPushButton('修改')
            edit_btn.clicked.connect(lambda checked, row=i, aid=action_id: self.edit_binding(row, aid))
            self.table.setCellWidget(i, 2, edit_btn)
        
        self.table.resizeColumnsToContents()
    
    def filter_bindings(self, text):
        """过滤快捷键"""
        for i in range(self.table.rowCount()):
            name = self.table.item(i, 0).text()
            self.table.setRowHidden(i, text.lower() not in name.lower())
    
    def edit_binding(self, row, action_id):
        """编辑快捷键"""
        dialog = KeySequenceDialog(self.key_manager.bindings[action_id]['name'], self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_shortcut = dialog.get_key_sequence()
            if new_shortcut:
                # 检查是否与其他快捷键冲突
                for aid, info in self.key_manager.bindings.items():
                    if aid != action_id and info['shortcut'] == new_shortcut:
                        QMessageBox.warning(self, '警告', f'快捷键 "{new_shortcut}" 已被 "{info["name"]}" 使用')
                        return
                
                # 更新快捷键
                self.key_manager.set_shortcut(action_id, new_shortcut)
                self.table.item(row, 1).setText(new_shortcut)
    
    def reset_bindings(self):
        """恢复默认快捷键"""
        reply = QMessageBox.question(
            self, '确认', 
            '确定要恢复默认快捷键吗？所有自定义设置将丢失。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.key_manager.reset_to_default()
            self.load_bindings_to_table()


class KeySequenceDialog(QDialog):
    """快捷键输入对话框"""
    
    def __init__(self, action_name, parent=None):
        super().__init__(parent)
        self.action_name = action_name
        self.key_sequence = None
        self.init_ui()
        self.setStyleSheet('''
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #d4d4d4;
                font-size: 14px;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:disabled {
                background-color: #555555;
            }
        ''')
    
    def init_ui(self):
        self.setWindowTitle('设置快捷键')
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout(self)
        
        # 提示标签
        label = QLabel(f'为 "{self.action_name}" 设置快捷键')
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        # 快捷键显示
        self.key_label = QLabel('请按下快捷键...')
        self.key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.key_label.setStyleSheet('''
            QLabel {
                background-color: #3c3c3c;
                border: 2px dashed #555555;
                border-radius: 5px;
                padding: 15px;
                font-size: 18px;
                font-weight: bold;
                color: #007acc;
            }
        ''')
        layout.addWidget(self.key_label)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.ok_btn = QPushButton('确定')
        self.ok_btn.setEnabled(False)
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_btn)
        
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def keyPressEvent(self, event):
        """捕获按键"""
        key = event.key()
        modifiers = event.modifiers()
        
        # 忽略单独的功能键
        if key in [Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta]:
            return
        
        # 构建快捷键字符串
        sequence = []
        
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            sequence.append('Ctrl')
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            sequence.append('Shift')
        if modifiers & Qt.KeyboardModifier.AltModifier:
            sequence.append('Alt')
        
        # 获取按键名称
        key_name = QKeySequence(key).toString()
        if key_name:
            sequence.append(key_name)
        
        if sequence:
            self.key_sequence = '+'.join(sequence)
            self.key_label.setText(self.key_sequence)
            self.ok_btn.setEnabled(True)
    
    def get_key_sequence(self):
        """获取快捷键"""
        return self.key_sequence
