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
# 可选：第一个参数指定输出目录名，默认 dist_pkg
#   python build_package.py dist_v102
# 重新打包时建议换个新目录名：PyInstaller 会先删掉同名旧目录，
# 如果旧目录里文件很多，可能被本机的批量删除保护拦下来。
DIST = os.path.join(ROOT, sys.argv[1] if len(sys.argv) > 1 else 'dist_pkg')
PY = sys.executable

if os.path.isdir(DIST) and os.listdir(DIST):
    print('[提示] 输出目录已存在：%s' % DIST)
    print('      PyInstaller 会尝试先删除它；若被批量删除保护拦截，')
    print('      请改用新的目录名，例如：python build_package.py dist_v2')
    print()

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

# 3. 把 dist_template 里的启动脚本和说明复制到 dist_pkg 顶层
#    （和「账单截图识别工具」文件夹同级，直接压缩 dist_pkg 就能分发）
TPL = os.path.join(ROOT, 'dist_template')
if os.path.isdir(TPL):
    for name in os.listdir(TPL):
        shutil.copy(os.path.join(TPL, name), os.path.join(DIST, name))
        print('已复制到 %s 顶层: %s' % (os.path.basename(DIST), name))

print()
print('分发方式：把 %s 整个文件夹压缩后发给别人，解压后双击「启动.bat」。'
      % os.path.basename(DIST))
print('注意：dist_template/*.bat 必须是 GBK(cp936) + CRLF 编码，改动前请先看文件头部注释。')
