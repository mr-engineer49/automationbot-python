# 🤖 Automated Bot Platform

### A desktop-based automation framework for APIs, bots, and integrations.

This tool provides a modular environment for creating, connecting, and automating workflows using:
- **Airtable** (data-driven campaigns and storage)
- **Make.com** (automation integration)
- **n8n** (local or hosted automation flows)
- **Proxy management** (via Proxifly API or JSON configurations)
- **Browser automation** (via Selenium and PySide6 GUI)

It serves as a control panel for marketing automation, web data extraction, and intelligent task management — designed to be extendable for both developers and non-technical users.

---

## 📦 Features

✅ **Desktop GUI (PySide6)**
- Central dashboard for all automation tools.
- Tabs for Web Automation, API, Proxy, and n8n integration.

✅ **Automation Integrations**
- Run workflows with **n8n** or **Make.com** directly from the app.
- Manage automations from local or cloud environments.

✅ **Proxy Management**
- Load and test SOCKS5/HTTP proxies from Proxifly or JSON files.
- Rotate proxies automatically during browser runs.

✅ **Airtable Integration**
- Fetch, view, and update Airtable tables via API key and base ID.
- Store configuration securely in user space.

✅ **Web Automation**
- Control browsers with Selenium.
- Run campaign scripts, load URLs dynamically, and test proxies.

---

## 🗂️ Project Structure

automated-bot-py/
│
├── desktopapp/
│ ├── app.py # Main entry point for launching the app
│ ├── pages/
│ │ ├── appbot.py # Main automation control window
│ │ ├── WebAutomationBot.py # Web automation page with proxy + Selenium integration
│ │ ├── apipages.py # API interface for calling endpoints and webhooks
│ │ ├── n8nPage.py # n8n integration and management
│ │ ├── airtableConnector.py # Airtable connection and settings GUI
│ │ ├── proxyConnector.py # Proxy configuration and testing logic
│ │ └── ...
│ │
│ ├── integrations/ # External service connections
│ │ ├── make_automation/ # Make.com integration
│ │ ├── n8n_automation/ # n8n automation scripts
│ │ └── airtable_automation/ # Airtable workflows
│ │
│ ├── automations/ # Custom user or system automations
│ │ ├── web/ # Browser automation
│ │ ├── marketing/ # Affiliate / campaign automation
│ │ └── ...
│ │
│ └── config_files/ # User configuration files
│ ├── airtable_config.json
│ ├── proxy_config.json
│ └── ...
│
├── requirements.txt
├── README.md
└── .gitignore

yaml
Copy code

---

## ⚙️ Installation

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/<your-username>/automated-bot-py.git
cd automated-bot-py/desktopapp
2️⃣ Create and Activate Virtual Environment
bash
Copy code
python -m venv venv
venv\Scripts\activate       # On Windows
source venv/bin/activate    # On macOS/Linux
3️⃣ Install Dependencies
bash
Copy code
pip install -r requirements.txt
4️⃣ Install n8n (optional)
If you plan to use n8n locally:

bash
Copy code
npm install -g n8n
Then verify installation:

bash
Copy code
n8n --version
▶️ Running the App
Once dependencies are installed, run:

bash
Copy code
python app.py
This will launch the main GUI window, from which you can:

Configure Airtable and proxy settings

Run web automation scripts

Start or monitor n8n automations

Connect to Make.com workflows

🧩 Configurations
🔑 Airtable
You can configure your Airtable connection in the AirtableConnector tab:

json
Copy code
{
  "api_key": "your_api_key",
  "base_id": "appXXXXXXX",
  "table_name": "tblXXXXXXX",
  "view_name": "Ready to Run View"
}
This is saved automatically in:

makefile
Copy code
C:\Users\<YourUser>\.autoflowai_configs\airtable_config.json
🌍 Proxy Configuration
Example JSON structure for proxy file:

json
Copy code
{
  "proxy": "proxyapi",
  "protocol": "socks5",
  "ip": "202.5.47.181",
  "port": 1080,
  "https": false,
  "anonymity": "transparent",
  "score": 1,
  "geolocation": {
    "country": "BD",
    "city": ""
  }
}
💻 Developer Mode
To modify UI or logic:

Each tool or integration is modularized in /pages/.

Add new tabs or connectors by creating a subclass of QMainWindow or QWidget.

The main app loads them dynamically through QStackedLayout or QTabWidget.

🚀 Roadmap
✅ Version 1.0:

Proxy rotation

Airtable connection

Web automation

🧠 Planned (next releases):

n8n workflow visualizer

AI-powered campaign generator

Make.com bidirectional sync

Built-in task scheduler for 24/7 automations


🧑‍💻 Author
Enea Hysa

Automation Engineer & Developer
📧 eneahysa49@gmail.com
🌐 https://enea-testoralabs.web.app/# automationbot.py
