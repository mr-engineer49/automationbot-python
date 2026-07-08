# enhanced_web_automation.py
import sys
import os
import json
import time
import random
import threading
import traceback
from typing import List, Dict, Optional

import requests
from PySide6.QtCore import Qt, QThread, Signal, Slot, QMetaObject, Q_ARG, QDateTime, QTimer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar,
    QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QSizePolicy, QDialog, QFormLayout, QComboBox, QDateTimeEdit,
    QSpinBox, QCheckBox, QSplitter, QGroupBox, QInputDialog
)

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import WebDriverException

# Import existing automation integrations
from pages.automations_integrations.make_automation import MakePage
from pages.automations_integrations.n8n_automation import N8nPage

# Configuration directory
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config_files")
os.makedirs(CONFIG_DIR, exist_ok=True)


# ==============================
# UTILITY MODAL CLASSES
# ==============================

class SchedulerDialog(QDialog):
    """Task Scheduler Modal"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⏰ Task Scheduler")
        self.setMinimumSize(500, 400)
        self.scheduler_file = os.path.join(CONFIG_DIR, "scheduled_tasks.json")
        self.scheduled_tasks = self._load_tasks_from_file()
        self._build_ui()
        # Load tasks into table after UI is built
        QTimer.singleShot(0, self.refresh_table)

    def _load_tasks_from_file(self):
        """Load scheduled tasks from JSON file"""
        if not os.path.exists(self.scheduler_file):
            return []
        try:
            with open(self.scheduler_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading scheduled tasks: {e}")
            return []

    def _save_tasks_to_file(self):
        """Save scheduled tasks to JSON file"""
        try:
            with open(self.scheduler_file, "w", encoding="utf-8") as f:
                json.dump(self.scheduled_tasks, f, indent=2)
            return True
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save tasks: {e}")
            return False

    def _build_ui(self):
        layout = QVBoxLayout()

        # Task Configuration
        config_group = QGroupBox("Schedule New Task")
        config_layout = QFormLayout()

        self.task_name = QLineEdit()
        self.task_name.setPlaceholderText("Task name")
        config_layout.addRow("Task Name:", self.task_name)

        self.task_type = QComboBox()
        self.task_type.addItems(["Run Campaign", "Fetch Airtable", "Custom Script", "API Request"])
        self.task_type.currentTextChanged.connect(self._on_task_type_changed)
        config_layout.addRow("Task Type:", self.task_type)

        # Quick load buttons for integration
        quick_load_row = QHBoxLayout()
        self.load_script_btn = QPushButton("📜 Load from Scripts")
        self.load_script_btn.clicked.connect(self._load_from_scripts)
        self.load_script_btn.setEnabled(False)
        self.load_api_btn = QPushButton("📡 Load from API History")
        self.load_api_btn.clicked.connect(self._load_from_api_history)
        self.load_api_btn.setEnabled(False)
        quick_load_row.addWidget(self.load_script_btn)
        quick_load_row.addWidget(self.load_api_btn)
        config_layout.addRow(quick_load_row)

        self.schedule_time = QDateTimeEdit()
        self.schedule_time.setCalendarPopup(True)
        self.schedule_time.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.schedule_time.setDateTime(QDateTime.currentDateTime())
        config_layout.addRow("Schedule Time:", self.schedule_time)

        self.repeat_interval = QSpinBox()
        self.repeat_interval.setRange(0, 365)
        self.repeat_interval.setValue(0)
        self.repeat_interval.setSuffix(" days")
        config_layout.addRow("Repeat Every:", self.repeat_interval)

        self.enabled_check = QCheckBox("Enable Task")
        self.enabled_check.setChecked(True)
        config_layout.addRow("", self.enabled_check)

        add_btn = QPushButton("Add Schedule")
        add_btn.clicked.connect(self.add_task)
        config_layout.addRow(add_btn)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Scheduled Tasks List
        tasks_group = QGroupBox("Scheduled Tasks")
        tasks_layout = QVBoxLayout()
        self.tasks_table = QTableWidget(0, 4)
        self.tasks_table.setHorizontalHeaderLabels(["Task Name", "Type", "Schedule", "Status"])
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tasks_layout.addWidget(self.tasks_table)

        btn_row = QHBoxLayout()
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_task)
        run_now_btn = QPushButton("Run Now")
        run_now_btn.clicked.connect(self.run_task_now)
        btn_row.addWidget(delete_btn)
        btn_row.addWidget(run_now_btn)
        tasks_layout.addLayout(btn_row)

        tasks_group.setLayout(tasks_layout)
        layout.addWidget(tasks_group)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def add_task(self):
        name = self.task_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a task name")
            return

        task = {
            "name": name,
            "type": self.task_type.currentText(),
            "schedule": self.schedule_time.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            "repeat": self.repeat_interval.value(),
            "enabled": self.enabled_check.isChecked()
        }
        self.scheduled_tasks.append(task)
        if self._save_tasks_to_file():
            QTimer.singleShot(0, self.refresh_table)
            self.task_name.clear()
            QMessageBox.information(self, "Success", "Task scheduled successfully")

    def delete_task(self):
        row = self.tasks_table.currentRow()
        if row >= 0:
            del self.scheduled_tasks[row]
            self._save_tasks_to_file()
            QTimer.singleShot(0, self.refresh_table)

    def run_task_now(self):
        row = self.tasks_table.currentRow()
        if row >= 0:
            task = self.scheduled_tasks[row]
            task_type = task['type']
            task_name = task['name']

            if task_type == "Custom Script":
                # Load and execute the custom script
                scripts_file = os.path.join(CONFIG_DIR, "custom_scripts.json")
                if os.path.exists(scripts_file):
                    try:
                        with open(scripts_file, "r", encoding="utf-8") as f:
                            scripts = json.load(f)
                        # Find the script by name
                        script = next((s for s in scripts if s['name'] == task_name), None)
                        if script:
                            self._execute_script_direct(script)
                        else:
                            QMessageBox.warning(self, "Not Found", f"Script '{task_name}' not found")
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Failed to load script: {e}")
                else:
                    QMessageBox.warning(self, "Not Found", "No custom scripts saved yet")

            elif task_type == "API Request":
                # Load and execute the API request
                api_file = os.path.join(CONFIG_DIR, "api_request_history.json")
                if os.path.exists(api_file):
                    try:
                        with open(api_file, "r", encoding="utf-8") as f:
                            history = json.load(f)
                        # Find the API request by name (using URL as identifier)
                        api_req = next((req for req in history if req['url'] == task_name), None)
                        if api_req:
                            self._execute_api_direct(api_req)
                        else:
                            QMessageBox.warning(self, "Not Found", f"API request '{task_name}' not found")
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Failed to load API request: {e}")
                else:
                    QMessageBox.warning(self, "Not Found", "No API requests saved yet")

            elif task_type == "Run Campaign":
                QMessageBox.information(self, "Campaign", f"Would run campaign: {task_name}\n(Requires campaign configuration)")

            elif task_type == "Fetch Airtable":
                QMessageBox.information(self, "Airtable", f"Would fetch from Airtable: {task_name}\n(Requires Airtable configuration)")

            else:
                QMessageBox.information(self, "Running", f"Running task: {task_name}")

    def _execute_script_direct(self, script):
        """Execute a script directly without opening the dialog"""
        dialog = CustomScriptsDialog(self)
        dialog.scripts = [script]  # Set the script to execute
        dialog.execute_script()

    def _execute_api_direct(self, api_req):
        """Execute an API request directly without opening the dialog"""
        dialog = APIRunnerDialog(self)
        dialog.method_combo.setCurrentText(api_req['method'])
        dialog.url_input.setText(api_req['url'])
        dialog.headers_input.setPlainText(api_req['headers'])
        dialog.body_input.setPlainText(api_req['body'])
        dialog.send_request()

    def _on_task_type_changed(self, text):
        """Enable/disable load buttons based on task type"""
        self.load_script_btn.setEnabled(text == "Custom Script")
        self.load_api_btn.setEnabled(text == "API Request")

    def _load_from_scripts(self):
        """Load script names for easy scheduling"""
        scripts_file = os.path.join(CONFIG_DIR, "custom_scripts.json")
        if not os.path.exists(scripts_file):
            QMessageBox.information(self, "No Scripts", "No custom scripts found. Create some first!")
            return

        try:
            with open(scripts_file, "r", encoding="utf-8") as f:
                scripts = json.load(f)

            if not scripts:
                QMessageBox.information(self, "No Scripts", "No custom scripts found.")
                return

            # Create a simple selection dialog
            script_names = [s['name'] for s in scripts]
            name, ok = QInputDialog.getItem(self, "Select Script", "Choose a script to schedule:", script_names, 0, False)
            if ok and name:
                self.task_name.setText(name)
                self.task_type.setCurrentText("Custom Script")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load scripts: {e}")

    def _load_from_api_history(self):
        """Load API request URLs for easy scheduling"""
        api_file = os.path.join(CONFIG_DIR, "api_request_history.json")
        if not os.path.exists(api_file):
            QMessageBox.information(self, "No API History", "No API requests found. Make some requests first!")
            return

        try:
            with open(api_file, "r", encoding="utf-8") as f:
                history = json.load(f)

            if not history:
                QMessageBox.information(self, "No API History", "No API requests found.")
                return

            # Create a simple selection dialog
            api_urls = [req['url'] for req in history]
            url, ok = QInputDialog.getItem(self, "Select API Request", "Choose an API request to schedule:", api_urls, 0, False)
            if ok and url:
                self.task_name.setText(url)
                self.task_type.setCurrentText("API Request")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load API history: {e}")

    @Slot()
    def refresh_table(self):
        self.tasks_table.setRowCount(0)
        for task in self.scheduled_tasks:
            row = self.tasks_table.rowCount()
            self.tasks_table.insertRow(row)
            self.tasks_table.setItem(row, 0, QTableWidgetItem(task['name']))
            self.tasks_table.setItem(row, 1, QTableWidgetItem(task['type']))
            self.tasks_table.setItem(row, 2, QTableWidgetItem(task['schedule']))
            status = "Enabled" if task['enabled'] else "Disabled"
            self.tasks_table.setItem(row, 3, QTableWidgetItem(status))


class CustomScriptsDialog(QDialog):
    """Custom Scripts Manager Modal"""
    log_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📜 Custom Scripts Manager")
        self.setMinimumSize(600, 500)
        self.scripts_file = os.path.join(CONFIG_DIR, "custom_scripts.json")
        self.scripts = self._load_scripts_from_file()
        self.log_signal.connect(self._append_log)
        self._build_ui()
        # Load scripts into table after UI is built
        QTimer.singleShot(0, self.refresh_table)

    def _load_scripts_from_file(self):
        """Load scripts from JSON file"""
        if not os.path.exists(self.scripts_file):
            return []
        try:
            with open(self.scripts_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading scripts: {e}")
            return []

    def _save_scripts_to_file(self):
        """Save scripts to JSON file"""
        try:
            with open(self.scripts_file, "w", encoding="utf-8") as f:
                json.dump(self.scripts, f, indent=2)
            return True
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save scripts: {e}")
            return False

    def _build_ui(self):
        layout = QVBoxLayout()

        # Script Editor
        editor_group = QGroupBox("Script Editor")
        editor_layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.script_name = QLineEdit()
        self.script_name.setPlaceholderText("Script name")
        form_layout.addRow("Script Name:", self.script_name)

        self.script_language = QComboBox()
        self.script_language.addItems(["JavaScript", "Python", "Shell/Bash"])
        form_layout.addRow("Language:", self.script_language)

        editor_layout.addLayout(form_layout)

        self.script_editor = QTextEdit()
        self.script_editor.setPlaceholderText("// Enter your script here...")
        self.script_editor.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")
        self.script_editor.setMinimumHeight(200)
        editor_layout.addWidget(QLabel("Script Code:"))
        editor_layout.addWidget(self.script_editor)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾 Save Script")
        save_btn.clicked.connect(self.save_script)
        load_btn = QPushButton("📂 Load Script")
        load_btn.clicked.connect(self.load_script)
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.clear_editor)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(load_btn)
        btn_row.addWidget(clear_btn)
        editor_layout.addLayout(btn_row)

        editor_group.setLayout(editor_layout)
        layout.addWidget(editor_group)

        # Execution Log
        log_group = QGroupBox("Execution Log")
        log_layout = QVBoxLayout()
        self.execution_log = QTextEdit()
        self.execution_log.setReadOnly(True)
        self.execution_log.setStyleSheet("font-family: Consolas, monospace; font-size: 11px; background-color: #1e1e1e; color: #00ff00;")
        self.execution_log.setMinimumHeight(150)
        log_layout.addWidget(self.execution_log)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # Saved Scripts List
        list_group = QGroupBox("Saved Scripts")
        list_layout = QVBoxLayout()
        self.scripts_table = QTableWidget(0, 3)
        self.scripts_table.setHorizontalHeaderLabels(["Name", "Language", "Created"])
        self.scripts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        list_layout.addWidget(self.scripts_table)

        list_btn_row = QHBoxLayout()
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.clicked.connect(self.edit_script)
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.clicked.connect(self.delete_script)
        execute_btn = QPushButton("▶️ Execute")
        execute_btn.clicked.connect(self.execute_script)
        create_api_btn = QPushButton("📡 Create from API")
        create_api_btn.clicked.connect(self.create_from_api)
        schedule_btn = QPushButton("⏰ Schedule This")
        schedule_btn.clicked.connect(self.schedule_current_script)
        list_btn_row.addWidget(edit_btn)
        list_btn_row.addWidget(delete_btn)
        list_btn_row.addWidget(execute_btn)
        list_btn_row.addWidget(create_api_btn)
        list_btn_row.addWidget(schedule_btn)
        list_layout.addLayout(list_btn_row)

        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def save_script(self):
        name = self.script_name.text().strip()
        code = self.script_editor.toPlainText()
        if not name or not code:
            QMessageBox.warning(self, "Error", "Please enter script name and code")
            return

        # Check if updating existing script
        existing_index = -1
        for i, script in enumerate(self.scripts):
            if script['name'] == name:
                existing_index = i
                break

        script = {
            "name": name,
            "language": self.script_language.currentText(),
            "code": code,
            "created": time.strftime("%Y-%m-%d %H:%M:%S") if existing_index == -1 else self.scripts[existing_index]['created']
        }

        if existing_index >= 0:
            self.scripts[existing_index] = script  # Update existing
        else:
            self.scripts.append(script)  # Add new

        if self._save_scripts_to_file():
            QTimer.singleShot(0, self.refresh_table)
            self.script_name.clear()
            self.script_editor.clear()
            QMessageBox.information(self, "Success", "Script saved successfully")

    def load_script(self):
        row = self.scripts_table.currentRow()
        if row >= 0:
            script = self.scripts[row]
            self.script_name.setText(script['name'])
            self.script_language.setCurrentText(script['language'])
            self.script_editor.setPlainText(script['code'])

    def edit_script(self):
        self.load_script()

    def delete_script(self):
        row = self.scripts_table.currentRow()
        if row >= 0:
            del self.scripts[row]
            self._save_scripts_to_file()
            QTimer.singleShot(0, self.refresh_table)

    def execute_script(self):
        row = self.scripts_table.currentRow()
        if row >= 0:
            script = self.scripts[row]
            # Clear log on main thread
            self.execution_log.clear()
            self.log_signal.emit(f"=== Executing: {script['name']} ===")
            self.log_signal.emit(f"Language: {script['language']}")
            self.log_signal.emit(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.log_signal.emit("-" * 50)

            def worker():
                try:
                    language = script['language']
                    code = script['code']

                    if language == "Python":
                        self.log_signal.emit("📝 Executing Python script...")
                        try:
                            # Create a namespace for execution
                            namespace = {'__name__': '__main__'}
                            exec(code, namespace)
                            self.log_signal.emit("✅ Python script executed successfully")
                        except Exception as e:
                            self.log_signal.emit(f"❌ Python execution error: {str(e)}")
                            import traceback
                            self.log_signal.emit(traceback.format_exc())

                    elif language == "JavaScript":
                        self.log_signal.emit("📝 Executing JavaScript script...")
                        try:
                            # For JavaScript, we can use a simple eval or note that it requires browser context
                            self.log_signal.emit("⚠️ JavaScript execution requires browser context (Selenium)")
                            self.log_signal.emit("💡 Tip: Use JavaScript scripts in the Campaign automation with Selenium")
                            # Simulate execution for demo
                            self.log_signal.emit(f"📜 Script preview: {code[:100]}...")
                        except Exception as e:
                            self.log_signal.emit(f"❌ JavaScript execution error: {str(e)}")

                    elif language == "Shell/Bash":
                        self.log_signal.emit("📝 Executing Shell/Bash script...")
                        try:
                            import subprocess
                            result = subprocess.run(code, shell=True, capture_output=True, text=True, timeout=30)
                            self.log_signal.emit(f"📤 Output:\n{result.stdout}")
                            if result.stderr:
                                self.log_signal.emit(f"⚠️ Errors:\n{result.stderr}")
                            self.log_signal.emit(f"📊 Exit code: {result.returncode}")
                            if result.returncode == 0:
                                self.log_signal.emit("✅ Shell script executed successfully")
                            else:
                                self.log_signal.emit("❌ Shell script failed")
                        except subprocess.TimeoutExpired:
                            self.log_signal.emit("❌ Script timed out after 30 seconds")
                        except Exception as e:
                            self.log_signal.emit(f"❌ Shell execution error: {str(e)}")

                    self.log_signal.emit(f"Completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

                except Exception as e:
                    self.log_signal.emit(f"❌ Execution failed: {str(e)}")
                    import traceback
                    self.log_signal.emit(traceback.format_exc())

            threading.Thread(target=worker, daemon=True).start()

    def clear_editor(self):
        self.script_name.clear()
        self.script_editor.clear()

    @Slot(str)
    def _append_log(self, text: str):
        """Thread-safe log append"""
        self.execution_log.append(text)

    @Slot()
    def refresh_table(self):
        self.scripts_table.setRowCount(0)
        for script in self.scripts:
            row = self.scripts_table.rowCount()
            self.scripts_table.insertRow(row)
            self.scripts_table.setItem(row, 0, QTableWidgetItem(script['name']))
            self.scripts_table.setItem(row, 1, QTableWidgetItem(script['language']))
            self.scripts_table.setItem(row, 2, QTableWidgetItem(script['created']))

    def create_from_api(self):
        """Create a Python script from an API request"""
        api_file = os.path.join(CONFIG_DIR, "api_request_history.json")
        if not os.path.exists(api_file):
            QMessageBox.information(self, "No API History", "No API requests found. Make some requests first!")
            return

        try:
            with open(api_file, "r", encoding="utf-8") as f:
                history = json.load(f)

            if not history:
                QMessageBox.information(self, "No API History", "No API requests found.")
                return

            # Create a simple selection dialog
            api_descriptions = [f"{req['method']} - {req['url']}" for req in history]
            selected, ok = QInputDialog.getItem(self, "Select API Request", "Choose an API request to convert:", api_descriptions, 0, False)
            if ok and selected:
                # Parse the selection to get the index
                index = api_descriptions.index(selected)
                api_req = history[index]

                # Generate Python script
                script_code = f'''import requests
import json

# API Request generated from API Runner
url = "{api_req['url']}"
method = "{api_req['method']}"
headers = {api_req['headers']}
body = {api_req['body']}

try:
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=body)
    elif method == "PUT":
        response = requests.put(url, headers=headers, json=body)
    elif method == "DELETE":
        response = requests.delete(url, headers=headers)
    elif method == "PATCH":
        response = requests.patch(url, headers=headers, json=body)

    print("Status Code:", response.status_code)
    print("Response:", response.text)

except Exception as e:
    print("Error:", e)
'''

                # Set the script in the editor
                self.script_name.setText(f"API_{api_req['method']}_{api_req['url'].replace('https://', '').replace('/', '_')[:20]}")
                self.script_language.setCurrentText("Python")
                self.script_editor.setPlainText(script_code)
                QMessageBox.information(self, "Success", "API request converted to Python script! Review and save it.")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load API history: {e}")

    def schedule_current_script(self):
        """Schedule the current script"""
        name = self.script_name.text().strip()
        if not name:
            QMessageBox.warning(self, "No Script", "Enter a script name first")
            return

        # Open scheduler dialog with pre-filled data
        scheduler = SchedulerDialog(self)
        scheduler.task_name.setText(name)
        scheduler.task_type.setCurrentText("Custom Script")
        scheduler.exec()


class APIRunnerDialog(QDialog):
    """API Request Runner Modal"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📡 API Request Runner")
        self.setMinimumSize(600, 500)
        self.api_history_file = os.path.join(CONFIG_DIR, "api_request_history.json")
        self.request_history = self._load_history_from_file()
        self._build_ui()
        # Load history into table after UI is built
        QTimer.singleShot(0, self._refresh_history)

    def _load_history_from_file(self):
        """Load API request history from JSON file"""
        if not os.path.exists(self.api_history_file):
            return []
        try:
            with open(self.api_history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading API history: {e}")
            return []

    def _save_history_to_file(self):
        """Save API request history to JSON file"""
        try:
            with open(self.api_history_file, "w", encoding="utf-8") as f:
                json.dump(self.request_history, f, indent=2)
            return True
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save history: {e}")
            return False

    def _build_ui(self):
        layout = QVBoxLayout()

        # Request Configuration
        request_group = QGroupBox("API Request Configuration")
        request_layout = QFormLayout()

        self.method_combo = QComboBox()
        self.method_combo.addItems(["GET", "POST", "PUT", "DELETE", "PATCH"])
        request_layout.addRow("Method:", self.method_combo)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://api.example.com/endpoint")
        request_layout.addRow("URL:", self.url_input)

        # Headers
        self.headers_input = QTextEdit()
        self.headers_input.setPlaceholderText('{"Authorization": "Bearer token", "Content-Type": "application/json"}')
        self.headers_input.setMaximumHeight(80)
        request_layout.addRow("Headers (JSON):", self.headers_input)

        # Body
        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText('{"key": "value"}')
        self.body_input.setMaximumHeight(80)
        request_layout.addRow("Request Body (JSON):", self.body_input)

        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" seconds")
        request_layout.addRow("Timeout:", self.timeout_spin)

        send_btn = QPushButton("🚀 Send Request")
        send_btn.clicked.connect(self.send_request)
        request_layout.addRow(send_btn)

        request_group.setLayout(request_layout)
        layout.addWidget(request_group)

        # Response Display
        response_group = QGroupBox("Response")
        response_layout = QVBoxLayout()

        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("font-weight: bold;")
        response_layout.addWidget(self.status_label)

        self.response_output = QTextEdit()
        self.response_output.setReadOnly(True)
        self.response_output.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        response_layout.addWidget(self.response_output)

        response_group.setLayout(response_layout)
        layout.addWidget(response_group)

        # Request History
        history_group = QGroupBox("Request History")
        history_layout = QVBoxLayout()
        self.history_table = QTableWidget(0, 3)
        self.history_table.setHorizontalHeaderLabels(["Method", "URL", "Status"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        history_layout.addWidget(self.history_table)

        replay_btn = QPushButton("🔄 Replay Selected")
        replay_btn.clicked.connect(self.replay_request)
        schedule_btn = QPushButton("⏰ Schedule This")
        schedule_btn.clicked.connect(self.schedule_current_request)
        history_layout.addWidget(replay_btn)
        history_layout.addWidget(schedule_btn)

        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def send_request(self):
        method = self.method_combo.currentText()
        url = self.url_input.text().strip()
        headers_text = self.headers_input.toPlainText()
        body_text = self.body_input.toPlainText()
        timeout = self.timeout_spin.value()

        if not url:
            QMessageBox.warning(self, "Error", "Please enter a URL")
            return

        try:
            headers = json.loads(headers_text) if headers_text else {}
            body = json.loads(body_text) if body_text else None
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "JSON Error", f"Invalid JSON: {e}")
            return

        def worker():
            try:
                start_time = time.time()
                if method == "GET":
                    response = requests.get(url, headers=headers, timeout=timeout)
                elif method == "POST":
                    response = requests.post(url, headers=headers, json=body, timeout=timeout)
                elif method == "PUT":
                    response = requests.put(url, headers=headers, json=body, timeout=timeout)
                elif method == "DELETE":
                    response = requests.delete(url, headers=headers, timeout=timeout)
                elif method == "PATCH":
                    response = requests.patch(url, headers=headers, json=body, timeout=timeout)

                elapsed = time.time() - start_time

                # Update UI on main thread
                QMetaObject.invokeMethod(self, "_show_response", Qt.QueuedConnection,
                    Q_ARG(str, str(response.status_code)),
                    Q_ARG(str, response.text),
                    Q_ARG(str, f"{elapsed:.2f}s"))

                # Add to history
                self.request_history.append({
                    "method": method,
                    "url": url,
                    "headers": headers_text,
                    "body": body_text,
                    "status": response.status_code
                })
                # Save history (file operations are generally thread-safe)
                try:
                    with open(self.api_history_file, "w", encoding="utf-8") as f:
                        json.dump(self.request_history, f, indent=2)
                except Exception as e:
                    print(f"Failed to save history: {e}")
                # Refresh history table on main thread
                QMetaObject.invokeMethod(self, "_refresh_history", Qt.QueuedConnection)

            except Exception as e:
                QMetaObject.invokeMethod(self, "_show_error", Qt.QueuedConnection, Q_ARG(str, str(e)))

        threading.Thread(target=worker, daemon=True).start()

    @Slot(str, str, str)
    def _show_response(self, status: str, text: str, elapsed: str):
        self.status_label.setText(f"Status: {status} (Time: {elapsed})")
        self.status_label.setStyleSheet(f"font-weight: bold; color: {'green' if status.startswith('2') else 'red'};")
        self.response_output.setPlainText(text)

    @Slot(str)
    def _show_error(self, error: str):
        self.status_label.setText("Status: Error")
        self.status_label.setStyleSheet("font-weight: bold; color: red;")
        self.response_output.setPlainText(f"Error: {error}")

    @Slot()
    def _refresh_history(self):
        self.history_table.setRowCount(0)
        for req in self.request_history:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            self.history_table.setItem(row, 0, QTableWidgetItem(req['method']))
            self.history_table.setItem(row, 1, QTableWidgetItem(req['url']))
            self.history_table.setItem(row, 2, QTableWidgetItem(str(req['status'])))

    def replay_request(self):
        row = self.history_table.currentRow()
        if row >= 0:
            req = self.request_history[row]
            self.method_combo.setCurrentText(req['method'])
            self.url_input.setText(req['url'])
            self.headers_input.setPlainText(req['headers'])
            self.body_input.setPlainText(req['body'])
            self.send_request()

    def schedule_current_request(self):
        """Schedule the current API request"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "No URL", "Enter a URL first")
            return

        # Open scheduler dialog with pre-filled data
        scheduler = SchedulerDialog(self)
        scheduler.task_name.setText(url)
        scheduler.task_type.setCurrentText("API Request")
        scheduler.exec()

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
    append_signal = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Web Automation Dashboard")
        self.setMinimumSize(400, 700)

        self.settings = load_settings()
        self.proxies: List[Dict] = []
        self.records: List[Dict] = []
        self.worker: Optional[AutomationThread] = None
        self.append_signal.connect(self._append_log_impl)

        # central widget & layout
        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        #back button
        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(self.back)
        tabs.addTab(self.back_btn, "Back")

        # Automate Web Tasks
        self.build_automate_web_tab = QWidget()
        self._build_automate_web_tab()
        tabs.addTab(self.build_automate_web_tab, "Automate Web")

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



    def _build_automate_web_tab(self):
        layout = QVBoxLayout()
        self.build_automate_web_tab.setLayout(layout)

        # 🔹 CENTRAL AUTOMATION HUB - ALL TOOLS LINKED TOGETHER
        header = QLabel("⚡ ALL AUTOMATIONS - ALL IN ONE PLACE")
        header.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            margin: 12px 0;
            color: #2c3e50;
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        subheader = QLabel("Every automation tool integrated and connected from this single hub")
        subheader.setAlignment(Qt.AlignCenter)
        subheader.setStyleSheet("color: #7f8c8d; margin-bottom: 15px;")
        layout.addWidget(subheader)

        # 🔹 Status Monitor
        status_row = QHBoxLayout()
        self.hub_status = QLabel("✅ All Systems Online")
        self.hub_status.setStyleSheet("font-weight: bold; color: #27ae60;")
        status_row.addWidget(self.hub_status)
        status_row.addStretch()
        layout.addLayout(status_row)

        layout.addSpacing(10)

        # 🔹 1. EXTERNAL AUTOMATION PLATFORMS - DIRECT LINKS
        plat_label = QLabel("🔗 INTEGRATED PLATFORMS")
        plat_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #2980b9;")
        layout.addWidget(plat_label)

        platform_row = QHBoxLayout()
        
        self.btn_make = QPushButton("⚙️ Make.com")
        self.btn_make.clicked.connect(self.open_make_automation)
        self.btn_make.setStyleSheet("padding: 12px; background-color: #f39c12; color: white; font-weight: bold;")

        self.btn_n8n = QPushButton("🔗 n8n Workflows")
        self.btn_n8n.clicked.connect(self.open_n8n_automation)
        self.btn_n8n.setStyleSheet("padding: 12px; background-color: #e74c3c; color: white; font-weight: bold;")

        self.btn_airtable = QPushButton("📋 Airtable")
        self.btn_airtable.clicked.connect(self.fetch_airtable_records)
        self.btn_airtable.setStyleSheet("padding: 12px; background-color: #2ecc71; color: white; font-weight: bold;")

        platform_row.addWidget(self.btn_make)
        platform_row.addWidget(self.btn_n8n)
        platform_row.addWidget(self.btn_airtable)
        layout.addLayout(platform_row)

        layout.addSpacing(10)

        # 🔹 2. BROWSER AUTOMATION TOOLS
        browser_label = QLabel("🌐 BROWSER & WEB AUTOMATION")
        browser_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #2980b9;")
        layout.addWidget(browser_label)

        browser_row = QHBoxLayout()
        
        self.btn_chrome = QPushButton("🌐 Launch Chrome")
        self.btn_chrome.clicked.connect(self.launch_chrome_browser)
        self.btn_chrome.setStyleSheet("padding: 10px; background-color: #3498db; color: white;")

        self.btn_headless = QPushButton("👻 Headless Mode")
        self.btn_headless.clicked.connect(self.run_headless_session)
        self.btn_headless.setStyleSheet("padding: 10px; background-color: #9b59b6; color: white;")

        self.btn_proxies = QPushButton("🔌 Proxy Manager")
        self.btn_proxies.clicked.connect(self.load_proxies_from_ui)
        self.btn_proxies.setStyleSheet("padding: 10px; background-color: #e67e22; color: white;")

        browser_row.addWidget(self.btn_chrome)
        browser_row.addWidget(self.btn_headless)
        browser_row.addWidget(self.btn_proxies)
        layout.addLayout(browser_row)

        layout.addSpacing(10)

        # 🔹 3. UTILITY AUTOMATIONS
        util_label = QLabel("🛠️ UTILITIES")
        util_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #2980b9;")
        layout.addWidget(util_label)

        util_row = QHBoxLayout()
        
        self.btn_scheduler = QPushButton("⏰ Scheduler")
        self.btn_scheduler.setStyleSheet("padding: 10px;")
        self.btn_scheduler.clicked.connect(self.open_scheduler)

        self.btn_custom = QPushButton("📜 Custom Scripts")
        self.btn_custom.setStyleSheet("padding: 10px;")
        self.btn_custom.clicked.connect(self.open_custom_scripts)

        self.btn_api = QPushButton("📡 API Runner")
        self.btn_api.setStyleSheet("padding: 10px;")
        self.btn_api.clicked.connect(self.open_api_runner)

        util_row.addWidget(self.btn_scheduler)
        util_row.addWidget(self.btn_custom)
        util_row.addWidget(self.btn_api)
        layout.addLayout(util_row)

        layout.addSpacing(15)

        # 🔹 UNIVERSAL LOG - EVERYTHING LOGS HERE
        log_label = QLabel("📋 MASTER ACTIVITY LOG - ALL AUTOMATIONS")
        log_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(log_label)

        self.master_log = QTextEdit()
        self.master_log.setReadOnly(True)
        self.master_log.setMinimumHeight(260)
        self.master_log.setStyleSheet("""
            background-color: #1e272e;
            color: #00ff00;
            font-family: Consolas, monospace;
            font-size: 12px;
            border-radius: 4px;
        """)
        layout.addWidget(self.master_log)

        # 🔹 GLOBAL CONTROLS
        control_row = QHBoxLayout()
        
        self.btn_stop_all = QPushButton("⏹️ EMERGENCY STOP ALL")
        self.btn_stop_all.clicked.connect(self.stop_all_automations)
        self.btn_stop_all.setStyleSheet("padding: 12px; background-color: #c0392b; color: white; font-weight: bold;")

        self.btn_clear = QPushButton("🗑️ Clear Log")
        self.btn_clear.clicked.connect(lambda: self.master_log.clear())

        control_row.addWidget(self.btn_stop_all)
        control_row.addWidget(self.btn_clear)
        layout.addLayout(control_row)

        layout.addStretch()

        self.log_to_hub("✅ Automation Hub Ready. All tools connected and ready.")



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
        self.append_signal.emit(txt, which)

    def _append_log_impl(self, txt: str, which="overview"):
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

        def worker():
            good = 0
            for p in random.sample(self.proxies, min(6, len(self.proxies))):
                pstr = normalize_proxy(p)
                ok = proxy_is_working(pstr) if pstr else False
                self.append_log(f"Tested {pstr} => {ok}", "proxies")
                if ok:
                    good += 1
            self.append_log(f"Sample testing: {good} working among sampled proxies.", "proxies")
        threading.Thread(target=worker, daemon=True).start()

    def test_random_proxy(self):
        if not self.proxies:
            QMessageBox.information(self, "No proxies", "Load proxies first.")
            return
        p = random.choice(self.proxies)
        pstr = normalize_proxy(p)
        def worker():
            ok = proxy_is_working(pstr)
            QMetaObject.invokeMethod(self, "_show_proxy_result", Qt.QueuedConnection, Q_ARG(str, pstr), Q_ARG(bool, ok))
        threading.Thread(target=worker, daemon=True).start()

    @Slot(str, bool)
    def _show_proxy_result(self, pstr: str, ok: bool):
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
        def worker():
            try:
                svc = AirtableService(api_key, base_id, table_name, view_name)
                records = svc.fetch_all_records()
                QMetaObject.invokeMethod(self, "_on_airtable_fetched", Qt.QueuedConnection,
                    Q_ARG(list, records))
            except Exception as e:
                QMetaObject.invokeMethod(self, "_on_airtable_error", Qt.QueuedConnection,
                    Q_ARG(str, str(e)))
        threading.Thread(target=worker, daemon=True).start()

    @Slot(list)
    def _on_airtable_fetched(self, records: List[Dict]):
        self.records = records
        self.lbl_count_campaigns.setText(f"Campaigns: {len(records)}")
        self.append_log(f"Fetched {len(records)} records.")
        self.populate_table(records)

    @Slot(str)
    def _on_airtable_error(self, error: str):
        QMessageBox.critical(self, "Airtable Error", error)
        self.append_log(f"Error fetching Airtable: {error}")

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

    # ==============================
    # AUTOMATION HUB HELPER METHODS
    # ==============================
    def log_to_hub(self, txt: str):
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {txt}"
        self.master_log.append(line)

    def open_make_automation(self):
        self.log_to_hub("🔌 Opening Make.com Automation Interface")
        self.make_window = MakePage()
        self.make_window.show()

    def open_n8n_automation(self):
        self.log_to_hub("🔗 Opening n8n Workflow Manager")
        self.n8n_window = N8nPage()
        self.n8n_window.show()

    def launch_chrome_browser(self):
        self.log_to_hub("🌐 Launching Chrome Browser instance")
        def worker():
            try:
                driver = self.build_chrome_driver(None)
                self.log_to_hub("✅ Chrome browser launched successfully")
            except Exception as e:
                self.log_to_hub(f"❌ Failed to launch Chrome: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def run_headless_session(self):
        self.log_to_hub("👻 Starting Headless Automation Session")
        def worker():
            try:
                driver = self.build_chrome_driver(None, headless=True)
                self.log_to_hub("✅ Headless Chrome browser launched successfully")
            except Exception as e:
                self.log_to_hub(f"❌ Failed to launch headless Chrome: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def test_all_proxies(self):
        self.log_to_hub("🔌 Running full proxy validation test")
        self.load_proxies_from_ui()

    def build_chrome_driver(self, proxy: Optional[str], headless=False):
        options = ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        if proxy:
            options.add_argument(f"--proxy-server={proxy}")
            self.log_to_hub(f"Launching Chrome with proxy: {proxy}")
        else:
            self.log_to_hub("Launching Chrome without proxy")
        driver = webdriver.Chrome(options=options)
        return driver

    def open_scheduler(self):
        self.log_to_hub("⏰ Opening Scheduler Utility")
        self.scheduler_dialog = SchedulerDialog(self)
        self.scheduler_dialog.exec()
        self.log_to_hub("✅ Scheduler dialog closed")

    def open_custom_scripts(self):
        self.log_to_hub("📜 Opening Custom Scripts Manager")
        self.scripts_dialog = CustomScriptsDialog(self)
        self.scripts_dialog.exec()
        self.log_to_hub("✅ Custom scripts dialog closed")

    def open_api_runner(self):
        self.log_to_hub("📡 Opening API Runner Utility")
        self.api_dialog = APIRunnerDialog(self)
        self.api_dialog.exec()
        self.log_to_hub("✅ API runner dialog closed")

    def stop_all_automations(self):
        self.log_to_hub("⚠️ EMERGENCY STOP ACTIVATED")
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.log_to_hub("✅ Automation worker stopped")
        self.hub_status.setText("🔴 All Systems Stopped")
        self.log_to_hub("✅ All automations have been terminated")

