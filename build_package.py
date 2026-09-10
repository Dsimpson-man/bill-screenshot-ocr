#!/usr/bin/env python3
"""把 Web UI 打包成独立可执行程序（供没有安装 Python 的电脑使用）

用法:
    pip install pyinstaller
    python build_package.py

产物:
    dist_pkg/账单截图识别工具/     ← 整个文件夹一起分发，约 230MB（内含 OCR 模型）

注意:
    分发时「启动.bat」「使用说明.txt」要和「账单截图识别工具」文件夹放在同级目录。
"""
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(ROOT, 'build_pkg')
DIST = os.path.join(ROOT, 'dist_pkg')
PY = sys.executable

# 1. 整理打包目录（单一来源：bill_ui/ + 根目录 batch_ocr_bills.py）
if os.path.exists(PKG):
    shutil.rmtree(PKG)
os.makedirs(PKG)
shutil.copy(os.path.join(ROOT, 'bill_ui', 'bill_ui.py'), os.path.join(PKG, 'app.py'))
shutil.copy(os.path.join(ROOT, 'bill_ui', 'index.html'), os.path.join(PKG, 'index.html'))
shutil.copy(os.path.join(ROOT, 'batch_ocr_bills.py'), os.path.join(PKG, 'batch_ocr_bills.py'))
print('打包目录就绪:', PKG)

# 2. PyInstaller
cmd = [
    PY, '-m', 'PyInstaller',
    '--noconfirm', '--onedir', '--console',
    '--distpath', DIST,
    '--workpath', os.path.join(ROOT, 'build_tmp'),
    '--specpath', PKG,
    '--name', '账单截图识别工具',
    '--collect-all', 'rapidocr_onnxruntime',
    '--add-data', os.path.join(PKG, 'index.html') + os.pathsep + '.',
    '--icon', 'NONE',
    os.path.join(PKG, 'app.py'),
]
print('开始打包，这一步较慢…')
t0 = time.time()
r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                   encoding='utf-8', errors='replace')
print('耗时 %.0f 秒，退出码 %s' % (time.time() - t0, r.returncode))
if r.returncode != 0:
    print((r.stdout or '')[-3000:] + (r.stderr or '')[-3000:])
    sys.exit(1)
print('打包完成 →', os.path.join(DIST, '账单截图识别工具'))
