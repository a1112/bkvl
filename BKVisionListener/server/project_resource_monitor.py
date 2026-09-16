"""Application process-tree sampling and an optional Qt Quick monitor.

Sampling opens no network listener. CPU is normalized to machine capacity;
memory is summed RSS (shared pages may be counted more than once).
"""
import importlib
import os
import time
from concurrent.futures import ThreadPoolExecutor


class ResourceSampler:
    """Maintain baselines by PID and creation time, including current children."""

    def __init__(self) -> None:
        self._previous = {}
        self._sampled_at = None

    def sample(self) -> dict:
        """Return nullable metrics; never substitute zero for an unavailable metric."""
        try:
            import psutil
        except ImportError:
            return {"available": False, "reason": "需要安装 psutil 以读取应用资源"}
        now = time.monotonic()
        elapsed = now - self._sampled_at if self._sampled_at is not None else None
        root = psutil.Process(os.getpid())
        processes = [root] + root.children(recursive=True)
        current = {}
        cpu_delta = reads = writes = memory = 0
        partial = False
        io_available = True
        for process in processes:
            try:
                with process.oneshot():
                    identity = (process.pid, process.create_time())
                    cpu_time = process.cpu_times()
                    cpu = cpu_time.user + cpu_time.system
                    rss = process.memory_info().rss
                    try:
                        io = process.io_counters()
                        read, written = io.read_bytes, io.write_bytes
                    except (AttributeError, NotImplementedError, psutil.AccessDenied):
                        read = written = None
                        io_available = False
                memory += rss
                old = self._previous.get(identity)
                if old is not None:
                    cpu_delta += max(0, cpu - old[0])
                    if read is not None and old[1] is not None:
                        reads += max(0, read - old[1])
                        writes += max(0, written - old[2])
                current[identity] = (cpu, read, written)
            except psutil.NoSuchProcess:
                continue
            except psutil.AccessDenied:
                partial = True
        self._previous = current
        self._sampled_at = now
        baseline = elapsed is not None and elapsed > 0
        return {
            "available": bool(current),
            "cpu_percent": min(100.0, cpu_delta / elapsed / (psutil.cpu_count() or 1) * 100) if baseline else None,
            "memory_bytes": memory if current else None,
            "read_bytes_per_second": reads / elapsed if baseline and io_available else None,
            "write_bytes_per_second": writes / elapsed if baseline and io_available else None,
            "process_count": len(current), "partial": partial,
            "gpu_percent": None,
        }


def install(engine, widget=None) -> None:
    """Attach one monitor per Qt Quick window using the application's Qt binding."""
    binding = type(engine).__module__.split(".")[0]
    core = importlib.import_module(binding + ".QtCore")
    qml = importlib.import_module(binding + ".QtQml")
    quick = importlib.import_module(binding + ".QtQuick")
    values = qml.QQmlPropertyMap(engine)
    values.insert("summary", "资源监控 · 采样中")
    values.insert("details", "正在采样…")
    engine.rootContext().setContextProperty("projectResourceMonitor", values)
    panels = []
    components = []

    def attach(window, _url) -> None:
        if not isinstance(window, quick.QQuickWindow):
            return
        component = qml.QQmlComponent(engine)
        component.setData(_PANEL.encode("utf-8"), core.QUrl())
        panel = component.create(engine.rootContext())
        if panel is not None:
            qml.QQmlEngine.setObjectOwnership(panel, qml.QQmlEngine.CppOwnership)
            content = window.contentItem()
            qml.QQmlEngine.setObjectOwnership(content, qml.QQmlEngine.CppOwnership)
            panel.setParent(content)
            panel.setParentItem(content)
            panels.append(panel)
            components.append((component, window, content))

    if widget is None:
        engine.objectCreated.connect(attach)
    else:
        attach(widget.quickWindow(), core.QUrl())
        widget._project_resource_monitor_engine = engine
    sampler = ResourceSampler()
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="app-resource-monitor")
    pending = [None]
    timer = core.QTimer(engine)
    timer.setInterval(2000)

    def tick() -> None:
        visible = widget.isVisible() if widget is not None else any(
            isinstance(root, quick.QQuickWindow) and root.isVisible() and root.windowState() != core.Qt.WindowMinimized
            for root in engine.rootObjects())
        if not visible:
            return
        if pending[0] is not None and pending[0].done():
            try:
                metrics = pending[0].result()
                if not metrics["available"]:
                    raise RuntimeError(metrics.get("reason", "无法读取进程信息"))
                cpu = metrics["cpu_percent"]
                cpu_text = "采样中" if cpu is None else f"{cpu:.1f}%"
                values.insert("summary", f"CPU {cpu_text} · {metrics['memory_bytes'] / 1048576:.1f} MiB")
                def rate(key: str) -> str:
                    value = metrics[key]
                    return "不可用 / 等待基线" if value is None else f"{value / 1024:.1f} KiB/s"
                values.insert("details", f"读 {rate('read_bytes_per_second')} · 写 {rate('write_bytes_per_second')}\n"
                              f"{metrics['process_count']} 个进程 · GPU：不可用\n"
                              "本应用及子进程；CPU 按整机容量计，内存 RSS 求和可能含共享页。隐藏时暂停。"
                              + (" 部分进程权限不足。" if metrics["partial"] else ""))
            except Exception:
                values.insert("summary", "资源监控 · 暂不可用")
                values.insert("details", "采样失败；请检查 psutil 依赖及当前进程权限。")
            pending[0] = None
        if pending[0] is None:
            pending[0] = executor.submit(sampler.sample)

    timer.timeout.connect(tick)
    timer.start()
    def close() -> None:
        timer.stop()
        executor.shutdown(wait=False)
    core.QCoreApplication.instance().aboutToQuit.connect(close)
    engine._project_resource_monitor = (values, panels, sampler, executor, timer, tick, attach, close, components)


_PANEL = r'''import QtQuick 2.12
Rectangle {
    anchors.right: parent.right; anchors.bottom: parent.bottom
    anchors.margins: 12; z: 100000
    width: expanded ? 310 : label.implicitWidth + 20
    height: expanded ? 170 : 30; radius: 6; color: "#182334"; border.color: "#64748b"
    property bool expanded: false
    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: "Application resource monitor"
    Keys.onSpacePressed: expanded = !expanded
    Keys.onReturnPressed: expanded = !expanded
    Keys.onEscapePressed: expanded = false
    Text { id: label; x: 10; y: 6; color: "#eef2ff"; font.pixelSize: 12; text: projectResourceMonitor.summary }
    Text { x: 10; y: 32; width: parent.width - 20; visible: parent.expanded; color: "#eef2ff"; font.pixelSize: 12; wrapMode: Text.Wrap; text: projectResourceMonitor.details }
    MouseArea { anchors.fill: parent; onClicked: { parent.forceActiveFocus(); parent.expanded = !parent.expanded } }
}'''


def attach_fastapi(app) -> None:
    """Add an in-service monitor on the existing listener and app middleware."""
    from threading import Lock
    from fastapi.responses import HTMLResponse, Response
    if getattr(app.state, "project_resource_monitor", False):
        return
    app.state.project_resource_monitor = True
    sampler = ResourceSampler()
    lock = Lock()
    cache = [None, 0.0]

    @app.get("/resource-monitor/snapshot", tags=["Application resources"])
    def snapshot() -> dict:
        with lock:
            now = time.monotonic()
            if cache[0] is None or now - cache[1] >= 1.0:
                cache[0] = sampler.sample()
                cache[1] = now
            return cache[0]

    @app.get("/resource-monitor/monitor.js", include_in_schema=False)
    def monitor_script():
        return Response(_MONITOR_SCRIPT, media_type="application/javascript")

    @app.get("/resource-monitor/", response_class=HTMLResponse, include_in_schema=False)
    def monitor_page() -> str:
        return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>应用资源监控</title><body><h1>应用资源监控</h1><p>当前服务及子进程，每 2 秒采样；页面隐藏时暂停。</p><script src="./monitor.js" defer></script></body></html>'

_MONITOR_SCRIPT = "(() => {\n  'use strict';\n  if (window.top !== window || window.__projectResourceMonitor) return;\n  window.__projectResourceMonitor = true;\n  const mount = () => {\n    const host = document.createElement('div');\n    host.id = 'project-resource-monitor';\n    host.style.cssText = 'position:fixed;right:12px;bottom:12px;z-index:2147483000;';\n    const root = host.attachShadow({ mode: 'open' });\n    root.innerHTML = `<style>\n      :host{font:12px/1.5 system-ui,sans-serif;color:#eef2ff;color-scheme:dark}\n      button{font:inherit;color:inherit;cursor:pointer;border:1px solid #64748b;border-radius:7px;padding:5px 10px;background:#182334}\n      button:focus-visible{outline:2px solid #60a5fa;outline-offset:2px}\n      section{background:#182334;border:1px solid #64748b;border-radius:9px;padding:12px;margin-bottom:6px;width:250px;box-shadow:0 4px 20px #0004}\n      section[hidden]{display:none}h2{font-size:13px;margin:0 0 8px}dl{margin:0;display:grid;grid-template-columns:1fr auto;gap:5px 12px}dd{margin:0;font-variant-numeric:tabular-nums}p{color:#cbd5e1;font-size:11px;margin:8px 0 0}footer{text-align:right}\n    </style><section id=\"details\" hidden><h2>应用资源消耗</h2><dl>\n      <dt>CPU</dt><dd data-value=\"cpu\">采样中</dd><dt>内存（RSS）</dt><dd data-value=\"memory\">采样中</dd>\n      <dt>磁盘读取</dt><dd data-value=\"read\">采样中</dd><dt>磁盘写入</dt><dd data-value=\"write\">采样中</dd>\n      <dt>进程数</dt><dd data-value=\"count\">—</dd><dt>GPU</dt><dd>不可用</dd></dl>\n      <p>范围：服务进程及当前子进程（不含浏览器或远程设备）。CPU 按整机容量计；内存为各进程 RSS 之和，可能含共享页。GPU 尚无可靠采样源。</p><p id=\"status\" role=\"status\">正在采样…</p>\n    </section><footer><button type=\"button\" aria-expanded=\"false\" aria-controls=\"details\">资源监控</button></footer>`;\n    document.body.append(host);\n    const button = root.querySelector('button');\n    const details = root.querySelector('section');\n    const status = root.querySelector('#status');\n    button.addEventListener('click', () => {\n      details.hidden = !details.hidden;\n      button.setAttribute('aria-expanded', String(!details.hidden));\n    });\n    root.addEventListener('keydown', event => {\n      if (event.key === 'Escape') { details.hidden = true; button.setAttribute('aria-expanded', 'false'); button.focus(); }\n    });\n    const bytes = value => {\n      if (!Number.isFinite(value) || value < 0) return '不可用';\n      const units = ['B', 'KiB', 'MiB', 'GiB'];\n      let i = 0;\n      while (value >= 1024 && i < units.length - 1) { value /= 1024; i++; }\n      return `${value.toFixed(i ? 1 : 0)} ${units[i]}`;\n    };\n    const write = (key, value) => { root.querySelector(`[data-value=\"${key}\"]`).textContent = value; };\n    let timer, busy = false, stopped = false, lastSuccess = null;\n    const sample = async () => {\n      clearTimeout(timer);\n      if (stopped || document.hidden || busy) return;\n      busy = true;\n      try {\n        const data = await fetch('./snapshot', { credentials: 'same-origin', cache: 'no-store' }).then(async response => {\n          if (!response.ok) throw new Error('monitor unavailable');\n          const sample = await response.json();\n          if (!sample.available) throw new Error('monitor unavailable');\n          return { cpuPercent: sample.cpu_percent, memoryBytes: sample.memory_bytes,\n            readBytesPerSecond: sample.read_bytes_per_second, writeBytesPerSecond: sample.write_bytes_per_second,\n            processCount: sample.process_count };\n        });\n        if (stopped || document.hidden) return;\n        const cpu = Number.isFinite(data.cpuPercent) ? `${data.cpuPercent.toFixed(1)}%` : '采样中';\n        write('cpu', cpu); write('memory', bytes(data.memoryBytes));\n        write('read', data.readBytesPerSecond == null ? '采样中' : `${bytes(data.readBytesPerSecond)}/s`);\n        write('write', data.writeBytesPerSecond == null ? '采样中' : `${bytes(data.writeBytesPerSecond)}/s`);\n        write('count', String(data.processCount));\n        lastSuccess = new Date().toLocaleTimeString();\n        status.textContent = `更新于 ${lastSuccess} · 每 2 秒采样`;\n        button.textContent = `CPU ${cpu} · ${bytes(data.memoryBytes)}`;\n      } catch (_) {\n        status.textContent = lastSuccess ? `采样失败，保留 ${lastSuccess} 的数据` : '资源监控暂不可用';\n        button.textContent = '资源监控 · 暂不可用';\n      } finally {\n        busy = false;\n        if (!stopped && !document.hidden) timer = setTimeout(sample, 2000);\n      }\n    };\n    document.addEventListener('visibilitychange', () => {\n      clearTimeout(timer);\n      if (!document.hidden) sample();\n    });\n    window.addEventListener('pagehide', () => { stopped = true; clearTimeout(timer); });\n    window.addEventListener('pageshow', () => { stopped = false; sample(); });\n    button.click();\n    sample();\n  };\n  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, { once: true });\n  else mount();\n})();\n"
