#this app is to make connection with any proxies easily and using gui for better usage of this bot
from ctypes import alignment
from PySide6.QtWidgets import QFrame, QMainWindow, QApplication, QWidget, QLabel, QPushButton,QHBoxLayout,QLabel,QMainWindow,QPushButton,QStackedLayout,QVBoxLayout,QWidget
from PySide6.QtCore import Qt
import sys
from pages.appbot import AppBot
from pages.WebAutomation import WebAutomationBot
from pages.ApiPages import APIPage
from pages.automations_integrations.automation_tabs import AutomationTabs
from pages.ProxyServer import ProxyServer
from PySide6.QtGui import QFont

#create the class of each window/page here
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("🤖 Bot Controller")
        self.resize(400, 600)
        self.setMinimumSize(400, 600)
        self.app_bot = None
        self.connector = None


        # Main container
        container = QWidget()
        container.setStyleSheet("background-color: #f7f9fc;")  # light neutral tone
        self.setCentralWidget(container)

        # Create layout for container
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container.setLayout(main_layout)


        # --- Header section ---
        header = QLabel("Bot Control Panel")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #333; margin-bottom: 20px;")
        main_layout.addWidget(header)

        # --- Divider line ---
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #aaa; margin-bottom: 20px;")
        main_layout.addWidget(line)

        # --- Buttons section ---
        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(12)
        main_layout.addLayout(button_layout)

        # Minimalist button style - clean, simple, modern
        button_style = """
        QPushButton {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 14px 24px;
            font-size: 14px;
            font-family: Segoe UI;
            font-weight: 500;
            min-width: 240px;
            min-height: 44px;
        }
        QPushButton:hover {
            background-color: #f5f5f5;
            border: 1px solid #c0c0c0;
        }
        QPushButton:pressed {
            background-color: #eeeeee;
            border: 1px solid #b0b0b0;
        }
        """

        # Create buttons with uniform minimalist design
        proxy_server = QPushButton("Custom Proxy Server")
        proxy_server.setStyleSheet(button_style)
        proxy_server.clicked.connect(self.create_proxy_server)
        button_layout.addWidget(proxy_server)

        main_button = QPushButton("PPC Bot Farm")
        main_button.setStyleSheet(button_style)
        main_button.clicked.connect(self.open_app_bot_window)
        button_layout.addWidget(main_button)

        automation_button = QPushButton("Web Automation Bot")
        automation_button.setStyleSheet(button_style)
        automation_button.clicked.connect(self.open_web_automation_bot_window)
        button_layout.addWidget(automation_button)

        api_button = QPushButton("API")
        api_button.setStyleSheet(button_style)
        api_button.clicked.connect(self.api_page_function)
        button_layout.addWidget(api_button)

        auto_button = QPushButton("Automation & Integration")
        auto_button.setStyleSheet(button_style)
        auto_button.clicked.connect(self.open_automation_bot_window)
        button_layout.addWidget(auto_button)


    def create_proxy_server(self):
        self.proxy_server = ProxyServer()
        self.proxy_server.show()
        self.close()


    def open_automation_bot_window(self):
        self.automation_bot = AutomationTabs()
        self.automation_bot.show()
        self.close()    

    def api_page_function(self):
        self.api_page = APIPage()
        self.api_page.show()
        self.close()    

    def open_web_automation_bot_window(self):
        self.web_automation_bot = WebAutomationBot()
        self.web_automation_bot.show()
        self.close()

    def open_app_bot_window(self):
        self.app_bot = AppBot()
        self.app_bot.show()
        self.close()
        

#app running settings
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show() 
    app.exec()