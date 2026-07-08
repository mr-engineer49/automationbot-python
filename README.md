# AutomationBot Python

A desktop automation platform built with PySide6 that brings together web automation, API testing, proxy management, and task scheduling into one unified interface.

## What This Tool Does Right Now

This is a work-in-progress automation toolkit. Currently, it handles:

**Web Automation**
- Launch Chrome browsers (headless or visible) with Selenium
- Apply proxy configurations to browser sessions
- Basic campaign automation framework

**Proxy Management**
- Import proxies from JSON files or Proxifly API
- Test HTTP, HTTPS, and SOCKS5 proxies
- View proxy performance and geolocation data
- Handle malformed proxy entries gracefully

**API Testing**
- Make HTTP requests (GET, POST, PUT, DELETE, PATCH)
- Set custom headers and JSON bodies
- View response status, time, and body
- Save request history to file for replay

**Custom Scripts**
- Write and save Python, JavaScript, or Shell/Bash scripts
- Execute scripts with real-time logging
- Convert API requests into Python scripts automatically
- Scripts persist across app restarts

**Task Scheduling**
- Schedule tasks to run at specific times
- Schedule custom scripts and API requests
- Load existing scripts/APIs directly into scheduler
- Execute scheduled tasks on demand

**Airtable Integration**
- Connect to Airtable via API key
- Fetch records from tables
- Use data for automation workflows

## Current Features

### File Persistence
All your data is saved to `~/.config_files/`:
- `scheduled_tasks.json` - Your scheduled tasks
- `custom_scripts.json` - Your saved scripts
- `api_request_history.json` - API request history
- `airtable_config.json` - Airtable credentials
- `settings.json` - General settings

### Module Integration
The three main utility modules work together:
- **API Runner** → Convert requests to scripts → Schedule them
- **Custom Scripts** → Execute scripts → Schedule them
- **Scheduler** → Load scripts/APIs → Execute them on schedule

### Thread-Safe Operations
- Background tasks don't freeze the UI
- Proper Qt signal/slot handling for cross-thread updates
- Safe file operations from worker threads

## Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/automationbot-python.git
cd automationbot-python

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

## Project Structure

```
automationbot-python/
├── app.py                          # Main entry point
├── pages/
│   ├── WebAutomation.py            # Web automation + utilities
│   ├── ProxyServer.py              # Proxy management + VM control
│   ├── appbot.py                   # Airtable automation
│   ├── ApiPages.py                 # API interface
│   └── automations_integrations/   # Make.com, n8n integrations
├── requirements.txt
└── README.md
```

## How to Use

### Proxy Management
1. Go to the Proxies tab
2. Import proxies from JSON or use Proxifly API
3. Test proxies to verify they work
4. Proxies are saved and can be used in browser automation

### API Testing
1. Click "API Runner" in Web Automation
2. Enter URL, select method, add headers/body
3. Click "Send Request"
4. View response in the output panel
5. History is saved automatically

### Custom Scripts
1. Click "Custom Scripts" in Web Automation
2. Write your script (Python, JavaScript, or Shell)
3. Save it with a name
4. Execute it and view logs in real-time
5. Use "Create from API" to convert API requests to scripts

### Task Scheduling
1. Click "Scheduler" in Web Automation
2. Choose task type (Custom Script, API Request, etc.)
3. Use "Load from Scripts" or "Load from API History" to quickly populate
4. Set schedule time and repeat interval
5. Click "Run Now" to test, or save for scheduled execution

## What's Working

✅ Proxy import and testing (HTTP, HTTPS, SOCKS5)
✅ API request sending and history
✅ Custom script execution with logging
✅ Task scheduling with file persistence
✅ Module integration (API → Script → Schedule workflow)
✅ Airtable connection and data fetching
✅ Thread-safe UI updates
✅ File-based configuration persistence

## What Needs Major Upgrades

### High Priority
1. **Actual Scheduled Execution**
   - Currently, "Run Now" works but automatic scheduled execution doesn't run in background
   - Need a background scheduler service that checks and runs tasks at their scheduled times
   - Should handle repeat intervals and enable/disable states

2. **Campaign Automation**
   - The campaign framework exists but isn't fully implemented
   - Need actual campaign logic that uses Airtable data
   - Should integrate with proxy rotation and browser automation

3. **Error Handling & Logging**
   - Need better error messages throughout
   - Centralized logging system instead of print statements
   - Error recovery mechanisms (retry failed requests, etc.)

4. **Proxy Rotation in Browser**
   - Proxy configuration exists but rotation during automation isn't implemented
   - Need to cycle through proxies during long-running tasks

### Medium Priority
5. **n8n Integration**
   - The n8n page exists but needs actual workflow execution
   - Should be able to trigger n8n webhooks and monitor status

6. **Make.com Integration**
   - Similar to n8n - needs actual API calls to Make.com
   - Webhook triggers and response handling

7. **UI Improvements**
   - Some buttons and layouts could be cleaner
   - Better visual feedback during long operations
   - Progress bars for file operations and network requests

8. **Configuration Management**
   - Need a proper settings dialog instead of JSON editing
   - Should be able to configure all settings from GUI

### Nice to Have
9. **Script Templates**
   - Pre-built script templates for common tasks
   - API request templates for popular services

10. **Export/Import**
    - Export scripts, tasks, and configurations for backup
    - Import configurations from other instances

11. **Dashboard**
    - Overview screen showing running tasks, recent activity
    - Statistics (success rates, proxy performance, etc.)

12. **Browser Automation Enhancements**
    - More browser options (Firefox, Edge)
    - Better element selection and interaction
    - Screenshot capture and video recording

## Known Issues & Limitations

### Critical Issues
- **No automatic task execution**: Scheduled tasks are saved but don't run automatically. You must manually click "Run Now". There's no background scheduler service checking times and executing tasks.
- **Campaign automation not implemented**: The campaign framework exists but has no actual logic. It doesn't use Airtable data or perform any automation.
- **JavaScript execution doesn't work**: JavaScript scripts show a message saying they need browser context, but there's no actual integration with Selenium for JS execution.

### Functional Limitations
- **No proxy rotation**: Proxies can be configured but don't rotate during long-running tasks. The same proxy is used throughout a session.
- **No retry logic**: Failed API requests or proxy tests don't automatically retry. You have to manually retry.
- **No browser automation beyond launching**: You can launch Chrome with Selenium, but there's no actual automation logic (clicking, form filling, data extraction).
- **n8n and Make.com are placeholders**: These integrations exist as pages but don't actually connect to or trigger workflows.
- **No SSH automation for VMs**: The VM tab has SSH connection logic but no actual automation or command execution.

### Technical Issues
- **Print statements instead of logging**: Many errors and debug messages use `print()` instead of a proper logging system, making debugging difficult.
- **File operations aren't atomic**: Saving JSON files could corrupt data if the app crashes mid-write. No temp file + rename pattern.
- **Thread safety gaps**: While most UI updates use Qt signals, some file operations and data manipulations might not be fully thread-safe.
- **No input validation**: Some user inputs aren't validated before use, which could cause crashes with malformed data.
- **SOCKS5 SSL issues**: SOCKS5 proxies can fail with SSL certificate verification, requiring `verify=False` which is insecure.

### UX Issues
- **No settings GUI**: All configuration requires editing JSON files manually in `~/.config_files/`.
- **No backup/restore**: No way to export or import configurations, scripts, or tasks for backup or sharing.
- **No progress indicators**: Long operations (file loads, network requests) don't show progress bars.
- **Error messages are generic**: Many errors just show "Error occurred" without specific details about what went wrong.
- **UI can freeze**: Some operations block the main thread despite threading being used elsewhere.

### Data Issues
- **No data migration**: If the JSON schema changes, old files won't automatically upgrade. You might lose data.
- **No duplicate detection**: You can save multiple scripts or tasks with the same name, causing confusion.
- **No cleanup**: Old API history accumulates indefinitely with no way to clear or prune it.
- **No search/filter**: Can't search through scripts, tasks, or API history when lists get long.

### Security Concerns
- **SSL verification disabled**: Proxy testing uses `verify=False` to handle public proxies, which is insecure for production use.
- **Credentials stored in plain text**: API keys and passwords are stored in JSON files without encryption.
- **No rate limiting**: API requests can be sent as fast as you click, potentially getting you rate-limited or banned.

## Dependencies

- PySide6 (Qt GUI framework)
- Selenium (browser automation)
- requests (HTTP requests)
- paramiko (SSH for VM management)
- Other standard Python libraries

## Author

Enea Hysa
Automation Engineer & Developer
eneahysa49@gmail.com

## License

This is a personal project. Use it, modify it, break it - it's here to help with automation tasks.
