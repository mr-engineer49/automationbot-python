from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame, QHBoxLayout, QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import requests




class MakePage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("💡 Make Automation")
        self.resize(400, 700)

        # --- Central Container ---
        container = QWidget()
        self.setCentralWidget(container)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 20, 20, 20)

        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.back)
        main_layout.addWidget(back_btn)

        # --- Header ---
        header = QLabel("Make Automation Dashboard")
        header.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        # --- API Connection Section ---
        connection_layout = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter Make API Key")
        self.connect_btn = QPushButton("Connect to Make")
        self.connect_btn.clicked.connect(self.connect_make)
        connection_layout.addWidget(self.api_key_input)
        connection_layout.addWidget(self.connect_btn)
        main_layout.addLayout(connection_layout)

        # --- Divider ---
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)

        # --- Automation / Scenarios Section ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scenario_container = QWidget()
        self.scenario_layout = QVBoxLayout(self.scenario_container)
        self.scroll_area.setWidget(self.scenario_container)
        main_layout.addWidget(self.scroll_area)

        # Status label
        self.status_label = QLabel("Not connected")
        main_layout.addWidget(self.status_label)



    def back(self):
        from app import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()   



    def connect_make(self):
        """Connect to Make API and list scenarios."""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            self.status_label.setText("❌ Enter a valid API key")
            return

        self.api_key = api_key
        self.status_label.setText("Connecting...")

        # Make API call
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get("https://api.make.com/v2/scenarios", headers=headers)
            response.raise_for_status()
            scenarios = response.json()["scenarios"]

            # Clear previous
            for i in reversed(range(self.scenario_layout.count())):
                widget = self.scenario_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

            # Populate scenarios
            for scenario in scenarios:
                name = scenario["name"]
                scenario_id = scenario["id"]
                btn = QPushButton(f"Run: {name}")
                btn.clicked.connect(lambda checked, sid=scenario_id: self.run_scenario(sid))
                self.scenario_layout.addWidget(btn)

            self.status_label.setText(f"✅ Connected: {len(scenarios)} scenarios loaded")
        except Exception as e:
            self.status_label.setText(f"❌ Connection failed: {e}")

    def run_scenario(self, scenario_id):
        """Trigger a Make scenario."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            url = f"https://api.make.com/v2/scenarios/{scenario_id}/run"
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            self.status_label.setText(f"✅ Scenario {scenario_id} triggered!")
        except Exception as e:
            self.status_label.setText(f"❌ Failed to run scenario: {e}")
