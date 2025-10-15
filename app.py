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
        self.resize(1100, 700)
        self.setMinimumSize(900, 600)
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
        button_layout.setSpacing(15)

        # Create buttons
        main_button, automation_button, api_button, auto_button = {
            "Main Bot": "background-color: #0078d7; color: white;",
            "Automation": "background-color: #5c2d91; color: white;",
            "API Settings": "background-color: #107c10; color: white;",
            "Auto Mode": "background-color: #d83b01; color: white;"
        }

        proxy_server = QPushButton("Custom Proxy Server")
        proxy_server.setFont(QFont("Spotify", 18, QFont.Weight.Bold))
        proxy_server.setStyleSheet("color: #0078d7; background-color: white; margin-bottom: 20px; font-size: 16px; padding: 10px; border-radius: 5px")
        proxy_server.clicked.connect(self.create_proxy_server)
        main_layout.addWidget(proxy_server)

         # Create button
        main_button = QPushButton("PPC Bot Farm")
        main_button.setFont(QFont("Spotify", 18, QFont.Weight.Bold))
        main_button.setFixedSize(100, 50)
        main_button.clicked.connect(self.open_app_bot_window)
        main_button.setStyleSheet("color: white; background-color: green;  font-size: 16px; padding: 10px; border-radius: 5px;")
        main_layout.addWidget(main_button)

        automation_button = QPushButton("Web Automation Bot")
        automation_button.setFont(QFont("Spotify", 18, QFont.Weight.Bold))
        automation_button.setFixedSize(200, 50)
        automation_button.clicked.connect(self.open_web_automation_bot_window)
        automation_button.setStyleSheet("color: blue; background-color: white; font-size: 16px; border-radius: 5px;")
        main_layout.addWidget(automation_button)

        api_button = QPushButton("API")
        api_button.setFont(QFont("Spotify", 18, QFont.Weight.Bold))
        api_button.setFixedSize(100, 50)
        api_button.clicked.connect(self.api_page_function)
        api_button.setStyleSheet("color: white; background-color: red; font-size: 16px; padding: 10px; border-radius: 5px; width: fit-content")
        main_layout.addWidget(api_button)

        auto_button = QPushButton("Automation & Integration")
        auto_button.setFont(QFont("Spotify", 18, QFont.Weight.Bold))
        auto_button.setFixedSize(200, 50)
        auto_button.clicked.connect(self.open_automation_bot_window)
        auto_button.setStyleSheet("color: black; background-color: white; font-size: 16px; bottom: 20px; border-radius: 5px;")
        main_layout.addWidget(auto_button)


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
