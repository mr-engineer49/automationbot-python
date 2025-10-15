from multiprocessing import connection
import sys
import os
import json
import threading
import time
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QProgressBar,
    QTextEdit,
    QMessageBox,
)
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtCore import Qt, Signal, QObject, QMetaObject, Q_ARG, Slot, QTimer
from connector.AirtableConnector import AirtableConnection
from connector.ProxyConnector import ProxyConnection
import requests
import random
from bot import AutomatedBot
from broweser_proxy_config import BrowserProxyConfig


CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config_files")
CONFIG_FILE = os.path.join(CONFIG_DIR, "airtable_config.json")


# ----------------------------------------
# Helper class for thread-safe logging
# ----------------------------------------
class LogSignal(QObject):
    message = Signal(str)
    progress = Signal(int)



class AppBot(QMainWindow):
    # Define a custom signal for queued updates
    _queued_signal = Signal(object, tuple)
    btn_airtable = None
    btn_proxy = None
    btn_start = None


    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Automation Bot Dashboard")
        self.setFixedSize(800, 500)
        
        # Thread-safe update queue
        self._updates = []
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._process_updates)
        self._update_timer.start(100)  # Process updates every 100ms
        
        # Connect the queued signal
        self._queued_signal.connect(self._handle_queued_update, 
                                  Qt.ConnectionType.QueuedConnection)
        
        # Track running state
        self._is_running = False

        # Colors and appearance
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#f2f4f7"))
        self.setPalette(palette)

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_widget.setLayout(layout)

        #back button
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.back)
        layout.addWidget(back_btn)

        # Title label
        title = QLabel("Automation Bot for PPC or Similar Campaigns")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Buttons
        btn_airtable = QPushButton("🔗 Connect Airtable")
        btn_airtable.clicked.connect(self.connect_airtable)
        layout.addWidget(btn_airtable)

        btn_proxy = QPushButton("🌐 Connect Proxy")
        btn_proxy.clicked.connect(self.connect_proxy)
        layout.addWidget(btn_proxy)

        btn_start = QPushButton("🚀 Start Automation")
        btn_start.clicked.connect(self.start_automation)
        layout.addWidget(btn_start)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setFixedHeight(20)
        layout.addWidget(self.progress_bar)

        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(200)
        self.log_output.setStyleSheet("background-color: #fff; border: 1px solid #ccc;")
        layout.addWidget(self.log_output)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Initialize log signal (kept for backward compatibility)
        self.log_signal = LogSignal()
        self.log_signal.message.connect(self.log)  # Connect to our new log method
        self.log_signal.progress.connect(self.update_progress)
        self.airtable_connection = None


    def safe_update(self, callback, *args):
        """Safely update UI from any thread"""
        # Use a lambda with a queued connection for simple callbacks
        if not args:
            QMetaObject.invokeMethod(self, 
                                   callback.__name__, 
                                   Qt.ConnectionType.QueuedConnection)
        else:
            # For callbacks with arguments, use a queued signal
            self._queued_signal.emit(callback, args)

    def _handle_queued_update(self, callback, args):
        """Handle queued updates with arguments"""
        try:
            callback(*args)
        except Exception as e:
            print(f"Error in UI update: {e}")

    @Slot()
    def _set_progress_value(self, value: int):
        """Internal method to set progress bar value"""
        self.progress_bar.setValue(value)

    @Slot()
    def _append_log_text(self, text: str):
        """Internal method to append text to log"""
        self.log_output.append(text)
        # Auto-scroll to bottom
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _process_updates(self):
        """Process queued UI updates"""
        if not hasattr(self, '_updates') or not self._updates:
            return
            
        updates = self._updates.copy()
        self._updates.clear()
        
        for callback, args in updates:
            try:
                callback(*args)
            except Exception as e:
                print(f"Error in update: {e}")


    def log(self, text: str):
        """Thread-safe logging"""
        self._queued_signal.emit(self._append_log_text, (text,))
        
    def _append_log_text(self, text: str):
        """Internal method to append text to log"""
        self.log_output.append(text)
        # Auto-scroll to bottom
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_progress(self, value: int):
        """Thread-safe progress update"""
        self._queued_signal.emit(self._set_progress_value, (value,))

    def back(self):
        from app import MainWindow
        self.main = MainWindow()
        self.main.show()
        self.close()    


    def connect_airtable(self):
        self.log("Connecting to Airtable...")
        self.simulate_task("Airtable connection establishing.", 5)
        self.simulate_task("Make New Connection", 10)
        self.airtable_connection = AirtableConnection()
        self.airtable_connection.show()

    def connect_proxy(self):
        self.log("Loading proxy list...")
        self.simulate_task("Proxy successfully configured.", 15)
        self.proxy_connection = ProxyConnection()
        self.proxy_connection.show()

    def start_automation(self):
        """Start the automation in a background thread."""
        if self._is_running:
            self.log("Automation is already running")
            return
            
        self._is_running = True
        self.log("🚀 Starting automation process...")
        self.update_progress(5)
        self.safe_update(self.status_label.setText, "Running automation...")

        # Disable buttons during automation
        self.safe_update(self._set_buttons_enabled, False)

        # Run in background thread
        self.worker_thread = threading.Thread(target=self._run_bot_wrapper)
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def _set_buttons_enabled(self, enabled):
        """Helper to enable/disable UI buttons"""
        for btn in [self.btn_airtable, self.btn_proxy, self.btn_start]:
            if hasattr(self, btn):
                getattr(self, btn).setEnabled(enabled)

    def _run_bot_wrapper(self):
        """Wrapper to handle thread cleanup"""
        try:
            self.run_bot_logic()
        except Exception as e:
            self.log(f"❌ Error in automation: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
        finally:
            self._cleanup_automation()

    def _cleanup_automation(self):
        """Clean up after automation completes"""
        self._is_running = False
        self.update_progress(100)
        self.safe_update(self.status_label.setText, "Ready")
        self.safe_update(self._set_buttons_enabled, True)
        self.log("✅ Automation completed")


    def run_bot_logic(self):
        """Simulated automation process (replace with your real code)."""
        try:
            self.simulate_task("Bot is starting", 5)
            #getting the connection with airtable using info from saved json for airtable_connection
            airtable_connection = AirtableConnection()
            airtable_connection.load_airtable_info()
            api_key = airtable_connection.api_key_input.text().strip()
            base_id = airtable_connection.base_id_input.text().strip()
            table_name = airtable_connection.table_name_input.text().strip()
            view_name = airtable_connection.view_name_input.text().strip()
            self.simulate_task("Configuration loaded from file.", 20)

            if not api_key:
                self.simulate_task("Error: AIRTABLE_API_KEY not found in environment variables.", 25)
                print("Error: AIRTABLE_API_KEY not found in environment variables.")
                return

            self.simulate_task("Fetching new items from Airtable...", 30)
            print("Fetching new items from Airtable...")


            url = f"https://api.airtable.com/v0/{base_id}/{table_name}"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            params = {"view": view_name}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            records = data.get('records', [])

            if not records:
                self.simulate_task("No logs found from Airtable!", 35)
                print(" No records found.")
                return

            self.simulate_task("Airtable data received.", 35)
            urls = []
            for record in records:
                fields = record.get('fields', {})
                title = fields.get('Campaign Name')
                link = fields.get('Affiliate URl')
                script_area = fields.get('Script Area')
                if link:
                    urls.append((title, link, script_area))

            if not urls:
                self.simulate_task("No urls found. ", 35)
                print(" No URLs found.")
                return
            title, random_url, script_area = random.choice(urls)
            self.simulate_task(f"CampaignName: {title} | Selected URl: {random_url}", 40)
            print(f"CampaignName: {title} | Selected URl: {random_url}")

            proxy_bot = BrowserProxyConfig()
            proxy = proxy_bot.load_proxifly_proxy_from_json()
            bot = BrowserProxyConfig(proxy=proxy)
            if not proxy:
                self.simulate_task("No proxies available.", 40)
                print(" No proxies available.")
                return
            print(f" Using Proxy: {proxy}")
            self.simulate_task(f" Using Proxy: {proxy}", 45)

            browser_bot = BrowserProxyConfig(proxy=proxy)
            browser_bot.browser_type_google()
            browser_bot.open_url(random_url)
            self.simulate_task("Bot opening URL...", 70)
            self.simulate_task("Starting to excecute the script", 75)
            try:
                if browser_bot:
                    browser_bot.driver.execute_script(script_area)
                    self.simulate_task("Script executed successfully with browser bot.", 80)
                elif bot:
                    bot.driver.execute_script(script_area)
                    self.simulate_task("Script executed successfully with bot.", 80)
                else:
                    raise Exception("No script area found.")
            except Exception as e:
                self.simulate_task(f"Error: {e}", 80)
            self.simulate_task("Script finished. Closing browser.", 80)
            browser_bot.close()
            self.simulate_task("Script finished. Closing browser.", 90)
            self.status_label.setText("Completed")
            self.simulate_task("All tasks done.", 100)
        except Exception as e:
            self.status_label.setText("Error occurred")
            self.simulate_task(f"Error: {e}", 70)


    def simulate_task(self, message: str, progress: int):
        """Quick feedback for short tasks."""
        self.log(message)  # Use thread-safe log method
        self.update_progress(progress)  # Use thread-safe progress update

    def show_error(self, message: str):
        msg = QMessageBox(self)
        msg.setWindowTitle("Error")
        msg.setText(message)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppBot()
    window.show()
    sys.exit(app.exec())
