from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from pages.automations_integrations.n8n_automation import N8nPage
from pages.automations_integrations.make_automation import MakePage
class AutomationTabs(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Automation Tabs")
        self.resize(1100, 700)
        self.setMinimumSize(900, 600)

         # Main container
        container = QWidget()
        container.setStyleSheet("background-color: #f7f9fc;")  # light neutral tone
        self.setCentralWidget(container)

        # Create layout for container
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container.setLayout(main_layout)


        # --- Header section ---
        header = QLabel("Select an automation tool")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #333; margin-bottom: 20px;")
        main_layout.addWidget(header)


        n8n_btn = QPushButton("n8n")
        n8n_btn.clicked.connect(self.open_n8n_automation)
        n8n_btn.setFixedSize(100, 50)
        n8n_btn.setStyleSheet("background-color: #0078d7; color: white;")
        main_layout.addWidget(n8n_btn)

        make_btn = QPushButton("Make.com")
        make_btn.clicked.connect(self.open_make_automation)
        make_btn.setFixedSize(100, 50)
        make_btn.setStyleSheet("background-color: #0078d7; color: white;")
        main_layout.addWidget(make_btn)
        

    def open_n8n_automation(self):
        self.n8n_automation = N8nPage()
        self.n8n_automation.show()
        self.close()

    def open_make_automation(self):
        self.make_automation = MakePage()
        self.make_automation.show()
        self.close()    