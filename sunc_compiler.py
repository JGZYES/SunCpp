"""
SunC++ 内置编译器系统
支持 C、C++、C# 语言的编译和运行
模仿 Dev-C++ 的实现方式
"""

import os
import sys
import subprocess
import shutil
import tempfile
from typing import Tuple, List, Dict, Optional
from enum import Enum, auto

class TokenType(Enum):
    """词法标记类型"""
    # 字面量
    INT_LITERAL = auto()
    FLOAT_LITERAL = auto()
    STRING_LITERAL = auto()
    CHAR_LITERAL = auto()
    BOOL_LITERAL = auto()
    
    # 标识符
    IDENTIFIER = auto()
    
    # 关键字 - C/C++
    INT = auto()
    FLOAT = auto()
    DOUBLE = auto()
    CHAR = auto()
    VOID = auto()
    BOOL = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    RETURN = auto()
    BREAK = auto()
    CONTINUE = auto()
    CLASS = auto()
    STRUCT = auto()
    PUBLIC = auto()
    PRIVATE = auto()
    PROTECTED = auto()
    CONST = auto()
    STATIC = auto()
    VIRTUAL = auto()
    NEW = auto()
    DELETE = auto()
    
    # 关键字 - C#
    NAMESPACE = auto()
    USING = auto()
    INTERFACE = auto()
    ABSTRACT = auto()
    SEALED = auto()
    OVERRIDE = auto()
    GET = auto()
    SET = auto()
    
    # 操作符
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    ASSIGN = auto()
    EQ = auto()
    NE = auto()
    LT = auto()
    GT = auto()
    LE = auto()
    GE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    INC = auto()
    DEC = auto()
    
    # 分隔符
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    SEMICOLON = auto()
    COMMA = auto()
    DOT = auto()
    COLON = auto()
    ARROW = auto()
    SCOPE = auto()
    
    # 预处理器
    PREPROC = auto()
    
    # 特殊
    EOF = auto()
    NEWLINE = auto()

class Token:
    """词法标记"""
    def __init__(self, type_: TokenType, value: str, line: int = 1, col: int = 1):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col
    
    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.col})"

class Lexer:
    """词法分析器 - 支持 C/C++/C#"""
    
    # C/C++ 关键字
    CPP_KEYWORDS = {
        'int': TokenType.INT,
        'float': TokenType.FLOAT,
        'double': TokenType.DOUBLE,
        'char': TokenType.CHAR,
        'void': TokenType.VOID,
        'bool': TokenType.BOOL,
        'if': TokenType.IF,
        'else': TokenType.ELSE,
        'while': TokenType.WHILE,
        'for': TokenType.FOR,
        'return': TokenType.RETURN,
        'break': TokenType.BREAK,
        'continue': TokenType.CONTINUE,
        'class': TokenType.CLASS,
        'struct': TokenType.STRUCT,
        'public': TokenType.PUBLIC,
        'private': TokenType.PRIVATE,
        'protected': TokenType.PROTECTED,
        'const': TokenType.CONST,
        'static': TokenType.STATIC,
        'virtual': TokenType.VIRTUAL,
        'new': TokenType.NEW,
        'delete': TokenType.DELETE,
        'true': TokenType.BOOL_LITERAL,
        'false': TokenType.BOOL_LITERAL,
        'nullptr': TokenType.IDENTIFIER,
        'NULL': TokenType.IDENTIFIER,
    }
    
    # C# 关键字
    CS_KEYWORDS = {
        'namespace': TokenType.NAMESPACE,
        'using': TokenType.USING,
        'interface': TokenType.INTERFACE,
        'abstract': TokenType.ABSTRACT,
        'sealed': TokenType.SEALED,
        'override': TokenType.OVERRIDE,
        'get': TokenType.GET,
        'set': TokenType.SET,
        'string': TokenType.IDENTIFIER,
        'object': TokenType.IDENTIFIER,
    }
    
    def __init__(self, source: str, language: str = 'cpp'):
        self.source = source
        self.language = language
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens = []
        
        # 合并关键字
        self.keywords = self.CPP_KEYWORDS.copy()
        if language == 'csharp':
            self.keywords.update(self.CS_KEYWORDS)
    
    def error(self, msg: str):
        raise SyntaxError(f"[{self.line}:{self.col}] {msg}")
    
    def peek(self, offset: int = 0) -> str:
        pos = self.pos + offset
        if pos >= len(self.source):
            return '\0'
        return self.source[pos]
    
    def advance(self) -> str:
        char = self.peek()
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return char
    
    def skip_whitespace(self):
        while self.peek() in ' \t\r':
            self.advance()
    
    def skip_comment(self):
        if self.peek() == '/' and self.peek(1) == '/':
            while self.peek() != '\n' and self.peek() != '\0':
                self.advance()
        elif self.peek() == '/' and self.peek(1) == '*':
            self.advance()
            self.advance()
            while not (self.peek() == '*' and self.peek(1) == '/'):
                if self.peek() == '\0':
                    self.error("未结束的块注释")
                self.advance()
            self.advance()
            self.advance()
    
    def read_string(self, quote: str) -> str:
        start_line, start_col = self.line, self.col
        self.advance()  # 跳过开头的引号
        result = []
        
        while self.peek() != quote:
            if self.peek() == '\0':
                self.error(f"未结束的字符串字面量")
            if self.peek() == '\\':
                self.advance()
                escape = self.advance()
                escape_chars = {
                    'n': '\n', 't': '\t', 'r': '\r',
                    '\\': '\\', '"': '"', "'": "'",
                    '0': '\0', 'a': '\a', 'b': '\b',
                    'f': '\f', 'v': '\v'
                }
                result.append(escape_chars.get(escape, escape))
            else:
                result.append(self.advance())
        
        self.advance()  # 跳过结尾的引号
        return ''.join(result)
    
    def read_number(self) -> Token:
        start_line, start_col = self.line, self.col
        num_str = []
        is_float = False
        
        # 处理十六进制
        if self.peek() == '0' and self.peek(1) in 'xX':
            num_str.append(self.advance())
            num_str.append(self.advance())
            while self.peek().isdigit() or self.peek() in 'abcdefABCDEF':
                num_str.append(self.advance())
            return Token(TokenType.INT_LITERAL, ''.join(num_str), start_line, start_col)
        
        # 处理八进制
        if self.peek() == '0' and self.peek(1).isdigit():
            while self.peek().isdigit():
                num_str.append(self.advance())
            return Token(TokenType.INT_LITERAL, ''.join(num_str), start_line, start_col)
        
        # 处理十进制
        while self.peek().isdigit():
            num_str.append(self.advance())
        
        if self.peek() == '.' and (self.peek(1).isdigit() or self.peek(1) in 'eE'):
            is_float = True
            num_str.append(self.advance())
            while self.peek().isdigit():
                num_str.append(self.advance())
        
        # 科学计数法
        if self.peek() in 'eE':
            is_float = True
            num_str.append(self.advance())
            if self.peek() in '+-':
                num_str.append(self.advance())
            while self.peek().isdigit():
                num_str.append(self.advance())
        
        # 后缀
        suffix = ''
        while self.peek() in 'fFlLuU':
            suffix += self.advance()
        
        value = ''.join(num_str)
        if is_float or 'f' in suffix.lower():
            return Token(TokenType.FLOAT_LITERAL, value + suffix, start_line, start_col)
        else:
            return Token(TokenType.INT_LITERAL, value + suffix, start_line, start_col)
    
    def read_identifier(self) -> Token:
        start_line, start_col = self.line, self.col
        ident = []
        
        while self.peek().isalnum() or self.peek() == '_':
            ident.append(self.advance())
        
        value = ''.join(ident)
        token_type = self.keywords.get(value, TokenType.IDENTIFIER)
        return Token(token_type, value, start_line, start_col)
    
    def read_preprocessor(self) -> Token:
        start_line, start_col = self.line, self.col
        self.advance()  # 跳过 #
        
        content = ['#']
        while self.peek() != '\n' and self.peek() != '\0':
            content.append(self.advance())
        
        return Token(TokenType.PREPROC, ''.join(content), start_line, start_col)
    
    def tokenize(self) -> List[Token]:
        while self.peek() != '\0':
            # 跳过空白
            self.skip_whitespace()
            
            # 跳过注释
            if self.peek() == '/' and self.peek(1) in '/*':
                self.skip_comment()
                continue
            
            if self.peek() == '\0':
                break
            
            start_line, start_col = self.line, self.col
            char = self.peek()
            
            # 换行
            if char == '\n':
                self.advance()
                self.tokens.append(Token(TokenType.NEWLINE, '\n', start_line, start_col))
            
            # 字符串
            elif char in '"\'':
                quote_type = TokenType.STRING_LITERAL if char == '"' else TokenType.CHAR_LITERAL
                self.tokens.append(Token(quote_type, self.read_string(char), start_line, start_col))
            
            # 数字
            elif char.isdigit():
                self.tokens.append(self.read_number())
            
            # 标识符/关键字
            elif char.isalpha() or char == '_':
                self.tokens.append(self.read_identifier())
            
            # 预处理器
            elif char == '#':
                self.tokens.append(self.read_preprocessor())
            
            # 操作符和分隔符
            elif char == '+':
                self.advance()
                if self.peek() == '+':
                    self.advance()
                    self.tokens.append(Token(TokenType.INC, '++', start_line, start_col))
                elif self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.ASSIGN, '+=', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.PLUS, '+', start_line, start_col))
            
            elif char == '-':
                self.advance()
                if self.peek() == '-':
                    self.advance()
                    self.tokens.append(Token(TokenType.DEC, '--', start_line, start_col))
                elif self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.ASSIGN, '-=', start_line, start_col))
                elif self.peek() == '>':
                    self.advance()
                    self.tokens.append(Token(TokenType.ARROW, '->', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.MINUS, '-', start_line, start_col))
            
            elif char == '*':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.ASSIGN, '*=', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.STAR, '*', start_line, start_col))
            
            elif char == '/':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.ASSIGN, '/=', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.SLASH, '/', start_line, start_col))
            
            elif char == '%':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.ASSIGN, '%=', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.PERCENT, '%', start_line, start_col))
            
            elif char == '=':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.EQ, '==', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.ASSIGN, '=', start_line, start_col))
            
            elif char == '!':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.NE, '!=', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.NOT, '!', start_line, start_col))
            
            elif char == '<':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.LE, '<=', start_line, start_col))
                elif self.peek() == '<':
                    self.advance()
                    self.tokens.append(Token(TokenType.ASSIGN, '<<=', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.LT, '<', start_line, start_col))
            
            elif char == '>':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.GE, '>=', start_line, start_col))
                elif self.peek() == '>':
                    self.advance()
                    self.tokens.append(Token(TokenType.ASSIGN, '>>=', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.GT, '>', start_line, start_col))
            
            elif char == '&':
                self.advance()
                if self.peek() == '&':
                    self.advance()
                    self.tokens.append(Token(TokenType.AND, '&&', start_line, start_col))
                elif self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.ASSIGN, '&=', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.IDENTIFIER, '&', start_line, start_col))
            
            elif char == '|':
                self.advance()
                if self.peek() == '|':
                    self.advance()
                    self.tokens.append(Token(TokenType.OR, '||', start_line, start_col))
                elif self.peek() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.ASSIGN, '|=', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.IDENTIFIER, '|', start_line, start_col))
            
            elif char == '(':
                self.advance()
                self.tokens.append(Token(TokenType.LPAREN, '(', start_line, start_col))
            
            elif char == ')':
                self.advance()
                self.tokens.append(Token(TokenType.RPAREN, ')', start_line, start_col))
            
            elif char == '{':
                self.advance()
                self.tokens.append(Token(TokenType.LBRACE, '{', start_line, start_col))
            
            elif char == '}':
                self.advance()
                self.tokens.append(Token(TokenType.RBRACE, '}', start_line, start_col))
            
            elif char == '[':
                self.advance()
                self.tokens.append(Token(TokenType.LBRACKET, '[', start_line, start_col))
            
            elif char == ']':
                self.advance()
                self.tokens.append(Token(TokenType.RBRACKET, ']', start_line, start_col))
            
            elif char == ';':
                self.advance()
                self.tokens.append(Token(TokenType.SEMICOLON, ';', start_line, start_col))
            
            elif char == ',':
                self.advance()
                self.tokens.append(Token(TokenType.COMMA, ',', start_line, start_col))
            
            elif char == '.':
                self.advance()
                self.tokens.append(Token(TokenType.DOT, '.', start_line, start_col))
            
            elif char == ':':
                self.advance()
                if self.peek() == ':':
                    self.advance()
                    self.tokens.append(Token(TokenType.SCOPE, '::', start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.COLON, ':', start_line, start_col))
            
            else:
                self.error(f"未知字符: {char!r}")
        
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        return self.tokens


class SunCCompiler:
    """
    SunC++ 编译器主类
    支持 C、C++、C# 语言的编译
    """
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.language = 'cpp'
    
    def detect_language(self, file_path: str) -> str:
        """根据文件扩展名检测语言"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.c']:
            return 'c'
        elif ext in ['.cpp', '.cc', '.cxx', '.hpp']:
            return 'cpp'
        elif ext in ['.cs']:
            return 'csharp'
        return 'cpp'
    
    def compile(self, source_file: str, output_file: str = None) -> Tuple[bool, str]:
        """
        编译源文件
        
        Args:
            source_file: 源文件路径
            output_file: 输出文件路径（可选）
        
        Returns:
            (成功标志, 输出信息)
        """
        if not os.path.exists(source_file):
            return False, f"错误: 找不到源文件 '{source_file}'"
        
        # 检测语言
        self.language = self.detect_language(source_file)
        
        if output_file is None:
            base = os.path.splitext(source_file)[0]
            output_file = base + '.exe'
        
        try:
            # 读取源文件
            with open(source_file, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            # 词法分析
            lexer = Lexer(source, self.language)
            tokens = lexer.tokenize()
            
            # 根据语言选择编译方式
            if self.language == 'csharp':
                return self.compile_csharp(source_file, output_file)
            else:
                return self.compile_cpp(source_file, output_file)
                
        except Exception as e:
            return False, f"编译错误: {str(e)}"
    
    def compile_cpp(self, source_file: str, output_file: str) -> Tuple[bool, str]:
        """编译 C/C++ 代码"""
        # 查找系统编译器
        compiler = self.find_cpp_compiler()
        if not compiler:
            return False, """错误: 未找到 C++ 编译器

请安装以下编译器之一:
1. MinGW-w64 (推荐)
   下载地址: https://www.mingw-w64.org/downloads/
   安装后添加到系统 PATH

2. Visual Studio
   下载地址: https://visualstudio.microsoft.com/
   安装 C++ 工作负载

3. MSYS2
   下载地址: https://www.msys2.org/
   安装后运行: pacman -S mingw-w64-x86_64-gcc
"""
        
        try:
            # 构建编译命令
            if 'cl' in compiler:
                # Visual Studio
                cmd = [compiler, '/EHsc', '/W3', source_file, f'/Fe{output_file}']
            else:
                # GCC/MinGW
                cmd = [compiler, '-std=c++17', '-Wall', '-o', output_file, source_file]
            
            # 执行编译，设置干净的环境变量以避免编译器冲突
            env = os.environ.copy()
            # 只保留 SunC++ 目录下的 MinGW 路径
            compiler_dir = os.path.dirname(compiler)
            env['PATH'] = compiler_dir + os.pathsep + env.get('PATH', '')
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                cwd=os.path.dirname(source_file) or '.',
                env=env
            )
            
            if result.returncode == 0:
                msg = f"编译成功: {output_file}"
                if result.stderr:
                    msg += f"\n警告:\n{result.stderr}"
                return True, msg
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                return False, f"编译失败:\n{error_msg}"
                
        except Exception as e:
            return False, f"编译过程中出错: {str(e)}"
    
    def compile_csharp(self, source_file: str, output_file: str) -> Tuple[bool, str]:
        """编译 C# 代码"""
        # 查找 C# 编译器
        compiler = self.find_csharp_compiler()
        if not compiler:
            return False, """错误: 未找到 C# 编译器

请安装以下之一:
1. .NET SDK (推荐)
   下载地址: https://dotnet.microsoft.com/download

2. Visual Studio
   下载地址: https://visualstudio.microsoft.com/
   安装 .NET 桌面开发工作负载
"""
        
        try:
            # 构建编译命令
            if 'dotnet' in compiler:
                # 使用 .NET CLI
                cmd = [compiler, 'build', source_file, '-o', os.path.dirname(output_file) or '.']
            else:
                # 使用 csc
                cmd = [compiler, source_file, f'/out:{output_file}']
            
            # 执行编译，设置干净的环境变量以避免编译器冲突
            env = os.environ.copy()
            # 只保留编译器所在目录的路径
            compiler_dir = os.path.dirname(compiler)
            env['PATH'] = compiler_dir + os.pathsep + env.get('PATH', '')
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                cwd=os.path.dirname(source_file) or '.',
                env=env
            )
            
            if result.returncode == 0:
                msg = f"编译成功: {output_file}"
                if result.stderr:
                    msg += f"\n警告:\n{result.stderr}"
                return True, msg
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                return False, f"编译失败:\n{error_msg}"
                
        except Exception as e:
            return False, f"编译过程中出错: {str(e)}"
    
    def find_cpp_compiler(self) -> Optional[str]:
        """查找 C++ 编译器"""
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
                return path
        
        for compiler in ['g++', 'clang++', 'cl']:
            path = shutil.which(compiler)
            if path:
                return path
        
        paths_to_check = [
            r'C:\mingw64\bin\g++.exe',
            r'C:\mingw32\bin\g++.exe',
            r'C:\MinGW\bin\g++.exe',
            r'C:\MinGW64\bin\g++.exe',
            r'C:\msys64\mingw64\bin\g++.exe',
            r'C:\msys64\mingw32\bin\g++.exe',
            r'C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.36.32532\bin\Hostx64\x64\cl.exe',
            r'C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\MSVC\14.36.32532\bin\Hostx64\x64\cl.exe',
            r'C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Tools\MSVC\14.36.32532\bin\Hostx64\x64\cl.exe',
            r'C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64\cl.exe',
            r'C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64\cl.exe',
            r'C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64\cl.exe',
        ]
        
        for path in paths_to_check:
            if os.path.exists(path):
                return path
        
        return None
    
    def find_csharp_compiler(self) -> Optional[str]:
        """查找 C# 编译器"""
        # 首先检查 .NET CLI
        dotnet = shutil.which('dotnet')
        if dotnet:
            return dotnet
        
        # 检查 csc
        csc = shutil.which('csc')
        if csc:
            return csc
        
        # 检查常见路径
        paths_to_check = [
            r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe',
            r'C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe',
        ]
        
        for path in paths_to_check:
            if os.path.exists(path):
                return path
        
        return None


# 便捷函数
def compile_file(source_file: str, output_file: str = None) -> Tuple[bool, str]:
    """编译文件的便捷函数"""
    compiler = SunCCompiler()
    return compiler.compile(source_file, output_file)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("SunC++ 编译器")
        print("用法: python sunc_compiler.py <源文件> [输出文件]")
        sys.exit(1)
    
    source = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None
    
    success, message = compile_file(source, output)
    print(message)
    sys.exit(0 if success else 1)
