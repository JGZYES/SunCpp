#!/usr/bin/env python3
"""
创建简单的文件类型图标
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_icon(filename, text, color):
    """创建一个简单的图标"""
    # 创建32x32的图像
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制圆角矩形背景
    draw.rounded_rectangle([2, 2, 30, 30], radius=4, fill=color)
    
    # 尝试使用默认字体
    try:
        font = ImageFont.truetype("arial.ttf", 10)
    except:
        font = ImageFont.load_default()
    
    # 计算文字位置使其居中
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (32 - text_width) // 2
    y = (32 - text_height) // 2 - 2
    
    # 绘制文字
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    
    # 保存
    img.save(filename)
    print(f'创建图标: {filename}')

def main():
    icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon')
    
    # 确保icon目录存在
    if not os.path.exists(icon_dir):
        os.makedirs(icon_dir)
    
    # 定义文件类型和对应的颜色
    file_types = {
        'cpp': ('C++', (0, 102, 204)),      # 蓝色
        'c': ('C', (0, 153, 153)),          # 青色
        'h': ('H', (153, 102, 204)),        # 紫色
        'hpp': ('H++', (153, 51, 204)),     # 深紫色
        'py': ('Py', (255, 204, 0)),        # 黄色
        'js': ('JS', (255, 204, 0)),        # 黄色
        'html': ('HTM', (255, 102, 0)),     # 橙色
        'css': ('CSS', (0, 153, 204)),      # 天蓝色
        'json': ('JSON', (128, 128, 128)),  # 灰色
        'xml': ('XML', (255, 153, 0)),      # 橙黄色
        'txt': ('TXT', (128, 128, 128)),    # 灰色
        'md': ('MD', (0, 0, 0)),            # 黑色
        'exe': ('EXE', (0, 153, 76)),       # 绿色
        'dll': ('DLL', (204, 0, 0)),        # 红色
        'zip': ('ZIP', (255, 153, 51)),     # 橙色
        'png': ('PNG', (0, 153, 76)),       # 绿色
        'jpg': ('JPG', (0, 153, 76)),       # 绿色
        'gif': ('GIF', (0, 153, 76)),       # 绿色
        'default': ('FILE', (128, 128, 128)), # 灰色
    }
    
    # 创建图标
    for ext, (text, color) in file_types.items():
        filename = os.path.join(icon_dir, f'{ext}.png')
        create_icon(filename, text, color)
    
    print(f'\n所有图标已创建到: {icon_dir}')
    print('你可以替换这些自动生成的图标为你自己的PNG图标')

if __name__ == '__main__':
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print('正在安装Pillow库...')
        import subprocess
        import sys
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'Pillow'])
        from PIL import Image, ImageDraw, ImageFont
    
    main()
