# core/n8n_connector.py
import requests
import json
from PySide6.QtWidgets import QMessageBox, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtCore import Qt
import subprocess
import os
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QTextEdit



CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config_files")
CONFIG_FILE = os.path.join(CONFIG_DIR, "n8n_config.json")


class N8nConnector(QMainWindow):
    def __init__(self):
        super().__init__()


        self.setWindowTitle("n8n Connector")
        self.setFixedSize(500, 400)


    # Central layout
        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        #n8n file location
        layout.addWidget((QLabel("n8n api key")))
        self.api_key = QLineEdit()
        self.api_key.setPlaceholderText("Enter the api key")
        layout.addWidget(self.api_key)

        #Proxy Api Keys
        layout.addWidget((QLabel("Connect n8n")))
        self.start_n8n_btn = QPushButton("Start n8n")
        self.start_n8n_btn.clicked.connect(self.start_n8n)
        layout.addWidget(self.start_n8n_btn)


        # Log Output
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        layout.addWidget(self.output_box)

        self.load_n8n()

    def log(self, msg):
        self.output_box.append(msg)

    def open_url_in_browser(self,url):
        QDesktopServices.openUrl(QUrl(url))

    def load_n8n(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                api_key = config.get("api_key")
            self.api_key.setText(api_key)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load n8n api key: {e}")


    def start_n8n(self):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        if not self.api_key.text().strip():
            QMessageBox.warning(self, "Missing Data", "n8n api key is required!")
            return

        n8n_data = {
            "api_key": self.api_key.text().strip(),
        }

        with open(CONFIG_FILE, "w") as f:
            json.dump(n8n_data, f, indent=4)

        QMessageBox.information(self, "Saved", "n8n api key saved successfully!")
        self.log("n8n api key saved successfully.")
        self.close()
            


