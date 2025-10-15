import sys
import os
import json
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QMessageBox, QComboBox,
    QVBoxLayout,QHBoxLayout
)
from PySide6.QtCore import Qt



CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config_files")
CONFIG_FILE = os.path.join(CONFIG_DIR, "proxy_config.json")


class ProxyConnection(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Proxy Connector")
        self.setFixedSize(500, 400)

        # Central layout
        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        #Proxy Api Keys
        layout.addWidget((QLabel("Api Key:")))
        self.api_key = QLineEdit()
        self.api_key.setPlaceholderText("Enter the Api Key Generated from...")
        layout.addWidget(self.api_key)


        # Proxy fields
        layout.addWidget(QLabel("Proxy Type:"))
        self.protocol_box = QComboBox()
        self.protocol_box.addItems(["http", "https", "socks4", "socks5"])
        layout.addWidget(self.protocol_box)

        layout.addWidget(QLabel("Proxy IP:"))
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter proxy IP (e.g., 123.45.67.89)")
        layout.addWidget(self.ip_input)

        layout.addWidget(QLabel("Proxy Port:"))
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Enter port (e.g., 8080)")
        layout.addWidget(self.port_input)

        # Optional auth
        layout.addWidget(QLabel("Username (optional):"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Proxy username (if needed)")
        layout.addWidget(self.username_input)

        layout.addWidget(QLabel("Password (optional):"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        # Buttons
        button_layout = QHBoxLayout()
        self.test_button = QPushButton("🔍 Test Proxy")
        self.save_button = QPushButton("💾 Save Proxy")
        self.load_button = QPushButton("📂 Load Proxy")

        button_layout.addWidget(self.test_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.load_button)
        layout.addLayout(button_layout)

        # Log box
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(150)
        layout.addWidget(self.log_output)

        # Button connections
        self.test_button.clicked.connect(self.test_proxy)
        self.save_button.clicked.connect(self.save_proxy)
        self.load_button.clicked.connect(self.load_proxy)

        # Auto-load saved proxy if any
        self.load_proxy()


    # -------------- UTILITIES --------------
    def log(self, msg):
        self.log_output.append(msg)

    # -------------- SAVE PROXY --------------
    def save_proxy(self):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)


        proxy_data = {
            "api_key": self.api_key.text().strip(),
            "protocol": self.protocol_box.currentText(),
            "ip": self.ip_input.text().strip(),
            "port": self.port_input.text().strip(),
            "username": self.username_input.text().strip(),
            "password": self.password_input.text().strip(),
        }

        if not proxy_data["ip"] or not proxy_data["port"]:
            QMessageBox.warning(self, "Missing Data", "Proxy IP and Port are required!")
            return

        with open(CONFIG_FILE, "w") as f:
            json.dump(proxy_data, f, indent=4)

        QMessageBox.information(self, "Saved", "Proxy configuration saved successfully!")
        self.log("Proxy settings saved.")
        self.close()


    # -------------- LOAD PROXY --------------
    def load_proxy(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                proxy_data = json.load(f)
            self.api_key.setText(proxy_data.get("api_key", ""))    
            self.protocol_box.setCurrentText(proxy_data.get("protocol", "http"))
            self.ip_input.setText(proxy_data.get("ip", ""))
            self.port_input.setText(proxy_data.get("port", ""))
            self.username_input.setText(proxy_data.get("username", ""))
            self.password_input.setText(proxy_data.get("password", ""))
            self.log("Loaded proxy configuration.")
        else:
            self.log("No saved proxy configuration found.")

    # -------------- TEST PROXY --------------
    def test_proxy(self):
        protocol = self.protocol_box.currentText()
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not ip or not port:
            QMessageBox.warning(self, "Missing Data", "Proxy IP and Port are required to test.")
            return

        proxy_auth = f"{username}:{password}@" if username and password else ""
        proxy_url = f"{protocol}://{proxy_auth}{ip}:{port}"

        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }

        self.log(f"Testing proxy: {proxy_url}")

        try:
            response = requests.get("https://ipinfo.io/json", proxies=proxies, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.log(f"Proxy is working!")
            self.log(f"Your IP: {data.get('ip')} — Location: {data.get('city')}, {data.get('country')}")
        except Exception as e:
            self.log(f"Proxy failed: {e}")
            QMessageBox.critical(self, "Proxy Test Failed", str(e))



# ----------------- RUN -----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProxyConnector()
    window.show()
    sys.exit(app.exec())





        