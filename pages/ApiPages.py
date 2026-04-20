import sys
import os
import json
import requests
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QComboBox, QGroupBox, QSizePolicy
)


class APIPage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧠 API & Webhook Automation Center")
        self.setMinimumSize(400, 700)

        tabs = QTabWidget()
        self.setCentralWidget(tabs)



        # === Tabs ===
        self.overview_tab = QWidget()
        self.api_tab = QWidget()
        self.webhook_tab = QWidget()

        # Build UI components
        self._build_overview_tab()
        self._build_api_tab()
        self._build_webhook_tab()

        # Add Tabs
        tabs.addTab(self.overview_tab, "📋 Overview")
        tabs.addTab(self.api_tab, "🔗 API Manager")
        tabs.addTab(self.webhook_tab, "🌐 Webhooks")

    def back(self):
        from app import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()   
        
         
    def _build_overview_tab(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.overview_tab.setLayout(layout)

        #back button
        self.back_btn = QPushButton("Back")
        self.back_btn.clicked.connect(self.back)
        layout.addWidget(self.back_btn)

        title = QLabel("📊 Automation Overview")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        desc = QLabel("Monitor and manage your API, webhook, and bot automations all in one place.")
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 15px; color: #555; margin-bottom: 20px;")
        layout.addWidget(desc)

        info_box = QGroupBox("System Status")
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel("✅ API Connections: Active"))
        info_layout.addWidget(QLabel("🌍 Webhooks: Listening"))
        info_layout.addWidget(QLabel("⚙️ Automation Bots: Idle"))
        info_box.setLayout(info_layout)
        layout.addWidget(info_box)

        progress = QProgressBar()
        progress.setValue(45)
        progress.setFormat("System Load: %p%")
        layout.addWidget(progress)


    def _build_api_tab(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.api_tab.setLayout(layout)

        title = QLabel("🔗 API Request Builder")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        api_box = QGroupBox("API Configuration")
        api_layout = QVBoxLayout()

        # HTTP Method
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("HTTP Method:"))
        self.method_box = QComboBox()
        self.method_box.addItems(["GET", "POST", "PUT", "DELETE"])
        self.method_box.setStyleSheet("font-weight:bold;")
        method_layout.addWidget(self.method_box)
        api_layout.addLayout(method_layout)

        # Data format
        data_layout = QHBoxLayout()
        data_layout.addWidget(QLabel("Data Format:"))
        self.data_format_box = QComboBox()
        self.data_format_box.addItems(["JSON", "XML", "CSV", "TSV"])
        data_layout.addWidget(self.data_format_box)
        api_layout.addLayout(data_layout)

        # Auth type
        auth_layout = QHBoxLayout()
        auth_layout.addWidget(QLabel("Auth Type:"))
        self.auth_box = QComboBox()
        self.auth_box.addItems(["None", "Basic", "Bearer"])
        auth_layout.addWidget(self.auth_box)
        api_layout.addLayout(auth_layout)

        # API URL
        url_layout = QVBoxLayout()
        url_layout.addWidget(QLabel("API Endpoint URL:"))
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("https://api.example.com/v1/data")
        url_layout.addWidget(self.api_url_input)
        api_layout.addLayout(url_layout)

        # Request Body
        body_layout = QVBoxLayout()
        body_layout.addWidget(QLabel("Request Body (JSON or Form Data):"))
        self.request_body = QTextEdit()
        self.request_body.setPlaceholderText("{\n   \"key\": \"value\"\n}")
        self.request_body.setFixedHeight(150)
        body_layout.addWidget(self.request_body)
        api_layout.addLayout(body_layout)

        # Send Button
        send_button = QPushButton("🚀 Send Request")
        send_button.clicked.connect(self._send_api_request)
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #005ea0;
            }
        """)
        api_layout.addWidget(send_button)

        api_box.setLayout(api_layout)
        layout.addWidget(api_box)

        # Response section
        response_box = QGroupBox("API Response")
        response_layout = QVBoxLayout()
        self.response_view = QTextEdit()
        self.response_view.setReadOnly(True)
        response_layout.addWidget(self.response_view)
        response_box.setLayout(response_layout)
        layout.addWidget(response_box)

    def _send_api_request(self):
        method = self.method_box.currentText()
        url = self.api_url_input.text().strip()
        headers = {}
        data = self.request_body.toPlainText().strip()

        if not url:
            QMessageBox.warning(self, "Error", "Please enter an API URL.")
            return

        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, data=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, data=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                response = None

            if response is not None:
                self.response_view.setPlainText(
                    f"Status: {response.status_code}\n\n{response.text}"
                )
        except Exception as e:
            QMessageBox.critical(self, "API Error", str(e))


    def _build_webhook_tab(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.webhook_tab.setLayout(layout)

        title = QLabel("🌐 Webhook Configuration")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        webhook_box = QGroupBox("Webhook Listener Setup")
        webhook_layout = QVBoxLayout()

        webhook_layout.addWidget(QLabel("Webhook URL:"))
        self.webhook_url = QLineEdit()
        self.webhook_url.setPlaceholderText("https://example.com/webhook-endpoint")
        webhook_layout.addWidget(self.webhook_url)

        webhook_layout.addWidget(QLabel("Event Type:"))
        self.webhook_event = QComboBox()
        self.webhook_event.addItems(["Campaign Trigger", "API Response", "Error Logs"])
        webhook_layout.addWidget(self.webhook_event)

        webhook_layout.addWidget(QLabel("Webhook Payload:"))
        self.webhook_payload = QTextEdit()
        self.webhook_payload.setPlaceholderText("{\n   \"event\": \"data_received\"\n}")
        self.webhook_payload.setFixedHeight(120)
        webhook_layout.addWidget(self.webhook_payload)

        webhook_button = QPushButton("🛰️ Send Test Webhook")
        webhook_button.clicked.connect(self._send_webhook_test)
        webhook_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1e7e34;
            }
        """)
        webhook_layout.addWidget(webhook_button)

        webhook_box.setLayout(webhook_layout)
        layout.addWidget(webhook_box)

        # Webhook logs
        log_box = QGroupBox("Webhook Logs")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        log_box.setLayout(log_layout)
        layout.addWidget(log_box)

    def _send_webhook_test(self):
        url = self.webhook_url.text().strip()
        data = self.webhook_payload.toPlainText().strip()

        if not url:
            QMessageBox.warning(self, "Error", "Please enter a webhook URL.")
            return

        try:
            res = requests.post(url, data=data, headers={"Content-Type": "application/json"})
            log_entry = f"✅ Sent to {url} | Status: {res.status_code}\nResponse: {res.text}\n\n"
            self.log_output.append(log_entry)
        except Exception as e:
            self.log_output.append(f"❌ Error sending webhook: {str(e)}\n")

