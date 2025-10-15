# ui/n8n_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QTextEdit,
    QHBoxLayout, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt, QThread, Signal
from connector.n8nConnector import N8nConnector
import time
import subprocess
import os
import json
import requests



CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config_files")
CONFIG_FILE = os.path.join(CONFIG_DIR, "n8n_config.json")



class N8nPage(QWidget):
    def __init__(self):
        super().__init__()
        self.connector = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

        #back button
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.back)
        layout.addWidget(back_btn)

        title = QLabel("🧩 n8n Automations Manager")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom:10px;")
        layout.addWidget(title)

        #start n8n enviorment
        start_n8n_btn = QPushButton("Start n8n")
        start_n8n_btn.clicked.connect(self.start_n8n)
        layout.addWidget(start_n8n_btn)

        # Connection Section
        layout.addWidget(QLabel("n8n Base URL:"))
        self.base_url_input = QLineEdit("http://localhost:5678")
        layout.addWidget(self.base_url_input)

        layout.addWidget(QLabel("API Key (optional):"))
        self.api_key_input = QLineEdit()
        layout.addWidget(self.api_key_input)

        connect_btn = QPushButton("🔗 Connect to n8n")
        connect_btn.clicked.connect(self.connect_to_n8n)
        layout.addWidget(connect_btn)

        # Workflow list
        layout.addWidget(QLabel("Available Workflows:"))
        self.workflow_list = QListWidget()
        layout.addWidget(self.workflow_list)

        # Action buttons
        button_layout = QHBoxLayout()
        self.run_btn = QPushButton("▶️ Run Selected")
        self.run_btn.clicked.connect(self.run_selected)
        self.stop_btn = QPushButton("⏹ Stop Selected")
        self.stop_btn.clicked.connect(self.stop_selected)
        self.refresh_btn = QPushButton("🔄 Refresh List")
        self.refresh_btn.clicked.connect(self.load_workflows)
        button_layout.addWidget(self.run_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.refresh_btn)
        layout.addLayout(button_layout)

        # Log Output
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        layout.addWidget(self.output_box)

    def back(self):
        from app import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()    

    def start_n8n(self):
        self.output_box.append("Starting n8n...")
        n8n_batch_file = os.path.join(os.path.dirname(__file__), "batch_files", "n8n.cmd")
        print(n8n_batch_file)
        self.output_box.append(n8n_batch_file)
        try:
            self.output_box.append("Starting n8n using the batch file...")
            run_n8n_batch_script = subprocess.Popen(["cmd.exe", "/c", "npx n8n"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE, text=True, universal_newlines=True, close_fds=True, cwd=os.path.dirname(__file__))
            if run_n8n_batch_script.stderr.read() == "Your Node.js version 18.16.1 is currently not supported":
                self.output_box.append("Your Node.js version 18.16.1 is currently not supported")
                run_n8n_batch_script_1 = subprocess.Popen(["cmd.exe", "/c", "nvm use 24.2.0"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE, text=True, universal_newlines=True, close_fds=True, cwd=os.path.dirname(__file__))
                run_n8n_batch_script_1.wait(timeout=30)
                self.output_box.append(run_n8n_batch_script_1.stderr.read())
                run_n8n_batch_script_2 = subprocess.Popen(["cmd.exe", "/c", "npx n8n"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE, text=True, universal_newlines=True, close_fds=True, cwd=os.path.dirname(__file__))
                run_n8n_batch_script_2.wait(timeout=30)
                self.output_box.append(run_n8n_batch_script_2.stderr.read())
            else:
                self.output_box.append(run_n8n_batch_script.stderr.read())    
            run_n8n_batch_script.wait(timeout=30)
            if run_n8n_batch_script.returncode != 0:
                self.output_box.append(f"❌ Error starting n8n: {run_n8n_batch_script.stderr.read()}")
                return
            self.output_box.append("✅ n8n started successfully.")
            self.open_url_in_browser("http://localhost:5678")
        except Exception as e:
            self.output_box.append(f"❌ Error starting n8n: {e}")

    def connect_to_n8n(self):
        self.connector = N8nConnector()
        self.connector.show()
        self.output_box.append("Trying to connect to n8n...\nOpening n8n connector...")

    def load_workflows(self):
        if not self.connector:
            QMessageBox.warning(self, "Warning", "Connect to n8n first.")
            return
        self.output_box.append("Trying to connect to n8n...")
        self.output_box.append("Getting api key from config file...")
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            api_key = config.get("api_key")
        self.output_box.append("Getting workflows...") 
        try:
            response = requests.get(
            "http://localhost:5678/api/v1/workflows",
            headers={
            "X-N8N-API-KEY": api_key
            },
            params={
            "limit": "25",
            }
        )
            response.raise_for_status()
            data = response.json()
            self.output_box.append("Workflows loaded successfully.")
            self.workflow_list.clear()
            for wf in data.get("data", []):
                name = wf.get("name", "Unnamed Workflow")
                wf_id = wf.get("id")
                self.workflow_list.addItem(f"{name} (ID: {wf_id})")
        except Exception as e:
            self.output_box.append(f"❌ Error loading workflows: {e}")

        self.load_workflows()

    def run_selected(self):
        selected = self.workflow_list.currentItem()
        if not selected or not self.connector:
            QMessageBox.warning(self, "Error", "Select a workflow first.")
            return

        wf_id = selected.text().split("(ID: ")[-1].replace(")", "")
        try:
            res = self.connector.run_workflow(wf_id)
            self.output_box.append(f"🚀 Workflow triggered: {res}\n")
        except Exception as e:
            self.output_box.append(f"❌ Failed to run workflow: {e}")

    def stop_selected(self):
        selected = self.workflow_list.currentItem()
        if not selected or not self.connector:
            QMessageBox.warning(self, "Error", "Select a workflow first.")
            return

        wf_id = selected.text().split("(ID: ")[-1].replace(")", "")
        try:
            res = self.connector.stop_workflow(wf_id)
            self.output_box.append(f"🛑 Workflow stopped: {res}\n")
        except Exception as e:
            self.output_box.append(f"❌ Failed to stop workflow: {e}")
