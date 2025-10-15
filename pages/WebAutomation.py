# enhanced_web_automation.py
import sys
import os
import json
import time
import random
import traceback
from typing import List, Dict, Optional

import requests
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar,
    QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QSizePolicy
)

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import WebDriverException

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config_files")
os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")
PROXIES_DEFAULT = os.path.join(os.path.dirname(__file__), "proxies.json")



def load_settings() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh) or {}
    except Exception:
        return {}

def save_settings(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)

def load_proxies_file(path: str) -> List[Dict]:
    if not path or not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []

def normalize_proxy(item: Dict) -> Optional[str]:
    """Return 'protocol://ip:port' or None"""
    if not item:
        return None
    if isinstance(item, str):
        return item
    if "proxy" in item and isinstance(item["proxy"], str):
        return item["proxy"]
    proto = item.get("protocol", "http")
    ip = item.get("ip") or item.get("host")
    port = item.get("port")
    if ip and port:
        return f"{proto}://{ip}:{port}"
    return None

def proxy_is_working(proxy_url: str, timeout=6.0) -> bool:
    try:
        proxies = {"http": proxy_url, "https": proxy_url}
        r = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


class AirtableService:
    def __init__(self, api_key: str, base_id: str, table_name: str, view_name: str = None):
        self.api_key = api_key
        self.base_id = base_id
        self.table_name = table_name
        self.view_name = view_name
        self.api_url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def fetch_all_records(self, page_size: int = 100) -> List[Dict]:
        params = {}
        if self.view_name:
            params["view"] = self.view_name
        all_records = []
        offset = None
        while True:
            if offset:
                params["offset"] = offset
            r = requests.get(self.api_url, headers=self.headers, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
            recs = data.get("records", [])
            all_records.extend(recs)
            offset = data.get("offset")
            if not offset:
                break
        return all_records


class AutomationThread(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    finished_signal = Signal()

    def __init__(self, records: List[Dict], proxies: List[Dict], headless=False, keep_browser=False):
        super().__init__()
        self.records = records[:]  # copy
        self.proxies = proxies[:]  # list of proxy item dicts
        self.headless = headless
        self.keep_browser = keep_browser
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def pick_working_proxy(self) -> Optional[str]:
        random.shuffle(self.proxies)
        for p in self.proxies:
            proxy_str = normalize_proxy(p)
            if not proxy_str:
                continue
            self.log_signal.emit(f"Testing proxy: {proxy_str}")
            if proxy_is_working(proxy_str, timeout=6):
                self.log_signal.emit(f"Proxy OK: {proxy_str}")
                return proxy_str
            self.log_signal.emit(f"Proxy failed: {proxy_str}")
        return None

    def build_chrome_driver(self, proxy: Optional[str]):
        options = ChromeOptions()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        if proxy:
            options.add_argument(f"--proxy-server={proxy}")
            self.log_signal.emit(f"Launching Chrome with proxy: {proxy}")
        else:
            self.log_signal.emit("Launching Chrome without proxy")
        driver = webdriver.Chrome(options=options)
        return driver

    def run(self):
        try:
            total = len(self.records)
            if total == 0:
                self.log_signal.emit("No records to process.")
                self.finished_signal.emit()
                return

            for idx, rec in enumerate(self.records, start=1):
                if self._stop_flag:
                    self.log_signal.emit("Stop requested. Ending worker.")
                    break

                fields = rec.get("fields", {})
                title = fields.get("Campaign Name") or fields.get("Name") or "Untitled"
                url = fields.get("Affiliate URl") or fields.get("Affiliate URL") or fields.get("url") or fields.get("link")
                script_area = fields.get("Script Area") or fields.get("Script") or fields.get("script_area")

                self.log_signal.emit(f"[{idx}/{total}] {title} -> {url}")
                self.progress_signal.emit(int((idx - 1) / total * 100))

                if not url:
                    self.log_signal.emit("No URL — skipping")
                    continue

                # choose a proxy for this session (optional)
                proxy_str = None
                if self.proxies:
                    proxy_str = self.pick_working_proxy()

                # start Chrome
                try:
                    driver = self.build_chrome_driver(proxy_str)
                except WebDriverException as e:
                    self.log_signal.emit(f"Failed to start Chrome: {e}")
                    continue

                try:
                    driver.get(url)
                    time.sleep(2)  # basic wait

                    if script_area and isinstance(script_area, str) and script_area.strip():
                        try:
                            self.log_signal.emit("Executing JavaScript from Airtable...")
                            driver.execute_script(script_area)
                            self.log_signal.emit("JS executed.")
                        except Exception as e:
                            self.log_signal.emit(f"JS execution error: {e}")

                    # optional: extra Selenium interactions could be performed here

                    time.sleep(1 + random.random())  # polite delay

                except Exception as e:
                    self.log_signal.emit(f"Runtime error during automation: {e}\n{traceback.format_exc()}")
                finally:
                    if not self.keep_browser:
                        try:
                            driver.quit()
                        except Exception:
                            pass

                self.progress_signal.emit(int(idx / total * 100))

            self.log_signal.emit("Automation worker finished.")
        except Exception as e:
            self.log_signal.emit(f"Worker crashed: {e}\n{traceback.format_exc()}")
        finally:
            self.finished_signal.emit()



class WebAutomationBot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Web Automation Dashboard")
        self.setMinimumSize(1000, 700)

        self.settings = load_settings()
        self.proxies: List[Dict] = []
        self.records: List[Dict] = []
        self.worker: Optional[AutomationThread] = None

        # central widget & layout
        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        #back button
        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(self.back)
        tabs.addTab(self.back_btn, "Back")

        # Overview tab
        self.overview_tab = QWidget()
        self._build_overview_tab()
        tabs.addTab(self.overview_tab, "Overview")

        # Campaigns tab
        self.campaigns_tab = QWidget()
        self._build_campaigns_tab()
        tabs.addTab(self.campaigns_tab, "Campaigns")

        # Proxies tab
        self.proxies_tab = QWidget()
        self._build_proxies_tab()
        tabs.addTab(self.proxies_tab, "Proxies")

        # Runner tab
        self.runner_tab = QWidget()
        self._build_runner_tab()
        tabs.addTab(self.runner_tab, "Runner")

        # Settings tab
        self.settings_tab = QWidget()
        self._build_settings_tab()
        tabs.addTab(self.settings_tab, "Settings")

        # Signals for worker updates handled by thread
        self.append_log("App ready.")



    def _build_overview_tab(self):
        layout = QVBoxLayout()
        self.overview_tab.setLayout(layout)

        self.lbl_status = QLabel("Status: Ready")
        self.lbl_status.setStyleSheet("font-weight:bold;")
        layout.addWidget(self.lbl_status)

        row = QHBoxLayout()
        self.lbl_count_proxies = QLabel("Proxies: 0")
        self.lbl_count_campaigns = QLabel("Campaigns: 0")
        row.addWidget(self.lbl_count_proxies)
        row.addWidget(self.lbl_count_campaigns)
        row.addStretch()
        layout.addLayout(row)

        btn_row = QHBoxLayout()
        self.btn_fetch = QPushButton("Fetch Airtable")
        self.btn_fetch.clicked.connect(self.fetch_airtable_records)
        self.btn_refresh_proxies = QPushButton("Load Proxies")
        self.btn_refresh_proxies.clicked.connect(self.load_proxies_from_ui)
        self.btn_run_all = QPushButton("Run All Campaigns")
        self.btn_run_all.clicked.connect(self.run_all_campaigns)
        btn_row.addWidget(self.btn_fetch)
        btn_row.addWidget(self.btn_refresh_proxies)
        btn_row.addWidget(self.btn_run_all)
        layout.addLayout(btn_row)

        self.overview_log = QTextEdit()
        self.overview_log.setReadOnly(True)
        self.overview_log.setFixedHeight(200)
        layout.addWidget(self.overview_log)

    def _build_campaigns_tab(self):
        layout = QVBoxLayout()
        self.campaigns_tab.setLayout(layout)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Record ID", "Campaign", "URL", "Script Area"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        row = QHBoxLayout()
        self.btn_preview = QPushButton("Preview Selected")
        self.btn_preview.clicked.connect(self.preview_selected)
        self.btn_run_selected = QPushButton("Run Selected")
        self.btn_run_selected.clicked.connect(self.run_selected_campaigns)
        row.addWidget(self.btn_preview)
        row.addWidget(self.btn_run_selected)
        layout.addLayout(row)

    def _build_proxies_tab(self):
        layout = QVBoxLayout()
        self.proxies_tab.setLayout(layout)

        row1 = QHBoxLayout()
        self.proxy_path_input = QLineEdit(self.settings.get("proxy_file", PROXIES_DEFAULT))
        self.btn_browse_proxies = QPushButton("Browse proxies.json")
        self.btn_browse_proxies.clicked.connect(self.browse_proxies)
        row1.addWidget(self.proxy_path_input)
        row1.addWidget(self.btn_browse_proxies)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.btn_load_proxies = QPushButton("Load & Validate Proxies")
        self.btn_load_proxies.clicked.connect(self.load_proxies_from_ui)
        self.btn_test_one = QPushButton("Test Random Proxy")
        self.btn_test_one.clicked.connect(self.test_random_proxy)
        row2.addWidget(self.btn_load_proxies)
        row2.addWidget(self.btn_test_one)
        layout.addLayout(row2)

        self.proxies_log = QTextEdit()
        self.proxies_log.setReadOnly(True)
        self.proxies_log.setFixedHeight(200)
        layout.addWidget(self.proxies_log)

    def _build_runner_tab(self):
        layout = QVBoxLayout()
        self.runner_tab.setLayout(layout)

        row = QHBoxLayout()
        self.headless_input = QLineEdit("False")
        self.keep_browser_input = QLineEdit("False")
        row.addWidget(QLabel("Headless:"))
        row.addWidget(self.headless_input)
        row.addWidget(QLabel("Keep browser open:"))
        row.addWidget(self.keep_browser_input)
        layout.addLayout(row)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        row2 = QHBoxLayout()
        self.btn_start = QPushButton("Start Worker")
        self.btn_start.clicked.connect(self.start_worker_from_ui)
        self.btn_stop = QPushButton("Stop Worker")
        self.btn_stop.clicked.connect(self.stop_worker)
        row2.addWidget(self.btn_start)
        row2.addWidget(self.btn_stop)
        layout.addLayout(row2)

        self.runner_log = QTextEdit()
        self.runner_log.setReadOnly(True)
        self.runner_log.setFixedHeight(300)
        layout.addWidget(self.runner_log)

    def _build_settings_tab(self):
        layout = QVBoxLayout()
        self.settings_tab.setLayout(layout)

        cfg = self.settings
        self.api_key_input = QLineEdit(cfg.get("api_key", ""))
        self.base_id_input = QLineEdit(cfg.get("base_id", ""))
        self.table_input = QLineEdit(cfg.get("table_name", ""))
        self.view_input = QLineEdit(cfg.get("view_name", ""))

        layout.addWidget(QLabel("Airtable API Key:"))
        layout.addWidget(self.api_key_input)
        layout.addWidget(QLabel("Base ID:"))
        layout.addWidget(self.base_id_input)
        layout.addWidget(QLabel("Table Name:"))
        layout.addWidget(self.table_input)
        layout.addWidget(QLabel("View Name:"))
        layout.addWidget(self.view_input)

        row = QHBoxLayout()
        self.btn_save_settings = QPushButton("Save Settings")
        self.btn_save_settings.clicked.connect(self.save_settings)
        row.addWidget(self.btn_save_settings)
        layout.addLayout(row)

    # -----------------------
    # UI actions & helpers
    # -----------------------
    def append_log(self, txt: str, which="overview"):
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {txt}"
        if which == "overview":
            self.overview_log.append(line)
        elif which == "proxies":
            self.proxies_log.append(line)
        elif which == "runner":
            self.runner_log.append(line)
        else:
            self.overview_log.append(line)



    def save_settings(self):
        self.settings["api_key"] = self.api_key_input.text().strip()
        self.settings["base_id"] = self.base_id_input.text().strip()
        self.settings["table_name"] = self.table_input.text().strip()
        self.settings["view_name"] = self.view_input.text().strip()
        self.settings["proxy_file"] = self.proxy_path_input.text().strip()
        save_settings(self.settings)
        QMessageBox.information(self, "Saved", f"Settings saved to {CONFIG_FILE}")
        self.append_log("Settings saved.")

    def browse_proxies(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select proxies.json", os.path.expanduser("~"), "JSON files (*.json)")
        if path:
            self.proxy_path_input.setText(path)
            self.append_log(f"Selected proxy file: {path}", "proxies")

    def back(self):
        from app import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()    

    def load_proxies_from_ui(self):
        path = self.proxy_path_input.text().strip()
        if not path:
            path = PROXIES_DEFAULT
        items = load_proxies_file(path)
        if not items:
            QMessageBox.warning(self, "No proxies", "No proxies found or file invalid.")
            return
        self.proxies = items
        self.lbl_count_proxies.setText(f"Proxies: {len(self.proxies)}")
        self.append_log(f"Loaded {len(self.proxies)} proxy items.", "proxies")

        # Run a quick validation test (non-blocking naive approach)
        good = 0
        for p in random.sample(self.proxies, min(6, len(self.proxies))):
            pstr = normalize_proxy(p)
            ok = proxy_is_working(pstr) if pstr else False
            self.append_log(f"Tested {pstr} => {ok}", "proxies")
            if ok:
                good += 1
        self.append_log(f"Sample testing: {good} working among sampled proxies.", "proxies")

    def test_random_proxy(self):
        if not self.proxies:
            QMessageBox.information(self, "No proxies", "Load proxies first.")
            return
        p = random.choice(self.proxies)
        pstr = normalize_proxy(p)
        ok = proxy_is_working(pstr)
        QMessageBox.information(self, "Proxy Test", f"{pstr}\nWorking: {ok}")

    def fetch_airtable_records(self):
        api_key = self.api_key_input.text().strip() or self.settings.get("api_key")
        base_id = self.base_id_input.text().strip() or self.settings.get("base_id")
        table_name = self.table_input.text().strip() or self.settings.get("table_name")
        view_name = self.view_input.text().strip() or self.settings.get("view_name")

        if not all([api_key, base_id, table_name]):
            QMessageBox.warning(self, "Missing", "Please provide API Key, Base ID, and Table Name in Settings.")
            return

        self.append_log("Fetching Airtable records...")
        try:
            svc = AirtableService(api_key, base_id, table_name, view_name)
            records = svc.fetch_all_records()
            self.records = records
            self.lbl_count_campaigns.setText(f"Campaigns: {len(records)}")
            self.append_log(f"Fetched {len(records)} records.")
            self.populate_table(records)
        except Exception as e:
            QMessageBox.critical(self, "Airtable Error", str(e))
            self.append_log(f"Error fetching Airtable: {e}")

    def populate_table(self, records: List[Dict]):
        self.table.setRowCount(0)
        for rec in records:
            fields = rec.get("fields", {})
            rec_id = rec.get("id", "")
            title = fields.get("Campaign Name") or fields.get("Name") or ""
            url = fields.get("Affiliate URl") or fields.get("Affiliate URL") or fields.get("url") or ""
            script_area = fields.get("Script Area") or fields.get("Script") or ""
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(rec_id))
            self.table.setItem(row, 1, QTableWidgetItem(title))
            self.table.setItem(row, 2, QTableWidgetItem(url))
            item = QTableWidgetItem(script_area[:120] + ("..." if len(script_area) > 120 else ""))
            self.table.setItem(row, 3, item)

    def preview_selected(self):
        sel = self.table.selectedItems()
        if not sel:
            QMessageBox.information(self, "Select", "Select a row first.")
            return
        row = sel[0].row()
        rec_id = self.table.item(row, 0).text()
        for rec in self.records:
            if rec.get("id") == rec_id:
                fields = rec.get("fields", {})
                url = fields.get("Affiliate URl") or fields.get("Affiliate URL") or ""
                script_area = fields.get("Script Area") or fields.get("Script") or ""
                dlg = QMessageBox(self)
                dlg.setWindowTitle("Preview")
                dlg.setText(f"URL:\n{url}\n\nScript:\n{script_area[:300] + ('...' if len(script_area) > 300 else '')}")
                dlg.exec()
                return



    def start_worker_from_ui(self):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "Worker", "Worker already running.")
            return
        if not self.records:
            QMessageBox.warning(self, "No records", "Fetch Airtable records first.")
            return
        headless = self.headless_input.text().strip().lower() in ("1", "true", "yes")
        keep_browser = self.keep_browser_input.text().strip().lower() in ("1", "true", "yes")
        # use all proxies loaded
        worker = AutomationThread(self.records, self.proxies, headless=headless, keep_browser=keep_browser)
        worker.log_signal.connect(lambda t: self.append_log(t, "runner"))
        worker.progress_signal.connect(self.progress.setValue)
        worker.finished_signal.connect(self.worker_finished)
        self.worker = worker
        worker.start()
        self.append_log("Worker started.", "runner")
        self.lbl_status.setText("Status: Running")

    def worker_finished(self):
        self.append_log("Worker finished.", "runner")
        self.lbl_status.setText("Status: Idle")
        self.worker = None

    def stop_worker(self):
        if not self.worker:
            QMessageBox.information(self, "Not running", "No worker running.")
            return
        self.worker.stop()
        self.append_log("Stop requested for worker.", "runner")

    def run_selected_campaigns(self):
        sel = self.table.selectedItems()
        if not sel:
            QMessageBox.information(self, "Select", "Select some rows first.")
            return
        rows = sorted({item.row() for item in sel})
        selected_recs = []
        for r in rows:
            rec_id = self.table.item(r, 0).text()
            for rec in self.records:
                if rec.get("id") == rec_id:
                    selected_recs.append(rec)
                    break
        if not selected_recs:
            QMessageBox.information(self, "No selection", "No matching records found.")
            return
        # start short-run worker with selected
        headless = self.headless_input.text().strip().lower() in ("1", "true", "yes")
        keep_browser = self.keep_browser_input.text().strip().lower() in ("1", "true", "yes")
        worker = AutomationThread(selected_recs, self.proxies, headless=headless, keep_browser=keep_browser)
        worker.log_signal.connect(lambda t: self.append_log(t, "runner"))
        worker.progress_signal.connect(self.progress.setValue)
        worker.finished_signal.connect(self.worker_finished)
        self.worker = worker
        worker.start()
        self.append_log(f"Worker started for {len(selected_recs)} selected records.", "runner")

    def run_all_campaigns(self):
        if not self.records:
            QMessageBox.information(self, "No records", "Fetch records first.")
            return
        self.start_worker_from_ui()


