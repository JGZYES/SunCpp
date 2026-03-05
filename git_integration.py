import subprocess
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QTextEdit, QSplitter, QTreeWidget, QTreeWidgetItem,
    QMenu, QMessageBox, QInputDialog, QComboBox, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont


class GitThread(QThread):
    """Git命令执行线程"""
    
    output_ready = pyqtSignal(str, bool)
    
    def __init__(self, command, cwd=None):
        super().__init__()
        self.command = command
        self.cwd = cwd
    
    def run(self):
        try:
            result = subprocess.run(
                self.command,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            output = result.stdout
            if result.stderr:
                output += '\n' + result.stderr
            
            self.output_ready.emit(output, result.returncode == 0)
        except Exception as e:
            self.output_ready.emit(f'错误: {str(e)}', False)


class GitIntegration:
    """Git集成管理器"""
    
    def __init__(self, project_path=None):
        self.project_path = project_path
    
    def set_project_path(self, path):
        """设置项目路径"""
        self.project_path = path
    
    def is_git_repo(self):
        """检查是否是Git仓库"""
        if not self.project_path:
            return False
        
        git_dir = os.path.join(self.project_path, '.git')
        return os.path.exists(git_dir)
    
    def execute_git_command(self, args):
        """执行Git命令"""
        if not self.project_path:
            return None, '未设置项目路径'
        
        command = ['git'] + args
        try:
            result = subprocess.run(
                command,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            return result.stdout, result.stderr if result.returncode != 0 else None
        except Exception as e:
            return None, str(e)
    
    def get_status(self):
        """获取Git状态"""
        return self.execute_git_command(['status', '--short'])
    
    def get_branches(self):
        """获取分支列表"""
        output, error = self.execute_git_command(['branch', '-a'])
        if error:
            return []
        
        branches = []
        for line in output.strip().split('\n'):
            line = line.strip()
            if line:
                # 移除*标记（当前分支）
                if line.startswith('*'):
                    line = line[1:].strip()
                branches.append(line)
        return branches
    
    def get_current_branch(self):
        """获取当前分支"""
        output, error = self.execute_git_command(['branch', '--show-current'])
        if error:
            return None
        return output.strip()
    
    def get_log(self, count=20):
        """获取提交历史"""
        return self.execute_git_command([
            'log', f'-{count}', 
            '--oneline', 
            '--graph', 
            '--decorate',
            '--all'
        ])
    
    def add_file(self, file_path):
        """添加文件到暂存区"""
        return self.execute_git_command(['add', file_path])
    
    def add_all(self):
        """添加所有更改"""
        return self.execute_git_command(['add', '.'])
    
    def commit(self, message):
        """提交更改"""
        return self.execute_git_command(['commit', '-m', message])
    
    def push(self, remote='origin', branch=None):
        """推送到远程"""
        if not branch:
            branch = self.get_current_branch()
        return self.execute_git_command(['push', remote, branch])
    
    def pull(self, remote='origin', branch=None):
        """从远程拉取"""
        if not branch:
            branch = self.get_current_branch()
        return self.execute_git_command(['pull', remote, branch])
    
    def checkout_branch(self, branch):
        """切换分支"""
        return self.execute_git_command(['checkout', branch])
    
    def create_branch(self, branch_name):
        """创建新分支"""
        return self.execute_git_command(['checkout', '-b', branch_name])
    
    def get_diff(self, file_path=None):
        """获取差异"""
        if file_path:
            return self.execute_git_command(['diff', file_path])
        return self.execute_git_command(['diff'])
    
    def stash(self, message=None):
        """暂存更改"""
        if message:
            return self.execute_git_command(['stash', 'push', '-m', message])
        return self.execute_git_command(['stash'])
    
    def stash_pop(self):
        """恢复暂存"""
        return self.execute_git_command(['stash', 'pop'])


class GitDialog(QDialog):
    """Git操作对话框"""
    
    def __init__(self, git_integration, parent=None):
        super().__init__(parent)
        self.git = git_integration
        self.init_ui()
        self.setStyleSheet('''
            QDialog {
                background-color: #1e1e1e;
            }
            QTreeWidget {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
            QTreeWidget::item:selected {
                background-color: #094771;
            }
            QListWidget {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                font-family: Consolas, monospace;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QLabel {
                color: #d4d4d4;
            }
            QComboBox {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: 1px solid #555555;
                padding: 5px;
            }
        ''')
    
    def init_ui(self):
        self.setWindowTitle('Git 版本控制')
        self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout(self)
        
        # 顶部信息栏
        info_layout = QHBoxLayout()
        
        self.branch_label = QLabel('当前分支: 未检测到')
        info_layout.addWidget(self.branch_label)
        
        info_layout.addStretch()
        
        # 分支选择
        info_layout.addWidget(QLabel('切换分支:'))
        self.branch_combo = QComboBox()
        self.branch_combo.setMinimumWidth(150)
        info_layout.addWidget(self.branch_combo)
        
        checkout_btn = QPushButton('切换')
        checkout_btn.clicked.connect(self.checkout_branch)
        info_layout.addWidget(checkout_btn)
        
        new_branch_btn = QPushButton('新建分支')
        new_branch_btn.clicked.connect(self.create_branch)
        info_layout.addWidget(new_branch_btn)
        
        layout.addLayout(info_layout)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：文件状态
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(QLabel('文件状态:'))
        
        self.status_list = QListWidget()
        self.status_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.status_list.customContextMenuRequested.connect(self.show_status_context_menu)
        left_layout.addWidget(self.status_list)
        
        # 状态操作按钮
        status_btn_layout = QHBoxLayout()
        
        add_all_btn = QPushButton('添加所有')
        add_all_btn.clicked.connect(self.add_all)
        status_btn_layout.addWidget(add_all_btn)
        
        commit_btn = QPushButton('提交')
        commit_btn.clicked.connect(self.commit)
        status_btn_layout.addWidget(commit_btn)
        
        left_layout.addLayout(status_btn_layout)
        
        splitter.addWidget(left_widget)
        
        # 中间：提交历史
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        
        middle_layout.addWidget(QLabel('提交历史:'))
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        middle_layout.addWidget(self.log_text)
        
        # 推送拉取按钮
        push_pull_layout = QHBoxLayout()
        
        pull_btn = QPushButton('拉取')
        pull_btn.clicked.connect(self.pull)
        push_pull_layout.addWidget(pull_btn)
        
        push_btn = QPushButton('推送')
        push_btn.clicked.connect(self.push)
        push_pull_layout.addWidget(push_btn)
        
        stash_btn = QPushButton('暂存')
        stash_btn.clicked.connect(self.stash)
        push_pull_layout.addWidget(stash_btn)
        
        stash_pop_btn = QPushButton('恢复暂存')
        stash_pop_btn.clicked.connect(self.stash_pop)
        push_pull_layout.addWidget(stash_pop_btn)
        
        middle_layout.addLayout(push_pull_layout)
        
        splitter.addWidget(middle_widget)
        
        # 右侧：差异显示
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        right_layout.addWidget(QLabel('差异:'))
        
        self.diff_text = QTextEdit()
        self.diff_text.setReadOnly(True)
        right_layout.addWidget(self.diff_text)
        
        diff_btn = QPushButton('查看差异')
        diff_btn.clicked.connect(self.show_diff)
        right_layout.addWidget(diff_btn)
        
        splitter.addWidget(right_widget)
        
        # 设置分割器比例
        splitter.setSizes([250, 350, 300])
        
        layout.addWidget(splitter)
        
        # 刷新按钮
        refresh_btn = QPushButton('刷新')
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)
        
        # 加载数据
        self.refresh()
    
    def refresh(self):
        """刷新Git状态"""
        if not self.git.is_git_repo():
            self.branch_label.setText('当前目录不是Git仓库')
            return
        
        # 更新当前分支
        current_branch = self.git.get_current_branch()
        if current_branch:
            self.branch_label.setText(f'当前分支: {current_branch}')
        
        # 更新分支列表
        self.branch_combo.clear()
        branches = self.git.get_branches()
        self.branch_combo.addItems(branches)
        
        # 更新状态
        self.status_list.clear()
        output, error = self.git.get_status()
        if output:
            for line in output.strip().split('\n'):
                if line.strip():
                    item = QListWidgetItem(line)
                    # 根据状态设置颜色
                    if line.startswith('M'):
                        item.setForeground(QColor('#ffcc00'))  # 修改
                    elif line.startswith('A'):
                        item.setForeground(QColor('#4caf50'))  # 添加
                    elif line.startswith('D'):
                        item.setForeground(QColor('#f44336'))  # 删除
                    elif line.startswith('?'):
                        item.setForeground(QColor('#9e9e9e'))  # 未跟踪
                    self.status_list.addItem(item)
        
        # 更新日志
        log_output, _ = self.git.get_log(30)
        if log_output:
            self.log_text.setText(log_output)
    
    def show_status_context_menu(self, position):
        """显示状态列表右键菜单"""
        item = self.status_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        add_action = menu.addAction('添加到暂存区')
        add_action.triggered.connect(lambda: self.add_file(item.text()))
        
        diff_action = menu.addAction('查看差异')
        diff_action.triggered.connect(lambda: self.show_file_diff(item.text()))
        
        menu.exec(self.status_list.mapToGlobal(position))
    
    def add_file(self, status_line):
        """添加文件"""
        # 从状态行中提取文件名
        file_path = status_line[3:].strip()
        self.git.add_file(file_path)
        self.refresh()
    
    def add_all(self):
        """添加所有更改"""
        self.git.add_all()
        self.refresh()
    
    def commit(self):
        """提交更改"""
        message, ok = QInputDialog.getText(
            self, '提交更改', '输入提交信息:'
        )
        
        if ok and message:
            output, error = self.git.commit(message)
            if error:
                QMessageBox.warning(self, '提交失败', error)
            else:
                QMessageBox.information(self, '提交成功', '更改已提交')
            self.refresh()
    
    def push(self):
        """推送到远程"""
        output, error = self.git.push()
        if error:
            QMessageBox.warning(self, '推送失败', error)
        else:
            QMessageBox.information(self, '推送成功', output)
        self.refresh()
    
    def pull(self):
        """从远程拉取"""
        output, error = self.git.pull()
        if error:
            QMessageBox.warning(self, '拉取失败', error)
        else:
            QMessageBox.information(self, '拉取成功', output)
        self.refresh()
    
    def checkout_branch(self):
        """切换分支"""
        branch = self.branch_combo.currentText()
        if branch:
            output, error = self.git.checkout_branch(branch)
            if error:
                QMessageBox.warning(self, '切换失败', error)
            else:
                QMessageBox.information(self, '切换成功', f'已切换到分支: {branch}')
            self.refresh()
    
    def create_branch(self):
        """创建新分支"""
        name, ok = QInputDialog.getText(
            self, '新建分支', '输入分支名称:'
        )
        
        if ok and name:
            output, error = self.git.create_branch(name)
            if error:
                QMessageBox.warning(self, '创建失败', error)
            else:
                QMessageBox.information(self, '创建成功', f'已创建并切换到分支: {name}')
            self.refresh()
    
    def show_diff(self):
        """显示差异"""
        output, error = self.git.get_diff()
        if output:
            self.diff_text.setText(output)
        elif error:
            self.diff_text.setText(error)
    
    def show_file_diff(self, status_line):
        """显示文件差异"""
        file_path = status_line[3:].strip()
        output, error = self.git.get_diff(file_path)
        if output:
            self.diff_text.setText(output)
        elif error:
            self.diff_text.setText(error)
    
    def stash(self):
        """暂存更改"""
        message, ok = QInputDialog.getText(
            self, '暂存更改', '输入暂存说明(可选):'
        )
        
        if ok:
            if message:
                output, error = self.git.stash(message)
            else:
                output, error = self.git.stash()
            
            if error:
                QMessageBox.warning(self, '暂存失败', error)
            else:
                QMessageBox.information(self, '暂存成功', output)
            self.refresh()
    
    def stash_pop(self):
        """恢复暂存"""
        output, error = self.git.stash_pop()
        if error:
            QMessageBox.warning(self, '恢复失败', error)
        else:
            QMessageBox.information(self, '恢复成功', output)
        self.refresh()
