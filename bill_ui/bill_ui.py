#!/usr/bin/env python3
"""账单长截图批量识别 Web 界面 —— 启动后浏览器打开 http://127.0.0.1:8848"""
import os, sys, threading, traceback, uuid, time
from collections import Counter, defaultdict

import numpy as np
from flask import Flask, request, jsonify, send_file, abort
from PIL import Image
from werkzeug.utils import secure_filename

SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))       # 源码/资源目录
APP_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else SOURCE_DIR  # 程序所在目录
sys.path.insert(0, SOURCE_DIR)
if os.path.exists(os.path.join(os.path.dirname(SOURCE_DIR), 'batch_ocr_bills.py')):
    sys.path.insert(0, os.path.dirname(SOURCE_DIR))
import batch_ocr_bills as B
from rapidocr_onnxruntime import RapidOCR

UPLOAD_DIR = os.path.join(APP_DIR, '临时文件')
OUT_DIR = os.path.join(APP_DIR, '识别结果')
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

BASE = SOURCE_DIR

app = Flask(__name__)
JOBS = {}
_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = RapidOCR()
    return _engine


def now_ms():
    return int(time.time() * 1000)


def log(job, msg):
    t = time.strftime('%H:%M:%S')
    job.setdefault('log', []).append([t, msg])
    job['beat'] = now_ms()


def ocr_with_progress(im, job, idx):
    """带进度回调的分块 OCR"""
    w, h = im.size
    engine = get_engine()
    item = job['files'][idx]
    boxes = []
    y = 0
    done = 0
    total_chunks = (h + max(B.CHUNK_H - B.OVERLAP, 1) - 1) // max(B.CHUNK_H - B.OVERLAP, 1)
    while y < h:
        y1 = min(h, y + B.CHUNK_H)
        res, _ = engine(np.array(im.crop((0, y, w, y1))))
        if res:
            for box, txt, score in res:
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                boxes.append({'y': sum(ys) / 4 + y, 'x0': min(xs), 'x1': max(xs),
                              'text': txt, 'score': float(score)})
        done += 1
        item['progress'] = min(99, int(done / total_chunks * 100))
        item['chunks'] = f'{done}/{total_chunks}'
        job['beat'] = now_ms()
        if y1 >= h:
            break
        y = y1 - B.OVERLAP
    return boxes


def worker(job_id):
    job = JOBS[job_id]
    per_image = []
    n = len(job['files'])
    try:
        job['started_at'] = now_ms()
        job['beat'] = now_ms()
        job['phase'] = '正在加载识别引擎'
        log(job, f'开始处理，共 {n} 个文件')
        get_engine()                       # 预热，首次加载要几秒

        for idx, item in enumerate(job['files']):
            name = item['name']
            path = item['path']
            item['status'] = 'running'
            item['t0'] = now_ms()
            job['phase'] = f'正在识别第 {idx + 1}/{n} 张 · {name}'
            log(job, f'[{idx + 1}/{n}] 开始 {name}')
            try:
                ok, msg, im = B.check_readable(path)
                if not ok:
                    item.update(status='skipped', msg=msg, progress=100)
                    job['bad'].append((name, '跳过', msg))
                    log(job, f'[{idx + 1}/{n}] 跳过：{msg}')
                    continue
                item['info'] = msg
                log(job, f'[{idx + 1}/{n}] {msg}')
                boxes = ocr_with_progress(im, job, idx)
                job['phase'] = f'正在整理第 {idx + 1}/{n} 张的文字块'
                lines = B.dedupe_boxes(boxes)
                left, right = B.detect_columns(lines, im.size[0])
                rows = [r for r in B.parse_records(lines, left, right, name)
                        if r['dt'] and r['amt_f'] is not None]
                item['elapsed'] = round((now_ms() - item['t0']) / 1000, 1)
                item.update(status='done', count=len(rows), progress=100)
                per_image.append((name, rows))
                log(job, f'[{idx + 1}/{n}] 完成 {name}：{len(rows)} 条，'
                         f'耗时 {item["elapsed"]} 秒')
            except Exception as e:
                item.update(status='error', msg=f'{type(e).__name__}: {e}', progress=100)
                job['bad'].append((name, '失败', f'{type(e).__name__}: {e}'))
                log(job, f'[{idx + 1}/{n}] 失败：{e}')
                traceback.print_exc()

        job['phase'] = '正在合并去重'
        log(job, '跨图去重中（剔除重叠截图，保留真实重复订单）')
        def key(r):
            return (r['dt'], r['shop_clean'], r['amt_f'])

        mult = defaultdict(int)
        for _, rows in per_image:
            cnt = Counter(key(r) for r in rows)
            for k, v in cnt.items():
                mult[k] = max(mult[k], v)
        emitted = Counter()
        for _, rows in per_image:
            for r in rows:
                k = key(r)
                if emitted[k] < mult[k]:
                    emitted[k] += 1
                    job['rows'].append(r)
        job['rows'].sort(key=lambda r: r['dt'], reverse=True)

        job['phase'] = '正在生成 Excel'
        log(job, f'去重完成，共 {len(job["rows"])} 条记录')
        out = os.path.join(OUT_DIR, f'{job_id}.xlsx')
        B.export(job['rows'], job['bad'], out)
        job['output'] = out
        job['status'] = 'done'
        job['phase'] = '全部完成'
        job['elapsed'] = round((now_ms() - job['started_at']) / 1000, 1)
        log(job, f'完成！共 {len(job["rows"])} 条，总耗时 {job["elapsed"]} 秒')
    except Exception as e:
        job['status'] = 'error'
        job['phase'] = '处理失败'
        job['error'] = f'{type(e).__name__}: {e}'
        log(job, f'失败：{e}')
        traceback.print_exc()


@app.route('/')
def index():
    r = send_file(os.path.join(BASE, 'index.html'))
    r.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return r


@app.route('/api/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files')
    files = [f for f in files if f.filename]
    if not files:
        return jsonify({'error': '没有收到文件'}), 400
    job_id = uuid.uuid4().hex[:8]
    job = {'id': job_id, 'status': 'running', 'files': [], 'rows': [], 'bad': [],
           'output': None, 'error': None, 'created': time.time()}
    for f in files:
        safe = secure_filename(f.filename) or f.filename
        path = os.path.join(UPLOAD_DIR, f'{job_id}_{safe}')
        f.save(path)
        job['files'].append({'name': f.filename, 'path': path, 'status': 'pending',
                             'progress': 0, 'count': 0, 'msg': '', 'info': ''})
    JOBS[job_id] = job
    threading.Thread(target=worker, args=(job_id,), daemon=True).start()
    return jsonify({'job_id': job_id})


@app.route('/api/ping')
def ping():
    return jsonify({'ok': True, 'jobs': len(JOBS)})


@app.route('/api/status/<job_id>')
def status(job_id):
    job = JOBS.get(job_id)
    if not job:
        abort(404)
    files = [{k: v for k, v in f.items() if k != 'path'} for f in job['files']]
    avg = int(sum(f['progress'] for f in files) / len(files)) if files else 0
    return jsonify({'id': job['id'], 'status': job['status'], 'progress': avg,
                    'phase': job.get('phase', ''), 'started_at': job.get('started_at'),
                    'beat': job.get('beat'), 'log': job.get('log', []),
                    'files': files, 'bad': job['bad'], 'error': job['error'],
                    'done': job['status'] == 'done'})


@app.route('/api/result/<job_id>')
def result(job_id):
    job = JOBS.get(job_id)
    if not job or job['status'] != 'done':
        abort(404)
    rows = job['rows']
    preview = [{'dt': r['dt'], 'type': r['type'], 'shop': r['shop_clean'],
                'prod': r['prod'], 'amt': r['amt_f'], 'note': r['note'], 'src': r['src']}
               for r in rows[:200]]
    mon = defaultdict(lambda: [0, 0.0, 0])
    for r in rows:
        m = mon[(r['dt'] or '')[:7]]
        m[0] += 1
        m[1] += r['amt_f'] or 0
        if r['type'] == '退款':
            m[2] += 1
    return jsonify({
        'count': len(rows),
        'total': round(sum(r['amt_f'] or 0 for r in rows), 2),
        'refunds': sum(1 for r in rows if r['type'] == '退款'),
        'shops': len({r['shop_clean'] for r in rows}),
        'range': ([rows[-1]['dt'], rows[0]['dt']] if rows else None),
        'months': [{'m': k, 'c': v[0], 's': round(v[1], 2), 'r': v[2]}
                   for k, v in sorted(mon.items(), reverse=True)],
        'preview': preview,
    })


@app.route('/api/download/<job_id>')
def download(job_id):
    job = JOBS.get(job_id)
    if not job or not job.get('output'):
        abort(404)
    stamp = time.strftime('%Y%m%d_%H%M')
    return send_file(job['output'], as_attachment=True,
                     download_name=f'账单汇总_{stamp}.xlsx')


PORT = 8848
URL = f'http://127.0.0.1:{PORT}'


def port_in_use(port):
    import socket
    s = socket.socket()
    try:
        s.connect(('127.0.0.1', port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def setup_runtime():
    """启动时的运行时准备：行缓冲输出 + 中文控制台标题。

    行缓冲很重要：stdout 被重定向到管道/文件时 Python 默认是块缓冲，
    诊断信息会一直攒着不显示，出问题时就看不到任何线索。
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(line_buffering=True)
        except Exception:
            pass
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW('账单截图识别工具 - 服务窗口')
        except Exception:
            pass


def open_in_browser(url):
    """依次尝试多种方式唤起浏览器，任一成功即返回 True。

    打包成 exe 后 webbrowser 模块的注册表探测可能失灵，所以这里逐级降级，
    并且把失败原因打印出来 —— 静默失败是上一版最难排查的问题。
    """
    # 1) webbrowser（正常情况走这条）
    try:
        import webbrowser
        if webbrowser.open(url):
            print('已请求浏览器打开：%s' % url)
            return True
        print('webbrowser.open 返回 False，换用其他方式…')
    except Exception as e:
        print('webbrowser.open 失败：%r' % (e,))

    if sys.platform == 'win32':
        # 2) 直接用系统默认程序打开（ShellExecute）
        try:
            os.startfile(url)
            print('已用系统默认程序打开：%s' % url)
            return True
        except Exception as e:
            print('os.startfile 失败：%r' % (e,))

        # 3) 兜底：交给 cmd 的 start
        try:
            import subprocess
            subprocess.Popen('start "" "%s"' % url, shell=True)
            print('已用 start 命令打开：%s' % url)
            return True
        except Exception as e:
            print('start 命令失败：%r' % (e,))

    print('自动打开浏览器失败，请手动访问：%s' % url)
    return False


def open_browser_when_ready(timeout=90):
    """等服务真正起来后再开浏览器，避免打开一个连不上的页面。"""
    import urllib.request
    t0 = time.time()
    ready = False
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(f'{URL}/api/ping', timeout=2) as r:
                if r.status == 200:
                    ready = True
                    break
        except Exception:
            time.sleep(0.5)
    if not ready:
        print('服务启动超时（%d 秒），请手动打开 %s' % (timeout, URL))
        return
    open_in_browser(URL)


if __name__ == '__main__':
    setup_runtime()

    if port_in_use(PORT):
        print(f'服务已在运行，直接打开 {URL}')
        open_in_browser(URL)
        try:
            input('按回车键退出...')
        except Exception:
            pass
        sys.exit(0)

    print(f'Web UI running at {URL}')
    threading.Thread(target=open_browser_when_ready, daemon=True).start()
    app.run(host='127.0.0.1', port=PORT, debug=False, threaded=True)
