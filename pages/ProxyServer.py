"""
proxy_and_vm_manager.py

PySide6 GUI combining:
 - Proxy Manager (add/test proxies)
 - VirtualBox VM Manager (list/create/start/stop/snapshot)
 - SSH Automation Runner (run commands inside a VM)

Run:
    python proxy_and_vm_manager.py

Notes:
 - Requires VirtualBox (VBoxManage) if you want VM control.
 - Requires paramiko for SSH automation.
 - This is a template/starter — adapt paths, ISO names, or cloud provider logic as needed.
"""

import sys
import subprocess
import threading
import time
import json
import os
from functools import partial

import requests
import paramiko

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QMessageBox, QFormLayout, QGroupBox,
    QTabWidget, QTextEdit, QFileDialog, QInputDialog, QSpinBox
)
from PySide6.QtCore import Qt, Slot

# ---------------------------
# Backend: VM management
# ---------------------------

class VMManager:
    """
    VMManager uses VBoxManage to interact with VirtualBox.
    Replace or extend with libvirt or cloud SDKs as needed.
    """

    def __init__(self, vboxmanage_cmd="VBoxManage"):
        self.vboxmanage = vboxmanage_cmd

    def list_vms(self):
        """Return list of tuples (name, uuid)."""
        try:
            out = subprocess.check_output([self.vboxmanage, "list", "vms"], text=True)
            vms = []
            for line in out.splitlines():
                # lines like: "Ubuntu20" {uuid}
                if line.strip():
                    parts = line.split()
                    name = parts[0].strip('"')
                    uuid = parts[-1].strip("{}")
                    vms.append((name, uuid))
            return vms
        except Exception as e:
            raise RuntimeError(f"Failed to list VMs: {e}")

    def start_vm(self, name_or_uuid, gui=False):
        mode = "gui" if gui else "headless"
        subprocess.check_call([self.vboxmanage, "startvm", name_or_uuid, "--type", mode])

    def stop_vm(self, name_or_uuid, acpi_shutdown=True):
        if acpi_shutdown:
            subprocess.check_call([self.vboxmanage, "controlvm", name_or_uuid, "acpipowerbutton"])
        else:
            subprocess.check_call([self.vboxmanage, "controlvm", name_or_uuid, "poweroff"])

    def create_vm_from_iso(self, vm_name, ostype="Ubuntu_64", basefolder=None, memory=2048, cpus=2,
                           disk_mb=20000, iso_path=None):
        """
        Creates a VM and attaches an ISO (for manual installation). For full automation you'd
        use unattended install options or cloud images.
        """
        # Create VM
        cmd = [self.vboxmanage, "createvm", "--name", vm_name, "--ostype", ostype, "--register"]
        if basefolder:
            cmd += ["--basefolder", basefolder]
        subprocess.check_call(cmd)

        # Set memory and CPU
        subprocess.check_call([self.vboxmanage, "modifyvm", vm_name, "--memory", str(memory), "--cpus", str(cpus)])

        # Create a disk
        disk_path = os.path.join(basefolder or os.getcwd(), f"{vm_name}.vdi")
        subprocess.check_call([self.vboxmanage, "createhd", "--filename", disk_path, "--size", str(disk_mb)])

        # Create storage controller and attach disk and iso
        subprocess.check_call([self.vboxmanage, "storagectl", vm_name, "--name", "SATA", "--add", "sata", "--controller", "IntelAhci"])
        subprocess.check_call([self.vboxmanage, "storageattach", vm_name, "--storagectl", "SATA", "--port", "0", "--device", "0", "--type", "hdd", "--medium", disk_path])

        if iso_path:
            subprocess.check_call([self.vboxmanage, "storageattach", vm_name, "--storagectl", "SATA", "--port", "1", "--device", "0", "--type", "dvddrive", "--medium", iso_path])

        return disk_path

    def take_snapshot(self, name_or_uuid, snapshot_name):
        subprocess.check_call([self.vboxmanage, "snapshot", name_or_uuid, "take", snapshot_name])

    def restore_snapshot(self, name_or_uuid, snapshot_name):
        subprocess.check_call([self.vboxmanage, "snapshot", name_or_uuid, "restore", snapshot_name])

# ---------------------------
# Backend: SSH Automation
# ---------------------------

class AutomationRunner:
    """
    Simple wrapper to run commands over SSH and upload files.
    Uses paramiko.
    """

    def __init__(self, hostname, port=22, username=None, password=None, pkey_path=None, timeout=10):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.pkey_path = pkey_path
        self.timeout = timeout
        self.client = None

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        kwargs = {}
        if self.pkey_path:
            pkey = paramiko.RSAKey.from_private_key_file(self.pkey_path)
            kwargs['pkey'] = pkey
        else:
            kwargs['password'] = self.password

        self.client.connect(self.hostname, port=self.port, username=self.username, timeout=self.timeout, **kwargs)

    def run_command(self, command, timeout=60):
        if not self.client:
            self.connect()
        stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
        out = stdout.read().decode()
        err = stderr.read().decode()
        rc = stdout.channel.recv_exit_status()
        return rc, out, err

    def upload_file(self, local_path, remote_path):
        if not self.client:
            self.connect()
        sftp = self.client.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()

    def close(self):
        if self.client:
            self.client.close()
            self.client = None

# ---------------------------
# UI: PySide6 Application
# ---------------------------

class ProxyTab(QWidget):
    def __init__(self):
        super().__init__()
        self.proxies = []  # list of dicts: {host, port, user, password}
        self._build_ui()



    def _build_ui(self):
        layout = QVBoxLayout(self)
    

        self.proxy_list = QListWidget()
        layout.addWidget(QLabel("Saved Proxies:"))
        layout.addWidget(self.proxy_list)

        form = QFormLayout()
        self.host_input = QLineEdit()
        self.port_input = QLineEdit()
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()

        form.addRow("Host:", self.host_input)
        form.addRow("Port:", self.port_input)
        form.addRow("Username:", self.user_input)
        form.addRow("Password:", self.pass_input)

        add_btn = QPushButton("Add Proxy")
        add_btn.clicked.connect(self.add_proxy)
        form.addRow(add_btn)

        layout.addLayout(form)

        controls = QHBoxLayout()
        self.test_btn = QPushButton("Test Selected")
        self.test_btn.clicked.connect(self.test_proxy)
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_proxy)
        self.export_btn = QPushButton("Export (.json)")
        self.export_btn.clicked.connect(self.export_proxies)
        self.import_btn = QPushButton("Import (.json)")
        self.import_btn.clicked.connect(self.import_proxies)

        controls.addWidget(self.test_btn)
        controls.addWidget(self.remove_btn)
        controls.addWidget(self.import_btn)
        controls.addWidget(self.export_btn)

        layout.addLayout(controls)
        self.setLayout(layout)

    
    
    def add_proxy(self):
        host = self.host_input.text().strip()
        port = self.port_input.text().strip()
        user = self.user_input.text().strip()
        pwd = self.pass_input.text().strip()
        if not host or not port:
            QMessageBox.warning(self, "Missing", "Host and port are required.")
            return
        entry = {"host": host, "port": port, "user": user, "password": pwd}
        self.proxies.append(entry)
        self.proxy_list.addItem(f"{host}:{port}")
        self.host_input.clear()
        self.port_input.clear()
        self.user_input.clear()
        self.pass_input.clear()

    def remove_proxy(self):
        i = self.proxy_list.currentRow()
        if i >= 0:
            self.proxy_list.takeItem(i)
            del self.proxies[i]

    def test_proxy(self):
        i = self.proxy_list.currentRow()
        if i < 0:
            QMessageBox.information(self, "Select", "Select a proxy to test.")
            return
        p = self.proxies[i]
        proxy_url = f"http://{p['host']}:{p['port']}"
        proxies = {"http": proxy_url, "https": proxy_url}
        self.test_btn.setEnabled(False)
        self.test_btn.setText("Testing...")
        def worker():
            try:
                start = time.time()
                r = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=8)
                elapsed = time.time() - start
                if r.status_code == 200:
                    QMessageBox.information(self, "Success", f"Proxy works — {elapsed:.2f}s")
                else:
                    QMessageBox.warning(self, "Failure", f"Status: {r.status_code}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"{e}")
            finally:
                self.test_btn.setEnabled(True)
                self.test_btn.setText("Test Selected")
        threading.Thread(target=worker, daemon=True).start()

    def export_proxies(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Proxies", filter="JSON Files (*.json)")
        if path:
            with open(path, "w", encoding="utf8") as f:
                json.dump(self.proxies, f, indent=2)
            QMessageBox.information(self, "Saved", f"Saved to {path}")

    def import_proxies(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Proxies", filter="JSON Files (*.json)")
        if path:
            with open(path, "r", encoding="utf8") as f:
                data = json.load(f)
            self.proxies = data
            self.proxy_list.clear()
            for p in self.proxies:
                self.proxy_list.addItem(f"{p.get('host')}:{p.get('port')}")
            QMessageBox.information(self, "Imported", f"Imported {len(self.proxies)} entries.")

class VMTab(QWidget):
    def __init__(self, vm_manager: VMManager):
        super().__init__()
        self.vm_manager = vm_manager
        self._build_ui()
        self.refresh_vms()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.vm_list = QListWidget()
        layout.addWidget(QLabel("VirtualBox VMs:"))
        layout.addWidget(self.vm_list)

        btns = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_vms)
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_vm)
        self.stop_btn = QPushButton("Stop (ACPI)")
        self.stop_btn.clicked.connect(self.stop_vm)
        self.poweroff_btn = QPushButton("Power Off")
        self.poweroff_btn.clicked.connect(partial(self.stop_vm, acpi=False))
        self.snapshot_btn = QPushButton("Snapshot")
        self.snapshot_btn.clicked.connect(self.take_snapshot)
        self.create_btn = QPushButton("Create VM (from ISO)")
        self.create_btn.clicked.connect(self.create_vm_dialog)

        btns.addWidget(self.refresh_btn)
        btns.addWidget(self.start_btn)
        btns.addWidget(self.stop_btn)
        btns.addWidget(self.poweroff_btn)
        btns.addWidget(self.snapshot_btn)
        btns.addWidget(self.create_btn)
        layout.addLayout(btns)

        # Automation section
        layout.addWidget(QLabel("Automation (SSH)"))
        form = QFormLayout()
        self.ssh_host = QLineEdit()
        self.ssh_port = QLineEdit()
        self.ssh_user = QLineEdit()
        self.ssh_pass = QLineEdit()
        form.addRow("SSH Host:", self.ssh_host)
        form.addRow("SSH Port:", self.ssh_port)
        form.addRow("User:", self.ssh_user)
        form.addRow("Password:", self.ssh_pass)
        layout.addLayout(form)

        auto_btns = QHBoxLayout()
        self.run_cmd_btn = QPushButton("Run Command")
        self.run_cmd_btn.clicked.connect(self.run_command_dialog)
        self.upload_btn = QPushButton("Upload File")
        self.upload_btn.clicked.connect(self.upload_file_dialog)
        auto_btns.addWidget(self.run_cmd_btn)
        auto_btns.addWidget(self.upload_btn)
        layout.addLayout(auto_btns)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        self.setLayout(layout)

    @Slot()
    def refresh_vms(self):
        try:
            vms = self.vm_manager.list_vms()
            self.vm_list.clear()
            for name, uuid in vms:
                item = QListWidgetItem(f"{name}  [{uuid}]")
                item.setData(Qt.UserRole, (name, uuid))
                self.vm_list.addItem(item)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _selected_vm(self):
        i = self.vm_list.currentRow()
        if i < 0:
            return None
        item = self.vm_list.currentItem()
        return item.data(Qt.UserRole)

    def start_vm(self):
        vm = self._selected_vm()
        if not vm:
            QMessageBox.information(self, "Select", "Select a VM first.")
            return
        name, uuid = vm
        try:
            self.vm_manager.start_vm(uuid, gui=False)
            QMessageBox.information(self, "Started", f"{name} starting headless.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Start failed: {e}")



    def stop_vm(self, acpi=True):
        vm = self._selected_vm()
        if not vm:
            QMessageBox.information(self, "Select", "Select a VM first.")
            return
        name, uuid = vm
        try:
            if acpi:
                self.vm_manager.stop_vm(uuid, acpi_shutdown=True)
            else:
                self.vm_manager.stop_vm(uuid, acpi_shutdown=False)
            QMessageBox.information(self, "Stopped", f"{name} stop/poweroff issued.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Stop failed: {e}")

    def take_snapshot(self):
        vm = self._selected_vm()
        if not vm:
            QMessageBox.information(self, "Select", "Select a VM first.")
            return
        name, uuid = vm
        snap_name, ok = QInputDialog.getText(self, "Snapshot", "Snapshot name:")
        if not ok or not snap_name:
            return
        try:
            self.vm_manager.take_snapshot(uuid, snap_name)
            QMessageBox.information(self, "Snapshot", f"Snapshot {snap_name} created for {name}.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Snapshot failed: {e}")

    def create_vm_dialog(self):
        vm_name, ok = QInputDialog.getText(self, "Create VM", "VM Name:")
        if not ok or not vm_name:
            return
        iso_path, _ = QFileDialog.getOpenFileName(self, "Select ISO")
        if not iso_path:
            QMessageBox.information(self, "ISO Required", "You must select an ISO to install from.")
            return
        memory, ok = QInputDialog.getInt(self, "Memory (MB)", "Memory (MB):", value=2048, min=512, max=65536)
        if not ok:
            return
        try:
            disk = self.vm_manager.create_vm_from_iso(vm_name, iso_path=iso_path, memory=memory, basefolder=os.getcwd())
            QMessageBox.information(self, "Created", f"VM {vm_name} created, disk at {disk}.")
            self.refresh_vms()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def run_command_dialog(self):
        host = self.ssh_host.text().strip()
        if not host:
            QMessageBox.information(self, "SSH Host", "Enter SSH host/IP.")
            return
        port = int(self.ssh_port.text().strip() or 22)
        user = self.ssh_user.text().strip()
        pwd = self.ssh_pass.text().strip()
        cmd, ok = QInputDialog.getMultiLineText(self, "Run Command", "Command to run:")
        if not ok or not cmd.strip():
            return

        def worker():
            self.output.append(f"> Connecting to {host}:{port} as {user}")
            runner = AutomationRunner(hostname=host, port=port, username=user, password=pwd)
            try:
                runner.connect()
                rc, out, err = runner.run_command(cmd)
                self.output.append(f"--- RC={rc} ---")
                if out:
                    self.output.append(out)
                if err:
                    self.output.append("ERROR:\n" + err)
            except Exception as e:
                self.output.append(f"Automation error: {e}")
            finally:
                runner.close()
        threading.Thread(target=worker, daemon=True).start()

    def upload_file_dialog(self):
        host = self.ssh_host.text().strip()
        if not host:
            QMessageBox.information(self, "SSH Host", "Enter SSH host/IP.")
            return
        port = int(self.ssh_port.text().strip() or 22)
        user = self.ssh_user.text().strip()
        pwd = self.ssh_pass.text().strip()
        local, _ = QFileDialog.getOpenFileName(self, "Select file to upload")
        if not local:
            return
        remote, ok = QInputDialog.getText(self, "Remote Path", "Remote path (absolute):", text="/tmp/uploaded.file")
        if not ok or not remote:
            return

        def worker():
            self.output.append(f"> Uploading {local} to {user}@{host}:{remote}")
            runner = AutomationRunner(hostname=host, port=port, username=user, password=pwd)
            try:
                runner.connect()
                runner.upload_file(local, remote)
                self.output.append("Upload completed.")
            except Exception as e:
                self.output.append(f"Upload error: {e}")
            finally:
                runner.close()
        threading.Thread(target=worker, daemon=True).start()

class ProxyServer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Proxy & VM Manager")
        self.setGeometry(150, 150, 1000, 700)
        self.vm_manager = VMManager()
        self._build_ui()


        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.back)
        self.page_layout.addWidget(back_btn)




    def _build_ui(self):
        self.page_layout = QVBoxLayout()
        tabs = QTabWidget()
        self.proxy_tab = ProxyTab()
        self.vm_tab = VMTab(self.vm_manager)
        tabs.addTab(self.proxy_tab, "Proxies")
        tabs.addTab(self.vm_tab, "VMs & Automation")
        self.setLayout(self.page_layout)
        self.page_layout.addWidget(tabs)



    def back(self):
        from app import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()    


