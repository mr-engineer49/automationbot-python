import sys
import os
import json
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt




CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config_files")
CONFIG_FILE = os.path.join(CONFIG_DIR, "airtable_config.json")


class AirtableConnection(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Airtable Connector")
        self.setFixedSize(500, 400)

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        central_widget.setLayout(layout)

        # Labels and input fields
        layout.addWidget(QLabel("API Key:"))
        self.api_key_input = QLineEdit()
        layout.addWidget(self.api_key_input)

        layout.addWidget(QLabel("Base ID:"))
        self.base_id_input = QLineEdit()
        layout.addWidget(self.base_id_input)

        layout.addWidget(QLabel("Table Name:"))
        self.table_name_input = QLineEdit()
        layout.addWidget(self.table_name_input)

        layout.addWidget(QLabel("View Name:"))
        self.view_name_input = QLineEdit()
        layout.addWidget(self.view_name_input)

        # Connect button
        self.connect_button = QPushButton("Test Connection")
        self.connect_button.clicked.connect(self.test_connection)
        layout.addWidget(self.connect_button)

        self.save_button = QPushButton("💾 Save Airtable")
        self.load_button = QPushButton("📂 Load Airtable")

        self.save_button.clicked.connect(self.save_airtable_info)
        layout.addWidget(self.save_button)
        self.load_button.clicked.connect(self.load_airtable_info)
        layout.addWidget(self.load_button) 

        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(150)
        layout.addWidget(self.log_output)

        self.load_airtable_info()

    def log(self, message):
        """Append log messages."""
        self.log_output.append(message)

    def test_connection(self):
        """Try connecting to Airtable and fetch sample records."""
        api_key = self.api_key_input.text().strip()
        base_id = self.base_id_input.text().strip()
        table_name = self.table_name_input.text().strip()
        view_name = self.view_name_input.text().strip()

        if not all([api_key, base_id, table_name]):
            QMessageBox.warning(self, "Input Error", "API Key, Base ID, and Table Name are required!")
            return

        url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        params = {}
        if view_name:
            params["view"] = view_name

        self.log("Requesting Airtable...")
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            records = data.get("records", [])

            self.log(f"Airtable connection successful! Retrieved {len(records)} records.")
            for r in records[:5]:  # Show first 5
                fields = r.get("fields", {})
                self.log(f"→ {fields}")

        except requests.exceptions.RequestException as e:
            self.log(f"Connection failed: {e}")


    def save_airtable_info(self):
        """Save user credentials to JSON config file."""
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)


        config = {
            "api_key": self.api_key_input.text().strip(),
            "base_id": self.base_id_input.text().strip(),
            "table_name": self.table_name_input.text().strip(),
            "view_name": self.view_name_input.text().strip()
        }

        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)

        QMessageBox.information(self, "Settings Saved", f"Airtable settings saved!\n\nSaved to:\n{CONFIG_FILE}")
        self.close()
        

    def load_airtable_info(self):
        """Load user credentials from JSON config file."""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)

            self.api_key_input.setText(config.get("api_key", ""))
            self.base_id_input.setText(config.get("base_id", ""))
            self.table_name_input.setText(config.get("table_name", ""))
            self.view_name_input.setText(config.get("view_name", ""))

            self.log("Configuration loaded from file.")
        else:
            self.log("No saved configuration found.")



# Run GUI standalone
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AirtableConnector()
    window.show()
    sys.exit(app.exec())
