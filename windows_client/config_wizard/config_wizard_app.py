import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import socket
import subprocess
import json
import os
import platform
import ipaddress # For IP validation

# Attempt to import requests, though it's for Ollama/Linux tests, not core GUI
try:
    import requests
except ImportError:
    requests = None # Will handle this gracefully

# --- Configuration ---
DEFAULT_OLLAMA_PORT = 11434
DEFAULT_MEM0_PORT = 8000 # Default for the Linux mem0 service
CONFIG_FILE_NAME = "linux_config.json" # Config file to be generated for the Linux side

class ConfigWizardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WeChatMemories Configuration Wizard")
        self.root.geometry("650x700") # Adjusted for more content

        # --- Variables ---
        self.windows_ip_var = tk.StringVar(value=self.get_local_ip())
        self.linux_ip_var = tk.StringVar()
        self.shared_folder_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Documents", "WeChatMemories", "RawLogs"))
        self.windows_share_username_var = tk.StringVar(value=os.getlogin()) # Pre-fill with current user
        self.windows_share_password_var = tk.StringVar() # Keep password field empty
        self.ollama_llm_model_var = tk.StringVar()
        self.ollama_embedding_model_var = tk.StringVar()
        self.shared_secret_var = tk.StringVar(value=self.generate_simple_secret())

        self.ollama_models = [] # To store list of models from ollama api

        # --- UI Layout ---
        self.notebook = ttk.Notebook(root)

        # Tab 1: Network Configuration
        self.tab_network = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_network, text='Network')
        self.create_network_tab(self.tab_network)

        # Tab 2: Windows Share & Ollama
        self.tab_windows = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_windows, text='Windows Setup')
        self.create_windows_tab(self.tab_windows)

        # Tab 3: Model Selection & Generation
        self.tab_models = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_models, text='Models & Config')
        self.create_models_tab(self.tab_models)

        # Tab 4: Testing
        self.tab_testing = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_testing, text='Connectivity Tests')
        self.create_testing_tab(self.tab_testing)

        self.notebook.pack(expand=1, fill='both', padx=10, pady=10)

        # Initial population
        self.refresh_ollama_models()


    def generate_simple_secret(self):
        # Basic secret, user should be encouraged to change if desired
        return os.urandom(16).hex()

    def get_local_ip(self):
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            # Check if it's a loopback or similar, try another way if so
            if local_ip.startswith("127."):
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(0)
                try:
                    # doesn't even have to be reachable
                    s.connect(('10.254.254.254', 1))
                    IP = s.getsockname()[0]
                except Exception:
                    IP = '127.0.0.1' # Fallback
                finally:
                    s.close()
                return IP
            return local_ip
        except socket.gaierror:
            return "Could not determine IP"

    def create_network_tab(self, tab):
        frame = ttk.LabelFrame(tab, text="IP Addresses & Shared Secret", padding=(10,10))
        frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(frame, text="Windows Local IP:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frame, textvariable=self.windows_ip_var, state="readonly", width=40).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame, text="Linux Remote IP:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frame, textvariable=self.linux_ip_var, width=40).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(frame, text="Help: Finding Linux IP", command=self.show_linux_ip_help).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(frame, text="Shared Secret Key:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frame, textvariable=self.shared_secret_var, width=40).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(frame, text="Generate New", command=lambda: self.shared_secret_var.set(self.generate_simple_secret())).grid(row=2, column=2, padx=5, pady=5)
        ttk.Label(frame, text="(Used for App-Level Authentication)").grid(row=3, column=1, padx=5, pady=2, sticky="w")


    def show_linux_ip_help(self):
        messagebox.showinfo("Finding Linux IP Address",
                            "On your Linux machine, open a terminal and type:\n"
                            "ip addr show\n\n"
                            "Look for an IPv4 address associated with your main network interface (e.g., eth0, enpXsY). It will typically be in a format like 192.168.x.x or 10.x.x.x.")

    def create_windows_tab(self, tab):
        # Windows Share Configuration
        share_frame = ttk.LabelFrame(tab, text="Windows Network Share (SMB)", padding=(10,10))
        share_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(share_frame, text="Shared Folder Path:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(share_frame, textvariable=self.shared_folder_var, width=50).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(share_frame, text="Browse", command=self.browse_shared_folder).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(share_frame, text="Windows Username (for share access):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(share_frame, textvariable=self.windows_share_username_var, width=30).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(share_frame, text="Windows Password (for share access):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(share_frame, textvariable=self.windows_share_password_var, show="*", width=30).grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Button(share_frame, text="Verify Share Path", command=self.verify_shared_folder_path).grid(row=3, column=1, padx=5, pady=10, sticky="w")
        ttk.Button(share_frame, text="Open SMB Setup Guide", command=lambda: self.open_guide("smb_setup_guide.md")).grid(row=3, column=0, padx=5, pady=10, sticky="w")


        # Ollama & Firewall
        ollama_frame = ttk.LabelFrame(tab, text="Ollama Service & Firewall", padding=(10,10))
        ollama_frame.pack(padx=10, pady=10, fill="x", expand=True)

        ttk.Button(ollama_frame, text="Check Ollama Port (11434) Firewall Rule", command=self.check_ollama_firewall_rule).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(ollama_frame, text="Open Ollama Setup Guide", command=lambda: self.open_guide("ollama_setup_guide.md")).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ollama_frame.grid_columnconfigure(0, weight=1)
        ollama_frame.grid_columnconfigure(1, weight=1)


    def browse_shared_folder(self):
        # User might not have created it yet, so initialdir is just a suggestion
        initial_dir = self.shared_folder_var.get()
        if not os.path.isdir(initial_dir):
            initial_dir = os.path.expanduser("~")

        directory = filedialog.askdirectory(initialdir=initial_dir, title="Select RawLogs Folder Location")
        if directory:
            self.shared_folder_var.set(directory)

    def verify_shared_folder_path(self):
        path = self.shared_folder_var.get()
        if not path:
            messagebox.showerror("Error", "Shared folder path is empty.")
            return
        if os.path.isdir(path):
            messagebox.showinfo("Success", f"Path '{path}' exists locally.\nEnsure it's correctly shared via SMB (see guide).")
        else:
            if messagebox.askyesno("Path Not Found", f"Path '{path}' does not exist locally. Create it now?"):
                try:
                    os.makedirs(path, exist_ok=True)
                    messagebox.showinfo("Success", f"Path '{path}' created locally.\nRemember to configure SMB sharing for it.")
                except Exception as e:
                    messagebox.showerror("Error", f"Could not create directory: {e}")

    def open_guide(self, guide_name):
        # Assumes guides are in a 'docs' subdirectory relative to this script's location
        # or in a 'docs' subdir of 'windows_client' if script is in 'windows_client/config_wizard'
        script_dir = os.path.dirname(os.path.abspath(__file__))
        guide_path_local = os.path.join(script_dir, "docs", guide_name) # if docs is inside config_wizard
        guide_path_project = os.path.join(script_dir, "..", "docs", guide_name) # if docs is in windows_client/docs

        actual_guide_path = ""
        if os.path.exists(guide_path_local):
            actual_guide_path = guide_path_local
        elif os.path.exists(guide_path_project):
            actual_guide_path = guide_path_project
        else:
            messagebox.showerror("Error", f"Guide '{guide_name}' not found at expected locations:\n{guide_path_local}\nOR\n{guide_path_project}")
            return

        try:
            if platform.system() == "Windows":
                os.startfile(actual_guide_path)
            elif platform.system() == "Darwin": # macOS
                subprocess.run(["open", actual_guide_path], check=True)
            else: # Linux
                subprocess.run(["xdg-open", actual_guide_path], check=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open guide: {e}")


    def check_ollama_firewall_rule(self):
        # This is a simplified check. PowerShell offers more robust ways.
        # For now, we inform the user or point to the guide.
        # A more advanced check would parse `netsh advfirewall firewall show rule name="Ollama Access (TCP 11434)"`
        # or use PowerShell Get-NetFirewallRule
        try:
            # Attempt to check if port is open using a simple socket connection (not a true firewall rule check)
            # This only checks if *something* is listening, not if firewall *allows* external.
            # For a true firewall check, we'd need admin rights and specific commands.
            # For now, point to the guide.
            messagebox.showinfo("Firewall Check",
                                "This wizard cannot directly modify firewall rules without admin rights.\n\n"
                                "Please refer to the 'Ollama Setup Guide' for instructions on how to:\n"
                                "1. Add a firewall rule for TCP port 11434.\n"
                                "2. Ensure Ollama is configured to listen on 0.0.0.0 (all interfaces) if needed.\n\n"
                                "You can try the 'Test Ollama Connection' in the 'Connectivity Tests' tab FROM THE LINUX MACHINE "
                                "once everything is set up to confirm.")
        except Exception as e:
            messagebox.showerror("Error", f"Firewall check helper error: {e}")


    def create_models_tab(self, tab):
        frame = ttk.LabelFrame(tab, text="Ollama Model Selection", padding=(10,10))
        frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(frame, text="Available Ollama Models:").grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self.model_listbox = tk.Listbox(frame, height=6, width=60)
        self.model_listbox.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        ttk.Button(frame, text="Refresh Model List", command=self.refresh_ollama_models).grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        ttk.Label(frame, text="Selected LLM Model:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.llm_model_combo = ttk.Combobox(frame, textvariable=self.ollama_llm_model_var, width=37, state="readonly")
        self.llm_model_combo.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame, text="Selected Embedding Model:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.embedding_model_combo = ttk.Combobox(frame, textvariable=self.ollama_embedding_model_var, width=37, state="readonly")
        self.embedding_model_combo.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        # Config file generation
        config_frame = ttk.LabelFrame(tab, text="Configuration File for Linux", padding=(10,10))
        config_frame.pack(padx=10, pady=10, fill="x", expand=True, side=tk.BOTTOM)

        self.config_path_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads", CONFIG_FILE_NAME))
        ttk.Label(config_frame, text="Save Config As:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(config_frame, textvariable=self.config_path_var, width=50).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(config_frame, text="Browse", command=self.browse_config_save_path).grid(row=0, column=2, padx=5, pady=5)

        ttk.Button(config_frame, text="Generate Linux Configuration File", command=self.generate_config_file).grid(row=1, column=0, columnspan=3, padx=5, pady=10)


    def refresh_ollama_models(self):
        self.model_listbox.delete(0, tk.END)
        self.ollama_models = []
        if not requests:
            self.model_listbox.insert(tk.END, "Python 'requests' module not found.")
            self.model_listbox.insert(tk.END, "Cannot fetch models. Please install it: pip install requests")
            return

        try:
            response = requests.get(f"http://{self.windows_ip_var.get()}:{DEFAULT_OLLAMA_PORT}/api/tags")
            response.raise_for_status()
            models_data = response.json()
            if "models" in models_data:
                self.ollama_models = sorted([model['name'] for model in models_data['models']])
                for model_name in self.ollama_models:
                    self.model_listbox.insert(tk.END, model_name)
                self.llm_model_combo['values'] = self.ollama_models
                self.embedding_model_combo['values'] = self.ollama_models
                if self.ollama_models:
                    # Try to pre-select common choices
                    llm_candidates = [m for m in self.ollama_models if any(k in m.lower() for k in ["llama", "mistral", "llm"])]
                    embed_candidates = [m for m in self.ollama_models if any(k in m.lower() for k in ["nomic-embed-text", "embedding", "embed"])]
                    if llm_candidates: self.ollama_llm_model_var.set(llm_candidates[0])
                    elif self.ollama_models: self.ollama_llm_model_var.set(self.ollama_models[0])
                    if embed_candidates: self.ollama_embedding_model_var.set(embed_candidates[0])
                    elif self.ollama_models: self.ollama_embedding_model_var.set(self.ollama_models[0])

            else:
                self.model_listbox.insert(tk.END, "No models found or unexpected API response.")
        except requests.exceptions.ConnectionError:
            self.model_listbox.insert(tk.END, f"Error: Could not connect to Ollama at")
            self.model_listbox.insert(tk.END, f"http://{self.windows_ip_var.get()}:{DEFAULT_OLLAMA_PORT}")
            self.model_listbox.insert(tk.END, "Ensure Ollama is running and accessible.")
        except requests.exceptions.RequestException as e:
            self.model_listbox.insert(tk.END, f"Error fetching models: {e}")
        except Exception as e:
            self.model_listbox.insert(tk.END, f"An unexpected error occurred: {e}")


    def browse_config_save_path(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile=CONFIG_FILE_NAME,
            initialdir=os.path.dirname(self.config_path_var.get()) or os.path.expanduser("~"),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Linux Configuration File"
        )
        if file_path:
            self.config_path_var.set(file_path)

    def generate_config_file(self):
        # Validation
        if not self.linux_ip_var.get():
            messagebox.showerror("Error", "Linux Remote IP is required.")
            return
        try:
            ipaddress.ip_address(self.linux_ip_var.get()) # Validate IP
        except ValueError:
            messagebox.showerror("Error", "Invalid Linux Remote IP address format.")
            return

        if not self.shared_folder_var.get():
            messagebox.showerror("Error", "Windows Shared Folder Path is required.")
            return
        if not self.windows_share_username_var.get():
            messagebox.showerror("Warning", "Windows Share Username is empty. This might cause issues on Linux.")
            # Allow proceeding but warn

        if not self.ollama_llm_model_var.get():
            messagebox.showerror("Error", "Ollama LLM Model selection is required.")
            return
        if not self.ollama_embedding_model_var.get():
            messagebox.showerror("Error", "Ollama Embedding Model selection is required.")
            return
        if not self.shared_secret_var.get():
            messagebox.showerror("Error", "Shared Secret Key is required.")
            return
        if not self.config_path_var.get():
            messagebox.showerror("Error", "Config file save path is required.")
            return

        config_data = {
            "windows_ip": self.windows_ip_var.get(),
            "windows_smb_share_path": self.shared_folder_var.get().replace("\\", "/"), # Convert to forward slashes for Linux
            "windows_smb_username": self.windows_share_username_var.get(),
            "windows_smb_password": self.windows_share_password_var.get(), # User should be aware this is saved
            "ollama_base_url": f"http://{self.windows_ip_var.get()}:{DEFAULT_OLLAMA_PORT}",
            "ollama_llm_model": self.ollama_llm_model_var.get(),
            "ollama_embedding_model": self.ollama_embedding_model_var.get(),
            "linux_ip": self.linux_ip_var.get(), # For potential future use or self-awareness on Linux side
            "mem0_port": DEFAULT_MEM0_PORT,
            "shared_secret_key": self.shared_secret_var.get()
        }

        try:
            with open(self.config_path_var.get(), 'w') as f:
                json.dump(config_data, f, indent=4)
            messagebox.showinfo("Success", f"Configuration file saved to:\n{self.config_path_var.get()}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration file: {e}")

    def create_testing_tab(self, tab):
        frame = ttk.LabelFrame(tab, text="Connectivity & Service Tests", padding=(10,10))
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.test_results_text = tk.Text(frame, height=15, width=70, wrap=tk.WORD, state=tk.DISABLED)
        self.test_results_text.pack(padx=5, pady=5, fill="both", expand=True)

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=5)

        ttk.Button(button_frame, text="Test Local Ollama Access", command=self.test_local_ollama).pack(side=tk.LEFT, padx=5, pady=2)
        ttk.Button(button_frame, text="Test Ping Linux Host", command=self.test_ping_linux_host).pack(side=tk.LEFT, padx=5, pady=2)
        ttk.Button(button_frame, text="Test Linux mem0 Service API", command=self.test_linux_mem0_api).pack(side=tk.LEFT, padx=5, pady=2)

    def _log_test_result(self, message):
        self.test_results_text.config(state=tk.NORMAL)
        self.test_results_text.insert(tk.END, message + "\n")
        self.test_results_text.see(tk.END) # Scroll to bottom
        self.test_results_text.config(state=tk.DISABLED)
        self.root.update_idletasks() # Ensure UI updates

    def test_local_ollama(self):
        self._log_test_result(f"--- Testing Local Ollama (http://{self.windows_ip_var.get()}:{DEFAULT_OLLAMA_PORT}) ---")
        if not requests:
            self._log_test_result("SKIPPED: Python 'requests' module not installed.")
            return

        try:
            url = f"http://{self.windows_ip_var.get()}:{DEFAULT_OLLAMA_PORT}/api/tags"
            self._log_test_result(f"Attempting to connect to {url}...")
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            self._log_test_result(f"SUCCESS: Connected to Ollama. Status: {response.status_code}")
            try:
                models = response.json().get("models", [])
                if models:
                    self._log_test_result(f"Found {len(models)} models.")
                    # self._log_test_result(f"Models: {[m['name'] for m in models]}")
                else:
                    self._log_test_result("No models found via API, but connection successful.")
            except json.JSONDecodeError:
                 self._log_test_result("WARNING: Ollama responded, but not with valid JSON for models list.")

        except requests.exceptions.Timeout:
            self._log_test_result(f"FAIL: Connection to Ollama timed out.")
        except requests.exceptions.ConnectionError:
            self._log_test_result(f"FAIL: Could not connect to Ollama. Ensure it's running and accessible.")
            self._log_test_result(f"       Check firewall and if Ollama listens on {self.windows_ip_var.get()} (or 0.0.0.0).")
        except requests.exceptions.HTTPError as e:
            self._log_test_result(f"FAIL: Connected to Ollama, but received HTTP error: {e.response.status_code} - {e.response.reason}")
        except Exception as e:
            self._log_test_result(f"FAIL: An unexpected error occurred: {e}")
        self._log_test_result("--- Test Finished ---")

    def test_ping_linux_host(self): # Renamed
        linux_ip = self.linux_ip_var.get()
        self._log_test_result(f"--- Testing Ping to Linux Host ({linux_ip}) ---")
        if not linux_ip:
            self._log_test_result("SKIPPED: Linux Remote IP not set.")
            return

        try:
            ipaddress.ip_address(linux_ip) # Validate
        except ValueError:
            self._log_test_result(f"FAIL: Invalid Linux IP address format: {linux_ip}")
            return

        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', '-w', '2000', linux_ip] # 1 packet, 2s timeout

        self._log_test_result(f"Executing: {' '.join(command)}")
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(timeout=5) # 5s for the whole process

            if process.returncode == 0:
                self._log_test_result(f"SUCCESS: Ping to {linux_ip} successful.")
                # self._log_test_result(f"Output:\n{stdout}") # Can be verbose
            else:
                self._log_test_result(f"FAIL: Ping to {linux_ip} failed. Return code: {process.returncode}")
                if stdout: self._log_test_result(f"Stdout:\n{stdout}")
                if stderr: self._log_test_result(f"Stderr:\n{stderr}")
        except subprocess.TimeoutExpired:
            self._log_test_result(f"FAIL: Ping command to {linux_ip} timed out.")
            if process: process.kill()
        except FileNotFoundError:
            self._log_test_result("FAIL: 'ping' command not found. Is it in your system's PATH?")
        except Exception as e:
            self._log_test_result(f"FAIL: An unexpected error occurred during ping: {e}")
        self._log_test_result("--- Test Finished ---")

    def test_linux_mem0_api(self):
        self._log_test_result(f"--- Testing Linux mem0 Service API ---")
        linux_ip = self.linux_ip_var.get()
        mem0_port = DEFAULT_MEM0_PORT # Assuming default, could be made configurable in wizard if needed
        secret = self.shared_secret_var.get()

        if not requests:
            self._log_test_result("SKIPPED: Python 'requests' module not installed.")
            return
        if not linux_ip:
            self._log_test_result("SKIPPED: Linux Remote IP not set.")
            return
        if not secret:
            self._log_test_result("SKIPPED: Shared Secret Key not set. Cannot authenticate to mem0 service.")
            return

        try:
            ipaddress.ip_address(linux_ip) # Validate Linux IP
        except ValueError:
            self._log_test_result(f"FAIL: Invalid Linux IP address format: {linux_ip}")
            return

        url = f"http://{linux_ip}:{mem0_port}/health"
        headers = {"X-Shared-Secret": secret}

        self._log_test_result(f"Attempting to connect to mem0 health endpoint: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)

            self._log_test_result(f"SUCCESS: Connected to mem0 service. Status: {response.status_code}")
            try:
                health_data = response.json()
                self._log_test_result(f"Mem0 Health Response: {health_data}")
                if health_data.get("status") == "ok":
                    self._log_test_result("Mem0 service reports OK.")
                else:
                    self._log_test_result("WARNING: Mem0 service connected but status is not 'ok'.")
            except json.JSONDecodeError:
                self._log_test_result("WARNING: Mem0 service responded, but not with valid JSON for health check.")

        except requests.exceptions.Timeout:
            self._log_test_result(f"FAIL: Connection to mem0 service at {url} timed out.")
        except requests.exceptions.ConnectionError:
            self._log_test_result(f"FAIL: Could not connect to mem0 service at {url}.")
            self._log_test_result(f"       Ensure the mem0 service is running on Linux, port {mem0_port} is open, and IP is correct.")
        except requests.exceptions.HTTPError as e:
            self._log_test_result(f"FAIL: Connected to mem0 service, but received HTTP error: {e.response.status_code} - {e.response.reason}")
            if e.response.status_code == 401:
                self._log_test_result("       Received 401 Unauthorized. Check if Shared Secret Key matches on both sides.")
            try:
                 # Try to log the error response from mem0 service if any
                error_details = e.response.json()
                self._log_test_result(f"       Error details from mem0 service: {error_details}")
            except json.JSONDecodeError:
                self._log_test_result(f"       Error response from mem0 service (not JSON): {e.response.text}")
        except Exception as e:
            self._log_test_result(f"FAIL: An unexpected error occurred while testing mem0 API: {e}")
        self._log_test_result("--- Test Finished ---")


if __name__ == '__main__':
    root = tk.Tk()
    app = ConfigWizardApp(root)
    root.mainloop()
