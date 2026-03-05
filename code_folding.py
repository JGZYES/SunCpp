from PyQt6.QtWidgets import QWidget, QTextEdit
from PyQt6.QtCore import Qt, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QFont, QMouseEvent, QTextCursor
import re


class CodeFoldingWidget(QWidget):
    """代码折叠控件"""
    
    folding_changed = pyqtSignal()
    
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setFixedWidth(15)
        self.folded_regions = {}  # 存储折叠区域 {开始行: 结束行}
        self.fold_markers = {}  # 存储可折叠的行号
        
        # 监听编辑器滚动
        if self.editor:
            self.editor.verticalScrollBar().valueChanged.connect(self.update)
            self.editor.textChanged.connect(self.update_fold_markers)
    
    def update_fold_markers(self):
        """更新可折叠标记"""
        if not self.editor:
            return
        
        self.fold_markers = {}
        text = self.editor.toPlainText()
        lines = text.split('\n')
        
        stack = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 检测代码块开始
            if stripped.endswith('{') and not stripped.startswith('//'):
                stack.append(i)
            # 检测代码块结束
            elif stripped == '}' and stack:
                start_line = stack.pop()
                self.fold_markers[start_line] = i
        
        self.update()
    
    def paintEvent(self, event):
        """绘制折叠标记"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 背景
        painter.fillRect(self.rect(), QColor(45, 45, 45))
        
        if not self.editor:
            return
        
        # 获取可见区域
        viewport = self.editor.viewport()
        doc = self.editor.document()
        
        # 绘制可折叠标记
        painter.setPen(QColor(128, 128, 128))
        painter.setBrush(QColor(80, 80, 80))
        
        for start_line in self.fold_markers:
            block = doc.findBlockByNumber(start_line)
            if block.isValid():
                cursor = QTextCursor(block)
                rect = self.editor.cursorRect(cursor)
                y = rect.y() + rect.height() // 2
                
                if 0 <= y <= self.height():
                    # 绘制折叠图标
                    if start_line in self.folded_regions:
                        # 已折叠，绘制展开图标
                        painter.drawRect(2, y - 4, 10, 8)
                        painter.setPen(QColor(255, 255, 255))
                        painter.drawLine(5, y, 9, y)
                        painter.drawLine(7, y - 2, 7, y + 2)
                    else:
                        # 未折叠，绘制折叠图标
                        painter.drawRect(2, y - 4, 10, 8)
                        painter.setPen(QColor(255, 255, 255))
                        painter.drawLine(5, y, 9, y)
                    
                    painter.setPen(QColor(128, 128, 128))
    
    def mousePressEvent(self, event: QMouseEvent):
        """处理鼠标点击折叠"""
        if not self.editor:
            return
        
        click_y = event.pos().y()
        doc = self.editor.document()
        
        for start_line in self.fold_markers:
            block = doc.findBlockByNumber(start_line)
            if block.isValid():
                cursor = QTextCursor(block)
                rect = self.editor.cursorRect(cursor)
                y = rect.y() + rect.height() // 2
                
                if abs(click_y - y) < 8:
                    self.toggle_fold(start_line)
                    break
    
    def toggle_fold(self, start_line):
        """切换折叠状态"""
        if start_line in self.folded_regions:
            self.unfold_region(start_line)
        else:
            self.fold_region(start_line)
        self.folding_changed.emit()
    
    def fold_region(self, start_line):
        """折叠代码区域"""
        if start_line not in self.fold_markers:
            return
        
        end_line = self.fold_markers[start_line]
        self.folded_regions[start_line] = end_line
        
        # 隐藏折叠的文本
        doc = self.editor.document()
        start_block = doc.findBlockByNumber(start_line + 1)
        end_block = doc.findBlockByNumber(end_line)
        
        if start_block.isValid() and end_block.isValid():
            cursor = QTextCursor(start_block)
            cursor.setPosition(end_block.position() + end_block.length(), QTextCursor.MoveMode.KeepAnchor)
            
            # 使用字符格式来隐藏文本
            char_format = cursor.charFormat()
            char_format.setForeground(QColor(0, 0, 0, 0))
            cursor.mergeCharFormat(char_format)
        
        self.update()
    
    def unfold_region(self, start_line):
        """展开代码区域"""
        if start_line not in self.folded_regions:
            return
        
        end_line = self.folded_regions.pop(start_line)
        
        # 恢复隐藏的文本
        doc = self.editor.document()
        start_block = doc.findBlockByNumber(start_line + 1)
        end_block = doc.findBlockByNumber(end_line)
        
        if start_block.isValid() and end_block.isValid():
            cursor = QTextCursor(start_block)
            cursor.setPosition(end_block.position() + end_block.length(), QTextCursor.MoveMode.KeepAnchor)
            
            # 恢复字符格式
            char_format = cursor.charFormat()
            char_format.clearForeground()
            cursor.setCharFormat(char_format)
        
        self.update()
    
    def unfold_all(self):
        """展开所有折叠区域"""
        folded_lines = list(self.folded_regions.keys())
        for start_line in folded_lines:
            self.unfold_region(start_line)


class FoldableCodeEditor(QTextEdit):
    """支持代码折叠的编辑器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.folding_widget = None
        self.setup_folding()
    
    def setup_folding(self):
        """设置代码折叠"""
        # 创建折叠控件
        self.folding_widget = CodeFoldingWidget(self, self)
        self.folding_widget.move(0, 0)
        self.folding_widget.show()
        
        # 监听文本变化
        self.textChanged.connect(self.on_text_changed)
    
    def on_text_changed(self):
        """文本变化时更新折叠标记"""
        if self.folding_widget:
            self.folding_widget.update_fold_markers()
    
    def resizeEvent(self, event):
        """调整大小时更新折叠控件"""
        super().resizeEvent(event)
        if self.folding_widget:
            self.folding_widget.setGeometry(0, 0, 15, self.height())
    
    def fold_current_region(self):
        """折叠当前区域"""
        if not self.folding_widget:
            return
        
        cursor = self.textCursor()
        current_line = cursor.blockNumber()
        
        # 查找当前行是否在可折叠区域
        for start_line in self.folding_widget.fold_markers:
            if start_line <= current_line <= self.folding_widget.fold_markers[start_line]:
                self.folding_widget.fold_region(start_line)
                break
    
    def unfold_current_region(self):
        """展开当前区域"""
        if not self.folding_widget:
            return
        
        cursor = self.textCursor()
        current_line = cursor.blockNumber()
        
        # 查找当前行是否在折叠区域
        for start_line in list(self.folding_widget.folded_regions.keys()):
            if start_line <= current_line <= self.folding_widget.folded_regions[start_line]:
                self.folding_widget.unfold_region(start_line)
                break
    
    def unfold_all(self):
        """展开所有区域"""
        if self.folding_widget:
            self.folding_widget.unfold_all()
