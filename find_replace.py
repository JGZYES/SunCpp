from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QLabel, QCheckBox, QComboBox,
    QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat


class FindReplaceWidget(QFrame):
    """搜索替换控件"""
    
    closed = pyqtSignal()
    
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.current_find = None
        self.init_ui()
        self.setStyleSheet('''
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
                border-radius: 3px;
            }
            QLineEdit {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #094771;
            }
            QCheckBox {
                color: #d4d4d4;
            }
            QLabel {
                color: #d4d4d4;
            }
        ''')
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 搜索行
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel('查找:'))
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText('输入要查找的内容...')
        self.find_input.textChanged.connect(self.on_find_text_changed)
        self.find_input.returnPressed.connect(self.find_next)
        find_layout.addWidget(self.find_input)
        
        # 查找按钮
        self.find_prev_btn = QPushButton('上一个')
        self.find_prev_btn.clicked.connect(self.find_previous)
        find_layout.addWidget(self.find_prev_btn)
        
        self.find_next_btn = QPushButton('下一个')
        self.find_next_btn.clicked.connect(self.find_next)
        find_layout.addWidget(self.find_next_btn)
        
        layout.addLayout(find_layout)
        
        # 替换行
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel('替换:'))
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText('输入替换内容...')
        self.replace_input.returnPressed.connect(self.replace_current)
        replace_layout.addWidget(self.replace_input)
        
        # 替换按钮
        self.replace_btn = QPushButton('替换')
        self.replace_btn.clicked.connect(self.replace_current)
        replace_layout.addWidget(self.replace_btn)
        
        self.replace_all_btn = QPushButton('全部替换')
        self.replace_all_btn.clicked.connect(self.replace_all)
        replace_layout.addWidget(self.replace_all_btn)
        
        layout.addLayout(replace_layout)
        
        # 选项行
        options_layout = QHBoxLayout()
        
        self.case_sensitive = QCheckBox('区分大小写')
        options_layout.addWidget(self.case_sensitive)
        
        self.whole_word = QCheckBox('全词匹配')
        options_layout.addWidget(self.whole_word)
        
        self.use_regex = QCheckBox('正则表达式')
        options_layout.addWidget(self.use_regex)
        
        options_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton('✕')
        close_btn.setFixedSize(25, 25)
        close_btn.clicked.connect(self.close_widget)
        options_layout.addWidget(close_btn)
        
        layout.addLayout(options_layout)
        
        # 状态标签
        self.status_label = QLabel('')
        self.status_label.setStyleSheet('color: #808080;')
        layout.addWidget(self.status_label)
    
    def showEvent(self, event):
        """显示时聚焦到搜索框"""
        super().showEvent(event)
        self.find_input.setFocus()
        self.find_input.selectAll()
    
    def close_widget(self):
        """关闭搜索替换控件"""
        self.hide()
        self.closed.emit()
        if self.editor:
            self.editor.setFocus()
    
    def on_find_text_changed(self, text):
        """搜索文本变化时高亮"""
        if text and self.editor:
            self.find_next()
        else:
            self.clear_highlight()
            self.status_label.setText('')
    
    def find_next(self):
        """查找下一个"""
        if not self.editor:
            return
        
        text = self.find_input.text()
        if not text:
            return
        
        cursor = self.editor.textCursor()
        document = self.editor.document()
        
        # 搜索选项
        flags = QTextDocument.FindFlag(0)
        if self.case_sensitive.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if self.whole_word.isChecked():
            flags |= QTextDocument.FindFlag.FindWholeWords
        
        # 从当前位置开始搜索
        cursor.movePosition(QTextCursor.MoveOperation.Right)
        new_cursor = document.find(text, cursor, flags)
        
        if new_cursor.isNull():
            # 从头开始搜索
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            new_cursor = document.find(text, cursor, flags)
        
        if not new_cursor.isNull():
            self.editor.setTextCursor(new_cursor)
            self.highlight_match(new_cursor)
            self.status_label.setText('')
        else:
            self.status_label.setText('未找到匹配项')
            self.status_label.setStyleSheet('color: #f44336;')
    
    def find_previous(self):
        """查找上一个"""
        if not self.editor:
            return
        
        text = self.find_input.text()
        if not text:
            return
        
        cursor = self.editor.textCursor()
        document = self.editor.document()
        
        # 搜索选项
        flags = QTextDocument.FindFlag.FindBackward
        if self.case_sensitive.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if self.whole_word.isChecked():
            flags |= QTextDocument.FindFlag.FindWholeWords
        
        # 从当前位置开始搜索
        cursor.movePosition(QTextCursor.MoveOperation.Left)
        new_cursor = document.find(text, cursor, flags)
        
        if new_cursor.isNull():
            # 从末尾开始搜索
            cursor.movePosition(QTextCursor.MoveOperation.End)
            new_cursor = document.find(text, cursor, flags)
        
        if not new_cursor.isNull():
            self.editor.setTextCursor(new_cursor)
            self.highlight_match(new_cursor)
            self.status_label.setText('')
        else:
            self.status_label.setText('未找到匹配项')
            self.status_label.setStyleSheet('color: #f44336;')
    
    def replace_current(self):
        """替换当前匹配项"""
        if not self.editor:
            return
        
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            replace_text = self.replace_input.text()
            cursor.insertText(replace_text)
            self.find_next()
    
    def replace_all(self):
        """替换所有匹配项"""
        if not self.editor:
            return
        
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()
        
        if not find_text:
            return
        
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        
        count = 0
        while True:
            cursor = self.editor.document().find(find_text, cursor)
            if cursor.isNull():
                break
            cursor.insertText(replace_text)
            count += 1
        
        cursor.endEditBlock()
        self.status_label.setText(f'已替换 {count} 处')
        self.status_label.setStyleSheet('color: #4caf50;')
    
    def highlight_match(self, cursor):
        """高亮匹配项"""
        if not cursor.hasSelection():
            return
        
        # 使用额外选择来高亮
        extra_selections = []
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor(255, 255, 0, 100))
        selection.format.setForeground(QColor(0, 0, 0))
        selection.cursor = cursor
        extra_selections.append(selection)
        
        self.editor.setExtraSelections(extra_selections)
    
    def clear_highlight(self):
        """清除高亮"""
        if self.editor:
            self.editor.setExtraSelections([])
