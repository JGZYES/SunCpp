from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QFont, QPen


class CodeMinimap(QWidget):
    """代码缩略图控件 - VSCode风格，覆盖在编辑器右上角"""
    
    clicked = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.editor = None
        self.visible_area_ratio = 0.0
        self.visible_area_start = 0.0
        self.setFixedWidth(100)
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_minimap)
        self.setMouseTracking(True)
        
        self.hover = False
        self.mini_font = QFont('Consolas', 2)
        self.line_height = 3
    
    def set_editor(self, editor):
        """设置关联的编辑器"""
        self.editor = editor
        if self.editor:
            self.editor.verticalScrollBar().valueChanged.connect(self.on_scroll)
            self.editor.textChanged.connect(self.schedule_update)
            self.update_minimap()
    
    def update_position(self):
        """更新缩略图位置到编辑器右上角"""
        if self.parent():
            parent_rect = self.parent().rect()
            x = parent_rect.width() - self.width() - 5
            y = 5
            
            if self.editor:
                doc = self.editor.document()
                line_count = doc.blockCount()
                total_height = line_count * self.line_height + 10
                
                available_height = parent_rect.height() - 10
                display_height = min(total_height, available_height)
            else:
                display_height = parent_rect.height() - 10
            
            self.setGeometry(x, y, self.width(), display_height)
            self.raise_()
    
    def showEvent(self, event):
        """显示时更新位置"""
        super().showEvent(event)
        self.update_position()
    
    def schedule_update(self):
        """延迟更新缩略图"""
        self.update_timer.start(100)
    
    def update_minimap(self):
        """更新缩略图"""
        if self.editor:
            self.update()
            self.update_position()
    
    def on_scroll(self):
        """滚动时更新可见区域"""
        if self.editor:
            scrollbar = self.editor.verticalScrollBar()
            if scrollbar.maximum() > 0:
                self.visible_area_start = scrollbar.value() / scrollbar.maximum()
                self.visible_area_ratio = scrollbar.pageStep() / (scrollbar.maximum() + scrollbar.pageStep())
            else:
                self.visible_area_start = 0.0
                self.visible_area_ratio = 1.0
            self.update()
    
    def paintEvent(self, event):
        """绘制缩略图"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        bg_alpha = 220 if self.hover else 200
        painter.fillRect(0, 0, width, height, QColor(40, 40, 40, bg_alpha))
        
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.drawLine(0, 0, 0, height)
        
        if not self.editor:
            return
        
        doc = self.editor.document()
        if not doc:
            return
        
        painter.setFont(self.mini_font)
        
        block = doc.begin()
        y = 3
        
        while block.isValid():
            text = block.text()
            if text.strip():
                if text.strip().startswith('#'):
                    color = QColor(255, 128, 0, 200)
                elif text.strip().startswith('//') or text.strip().startswith('/*'):
                    color = QColor(128, 128, 128, 200)
                elif any(kw in text for kw in ['int ', 'void ', 'return', 'if ', 'else', 'for ', 'while ', 'class ', 'struct ']):
                    color = QColor(86, 156, 214, 200)
                elif 'string' in text or '"' in text or "'" in text:
                    color = QColor(206, 145, 120, 200)
                else:
                    color = QColor(180, 180, 180, 200)
                
                painter.setPen(color)
                display_text = text[:50] if len(text) > 50 else text
                painter.drawText(2, y + self.line_height - 1, display_text)
            
            y += self.line_height
            if y > height - 5:
                break
            
            block = block.next()
        
        visible_area_height = max(20, height * self.visible_area_ratio)
        visible_area_y = height * self.visible_area_start
        
        painter.fillRect(0, int(visible_area_y), width, int(visible_area_height), 
                        QColor(80, 80, 80, 100))
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.drawRect(0, int(visible_area_y), width - 1, int(visible_area_height))
    
    def mousePressEvent(self, event):
        """鼠标点击跳转"""
        if self.editor and event.button() == Qt.MouseButton.LeftButton:
            scrollbar = self.editor.verticalScrollBar()
            click_ratio = event.position().y() / self.height()
            target_value = int(click_ratio * scrollbar.maximum())
            scrollbar.setValue(target_value)
    
    def mouseMoveEvent(self, event):
        """鼠标移动时显示手型光标"""
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def enterEvent(self, event):
        """鼠标进入时"""
        self.hover = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开时"""
        self.hover = False
        self.update()
        super().leaveEvent(event)
