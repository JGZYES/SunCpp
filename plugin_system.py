import os
import sys
import importlib.util
from typing import Dict, List, Any, Optional, Callable


class Plugin:
    """插件基类，所有插件都需要继承这个类"""
    
    name = "Unknown Plugin"
    version = "1.0.0"
    description = "No description"
    author = "Unknown"
    
    def __init__(self, editor):
        self.editor = editor
        self.enabled = True
    
    def on_load(self):
        """插件加载时调用"""
        pass
    
    def on_unload(self):
        """插件卸载时调用"""
        pass
    
    def on_text_changed(self, text: str):
        """文本变化时调用"""
        pass
    
    def on_file_opened(self, file_path: str):
        """文件打开时调用"""
        pass
    
    def on_file_saved(self, file_path: str):
        """文件保存时调用"""
        pass
    
    def on_compile_start(self):
        """编译开始时调用"""
        pass
    
    def on_compile_end(self, success: bool, output: str):
        """编译结束时调用"""
        pass
    
    def on_run_start(self):
        """运行开始时调用"""
        pass
    
    def on_run_end(self, exit_code: int, output: str):
        """运行结束时调用"""
        pass
    
    def get_menu_actions(self) -> List[Dict[str, Any]]:
        """返回插件要添加的菜单项"""
        return []
    
    def get_toolbar_actions(self) -> List[Dict[str, Any]]:
        """返回插件要添加的工具栏项"""
        return []


class PluginManager:
    """插件管理器，负责加载、卸载和管理插件"""
    
    def __init__(self, editor):
        self.editor = editor
        self.plugins: Dict[str, Plugin] = {}
        self.plugins_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plugins')
        
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir)
    
    def load_plugin(self, plugin_path: str) -> bool:
        """加载单个插件"""
        try:
            if not os.path.exists(plugin_path):
                return False
            
            plugin_name = os.path.basename(plugin_path).replace('.py', '')
            
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[plugin_name] = module
                spec.loader.exec_module(module)
                
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, Plugin) and 
                        attr != Plugin):
                        plugin = attr(self.editor)
                        plugin.on_load()
                        self.plugins[plugin_name] = plugin
                        print(f'已加载插件: {plugin.name} v{plugin.version}')
                        return True
            
            return False
        except Exception as e:
            print(f'加载插件失败 {plugin_path}: {str(e)}')
            return False
    
    def load_all_plugins(self):
        """加载所有插件"""
        if not os.path.exists(self.plugins_dir):
            return
        
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                plugin_path = os.path.join(self.plugins_dir, filename)
                self.load_plugin(plugin_path)
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            plugin.on_unload()
            del self.plugins[plugin_name]
            print(f'已卸载插件: {plugin.name}')
            return True
        return False
    
    def unload_all_plugins(self):
        """卸载所有插件"""
        for plugin_name in list(self.plugins.keys()):
            self.unload_plugin(plugin_name)
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """获取插件"""
        return self.plugins.get(plugin_name)
    
    def get_all_plugins(self) -> List[Plugin]:
        """获取所有插件"""
        return list(self.plugins.values())
    
    def trigger_event(self, event_name: str, *args, **kwargs):
        """触发插件事件"""
        for plugin in self.plugins.values():
            if plugin.enabled:
                method = getattr(plugin, event_name, None)
                if callable(method):
                    try:
                        method(*args, **kwargs)
                    except Exception as e:
                        print(f'插件事件处理失败 {plugin.name}: {str(e)}')
    
    def get_all_menu_actions(self) -> List[Dict[str, Any]]:
        """获取所有插件的菜单项"""
        actions = []
        for plugin in self.plugins.values():
            if plugin.enabled:
                try:
                    actions.extend(plugin.get_menu_actions())
                except Exception as e:
                    print(f'获取插件菜单项失败 {plugin.name}: {str(e)}')
        return actions
    
    def get_all_toolbar_actions(self) -> List[Dict[str, Any]]:
        """获取所有插件的工具栏项"""
        actions = []
        for plugin in self.plugins.values():
            if plugin.enabled:
                try:
                    actions.extend(plugin.get_toolbar_actions())
                except Exception as e:
                    print(f'获取插件工具栏项失败 {plugin.name}: {str(e)}')
        return actions
