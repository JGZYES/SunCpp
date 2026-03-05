import sys
import os
import subprocess
import shutil
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QMenuBar, QMenu,
    QFileDialog, QToolBar, QStatusBar, QMessageBox, QTreeView,
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QHeaderView, QTabWidget,
    QCompleter, QLabel
)
from PyQt6.QtGui import (
    QFont, QSyntaxHighlighter, QTextCharFormat, QColor, QIcon, QAction,
    QFileSystemModel, QTextCursor, QPixmap
)
from PyQt6.QtCore import Qt, QRegularExpression, QModelIndex, QStringListModel

# 导入内置编译器和插件系统
from sunc_compiler import SunCCompiler
from plugin_system import PluginManager
from code_minimap import CodeMinimap
from code_folding import CodeFoldingWidget
from find_replace import FindReplaceWidget
from keybindings import KeyBindingManager, KeyBindingDialog
from git_integration import GitIntegration, GitDialog


class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent, language):
        super().__init__(parent)
        self.language = language
        self.highlighting_rules = []
        self.setup_rules()
    
    def setup_rules(self):
        # 关键字颜色（更亮的蓝色）
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor('#0066FF'))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        # 字符串颜色（更亮的绿色）
        string_format = QTextCharFormat()
        string_format.setForeground(QColor('#00AA00'))
        
        # 注释颜色（更亮的灰色）
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor('#A0A0A0'))
        
        # 数字颜色（更亮的橙红色）
        number_format = QTextCharFormat()
        number_format.setForeground(QColor('#FF6600'))
        
        # 操作符颜色（更亮的橙色）
        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor('#FF9933'))
        
        # 数据类型颜色（更亮的绿色）
        datatype_format = QTextCharFormat()
        datatype_format.setForeground(QColor('#3CB371'))
        datatype_format.setFontWeight(QFont.Weight.Bold)
        
        # 转义字符颜色（更亮的紫色）
        escape_format = QTextCharFormat()
        escape_format.setForeground(QColor('#EE82EE'))
        
        # 模板颜色（更亮的深红色）
        template_format = QTextCharFormat()
        template_format.setForeground(QColor('#CD5C5C'))
        
        # Lambda表达式
        lambda_format = QTextCharFormat()
        lambda_format.setForeground(QColor('#BA55D3'))
        lambda_format.setFontWeight(QFont.Weight.Bold)
        
        # 指针和引用（更亮的棕色）
        pointer_format = QTextCharFormat()
        pointer_format.setForeground(QColor('#DEB887'))
        
        # 位运算符（更亮的栗色）
        bitwise_format = QTextCharFormat()
        bitwise_format.setForeground(QColor('#A52A2A'))
        
        # 初始化多行注释相关属性
        self.multi_comment_start = QRegularExpression(r'/\*')
        self.multi_comment_end = QRegularExpression(r'\*/')
        self.multi_comment_format = comment_format
        
        # Markdown 特殊格式
        md_header_format = QTextCharFormat()
        md_header_format.setForeground(QColor('#800080'))
        md_header_format.setFontWeight(QFont.Weight.Bold)
        
        md_bold_format = QTextCharFormat()
        md_bold_format.setFontWeight(QFont.Weight.Bold)
        
        md_italic_format = QTextCharFormat()
        md_italic_format.setFontItalic(True)
        
        md_code_format = QTextCharFormat()
        md_code_format.setForeground(QColor('#008080'))
        md_code_format.setFontFamily('Consolas')
        
        md_link_format = QTextCharFormat()
        md_link_format.setForeground(QColor('#0000FF'))
        md_link_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
        
        # C/C++/C# 关键字
        c_keywords = [
            'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
            'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
            'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static',
            'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while'
        ]
        
        # C++ 关键字
        cpp_keywords = [
            'bool', 'catch', 'class', 'const_cast', 'delete', 'dynamic_cast',
            'explicit', 'export', 'false', 'friend', 'inline', 'mutable', 'namespace',
            'new', 'operator', 'private', 'protected', 'public', 'reinterpret_cast',
            'static_cast', 'template', 'this', 'throw', 'true', 'try', 'typeid',
            'typename', 'using', 'virtual', 'wchar_t'
        ]
        
        # C# 关键字
        csharp_keywords = [
            'abstract', 'as', 'base', 'bool', 'break', 'byte', 'case', 'catch',
            'char', 'checked', 'class', 'const', 'continue', 'decimal', 'default',
            'delegate', 'do', 'double', 'else', 'enum', 'event', 'explicit',
            'extern', 'false', 'finally', 'fixed', 'float', 'for', 'foreach',
            'goto', 'if', 'implicit', 'in', 'int', 'interface', 'internal',
            'is', 'lock', 'long', 'namespace', 'new', 'null', 'object', 'operator',
            'out', 'override', 'params', 'private', 'protected', 'public', 'readonly',
            'ref', 'return', 'sbyte', 'sealed', 'short', 'sizeof', 'stackalloc', 'static',
            'string', 'struct', 'switch', 'this', 'throw', 'true', 'try', 'typeof',
            'uint', 'ulong', 'unchecked', 'unsafe', 'ushort', 'using', 'virtual',
            'void', 'volatile', 'while'
        ]
        
        # 如果是 Markdown 语言
        if self.language == 'markdown':
            # Markdown 标题
            for i in range(1, 7):
                pattern = QRegularExpression(r'^' + r'#' * i + r'\s+.*$')
                self.highlighting_rules.append((pattern, md_header_format))
            
            # Markdown 粗体
            pattern = QRegularExpression(r'\*\*(.*?)\*\*')
            self.highlighting_rules.append((pattern, md_bold_format))
            
            # Markdown 斜体
            pattern = QRegularExpression(r'\*(.*?)\*')
            self.highlighting_rules.append((pattern, md_italic_format))
            
            # Markdown 行内代码
            pattern = QRegularExpression(r'`(.*?)`')
            self.highlighting_rules.append((pattern, md_code_format))
            
            # Markdown 链接
            pattern = QRegularExpression(r'\[(.*?)\]\((.*?)\)')
            self.highlighting_rules.append((pattern, md_link_format))
            
            # Markdown 代码块
            pattern = QRegularExpression(r'```[\s\S]*?```')
            self.highlighting_rules.append((pattern, md_code_format))
            
            # Markdown 列表
            pattern = QRegularExpression(r'^\s*[-*+]\s+.*$')
            self.highlighting_rules.append((pattern, keyword_format))
            
            # Markdown 引用
            pattern = QRegularExpression(r'^>\s+.*$')
            self.highlighting_rules.append((pattern, comment_format))
        else:
            # 根据语言选择关键字
            keywords = c_keywords
            if self.language == 'cpp':
                keywords.extend(cpp_keywords)
            elif self.language == 'csharp':
                keywords = csharp_keywords
            
            # 添加关键字规则
            for keyword in keywords:
                pattern = QRegularExpression(r'\b' + keyword + r'\b')
                self.highlighting_rules.append((pattern, keyword_format))
            
            # 字符串规则
            string_pattern1 = QRegularExpression(r'"[^"]*"')
            string_pattern2 = QRegularExpression(r"'[^']*'")
            self.highlighting_rules.append((string_pattern1, string_format))
            self.highlighting_rules.append((string_pattern2, string_format))
            
            # 注释规则
            single_comment_pattern = QRegularExpression(r'//.*$')
            self.highlighting_rules.append((single_comment_pattern, comment_format))
            
            # 添加 # 注释支持
            hash_comment_pattern = QRegularExpression(r'#.*$')
            self.highlighting_rules.append((hash_comment_pattern, comment_format))
            
            # 数字规则
            number_pattern = QRegularExpression(r'\b\d+\.?\d*\b')
            self.highlighting_rules.append((number_pattern, number_format))
            
            # 操作符规则
            operator_pattern = QRegularExpression(r'[+\-*/%=!<>&|^~]')
            self.highlighting_rules.append((operator_pattern, operator_format))
            
            # 增加更多高亮规则
            # 预处理指令（更亮的橙红色）
            preprocessor_format = QTextCharFormat()
            preprocessor_format.setForeground(QColor('#FF6600'))
            preprocessor_format.setFontWeight(QFont.Weight.Bold)
            preprocessor_pattern = QRegularExpression(r'#\s*\w+')
            self.highlighting_rules.append((preprocessor_pattern, preprocessor_format))
            
            # 数据类型高亮
            data_types = [
                'int', 'char', 'float', 'double', 'long', 'short', 'void', 'bool',
                'signed', 'unsigned', 'const', 'static', 'volatile', 'extern', 'register',
                'int8_t', 'int16_t', 'int32_t', 'int64_t', 'uint8_t', 'uint16_t',
                'uint32_t', 'uint64_t', 'size_t', 'time_t', 'string', 'vector', 'list',
                'map', 'set', 'queue', 'stack', 'deque', 'array', 'tuple', 'pair'
            ]
            for dtype in data_types:
                pattern = QRegularExpression(r'\b' + dtype + r'\b')
                self.highlighting_rules.append((pattern, datatype_format))
            
            # 函数调用（更亮的蓝色）
            function_format = QTextCharFormat()
            function_format.setForeground(QColor('#4169E1'))
            function_pattern = QRegularExpression(r'\b\w+\s*\(')
            self.highlighting_rules.append((function_pattern, function_format))
            
            # 类名（更亮的紫色）
            class_format = QTextCharFormat()
            class_format.setForeground(QColor('#8A2BE2'))
            class_format.setFontWeight(QFont.Weight.Bold)
            class_pattern = QRegularExpression(r'\bclass\s+\w+')
            self.highlighting_rules.append((class_pattern, class_format))
            
            # 结构体名（更亮的紫色）
            struct_format = QTextCharFormat()
            struct_format.setForeground(QColor('#8A2BE2'))
            struct_format.setFontWeight(QFont.Weight.Bold)
            struct_pattern = QRegularExpression(r'\bstruct\s+\w+')
            self.highlighting_rules.append((struct_pattern, struct_format))
            
            # 枚举名（更亮的紫色）
            enum_format = QTextCharFormat()
            enum_format.setForeground(QColor('#8A2BE2'))
            enum_format.setFontWeight(QFont.Weight.Bold)
            enum_pattern = QRegularExpression(r'\benum\s+\w+')
            self.highlighting_rules.append((enum_pattern, enum_format))
            
            # 命名空间（更亮的绿色）
            namespace_format = QTextCharFormat()
            namespace_format.setForeground(QColor('#32CD32'))
            namespace_pattern = QRegularExpression(r'\bnamespace\s+\w+')
            self.highlighting_rules.append((namespace_pattern, namespace_format))
            
            # 转义字符
            escape_pattern = QRegularExpression(r'\\[ntr\\\"\\\'\\?\\a\\b\\f\\v\\0]')
            self.highlighting_rules.append((escape_pattern, escape_format))
            
            # 十六进制数字
            hex_pattern = QRegularExpression(r'\b0[xX][0-9a-fA-F]+\b')
            self.highlighting_rules.append((hex_pattern, number_format))
            
            # 八进制数字
            oct_pattern = QRegularExpression(r'\b0[0-7]+\b')
            self.highlighting_rules.append((oct_pattern, number_format))
            
            # 二进制数字
            bin_pattern = QRegularExpression(r'\b0[bB][01]+\b')
            self.highlighting_rules.append((bin_pattern, number_format))
            
            # 模板
            template_pattern = QRegularExpression(r'<[^<>]*>')
            self.highlighting_rules.append((template_pattern, template_format))
            
            # Lambda表达式
            lambda_pattern = QRegularExpression(r'\[\s*\]\s*\([^)]*\)\s*->?')
            self.highlighting_rules.append((lambda_pattern, lambda_format))
            
            # 指针和引用
            pointer_pattern = QRegularExpression(r'[*&](?!\w)')
            self.highlighting_rules.append((pointer_pattern, pointer_format))
            
            # 位运算符
            bitwise_pattern = QRegularExpression(r'[&|^~](?![&|])')
            self.highlighting_rules.append((bitwise_pattern, bitwise_format))
            
            # 访问修饰符（更亮的紫色）
            access_format = QTextCharFormat()
            access_format.setForeground(QColor('#9932CC'))
            access_format.setFontWeight(QFont.Weight.Bold)
            access_keywords = ['public', 'private', 'protected', 'internal', 'protected internal']
            for keyword in access_keywords:
                pattern = QRegularExpression(r'\b' + keyword + r'\b')
                self.highlighting_rules.append((pattern, access_format))
    
    def highlightBlock(self, text):
        # 处理普通规则
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
        
        # 处理多行注释
        self.setCurrentBlockState(0)
        start_index = 0
        if self.previousBlockState() != 1:
            match = self.multi_comment_start.match(text)
            if match.hasMatch():
                start_index = match.capturedStart()
                end_match = self.multi_comment_end.match(text, start_index + 2)
                if end_match.hasMatch():
                    self.setFormat(start_index, end_match.capturedEnd() - start_index, self.multi_comment_format)
                else:
                    self.setFormat(start_index, len(text) - start_index, self.multi_comment_format)
                    self.setCurrentBlockState(1)
        else:
            end_match = self.multi_comment_end.match(text)
            if end_match.hasMatch():
                self.setFormat(0, end_match.capturedEnd(), self.multi_comment_format)
            else:
                self.setFormat(0, len(text), self.multi_comment_format)
                self.setCurrentBlockState(1)

class CodeEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self.language = 'c'
        self.completer = None
        self.keywords = {}
        self.main_window = parent
        self.folding_widget = None
        self.find_replace_widget = None
        self.init_ui()
        self.load_keywords()
        self.setup_autocomplete()
        self.setup_folding()
    
    def init_ui(self):
        # 设置字体
        font = QFont('Consolas', 12)
        self.setFont(font)
        # 设置Tab宽度
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))
        # 启用行号显示（简化版）
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        # 初始语法高亮
        self.highlighter = SyntaxHighlighter(self.document(), self.language)
        # 设置左边距，为折叠控件留出空间
        self.setViewportMargins(15, 0, 0, 0)
    
    def setup_folding(self):
        """设置代码折叠"""
        self.folding_widget = CodeFoldingWidget(self, self)
        self.folding_widget.move(0, 0)
        self.folding_widget.show()
    
    def resizeEvent(self, event):
        """调整大小时更新折叠控件"""
        super().resizeEvent(event)
        if self.folding_widget:
            self.folding_widget.setGeometry(0, 0, 15, self.height())
    
    def show_find_replace(self, replace=False):
        """显示搜索替换控件"""
        if not self.find_replace_widget:
            self.find_replace_widget = FindReplaceWidget(self, self)
            self.find_replace_widget.setGeometry(10, 10, self.width() - 20, 140)
            self.find_replace_widget.closed.connect(self.on_find_replace_closed)
        
        self.find_replace_widget.show()
        if replace:
            self.find_replace_widget.replace_input.setFocus()
        else:
            self.find_replace_widget.find_input.setFocus()
    
    def on_find_replace_closed(self):
        """搜索替换关闭时的处理"""
        self.setFocus()
    
    def toggle_fold(self):
        """切换当前区域折叠"""
        if self.folding_widget:
            cursor = self.textCursor()
            current_line = cursor.blockNumber()
            
            for start_line in self.folding_widget.fold_markers:
                if start_line <= current_line <= self.folding_widget.fold_markers[start_line]:
                    self.folding_widget.toggle_fold(start_line)
                    break
    
    def unfold_all(self):
        """展开所有折叠区域"""
        if self.folding_widget:
            self.folding_widget.unfold_all()
    
    def load_keywords(self):
        """从JSON文件加载关键词库"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        keywords_file = os.path.join(script_dir, 'keywords.json')
        
        try:
            with open(keywords_file, 'r', encoding='utf-8') as f:
                self.keywords = json.load(f)
        except Exception as e:
            print(f'加载关键词库失败: {str(e)}')
            self.keywords = {'c': [], 'cpp': [], 'csharp': []}
    
    def setup_autocomplete(self):
        # 连接文本输入事件
        self.textChanged.connect(self.handle_text_change)
        self.textChanged.connect(self.on_text_change)
        
        # 确保编辑器支持Ctrl+C复制
        from PyQt6.QtGui import QKeySequence, QShortcut
        copy_shortcut = QShortcut(QKeySequence('Ctrl+C'), self)
        copy_shortcut.activated.connect(self.copy)
        
        # 创建QCompleter
        self.update_completer()
    
    def on_text_change(self):
        """文本变化时触发插件事件"""
        if self.main_window and self.main_window.plugin_manager:
            self.main_window.plugin_manager.trigger_event('on_text_changed', self.toPlainText())
        
        
    
    def update_completer(self):
        """根据当前语言更新补全器"""
        # 获取当前语言的关键词列表
        keywords = self.keywords.get(self.language, [])
        
        # 创建字符串列表模型
        model = QStringListModel()
        model.setStringList(keywords)
        
        # 创建补全器
        if not self.completer:
            self.completer = QCompleter()
            self.completer.setWidget(self)
            self.completer.activated.connect(self.insert_completion)
        
        self.completer.setModel(model)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
    
    def insert_completion(self, text):
        """插入补全文本"""
        cursor = self.textCursor()
        completion_prefix = self.completer.completionPrefix()
        # 先删除原来输入的前缀
        cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, len(completion_prefix))
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, len(completion_prefix))
        cursor.removeSelectedText()
        # 然后插入完整的补全文本
        cursor.insertText(text)
        self.setTextCursor(cursor)
    
    def keyPressEvent(self, event):
        # 如果补全器弹出，处理特殊键
        if self.completer and self.completer.popup().isVisible():
            if event.key() in [Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Escape, Qt.Key.Key_Tab, Qt.Key.Key_Backtab]:
                event.ignore()
                return
        
        key = event.key()
        text = event.text()
        
        # 处理回车键，实现自动缩进
        if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            # 获取当前光标位置
            cursor = self.textCursor()
            # 获取当前行的文本
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
            current_line = cursor.selectedText()
            
            # 计算当前行的缩进
            indent = len(current_line) - len(current_line.lstrip())
            
            # 检查当前行是否以{结尾
            if current_line.rstrip().endswith('{'):
                # 插入换行和缩进
                super().keyPressEvent(event)
                # 添加四个空格的缩进
                self.insertPlainText(' ' * 4)
                return
            
            # 检查当前位置前面是否有未闭合的{
            # 获取光标前的文本
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
            text_before_cursor = cursor.selectedText()
            
            # 计算{}的数量
            open_braces = text_before_cursor.count('{')
            close_braces = text_before_cursor.count('}')
            
            if open_braces > close_braces:
                # 插入换行和缩进
                super().keyPressEvent(event)
                # 添加与当前行相同的缩进
                self.insertPlainText(' ' * indent)
                return
        
        # 处理自动补全
        if text == '{':
            self.insert_brackets('{', '}')
            return
        elif text == '(':
            self.insert_brackets('(', ')')
            return
        elif text == '[':
            self.insert_brackets('[', ']')
            return
        elif text == '"':
            self.insert_quotes('"')
            return
        elif text == "'":
            self.insert_quotes("'")
            return
        
        super().keyPressEvent(event)
        
        # 处理代码补全
        if self.completer:
            # 获取当前光标下的单词
            cursor = self.textCursor()
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            completion_prefix = cursor.selectedText()
            
            # 如果单词长度小于2，隐藏补全器
            if len(completion_prefix) < 2:
                self.completer.popup().hide()
                return
            
            # 如果前缀改变，更新补全器
            if completion_prefix != self.completer.completionPrefix():
                self.completer.setCompletionPrefix(completion_prefix)
                self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))
            
            # 显示补全器
            rect = self.cursorRect()
            rect.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(rect)
    
    def insert_brackets(self, open_bracket, close_bracket):
        cursor = self.textCursor()
        cursor.insertText(open_bracket + close_bracket)
        cursor.movePosition(cursor.MoveOperation.Left)
        self.setTextCursor(cursor)
    
    def insert_quotes(self, quote):
        cursor = self.textCursor()
        cursor.insertText(quote + quote)
        cursor.movePosition(cursor.MoveOperation.Left)
        self.setTextCursor(cursor)
    
    def handle_text_change(self):
        # 处理特殊格式，如 int main {
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.StartOfWord, cursor.MoveMode.KeepAnchor)
        word = cursor.selectedText()
        
        # 检查是否输入了 "main {"
        cursor.movePosition(cursor.MoveOperation.EndOfWord)
        if cursor.position() > 5:
            # 检查前几个字符
            cursor.movePosition(cursor.MoveOperation.Left, cursor.MoveMode.KeepAnchor, 6)
            text = cursor.selectedText()
            if text.strip() == "main{":
                # 格式化 main 函数
                self.format_main_function(cursor)
    
    def format_main_function(self, cursor):
        # 获取当前行
        cursor.movePosition(cursor.MoveOperation.StartOfLine)
        cursor.movePosition(cursor.MoveOperation.EndOfLine, cursor.MoveMode.KeepAnchor)
        line_text = cursor.selectedText()
        
        # 检查是否是 int main {
        if 'main' in line_text and '{' in line_text:
            # 替换为格式化的版本
            indent = ' ' * (len(line_text) - len(line_text.lstrip()))
            # 按照用户要求的格式：int main { 然后换行，再换行，最后是}
            formatted = indent + 'int main {' + '\n\n' + indent + '}'
            cursor.insertText(formatted)
            
            # 将光标移动到正确位置（两行之间）
            cursor.movePosition(cursor.MoveOperation.Up)
            self.setTextCursor(cursor)
    
    def set_language(self, language):
        self.language = language
        self.highlighter = SyntaxHighlighter(self.document(), language)
        self.update_completer()
    
    def open_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.setPlainText(content)
            self.current_file = file_path
            # 根据文件扩展名设置语言
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.c', '.h']:
                self.set_language('c')
            elif ext in ['.cpp', '.cc', '.cxx', '.hpp']:
                self.set_language('cpp')
            elif ext in ['.cs']:
                self.set_language('csharp')
            elif ext in ['.md']:
                self.set_language('markdown')
            
            # 触发文件打开事件
            if self.main_window and self.main_window.plugin_manager:
                self.main_window.plugin_manager.trigger_event('on_file_opened', file_path)
            
            return True
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法打开文件: {str(e)}')
            return False
    
    def save_file(self, file_path=None):
        if file_path is None:
            file_path = self.current_file
        if file_path is None:
            return self.save_as_file()
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.toPlainText())
            self.current_file = file_path
            
            # 触发文件保存事件
            if self.main_window and self.main_window.plugin_manager:
                self.main_window.plugin_manager.trigger_event('on_file_saved', file_path)
            
            return True
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法保存文件: {str(e)}')
            return False
    
    def save_as_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, '保存文件', '',
            'C Files (*.c *.h);;C++ Files (*.cpp *.cc *.cxx *.hpp);;C# Files (*.cs);;All Files (*)'
        )
        if file_path:
            return self.save_file(file_path)
        return False

class WelcomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        title_label = QLabel('SunC++ 编辑器')
        title_font = QFont('Arial', 32, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet('color: #ffffff;')
        layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel('C/C++/C# 轻量级开发环境')
        subtitle_font = QFont('Arial', 14)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet('color: #808080;')
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(30)
        
        # 功能介绍
        features_label = QLabel('主要功能：')
        features_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        features_label.setStyleSheet('color: #d4d4d4;')
        layout.addWidget(features_label)
        
        features = [
            '📝 语法高亮支持 C、C++、C#',
            '💡 智能代码补全',
            '⚡ 内置编译器（MinGW）',
            '🐛 实时编译和运行',
            '📁 文件树管理',
            '🎨 现代化的用户界面'
        ]
        
        for feature in features:
            feature_label = QLabel(feature)
            feature_label.setFont(QFont('Arial', 11))
            feature_label.setStyleSheet('color: #a0a0a0; padding: 5px 0;')
            layout.addWidget(feature_label)
        
        layout.addSpacing(20)
        
        # 提示信息
        hint_label = QLabel('点击「文件」菜单或使用快捷键开始编码！')
        hint_label.setFont(QFont('Arial', 11))
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_label.setStyleSheet('color: #606060;')
        layout.addWidget(hint_label)
        
        layout.addStretch()
        
        self.setLayout(layout)
        self.setStyleSheet('''
            QWidget {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #d4d4d4;
            }
        ''')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化内置编译器和插件系统
        self.compiler = SunCCompiler()
        self.plugin_manager = None
        self.welcome_tab_index = None
        self.key_manager = KeyBindingManager()
        self.git_integration = GitIntegration()
        self.init_ui()
        self.setup_shortcuts()
    
    def init_ui(self):
        self.setWindowTitle('SunC++ - C/C++/C# 编辑器')
        self.setGeometry(100, 100, 1200, 700)
        
        # 创建主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建水平分割器（文件树 | 编辑器和控制台）
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 先创建文件树容器（但不初始化内容）
        self.file_tree_container = QWidget()
        file_tree_layout = QVBoxLayout(self.file_tree_container)
        file_tree_layout.setContentsMargins(0, 0, 0, 0)
        file_tree_layout.setSpacing(0)
        self.file_tree_container.setStyleSheet('''
            QWidget {
                background-color: #252526;
                border: none;
            }
        ''')
        self.main_splitter.addWidget(self.file_tree_container)
        
        # 创建右侧垂直分割器（编辑器/Markdown视图 + 控制台）
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # 添加新增标签页按钮
        from PyQt6.QtWidgets import QToolButton
        add_button = QToolButton()
        add_button.setText('+')
        add_button.setToolTip('新增标签页')
        add_button.setStyleSheet('''
            QToolButton {
                border: none;
                padding: 2px 8px;
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
                color: #cccccc;
            }
            QToolButton:hover {
                background-color: #3c3c3c;
                color: #ffffff;
                border-radius: 3px;
            }
        ''')
        add_button.clicked.connect(self.new_file)
        self.tab_widget.setCornerWidget(add_button, Qt.Corner.TopRightCorner)
        
        right_splitter.addWidget(self.tab_widget)
        
        # 添加欢迎页面标签页
        self.add_welcome_tab()
        self.statusBar().showMessage('欢迎使用 SunC++')
        
        # 创建控制台（暗色系主题）
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMinimumHeight(200)
        # 启用文本选择功能，支持Ctrl+C复制
        self.console.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        # 暗色系样式
        self.console.setStyleSheet('''
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                font-family: Consolas, Monaco, monospace;
                font-size: 12px;
                padding: 5px;
            }
            QTextEdit::selection {
                background-color: #264f78;
                color: #ffffff;
            }
        ''')
        right_splitter.addWidget(self.console)
        
        # 设置右侧分割器比例
        right_splitter.setSizes([500, 200])
        
        self.main_splitter.addWidget(right_splitter)
        
        # 设置拉伸因子
        self.main_splitter.setStretchFactor(0, 1)  # 文件树
        self.main_splitter.setStretchFactor(1, 4)  # 编辑器区域
        
        # 设置主分割器比例（文件树占20%，编辑器占80%）
        self.main_splitter.setSizes([250, 950])
        
        # 连接编辑器文本变化信号
        # 编辑器文本变化信号已在add_new_tab方法中连接
        
        # 为控制台添加Ctrl+C复制快捷键
        from PyQt6.QtGui import QKeySequence, QShortcut
        copy_shortcut = QShortcut(QKeySequence('Ctrl+C'), self.console)
        copy_shortcut.activated.connect(self.console.copy)
        
        # 初始化文件树内容（在控制台创建之后）
        self.init_file_tree()
        
        main_layout.addWidget(self.main_splitter)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 创建状态栏
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage('就绪')
        
        # 初始化插件系统
        self.init_plugin_system()
    
    def init_plugin_system(self):
        """初始化插件系统"""
        self.plugin_manager = PluginManager(self)
        self.plugin_manager.load_all_plugins()
        
        # 添加插件菜单项
        self.add_plugin_menu_items()
        
        # 添加插件工具栏项
        self.add_plugin_toolbar_items()
    
    def add_plugin_menu_items(self):
        """添加插件菜单项"""
        menu_bar = self.menuBar()
        
        # 查找或创建插件菜单
        plugin_menu = None
        for action in menu_bar.actions():
            if action.text() == '插件':
                plugin_menu = action.menu()
                break
        
        if not plugin_menu:
            plugin_menu = menu_bar.addMenu('插件')
        
        # 添加分隔符
        plugin_menu.addSeparator()
        
        # 添加所有插件的菜单项
        for action_info in self.plugin_manager.get_all_menu_actions():
            action = QAction(action_info['text'], self)
            if 'tooltip' in action_info:
                action.setToolTip(action_info['tooltip'])
            if 'shortcut' in action_info:
                action.setShortcut(action_info['shortcut'])
            action.triggered.connect(action_info['callback'])
            plugin_menu.addAction(action)
    
    def add_plugin_toolbar_items(self):
        """添加插件工具栏项"""
        # 查找工具栏
        for child in self.children():
            from PyQt6.QtWidgets import QToolBar
            if isinstance(child, QToolBar):
                # 添加分隔符
                child.addSeparator()
                
                # 添加所有插件的工具栏项
                for action_info in self.plugin_manager.get_all_toolbar_actions():
                    action = QAction(action_info['text'], self)
                    if 'tooltip' in action_info:
                        action.setToolTip(action_info['tooltip'])
                    action.triggered.connect(action_info['callback'])
                    child.addAction(action)
                break
    
    def add_welcome_tab(self):
        """添加欢迎页面标签页"""
        welcome_page = WelcomePage()
        self.welcome_tab_index = self.tab_widget.addTab(welcome_page, '欢迎')
        self.tab_widget.setCurrentIndex(self.welcome_tab_index)
    
    def add_new_tab(self, file_path=None):
        """添加新标签页"""
        # 创建编辑器容器
        editor_container = QWidget()
        editor_layout = QVBoxLayout(editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        
        # 创建Markdown分割器（源代码 + 渲染结果）
        md_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 创建编辑器
        editor = CodeEditor(self)
        md_splitter.addWidget(editor)
        
        # 创建Markdown渲染视图
        md_viewer = QTextEdit()
        md_viewer.setReadOnly(True)
        md_viewer.setStyleSheet('''
            QTextEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #3c3c3c;
                font-family: Arial, sans-serif;
                font-size: 14px;
                padding: 20px;
            }
        ''')
        md_splitter.addWidget(md_viewer)
        
        # 默认隐藏Markdown渲染视图
        md_splitter.setSizes([1000, 0])
        
        editor_layout.addWidget(md_splitter)
        
        # 创建缩略图（浮动在编辑器容器上）
        minimap = CodeMinimap(editor_container)
        minimap.set_editor(editor)
        minimap.show()
        
        # 保存缩略图引用并设置resize事件处理
        editor_container.minimap = minimap
        editor_container.resizeEvent = lambda e: (
            minimap.update_position() if minimap else None
        )
        
        # 打开文件
        if file_path:
            if editor.open_file(file_path):
                tab_name = os.path.basename(file_path)
            else:
                tab_name = '未命名'
        else:
            tab_name = '未命名'
        
        # 添加标签页
        tab_index = self.tab_widget.addTab(editor_container, tab_name)
        self.tab_widget.setCurrentIndex(tab_index)
        
        # 连接编辑器文本变化信号
        editor.textChanged.connect(lambda: self.on_editor_text_changed(editor, md_viewer))
        
        # 触发文本变化事件，更新Markdown视图
        self.on_editor_text_changed(editor, md_viewer)
        
        return editor
    

    
    def close_tab(self, index):
        """关闭标签页"""
        # 不允许关闭欢迎标签页
        if index == self.welcome_tab_index and self.tab_widget.count() > 1:
            return
        
        self.tab_widget.removeTab(index)
        
        # 更新欢迎标签页索引
        if index < self.welcome_tab_index:
            self.welcome_tab_index -= 1
        
        # 如果关闭的是欢迎标签页且还有其他标签页，不做特殊处理
        # 如果所有标签页都被关闭了，重新添加欢迎标签页
        if self.tab_widget.count() == 0:
            self.add_welcome_tab()
            self.setWindowTitle('SunC++ - C/C++/C# 编辑器')
            self.statusBar().showMessage('欢迎使用 SunC++')
    
    def get_current_editor(self):
        """获取当前标签页的编辑器"""
        if self.tab_widget.count() > 0:
            current_widget = self.tab_widget.widget(self.tab_widget.currentIndex())
            if isinstance(current_widget, QSplitter):
                editor = current_widget.widget(0)
                if isinstance(editor, CodeEditor):
                    return editor
        return None
    
    def on_tab_changed(self, index):
        """标签页切换时的处理"""
        if index >= 0:
            # 获取当前标签页的编辑器
            current_widget = self.tab_widget.widget(index)
            if isinstance(current_widget, QSplitter):
                editor = current_widget.widget(0)
                if isinstance(editor, CodeEditor) and editor.current_file:
                    self.setWindowTitle(f'SunC++ - {os.path.basename(editor.current_file)}')
                    self.statusBar().showMessage(f'已打开: {editor.current_file}')
                else:
                    self.setWindowTitle('SunC++ - 未命名')
                    self.statusBar().showMessage('新建文件')
    
    def log(self, message):
        """在控制台输出信息"""
        from PyQt6.QtCore import QDateTime
        timestamp = QDateTime.currentDateTime().toString('HH:mm:ss')
        self.console.append(f'[{timestamp}] {message}')
        self.console.verticalScrollBar().setValue(self.console.verticalScrollBar().maximum())
    
    def init_file_tree(self):
        """初始化文件树内容（在控制台创建之后调用）"""
        # 获取文件树容器的布局
        file_tree_layout = self.file_tree_container.layout()
        
        # 创建文件系统模型
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath('')
        
        # 设置过滤器，只显示文件和文件夹
        from PyQt6.QtCore import QDir
        self.file_model.setFilter(
            QDir.Filter.Dirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot
        )
        
        # 创建树形视图
        self.file_tree = QTreeView()
        self.file_tree.setModel(self.file_model)
        self.file_tree.setAnimated(True)
        self.file_tree.setIndentation(20)
        self.file_tree.setSortingEnabled(True)
        
        # 设置文件树样式（VS Code风格）
        self.file_tree.setStyleSheet('''
            QTreeView {
                background-color: #252526;
                color: #cccccc;
                border: none;
                outline: none;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QTreeView::item {
                height: 22px;
                padding: 2px 5px;
                border: none;
            }
            QTreeView::item:hover {
                background-color: #2a2d2e;
            }
            QTreeView::item:selected {
                background-color: #37373d;
                color: #ffffff;
            }
            QTreeView::item:selected:active {
                background-color: #094771;
            }
            QTreeView::branch {
                background-color: transparent;
            }
            QTreeView::branch:has-siblings:!adjoins-item {
                border-image: url(none);
            }
            QTreeView::branch:has-siblings:adjoins-item {
                border-image: url(none);
            }
            QTreeView::branch:!has-children:!has-siblings:adjoins-item {
                border-image: url(none);
            }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                image: url(none);
            }
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                image: url(none);
            }
            QHeaderView::section {
                background-color: #252526;
                color: #cccccc;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
        ''')
        
        # 隐藏表头
        self.file_tree.header().hide()
        
        # 隐藏除了名称列之外的其他列
        for i in range(1, self.file_model.columnCount()):
            self.file_tree.hideColumn(i)
        
        # 连接双击事件
        self.file_tree.doubleClicked.connect(self.on_file_tree_double_clicked)
        
        # 添加文件树到布局
        file_tree_layout.addWidget(self.file_tree)
        
        # 设置文件树宽度
        self.file_tree_container.setMinimumWidth(200)
        self.file_tree_container.setMaximumWidth(400)
        
        # 初始化根路径为当前工作目录
        self.set_file_tree_root(os.getcwd())
    
    def set_file_tree_root(self, path):
        """设置文件树的根目录"""
        if os.path.exists(path) and os.path.isdir(path):
            self.file_model.setRootPath(path)
            root_index = self.file_model.index(path)
            self.file_tree.setRootIndex(root_index)
            self.current_project_path = path
            self.log(f'打开文件夹: {path}')
    
    def is_binary_file(self, file_path):
        """检测文件是否为二进制文件"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                # 检查是否包含非ASCII字符
                if b'\x00' in chunk:
                    return True
                # 检查非文本字符的比例
                non_text = sum(1 for byte in chunk if byte < 32 and byte not in b'\t\n\r\f\v')
                return non_text > len(chunk) * 0.3
        except:
            return False

    def open_binary_file(self, file_path):
        """以二进制浏览器打开文件"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # 创建二进制查看器
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f'二进制查看器 - {os.path.basename(file_path)}')
            dialog.setGeometry(100, 100, 800, 600)
            
            layout = QVBoxLayout()
            
            # 十六进制显示
            hex_edit = QTextEdit()
            hex_edit.setReadOnly(True)
            hex_edit.setStyleSheet('background-color: #252526; color: #cccccc; font-family: Consolas, monospace;')
            
            # 生成十六进制视图
            hex_lines = []
            for i in range(0, len(content), 16):
                chunk = content[i:i+16]
                hex_part = ' '.join(f'{b:02x}' for b in chunk)
                ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
                hex_lines.append(f'{i:08x}: {hex_part:<48} | {ascii_part}')
            
            hex_edit.setPlainText('\n'.join(hex_lines))
            layout.addWidget(hex_edit)
            
            # 按钮
            button_layout = QHBoxLayout()
            close_btn = QPushButton('关闭')
            close_btn.clicked.connect(dialog.close)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            layout.addLayout(button_layout)
            
            dialog.setLayout(layout)
            dialog.exec()
            
            self.log(f'以二进制方式打开文件: {file_path}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法打开二进制文件: {str(e)}')

    def open_markdown_file(self, file_path):
        """以Markdown渲染窗口打开文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建Markdown渲染窗口
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QSplitter
            from PyQt6.QtCore import Qt
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f'Markdown预览 - {os.path.basename(file_path)}')
            dialog.setGeometry(100, 100, 1000, 700)
            
            layout = QVBoxLayout()
            
            # 创建分割器，左边显示源代码，右边显示渲染结果
            splitter = QSplitter(Qt.Orientation.Horizontal)
            
            # 源代码编辑器
            source_edit = QTextEdit()
            source_edit.setPlainText(content)
            source_edit.setReadOnly(True)
            source_edit.setStyleSheet('background-color: #252526; color: #cccccc; font-family: Consolas, monospace;')
            
            # 渲染结果
            render_edit = QTextEdit()
            render_edit.setReadOnly(True)
            render_edit.setStyleSheet('background-color: #ffffff; color: #000000; font-family: Arial, sans-serif;')
            
            # 简单的Markdown渲染
            def render_markdown(text):
                # 替换标题
                text = text.replace('# ', '<h1>').replace('</h1>', '</h1>')
                text = text.replace('## ', '<h2>').replace('</h2>', '</h2>')
                text = text.replace('### ', '<h3>').replace('</h3>', '</h3>')
                # 替换粗体
                text = text.replace('**', '<strong>').replace('**', '</strong>')
                # 替换斜体
                text = text.replace('*', '<em>').replace('*', '</em>')
                # 替换代码块
                text = text.replace('```', '<pre><code>').replace('```', '</code></pre>')
                # 替换行内代码
                text = text.replace('`', '<code>').replace('`', '</code>')
                # 替换链接
                import re
                text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
                # 替换换行
                text = text.replace('\n', '<br>')
                return text
            
            # 渲染Markdown
            html_content = render_markdown(content)
            render_edit.setHtml(f'<html><body style="padding: 20px;">{html_content}</body></html>')
            
            splitter.addWidget(source_edit)
            splitter.addWidget(render_edit)
            splitter.setSizes([500, 500])
            
            layout.addWidget(splitter)
            
            # 按钮
            button_layout = QHBoxLayout()
            close_btn = QPushButton('关闭')
            close_btn.clicked.connect(dialog.close)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            layout.addLayout(button_layout)
            
            dialog.setLayout(layout)
            dialog.exec()
            
            self.log(f'以Markdown方式打开文件: {file_path}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法打开Markdown文件: {str(e)}')

    def on_file_tree_double_clicked(self, index):
        """处理文件树双击事件"""
        file_path = self.file_model.filePath(index)
        if os.path.isfile(file_path):
            # 检查是否是二进制文件
            if self.is_binary_file(file_path):
                self.open_binary_file(file_path)
            else:
                # 创建新标签页并打开文件
                editor = self.add_new_tab(file_path)
                self.log(f'打开文件: {file_path}')
    
    def create_menu_bar(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)
        
        # 文件菜单
        file_menu = QMenu('文件', self)
        menu_bar.addMenu(file_menu)
        
        # 新建
        new_action = QAction('新建', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        # 打开文件
        open_action = QAction('打开文件', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # 打开文件夹
        open_folder_action = QAction('打开文件夹', self)
        open_folder_action.setShortcut('Ctrl+K')
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        # 保存
        save_action = QAction('保存', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        # 另存为
        save_as_action = QAction('另存为', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = QMenu('编辑', self)
        menu_bar.addMenu(edit_menu)
        
        # 复制
        copy_action = QAction('复制', self)
        copy_action.setShortcut('Ctrl+C')
        copy_action.triggered.connect(lambda: self.get_current_editor().copy() if self.get_current_editor() else None)
        edit_menu.addAction(copy_action)
        
        # 剪切
        cut_action = QAction('剪切', self)
        cut_action.setShortcut('Ctrl+X')
        cut_action.triggered.connect(lambda: self.get_current_editor().cut() if self.get_current_editor() else None)
        edit_menu.addAction(cut_action)
        
        # 粘贴
        paste_action = QAction('粘贴', self)
        paste_action.setShortcut('Ctrl+V')
        paste_action.triggered.connect(lambda: self.get_current_editor().paste() if self.get_current_editor() else None)
        edit_menu.addAction(paste_action)
        
        # 全选
        select_all_action = QAction('全选', self)
        select_all_action.setShortcut('Ctrl+A')
        select_all_action.triggered.connect(lambda: self.get_current_editor().selectAll() if self.get_current_editor() else None)
        edit_menu.addAction(select_all_action)
        
        edit_menu.addSeparator()
        
        # 查找
        find_action = QAction('查找', self)
        find_action.setShortcut('Ctrl+F')
        find_action.triggered.connect(self.show_find)
        edit_menu.addAction(find_action)
        
        # 替换
        replace_action = QAction('替换', self)
        replace_action.setShortcut('Ctrl+H')
        replace_action.triggered.connect(self.show_replace)
        edit_menu.addAction(replace_action)
        
        edit_menu.addSeparator()
        
        # 代码折叠
        fold_action = QAction('折叠/展开', self)
        fold_action.setShortcut('Ctrl+Shift+[')
        fold_action.triggered.connect(self.toggle_fold_current)
        edit_menu.addAction(fold_action)
        
        unfold_all_action = QAction('展开所有', self)
        unfold_all_action.setShortcut('Ctrl+K Ctrl+J')
        unfold_all_action.triggered.connect(self.unfold_all)
        edit_menu.addAction(unfold_all_action)
        
        # 语言菜单
        lang_menu = QMenu('语言', self)
        menu_bar.addMenu(lang_menu)
        
        # C语言
        c_action = QAction('C', self)
        c_action.triggered.connect(lambda: self.get_current_editor().set_language('c') if self.get_current_editor() else None)
        lang_menu.addAction(c_action)
        
        # C++语言
        cpp_action = QAction('C++', self)
        cpp_action.triggered.connect(lambda: self.get_current_editor().set_language('cpp') if self.get_current_editor() else None)
        lang_menu.addAction(cpp_action)
        
        # C#语言
        csharp_action = QAction('C#', self)
        csharp_action.triggered.connect(lambda: self.get_current_editor().set_language('csharp') if self.get_current_editor() else None)
        lang_menu.addAction(csharp_action)
        
        # 运行菜单
        run_menu = QMenu('运行', self)
        menu_bar.addMenu(run_menu)
        
        # 编译
        compile_action = QAction('编译', self)
        compile_action.setShortcut('F7')
        compile_action.triggered.connect(self.compile_code)
        run_menu.addAction(compile_action)
        
        # 运行
        run_action = QAction('运行', self)
        run_action.setShortcut('F5')
        run_action.triggered.connect(self.run_code)
        run_menu.addAction(run_action)
        
        # 编译并运行
        compile_run_action = QAction('编译并运行', self)
        compile_run_action.setShortcut('F9')
        compile_run_action.triggered.connect(self.compile_and_run)
        run_menu.addAction(compile_run_action)
        
        # Git菜单
        git_menu = QMenu('Git', self)
        menu_bar.addMenu(git_menu)
        
        # Git对话框
        git_action = QAction('Git版本控制', self)
        git_action.setShortcut('Ctrl+G')
        git_action.triggered.connect(self.show_git_dialog)
        git_menu.addAction(git_action)
        
        # 设置菜单
        settings_menu = QMenu('设置', self)
        menu_bar.addMenu(settings_menu)
        
        # 快捷键设置
        keybinding_action = QAction('快捷键设置', self)
        keybinding_action.triggered.connect(self.show_keybinding_dialog)
        settings_menu.addAction(keybinding_action)
        
        # 帮助菜单
        help_menu = QMenu('帮助', self)
        menu_bar.addMenu(help_menu)
        
        # 关于
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_tool_bar(self):
        tool_bar = QToolBar('工具栏', self)
        self.addToolBar(tool_bar)
        
        # 新建
        new_action = QAction('新建', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_file)
        tool_bar.addAction(new_action)
        
        # 打开
        open_action = QAction('打开', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        tool_bar.addAction(open_action)
        
        # 保存
        save_action = QAction('保存', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        tool_bar.addAction(save_action)
        
        # 分隔符
        tool_bar.addSeparator()
        
        # 复制
        copy_action = QAction('复制', self)
        copy_action.setShortcut('Ctrl+C')
        copy_action.triggered.connect(lambda: self.get_current_editor().copy() if self.get_current_editor() else None)
        tool_bar.addAction(copy_action)
        
        # 粘贴
        paste_action = QAction('粘贴', self)
        paste_action.setShortcut('Ctrl+V')
        paste_action.triggered.connect(lambda: self.get_current_editor().paste() if self.get_current_editor() else None)
        tool_bar.addAction(paste_action)
    
    def setup_shortcuts(self):
        """设置快捷键"""
        from PyQt6.QtGui import QShortcut, QKeySequence
        
        # 新建文件
        new_shortcut = QShortcut(QKeySequence(self.key_manager.get_shortcut('new_file')), self)
        new_shortcut.activated.connect(self.new_file)
        
        # 打开文件
        open_shortcut = QShortcut(QKeySequence(self.key_manager.get_shortcut('open_file')), self)
        open_shortcut.activated.connect(self.open_file)
        
        # 保存文件
        save_shortcut = QShortcut(QKeySequence(self.key_manager.get_shortcut('save_file')), self)
        save_shortcut.activated.connect(self.save_file)
        
        # 查找
        find_shortcut = QShortcut(QKeySequence(self.key_manager.get_shortcut('find')), self)
        find_shortcut.activated.connect(self.show_find)
        
        # 替换
        replace_shortcut = QShortcut(QKeySequence(self.key_manager.get_shortcut('replace')), self)
        replace_shortcut.activated.connect(self.show_replace)
        
        # 折叠
        fold_shortcut = QShortcut(QKeySequence(self.key_manager.get_shortcut('fold_region')), self)
        fold_shortcut.activated.connect(self.toggle_fold_current)
        
        # 展开所有
        unfold_shortcut = QShortcut(QKeySequence(self.key_manager.get_shortcut('unfold_all')), self)
        unfold_shortcut.activated.connect(self.unfold_all)
    
    def new_file(self):
        """新建文件"""
        # 创建新标签页
        self.add_new_tab()
        self.log('新建文件')
    
    def render_markdown(self, text):
        """渲染Markdown为HTML"""
        try:
            import markdown
            # 使用markdown库渲染
            html = markdown.markdown(text)
            return html
        except ImportError:
            # 如果没有安装markdown库，使用简单的替代方案
            # 替换标题
            text = text.replace('# ', '<h1>').replace('</h1>', '</h1>')
            text = text.replace('## ', '<h2>').replace('</h2>', '</h2>')
            text = text.replace('### ', '<h3>').replace('</h3>', '</h3>')
            # 替换粗体
            text = text.replace('**', '<strong>').replace('**', '</strong>')
            # 替换斜体
            text = text.replace('*', '<em>').replace('*', '</em>')
            # 替换代码块
            text = text.replace('```', '<pre><code>').replace('```', '</code></pre>')
            # 替换行内代码
            text = text.replace('`', '<code>').replace('`', '</code>')
            # 替换链接
            import re
            text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
            # 替换列表
            text = re.sub(r'^\s*[-*+]\s+(.*)$', r'<li>\1</li>', text, flags=re.MULTILINE)
            text = text.replace('</li>\n<li>', '</li><li>')
            text = text.replace('<li>', '<ul><li>', 1)
            text = text.replace('</li>', '</li></ul>', text.count('</li>') - 1)
            # 替换引用
            text = re.sub(r'^>\s+(.*)$', r'<blockquote>\1</blockquote>', text, flags=re.MULTILINE)
            # 替换换行
            text = text.replace('\n', '<br>')
            return text

    def on_editor_text_changed(self, editor, md_viewer):
        """编辑器文本变化时的处理"""
        # 检查当前文件是否是Markdown文件
        if editor.current_file and os.path.splitext(editor.current_file)[1].lower() == '.md':
            # 显示Markdown渲染视图
            splitter = editor.parent()
            if isinstance(splitter, QSplitter):
                splitter.setSizes([500, 500])
                # 渲染Markdown
                content = editor.toPlainText()
                html_content = self.render_markdown(content)
                md_viewer.setHtml(f'<html><body style="padding: 20px;">{html_content}</body></html>')
        else:
            # 隐藏Markdown渲染视图
            splitter = editor.parent()
            if isinstance(splitter, QSplitter):
                splitter.setSizes([1000, 0])

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, '打开文件', '',
            'C Files (*.c *.h);;C++ Files (*.cpp *.cc *.cxx *.hpp);;C# Files (*.cs);;Markdown Files (*.md);;ZIP Files (*.zip);;All Files (*)'
        )
        if file_path:
            # 检查是否是ZIP文件
            if file_path.lower().endswith('.zip'):
                self.add_new_tab(file_path)
                self.log(f'打开ZIP文件: {file_path}')
            # 检查是否是二进制文件
            elif self.is_binary_file(file_path):
                self.open_binary_file(file_path)
            else:
                # 创建新标签页并打开文件
                editor = self.add_new_tab(file_path)
                self.log(f'打开文件: {file_path}')
    
    def open_folder(self):
        """打开文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self, '打开文件夹', '',
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        if folder_path:
            self.set_file_tree_root(folder_path)
            self.statusBar().showMessage(f'已打开文件夹: {folder_path}')
    
    def save_file(self):
        editor = self.get_current_editor()
        if editor and editor.save_file():
            self.setWindowTitle(f'SunC++ - {os.path.basename(editor.current_file)}')
            self.statusBar().showMessage('文件已保存')
    
    def save_as_file(self):
        editor = self.get_current_editor()
        if editor and editor.save_as_file():
            self.setWindowTitle(f'SunC++ - {os.path.basename(editor.current_file)}')
            self.statusBar().showMessage('文件已保存')
    
    def show_about(self):
        QMessageBox.about(
            self, '关于 SunC++',
            'SunC++ 1.0\n\nC/C++/C# 编辑器\n使用 PyQt6 开发\n\n© 2026 SunC++'
        )
    
    def show_find(self):
        """显示查找对话框"""
        editor = self.get_current_editor()
        if editor:
            editor.show_find_replace(replace=False)
    
    def show_replace(self):
        """显示替换对话框"""
        editor = self.get_current_editor()
        if editor:
            editor.show_find_replace(replace=True)
    
    def toggle_fold_current(self):
        """切换当前代码折叠"""
        editor = self.get_current_editor()
        if editor:
            editor.toggle_fold()
    
    def unfold_all(self):
        """展开所有折叠"""
        editor = self.get_current_editor()
        if editor:
            editor.unfold_all()
    
    def show_git_dialog(self):
        """显示Git对话框"""
        # 更新Git项目路径
        current_editor = self.get_current_editor()
        if current_editor and current_editor.current_file:
            project_path = os.path.dirname(current_editor.current_file)
            self.git_integration.set_project_path(project_path)
        
        dialog = GitDialog(self.git_integration, self)
        dialog.exec()
    
    def show_keybinding_dialog(self):
        """显示快捷键设置对话框"""
        dialog = KeyBindingDialog(self.key_manager, self)
        dialog.exec()
    
    def compile_code(self):
        """编译代码"""
        editor = self.get_current_editor()
        if not editor or not editor.current_file:
            QMessageBox.warning(self, '警告', '请先保存文件')
            return
        
        file_path = editor.current_file
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.c', '.cpp', '.cc', '.cxx', '.hpp']:
            # C/C++ 编译
            self.compile_cpp(file_path)
        elif ext in ['.cs']:
            # C# 编译
            self.compile_csharp(file_path)
        else:
            QMessageBox.warning(self, '警告', '不支持的文件类型')
    
    def compile_cpp(self, file_path):
        """编译C++代码"""
        import subprocess
        import tempfile
        
        # 生成输出文件名
        output_file = os.path.splitext(file_path)[0] + '.exe'
        
        # 编译命令（使用 MinGW g++ 或 Visual Studio cl）
        compiler = self.find_compiler()
        if not compiler:
            self.log('错误: 未找到 C++ 编译器，请安装 MinGW 或 Visual Studio')
            self.statusBar().showMessage('编译失败')
            return
        
        try:
            # 构建编译命令
            if 'g++' in compiler:
                cmd = [compiler, file_path, '-o', output_file]
            elif 'cl' in compiler:
                cmd = [compiler, file_path, '/Fe' + output_file]
            else:
                self.log('错误: 不支持的编译器')
                self.statusBar().showMessage('编译失败')
                return
            
            self.log(f'开始编译: {file_path}')
            
            # 执行编译
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(file_path))
            
            if result.returncode == 0:
                self.log(f'编译成功: {output_file}')
                self.statusBar().showMessage(f'编译成功: {output_file}')
            else:
                error_msg = result.stderr or result.stdout
                self.log(f'编译失败:\n{error_msg}')
                self.statusBar().showMessage('编译失败')
                
        except Exception as e:
            self.log(f'编译过程中出错: {str(e)}')
            self.statusBar().showMessage('编译失败')
    
    def compile_csharp(self, file_path):
        """编译C#代码"""
        import subprocess
        
        # 生成输出文件名
        output_file = os.path.splitext(file_path)[0] + '.exe'
        
        # 查找 csc 编译器
        csc_path = self.find_csharp_compiler()
        if not csc_path:
            self.log('错误: 未找到 C# 编译器，请安装 .NET SDK')
            self.statusBar().showMessage('编译失败')
            return
        
        try:
            # 构建编译命令
            cmd = [csc_path, file_path, '/out:' + output_file]
            
            self.log(f'开始编译: {file_path}')
            
            # 执行编译
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(file_path))
            
            if result.returncode == 0:
                self.log(f'编译成功: {output_file}')
                self.statusBar().showMessage(f'编译成功: {output_file}')
            else:
                error_msg = result.stderr or result.stdout
                self.log(f'编译失败:\n{error_msg}')
                self.statusBar().showMessage('编译失败')
                
        except Exception as e:
            self.log(f'编译过程中出错: {str(e)}')
            self.statusBar().showMessage('编译失败')
    
    def run_code(self):
        """运行代码"""
        editor = self.get_current_editor()
        if not editor or not editor.current_file:
            QMessageBox.warning(self, '警告', '请先保存文件')
            return
        
        file_path = editor.current_file
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.c', '.cpp', '.cc', '.cxx', '.hpp', '.cs']:
            # 运行编译后的程序
            exe_file = os.path.splitext(file_path)[0] + '.exe'
            if os.path.exists(exe_file):
                self.run_exe(exe_file)
            else:
                QMessageBox.warning(self, '警告', '未找到可执行文件，请先编译')
                self.compile_code()
        else:
            QMessageBox.warning(self, '警告', '不支持的文件类型')

    def compile_and_run(self):
        """编译并运行代码"""
        editor = self.get_current_editor()
        if not editor or not editor.current_file:
            QMessageBox.warning(self, '警告', '请先保存文件')
            return
        
        file_path = editor.current_file
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.c', '.cpp', '.cc', '.cxx', '.hpp']:
            success = self.compile_cpp_and_check(file_path)
            if success:
                exe_file = os.path.splitext(file_path)[0] + '.exe'
                if os.path.exists(exe_file):
                    self.run_exe(exe_file)
            return success
        elif ext in ['.cs']:
            success = self.compile_csharp_and_check(file_path)
            if success:
                exe_file = os.path.splitext(file_path)[0] + '.exe'
                if os.path.exists(exe_file):
                    self.run_exe(exe_file)
            return success
        else:
            QMessageBox.warning(self, '警告', '不支持的文件类型')
            return False
    
    def compile_cpp_and_check(self, file_path):
        """编译C++代码并返回是否成功"""
        import os
        import subprocess
        
        output_file = os.path.splitext(file_path)[0] + '.exe'
        
        self.log(f'开始编译: {file_path}')
        
        # 直接使用mingw64/bin/g++.exe
        script_dir = os.path.dirname(os.path.abspath(__file__))
        compiler_path = os.path.join(script_dir, 'mingw64', 'bin', 'g++.exe')
        
        if not os.path.exists(compiler_path):
            self.log(f'错误: 未找到编译器: {compiler_path}')
            self.statusBar().showMessage('编译失败')
            return False
        
        self.log(f'使用编译器: {compiler_path}')
        
        try:
            # 构建编译命令，使用列表形式，避免shell转义问题
            cmd = [compiler_path, file_path, '-o', output_file]
            self.log(f'编译命令: {" ".join(cmd)}')
            
            # 执行编译，不使用shell，直接传递列表
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(file_path)
            )
            
            self.log(f'编译退出代码: {result.returncode}')
            if result.stdout:
                self.log(f'编译标准输出:\n{result.stdout}')
            if result.stderr:
                self.log(f'编译标准错误:\n{result.stderr}')
            
            if result.returncode == 0:
                if os.path.exists(output_file):
                    self.log(f'编译成功: {output_file}')
                    self.statusBar().showMessage(f'编译成功: {output_file}')
                    return True
                else:
                    self.log('错误: 编译退出代码为0，但未生成可执行文件')
                    self.statusBar().showMessage('编译失败')
                    return False
            else:
                self.log('编译失败')
                self.statusBar().showMessage('编译失败')
                return False
                
        except Exception as e:
            self.log(f'编译过程中出错: {str(e)}')
            self.statusBar().showMessage('编译失败')
            return False
    
    def compile_csharp_and_check(self, file_path):
        """编译C#代码并返回是否成功"""
        import subprocess
        
        output_file = os.path.splitext(file_path)[0] + '.exe'
        csc_path = self.find_csharp_compiler()
        
        if not csc_path:
            self.log('错误: 未找到 C# 编译器，请安装 .NET SDK')
            self.statusBar().showMessage('编译失败')
            return False
        
        try:
            cmd = [csc_path, file_path, '/out:' + output_file]
            self.log(f'开始编译: {file_path}')
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(file_path))
            
            if result.returncode == 0:
                self.log(f'编译成功: {output_file}')
                self.statusBar().showMessage(f'编译成功: {output_file}')
                return True
            else:
                error_msg = result.stderr or result.stdout
                self.log(f'编译失败:\n{error_msg}')
                self.statusBar().showMessage('编译失败')
                return False
                
        except Exception as e:
            self.log(f'编译过程中出错: {str(e)}')
            self.statusBar().showMessage('编译失败')
            return False
    
    def run_exe(self, exe_path):
        """运行可执行文件"""
        import subprocess
        import sys
        
        try:
            # 运行程序
            self.statusBar().showMessage(f'运行: {exe_path}')
            self.log(f'开始运行: {exe_path}')
            
            # 执行程序并捕获输出，使用text=False以捕获所有输出
            result = subprocess.run(
                [exe_path],
                capture_output=True,
                text=False,
                cwd=os.path.dirname(exe_path)
            )
            
            # 处理输出编码
            stdout = ''
            stderr = ''
            try:
                stdout = result.stdout.decode('gbk')
            except UnicodeDecodeError:
                try:
                    stdout = result.stdout.decode('utf-8')
                except UnicodeDecodeError:
                    stdout = str(result.stdout)
            
            try:
                stderr = result.stderr.decode('gbk')
            except UnicodeDecodeError:
                try:
                    stderr = result.stderr.decode('utf-8')
                except UnicodeDecodeError:
                    stderr = str(result.stderr)
            
            # 在控制台显示输出
            self.log(f'退出代码: {result.returncode}')
            if stdout:
                self.log(f'标准输出:\n{stdout}')
            if stderr:
                self.log(f'标准错误:\n{stderr}')
            
            self.statusBar().showMessage('运行完成')
            
        except Exception as e:
            self.log(f'运行过程中出错: {str(e)}')
            self.statusBar().showMessage('运行失败')
    
    def find_compiler(self):
        """查找C++编译器"""
        import os
        import subprocess
        
        # 首先检查 SunC++ 目录下的 MinGW
        script_dir = os.path.dirname(os.path.abspath(__file__))
        local_mingw_paths = [
            os.path.join(script_dir, 'mingw64', 'bin', 'g++.exe'),
            os.path.join(script_dir, 'mingw64', 'bin', 'gcc.exe'),
            os.path.join(script_dir, 'MinGW', 'bin', 'g++.exe'),
            os.path.join(script_dir, 'MinGW', 'bin', 'gcc.exe'),
            os.path.join(script_dir, 'mingw32', 'bin', 'g++.exe'),
        ]
        
        for path in local_mingw_paths:
            if os.path.exists(path):
                self.log(f'找到编译器: {path}')
                return path
        
        # 查找 MinGW g++
        mingw_paths = [
            r'C:\MinGW\bin\g++.exe',
            r'C:\MinGW64\bin\g++.exe',
            r'C:\msys64\mingw64\bin\g++.exe',
            r'C:\msys64\mingw32\bin\g++.exe',
            r'C:\Program Files\MinGW\bin\g++.exe',
            r'C:\Program Files (x86)\MinGW\bin\g++.exe',
            r'C:\Program Files\mingw-w64\x86_64-8.1.0-posix-seh-rt_v6-rev0\mingw64\bin\g++.exe',
            r'C:\Program Files (x86)\mingw-w64\i686-8.1.0-posix-dwarf-rt_v6-rev0\mingw32\bin\g++.exe'
        ]
        
        for path in mingw_paths:
            if os.path.exists(path):
                self.log(f'找到编译器: {path}')
                return path
        
        # 查找 Visual Studio cl.exe
        vs_paths = [
            r'C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.36.32532\bin\Hostx64\x64\cl.exe',
            r'C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\MSVC\14.36.32532\bin\Hostx64\x64\cl.exe',
            r'C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Tools\MSVC\14.36.32532\bin\Hostx64\x64\cl.exe',
            r'C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64\cl.exe',
            r'C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64\cl.exe',
            r'C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64\cl.exe'
        ]
        
        for path in vs_paths:
            if os.path.exists(path):
                self.log(f'找到编译器: {path}')
                return path
        
        # 检查系统PATH
        try:
            result = subprocess.run(['where', 'g++'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                # 过滤掉空字符串
                lines = [line.strip() for line in lines if line.strip()]
                if lines:
                    self.log(f'找到编译器: {lines[0]}')
                    return lines[0]
        except Exception as e:
            self.log(f'查找g++时出错: {str(e)}')
        
        try:
            result = subprocess.run(['where', 'cl'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                # 过滤掉空字符串
                lines = [line.strip() for line in lines if line.strip()]
                if lines:
                    self.log(f'找到编译器: {lines[0]}')
                    return lines[0]
        except Exception as e:
            self.log(f'查找cl时出错: {str(e)}')
        
        self.log('错误: 未找到C++编译器')
        return None
    
    def find_csharp_compiler(self):
        """查找C#编译器"""
        import os
        import subprocess
        
        # 查找 csc.exe
        csc_paths = [
            r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe',
            r'C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe'
        ]
        
        for path in csc_paths:
            if os.path.exists(path):
                return path
        
        # 检查系统PATH
        try:
            result = subprocess.run(['where', 'csc'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                # 过滤掉空字符串
                lines = [line.strip() for line in lines if line.strip()]
                if lines:
                    return lines[0]
        except:
            pass
        
        return None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
