#!/usr/bin/env python3
"""
Koga Agentic OS — Unified AI command center.
Sidebar tabs as buttons, merged quick launch, process manager, memory, activity.
"""

import sys, os, json, time, threading, subprocess, requests, psutil
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTabWidget, QFrame, QScrollArea,
    QTextEdit, QLineEdit, QComboBox, QProgressBar,
    QMessageBox, QListWidget, QListWidgetItem,
    QGroupBox, QCheckBox, QInputDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QUrl
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

# ===========================================================================
STYLE = """
QMainWindow, QWidget { background-color: #080d18; color: #c8d6e5; font-family: 'Segoe UI', sans-serif; }
QFrame#sidebar { background-color: #0c1220; border-right: 1px solid #1a2840; }
QFrame#rightpanel { background-color: #0c1220; border-left: 1px solid #1a2840; }
QFrame#statusbar { background-color: #0c1220; border-top: 1px solid #1a2840; }
QFrame#commandbar { background-color: #0c1220; border-top: 1px solid #1a2840; }
QLabel#title { color: #00d4ff; font-size: 20px; font-weight: bold; letter-spacing: 6px; }
QLabel#subtitle { color: #405070; font-size: 9px; letter-spacing: 3px; }
QLabel#section { color: #5070a0; font-size: 10px; font-weight: bold; letter-spacing: 2px; padding: 8px 0 4px 12px; }
QLabel#status_text { color: #506080; font-size: 11px; }
QLabel#dot { font-size: 14px; }
QPushButton {
    background-color: #121a2e; color: #c8d6e5;
    border: 1px solid #1a2840; border-radius: 6px;
    padding: 10px 12px; font-size: 11px; text-align: left;
}
QPushButton:hover { background-color: #1a2840; border-color: #00a0c0; color: #00d4ff; }
QPushButton:pressed { background-color: #00a0c0; color: #080d18; }
QPushButton#nav { text-align: left; font-weight: bold; }
QPushButton#nav:checked { background-color: #080d18; color: #00d4ff; border-left: 3px solid #00a0c0; border-radius: 0; }
QPushButton#nav:hover { background-color: #1a2840; }
QPushButton#launch { text-align: center; }
QPushButton#btn_start { color: #00ff96; }
QPushButton#btn_stop { color: #ff4060; }
QPushButton#btn_restart { color: #ffb000; }
QTextEdit { background-color: #0c1220; color: #c8d6e5; border: 1px solid #1a2840; border-radius: 6px; font-size: 12px; padding: 8px; }
QTextEdit#log { font-family: Consolas, monospace; font-size: 10px; }
QLineEdit { background-color: #0c1220; color: #c8d6e5; border: 1px solid #1a2840; border-radius: 6px; padding: 8px; font-size: 12px; }
QLineEdit:focus { border-color: #00a0c0; }
QLineEdit#command { font-size: 13px; padding: 10px; }
QComboBox { background-color: #121a2e; color: #c8d6e5; border: 1px solid #1a2840; border-radius: 6px; padding: 6px; font-size: 11px; }
QProgressBar { background-color: #0c1220; border: 1px solid #1a2840; border-radius: 4px; text-align: center; color: #c8d6e5; font-size: 9px; height: 14px; }
QProgressBar::chunk { background-color: #00a0c0; border-radius: 3px; }
QTableWidget { background-color: #0c1220; color: #c8d6e5; border: 1px solid #1a2840; border-radius: 6px; gridline-color: #1a2840; font-size: 11px; }
QHeaderView::section { background-color: #0c1220; color: #5070a0; border: 1px solid #1a2840; padding: 6px; font-weight: bold; }
QListWidget { background-color: #0c1220; color: #c8d6e5; border: 1px solid #1a2840; border-radius: 6px; font-size: 11px; padding: 4px; }
QGroupBox { border: 1px solid #1a2840; border-radius: 6px; margin-top: 12px; color: #5070a0; font-weight: bold; font-size: 11px; }
QStackedWidget { border: none; }
"""

C_GREEN = "#00ff96"; C_RED = "#ff4060"; C_AMBER = "#ffb000"; C_BLUE = "#00a0c0"; C_DIM = "#506080"

# ===========================================================================
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "koga_config.json")
DEFAULT_CONFIG = {
    "services": [
        {"name": "James", "type": "process", "check": "james.py",
         "start_cmd": "python C:\\Users\\Mickael\\james\\james.py", "auto_restart": False},
        {"name": "Hermes VPS", "type": "http", "url": "http://100.104.163.6:8642/health", "auto_restart": False},
        {"name": "Hermes Local", "type": "http", "url": "http://localhost:8642/health", "auto_restart": False},
        {"name": "Ollama", "type": "process", "check": "ollama.exe",
         "start_cmd": "ollama serve", "auto_restart": True},
        {"name": "Open WebUI", "type": "http", "url": "http://localhost:3000/health",
         "start_cmd": "docker start open-webui", "auto_restart": True},
        {"name": "Obsidian", "type": "process", "check": "Obsidian.exe",
         "start_cmd": "C:\\Users\\Mickael\\AppData\\Local\\Obsidian\\Obsidian.exe", "auto_restart": False},
    ],
    "nav_tabs": [
        {"name": "Chat", "type": "chat"},
        {"name": "Processes", "type": "processes"},
        {"name": "Memory", "type": "memory"},
        {"name": "Activity", "type": "activity"},
    ],
    "web_apps": [
        {"name": "Claude", "url": "https://claude.ai"},
        {"name": "Claude Cowork", "url": "https://claude.ai/cowork"},
        {"name": "ChatGPT", "url": "https://chat.openai.com"},
        {"name": "Gemini", "url": "https://gemini.google.com"},
        {"name": "Grok", "url": "https://grok.com"},
        {"name": "DeepSeek", "url": "https://chat.deepseek.com"},
        {"name": "Open WebUI", "url": "http://localhost:3000"},
        {"name": "Hermes Desktop", "url": "http://100.104.163.6:4860"},
    ],
    "quick_launch": {
        "James": "python C:\\Users\\Mickael\\james\\james.py",
        "Obsidian": "C:\\Users\\Mickael\\AppData\\Local\\Obsidian\\Obsidian.exe",
        "Claude Desktop": "C:\\Users\\Mickael\\AppData\\Local\\AnthropicClaude\\Claude.exe",
        "Terminal": "wt.exe",
    },
    "vps_url": "http://100.104.163.6:8642/v1/chat/completions", "vps_key": "",
    "ollama_url": "http://localhost:11434/v1/chat/completions", "ollama_model": "gemma4:e2b",
    "openrouter_key": "",
    "memory_path": "C:\\Users\\Mickael\\AppData\\Local\\hermes\\memories",
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg: cfg[k] = v
            return cfg
    return DEFAULT_CONFIG

def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

CFG = load_config()

# ===========================================================================
class ActivityLog:
    def __init__(self):
        self._lines = []; self._listeners = []
    def add(self, source, msg, level="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] [{level}] [{source}] {msg}"
        self._lines.append(line)
        if len(self._lines) > 500: self._lines = self._lines[-500:]
        for l in self._listeners: l(line)
    def get_lines(self): return list(self._lines)
    def subscribe(self, cb): self._listeners.append(cb)

ACTIVITY = ActivityLog()

# ===========================================================================
class StatusChecker(QThread):
    status_update = pyqtSignal(dict)
    def run(self):
        while True:
            results = {}
            for svc in CFG.get("services", []):
                name = svc["name"]
                if svc["type"] == "http":
                    try:
                        r = requests.get(svc["url"], timeout=3)
                        results[name] = "online" if r.status_code < 500 else "error"
                    except: results[name] = "offline"
                elif svc["type"] == "process":
                    found = False
                    for p in psutil.process_iter(["cmdline", "name"]):
                        cmd = " ".join(p.info.get("cmdline", []) or [])
                        nm = p.info.get("name", "") or ""
                        if svc["check"].lower() in cmd.lower() or svc["check"].lower() in nm.lower():
                            found = True; break
                    results[name] = "online" if found else "offline"
            results["cpu"] = psutil.cpu_percent()
            results["ram"] = psutil.virtual_memory().percent
            self.status_update.emit(results)
            time.sleep(5)

# ===========================================================================
class AIChatWidget(QWidget):
    def __init__(self, config):
        super().__init__(); self.config = config; self.history = []; self._init_ui()
    def _init_ui(self):
        layout = QVBoxLayout(self); layout.setSpacing(8); layout.setContentsMargins(12,12,12,12)
        top = QHBoxLayout(); top.addWidget(QLabel("Route:"))
        self.router = QComboBox(); self.router.addItems(["VPS Hermes","Local Ollama","OpenRouter"])
        top.addWidget(self.router); top.addStretch()
        self.model_label = QLabel(""); self.model_label.setStyleSheet(f"color:{C_DIM};font-size:10px;")
        top.addWidget(self.model_label); layout.addLayout(top)
        self.chat_display = QTextEdit(); self.chat_display.setReadOnly(True)
        self.chat_display.setHtml("<div style='color:#506080;text-align:center;padding:20px;'>Start a conversation.</div>")
        layout.addWidget(self.chat_display)
        ib = QHBoxLayout()
        self.input_field = QLineEdit(); self.input_field.setPlaceholderText("Ask anything...")
        self.input_field.returnPressed.connect(self._send); ib.addWidget(self.input_field)
        self.send_btn = QPushButton("Send"); self.send_btn.setFixedWidth(80); self.send_btn.clicked.connect(self._send); ib.addWidget(self.send_btn)
        self.clear_btn = QPushButton("Clear"); self.clear_btn.setFixedWidth(70); self.clear_btn.clicked.connect(self._clear); ib.addWidget(self.clear_btn)
        layout.addLayout(ib)
    def _send(self):
        text = self.input_field.text().strip()
        if not text: return
        self.input_field.clear(); self._append("You", text, "#00d4ff")
        route = self.router.currentText(); self.model_label.setText(f"Routing to {route}...")
        ACTIVITY.add("Chat", f"Query → {route}: {text[:50]}")
        threading.Thread(target=self._call, args=(text, route), daemon=True).start()
    def _call(self, text, route):
        try:
            if route == "VPS Hermes":
                r = requests.post(self.config["vps_url"], json={"model":"hermes-agent","messages":self.history+[{"role":"user","content":text}]}, headers={"Authorization":f"Bearer {self.config.get('vps_key','')}"}, timeout=120)
                reply = r.json()["choices"][0]["message"]["content"]
            elif route == "Local Ollama":
                r = requests.post(self.config["ollama_url"], json={"model":self.config.get("ollama_model","gemma4:e2b"),"messages":[{"role":"user","content":text}],"stream":False}, timeout=30)
                reply = r.json()["choices"][0]["message"]["content"]
            else:
                r = requests.post("https://openrouter.ai/api/v1/chat/completions", json={"model":"openrouter/auto-beta","messages":[{"role":"user","content":text}]}, headers={"Authorization":f"Bearer {self.config.get('openrouter_key','')}"}, timeout=60)
                reply = r.json()["choices"][0]["message"]["content"]
        except Exception as e: reply = f"Error: {e}"; ACTIVITY.add("Chat", f"Error: {str(e)[:80]}", "ERROR")
        self.history.append({"role":"user","content":text}); self.history.append({"role":"assistant","content":reply})
        QTimer.singleShot(0, lambda: self._append("AI", reply, "#00ff96"))
        QTimer.singleShot(0, lambda: self.model_label.setText(""))
    def _append(self, sender, text, color):
        safe = text.replace("<","&lt;").replace(">","&gt;")
        self.chat_display.append(f"<div style='margin:6px 0;'><b style='color:{color};'>{sender}:</b> <span style='color:#c8d6e5;'>{safe}</span></div>")
    def _clear(self): self.chat_display.clear(); self.history = []

# ===========================================================================
class WebTabWidget(QWidget):
    def __init__(self, url, name):
        super().__init__()
        layout = QVBoxLayout(self); layout.setContentsMargins(0,0,0,0)
        self.browser = QWebEngineView(); self.browser.setUrl(QUrl(url))
        s = self.browser.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        nav = QHBoxLayout(); nav.setContentsMargins(4,4,4,4)
        back = QPushButton("←"); back.setFixedWidth(40); back.clicked.connect(self.browser.back)
        fwd = QPushButton("→"); fwd.setFixedWidth(40); fwd.clicked.connect(self.browser.forward)
        rld = QPushButton("⟳"); rld.setFixedWidth(40); rld.clicked.connect(self.browser.reload)
        ul = QLabel(url); ul.setStyleSheet(f"color:{C_DIM};font-size:10px;padding:0 8px;")
        nav.addWidget(back); nav.addWidget(fwd); nav.addWidget(rld); nav.addWidget(ul, 1)
        layout.addLayout(nav); layout.addWidget(self.browser, 1)

# ===========================================================================
class ProcessManagerTab(QWidget):
    def __init__(self, config):
        super().__init__(); self.config = config; self._init_ui()
    def _init_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(12,12,12,12); layout.setSpacing(8)
        h = QHBoxLayout()
        t = QLabel("AI PROCESS MANAGER"); t.setStyleSheet(f"color:{C_BLUE};font-size:14px;font-weight:bold;letter-spacing:3px;")
        h.addWidget(t); h.addStretch()
        ra = QPushButton("Restart All"); ra.setObjectName("btn_restart"); ra.clicked.connect(self._restart_all); h.addWidget(ra)
        layout.addLayout(h)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Service","Status","CPU%","RAM%","Auto-Restart","Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setRowCount(len(self.config.get("services", [])))
        for i, svc in enumerate(self.config.get("services", [])):
            self.table.setItem(i, 0, QTableWidgetItem(svc["name"]))
            self.table.setItem(i, 1, QTableWidgetItem("Checking..."))
            self.table.setItem(i, 2, QTableWidgetItem("-"))
            self.table.setItem(i, 3, QTableWidgetItem("-"))
            cb = QCheckBox(); cb.setChecked(svc.get("auto_restart", False))
            cb.stateChanged.connect(lambda s, sv=svc: self._toggle(sv, s))
            self.table.setCellWidget(i, 4, cb)
            bw = QWidget(); bl = QHBoxLayout(bw); bl.setContentsMargins(2,2,2,2); bl.setSpacing(4)
            st = QPushButton("Start"); st.setObjectName("btn_start"); st.setFixedWidth(60); st.clicked.connect(lambda c, s=svc: self._start(s)); bl.addWidget(st)
            sp = QPushButton("Stop"); sp.setObjectName("btn_stop"); sp.setFixedWidth(60); sp.clicked.connect(lambda c, s=svc: self._stop(s)); bl.addWidget(sp)
            rs = QPushButton("Restart"); rs.setObjectName("btn_restart"); rs.setFixedWidth(70); rs.clicked.connect(lambda c, s=svc: self._restart(s)); bl.addWidget(rs)
            self.table.setCellWidget(i, 5, bw)
        layout.addWidget(self.table)
        lg = QGroupBox("Process Activity"); ll = QVBoxLayout(lg)
        self.log = QTextEdit(); self.log.setObjectName("log"); self.log.setReadOnly(True); self.log.setMaximumHeight(150)
        ll.addWidget(self.log); layout.addWidget(lg)
        ACTIVITY.subscribe(self._on_act)
    def _on_act(self, line): QTimer.singleShot(0, lambda: self.log.append(line))
    def update_status(self, status):
        for i, svc in enumerate(self.config.get("services", [])):
            state = status.get(svc["name"], "offline")
            color = C_GREEN if state == "online" else (C_AMBER if state == "error" else C_RED)
            item = self.table.item(i, 1); item.setText(state.upper()); item.setForeground(QColor(color))
    def _start(self, svc):
        cmd = svc.get("start_cmd","")
        if not cmd: ACTIVITY.add("ProcessMgr", f"No start cmd for {svc['name']}", "WARN"); return
        try: subprocess.Popen(cmd, shell=True); ACTIVITY.add("ProcessMgr", f"Started {svc['name']}")
        except Exception as e: ACTIVITY.add("ProcessMgr", f"Failed {svc['name']}: {e}", "ERROR")
    def _stop(self, svc):
        for p in psutil.process_iter(["cmdline","name","pid"]):
            cmd = " ".join(p.info.get("cmdline",[]) or []); nm = p.info.get("name","") or ""
            if svc["check"].lower() in cmd.lower() or svc["check"].lower() in nm.lower():
                try: p.terminate(); ACTIVITY.add("ProcessMgr", f"Stopped {svc['name']} (pid={p.info['pid']})")
                except: pass
    def _restart(self, svc): self._stop(svc); time.sleep(1); self._start(svc)
    def _restart_all(self):
        for svc in self.config.get("services", []):
            if svc.get("start_cmd"): self._restart(svc)
    def _toggle(self, svc, state):
        svc["auto_restart"] = bool(state); save_config(self.config)
        ACTIVITY.add("ProcessMgr", f"Auto-restart {svc['name']}: {'ON' if state else 'OFF'}")

# ===========================================================================
class MemoryTab(QWidget):
    def __init__(self, config):
        super().__init__(); self.config = config; self._init_ui()
    def _init_ui(self):
        layout = QHBoxLayout(self); layout.setContentsMargins(12,12,12,12); layout.setSpacing(8)
        left = QVBoxLayout(); left.addWidget(QLabel("MEMORY FILES"))
        self.file_list = QListWidget(); self.file_list.currentItemChanged.connect(self._load); left.addWidget(self.file_list, 1)
        br = QHBoxLayout()
        rf = QPushButton("Refresh"); rf.clicked.connect(self._refresh); br.addWidget(rf)
        sv = QPushButton("Save"); sv.clicked.connect(self._save); br.addWidget(sv)
        left.addLayout(br); layout.addLayout(left, 1)
        right = QVBoxLayout(); right.addWidget(QLabel("CONTENT"))
        self.editor = QTextEdit(); self.editor.setFont(QFont("Consolas", 10)); right.addWidget(self.editor, 1)
        self.file_label = QLabel("No file selected"); self.file_label.setStyleSheet(f"color:{C_DIM};font-size:10px;")
        right.addWidget(self.file_label); layout.addLayout(right, 2)
        self._refresh()
    def _refresh(self):
        self.file_list.clear()
        path = self.config.get("memory_path", "")
        if os.path.isdir(path):
            for f in sorted(os.listdir(path)):
                if f.endswith(".md") or f.endswith(".txt"): self.file_list.addItem(QListWidgetItem(f))
    def _load(self, item):
        if not item: return
        path = os.path.join(self.config.get("memory_path",""), item.text())
        try:
            with open(path, "r") as f: self.editor.setPlainText(f.read())
            self.file_label.setText(path); ACTIVITY.add("Memory", f"Loaded {item.text()}")
        except Exception as e: self.editor.setPlainText(f"Error: {e}")
    def _save(self):
        path = self.file_label.text()
        if not path or path == "No file selected": return
        try:
            with open(path, "w") as f: f.write(self.editor.toPlainText())
            ACTIVITY.add("Memory", f"Saved {os.path.basename(path)}")
        except Exception as e: QMessageBox.warning(self, "Save Error", str(e))

# ===========================================================================
class ActivityTab(QWidget):
    def __init__(self):
        super().__init__(); self._init_ui()
    def _init_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(12,12,12,12)
        h = QHBoxLayout()
        t = QLabel("ACTIVITY FEED"); t.setStyleSheet(f"color:{C_BLUE};font-size:14px;font-weight:bold;letter-spacing:3px;")
        h.addWidget(t); h.addStretch()
        cl = QPushButton("Clear"); cl.clicked.connect(lambda: self.feed.clear()); h.addWidget(cl)
        layout.addLayout(h)
        self.feed = QTextEdit(); self.feed.setObjectName("log"); self.feed.setReadOnly(True); layout.addWidget(self.feed)
        for line in ACTIVITY.get_lines(): self.feed.append(line)
        ACTIVITY.subscribe(lambda line: QTimer.singleShot(0, lambda: self.feed.append(line)))

# ===========================================================================
# SIDEBAR — tabs as buttons + merged quick launch
# ===========================================================================
class Sidebar(QWidget):
    def __init__(self, on_nav_click, on_webapp_click):
        super().__init__()
        self._init_ui(on_nav_click, on_webapp_click)

    def _init_ui(self, on_nav, on_webapp):
        self.setObjectName("sidebar")
        self.setFixedWidth(200)
        layout = QVBoxLayout(self); layout.setSpacing(4); layout.setContentsMargins(0, 12, 0, 12)

        title = QLabel("KOGA"); title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(title)
        sub = QLabel("AGENTIC OS"); sub.setObjectName("subtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(sub)
        layout.addSpacing(12)

        # SERVICES
        sec = QLabel("SERVICES"); sec.setObjectName("section"); layout.addWidget(sec)
        self.status_labels = {}
        for svc in CFG.get("services", []):
            row = QHBoxLayout()
            dot = QLabel("●"); dot.setObjectName("dot")
            dot.setStyleSheet(f"color:{C_DIM};font-size:14px;"); dot.setFixedWidth(20)
            nm = QLabel(svc["name"]); nm.setObjectName("status_text")
            row.addWidget(dot); row.addWidget(nm); row.addStretch()
            layout.addLayout(row); self.status_labels[svc["name"]] = dot
        layout.addSpacing(12)

        # NAV TABS (native — Chat, Processes, Memory, Activity)
        sec2 = QLabel("DASHBOARD"); sec2.setObjectName("section"); layout.addWidget(sec2)
        self.nav_buttons = []
        for i, tab in enumerate(CFG.get("nav_tabs", [])):
            btn = QPushButton(tab["name"]); btn.setObjectName("nav"); btn.setCheckable(True)
            btn.setChecked(i == 0)
            btn.clicked.connect(lambda checked, idx=i: on_nav(idx))
            layout.addWidget(btn); self.nav_buttons.append(btn)
        layout.addSpacing(12)

        # WEB APPS (open embedded in Koga OS)
        sec3 = QLabel("AI APPS"); sec3.setObjectName("section"); layout.addWidget(sec3)
        for app in CFG.get("web_apps", []):
            btn = QPushButton(app["name"]); btn.setObjectName("nav")
            btn.clicked.connect(lambda checked, name=app["name"], url=app["url"]: on_webapp(name, url))
            layout.addWidget(btn)

        layout.addStretch()

    def set_active_nav(self, idx):
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == idx)

    def update_status(self, status):
        for name, dot in self.status_labels.items():
            state = status.get(name, "offline")
            color = C_GREEN if state == "online" else C_RED
            dot.setStyleSheet(f"color:{color};font-size:14px;")

# ===========================================================================
# RIGHT PANEL — system stats + clock (no quick launch)
# ===========================================================================
class RightPanel(QWidget):
    def __init__(self, quick_launch=None):
        super().__init__(); self.quick_launch = quick_launch or {}; self._init_ui()
    def _init_ui(self):
        self.setObjectName("rightpanel"); self.setFixedWidth(220)
        layout = QVBoxLayout(self); layout.setSpacing(12); layout.setContentsMargins(12,12,12,12)
        sec = QLabel("SYSTEM"); sec.setObjectName("section"); layout.addWidget(sec)
        self.cpu_bar = QProgressBar(); self.cpu_bar.setFormat("CPU: %p%"); layout.addWidget(self.cpu_bar)
        self.ram_bar = QProgressBar(); self.ram_bar.setFormat("RAM: %p%"); layout.addWidget(self.ram_bar)
        layout.addSpacing(12)
        # Quick Launch moved here
        sec2 = QLabel("QUICK LAUNCH"); sec2.setObjectName("section"); layout.addWidget(sec2)
        for name, cmd in self.quick_launch.items():
            btn = QPushButton(name); btn.setObjectName("launch")
            btn.clicked.connect(lambda checked, c=cmd: subprocess.Popen(c, shell=True))
            layout.addWidget(btn)
        layout.addStretch()
        self.clock = QLabel(); self.clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock.setStyleSheet(f"color:{C_BLUE};font-size:22px;font-weight:bold;font-family:Consolas;")
        layout.addWidget(self.clock)
        self.date = QLabel(); self.date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date.setStyleSheet(f"color:{C_DIM};font-size:11px;"); layout.addWidget(self.date)
        t = QTimer(self); t.timeout.connect(self._clock); t.start(1000); self._clock()
    def _clock(self):
        n = time.localtime(); self.clock.setText(time.strftime("%H:%M:%S", n)); self.date.setText(time.strftime("%A, %d %B", n))
    def update_stats(self, status):
        self.cpu_bar.setValue(int(status.get("cpu", 0))); self.ram_bar.setValue(int(status.get("ram", 0)))

# ===========================================================================
# STATUS BAR
# ===========================================================================
class StatusBar(QWidget):
    def __init__(self):
        super().__init__(); self.setObjectName("statusbar"); self.setFixedHeight(30)
        layout = QHBoxLayout(self); layout.setContentsMargins(12,0,12,0)
        self.labels = {}
        for svc in CFG.get("services", []):
            dot = QLabel("●"); dot.setStyleSheet(f"color:{C_DIM};font-size:12px;")
            nm = QLabel(svc["name"]); nm.setStyleSheet(f"color:{C_DIM};font-size:10px;")
            layout.addWidget(dot); layout.addWidget(nm); layout.addSpacing(12); self.labels[svc["name"]] = dot
        layout.addStretch()
        v = QLabel("KOGA OS v1.0"); v.setStyleSheet(f"color:{C_DIM};font-size:10px;"); layout.addWidget(v)
    def update_status(self, status):
        for name, dot in self.labels.items():
            state = status.get(name, "offline")
            color = C_GREEN if state == "online" else C_RED
            dot.setStyleSheet(f"color:{color};font-size:12px;")

# ===========================================================================
# COMMAND BAR
# ===========================================================================
class CommandBar(QWidget):
    def __init__(self, config):
        super().__init__(); self.setObjectName("commandbar"); self.config = config
        layout = QHBoxLayout(self); layout.setContentsMargins(12,4,12,4)
        lb = QLabel("⌘"); lb.setStyleSheet(f"color:{C_BLUE};font-size:16px;font-weight:bold;"); layout.addWidget(lb)
        self.input = QLineEdit(); self.input.setObjectName("command")
        self.input.setPlaceholderText("Ask all agents... ('restart everything', 'check Telegram', 'summarise my day')")
        self.input.returnPressed.connect(self._exec); layout.addWidget(self.input)
    def _exec(self):
        text = self.input.text().strip()
        if not text: return
        self.input.clear(); ACTIVITY.add("CommandBar", f"Command: {text}")
        tl = text.lower()
        if "restart all" in tl or "restart everything" in tl:
            for svc in self.config.get("services", []):
                if svc.get("start_cmd"):
                    try:
                        for p in psutil.process_iter(["cmdline","name"]):
                            cmd = " ".join(p.info.get("cmdline",[]) or []); nm = p.info.get("name","") or ""
                            if svc["check"].lower() in cmd.lower() or svc["check"].lower() in nm.lower(): p.terminate(); break
                        time.sleep(0.5); subprocess.Popen(svc["start_cmd"], shell=True)
                        ACTIVITY.add("CommandBar", f"Restarted {svc['name']}")
                    except: pass
        elif any(w in tl for w in ["telegram","whatsapp","hermes","server","cron"]):
            threading.Thread(target=self._vps, args=(text,), daemon=True).start()
        else:
            threading.Thread(target=self._ollama, args=(text,), daemon=True).start()
    def _vps(self, text):
        try:
            r = requests.post(self.config["vps_url"], json={"model":"hermes-agent","messages":[{"role":"user","content":text}]}, headers={"Authorization":f"Bearer {self.config.get('vps_key','')}"}, timeout=120)
            r.raise_for_status(); reply = r.json()["choices"][0]["message"]["content"]
            ACTIVITY.add("CommandBar→VPS", f"Response: {reply[:80]}")
        except Exception as e: ACTIVITY.add("CommandBar", f"VPS error: {e}", "ERROR")
    def _ollama(self, text):
        try:
            r = requests.post(self.config["ollama_url"], json={"model":self.config.get("ollama_model","gemma4:e2b"),"messages":[{"role":"user","content":text}],"stream":False}, timeout=30)
            r.raise_for_status(); reply = r.json()["choices"][0]["message"]["content"]
            ACTIVITY.add("CommandBar→Ollama", f"Response: {reply[:80]}")
        except Exception as e: ACTIVITY.add("CommandBar", f"Ollama error: {e}", "ERROR")

# ===========================================================================
# MAIN WINDOW
# ===========================================================================
class KogaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Koga Agentic OS")
        self.setGeometry(50, 50, 1400, 850); self.setMinimumSize(1000, 600)

        central = QWidget(); self.setCentralWidget(central)
        main_layout = QVBoxLayout(central); main_layout.setSpacing(0); main_layout.setContentsMargins(0,0,0,0)

        top = QHBoxLayout(); top.setSpacing(0)

        # Sidebar with nav tabs + web apps (no quick launch here)
        self.sidebar = Sidebar(self._on_nav, self._on_webapp)
        top.addWidget(self.sidebar)

        # Center: tab widget (native + embedded web apps) + command bar
        center = QVBoxLayout(); center.setSpacing(0); center.setContentsMargins(0,0,0,0)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)

        # Build native tabs
        self.chat_widget = AIChatWidget(CFG); self.tabs.addTab(self.chat_widget, "Chat")
        self.proc_tab = ProcessManagerTab(CFG); self.tabs.addTab(self.proc_tab, "Processes")
        self.mem_tab = MemoryTab(CFG); self.tabs.addTab(self.mem_tab, "Memory")
        self.activity_tab = ActivityTab(); self.tabs.addTab(self.activity_tab, "Activity")

        self.tabs.setCurrentIndex(0)
        center.addWidget(self.tabs, 1)

        self.cmd_bar = CommandBar(CFG); center.addWidget(self.cmd_bar)
        top.addLayout(center, 1)

        # Right panel with quick launch
        self.right_panel = RightPanel(CFG.get("quick_launch", {})); top.addWidget(self.right_panel)
        main_layout.addLayout(top, 1)

        self.status_bar = StatusBar(); main_layout.addWidget(self.status_bar)

        self.checker = StatusChecker()
        self.checker.status_update.connect(self._on_status); self.checker.start()
        ACTIVITY.add("KogaOS", "Koga Agentic OS started")

    def _on_nav(self, idx):
        self.sidebar.set_active_nav(idx)
        self.tabs.setCurrentIndex(idx)
        nav_names = [t["name"] for t in CFG.get("nav_tabs", [])]
        if idx < len(nav_names):
            ACTIVITY.add("Nav", f"Switched to {nav_names[idx]}")

    def _on_webapp(self, name, url):
        # Open embedded in Koga OS as a new tab
        widget = WebTabWidget(url, name)
        idx = self.tabs.addTab(widget, name)
        self.tabs.setCurrentIndex(idx)
        ACTIVITY.add("Sidebar", f"Opened {name} as tab")

    def _close_tab(self, idx):
        # Don't close the first 4 native tabs
        if idx >= 4:
            self.tabs.removeTab(idx)

    def _on_status(self, status):
        self.sidebar.update_status(status)
        self.status_bar.update_status(status)
        self.right_panel.update_stats(status)
        self.proc_tab.update_status(status)

# ===========================================================================
def main():
    app = QApplication(sys.argv); app.setStyleSheet(STYLE)
    p = QPalette(); p.setColor(QPalette.ColorRole.Window, QColor(8,13,24))
    p.setColor(QPalette.ColorRole.WindowText, QColor(200,214,229)); app.setPalette(p)
    w = KogaWindow(); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
