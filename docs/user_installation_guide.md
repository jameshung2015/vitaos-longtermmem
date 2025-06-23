# WeChatMemories - User Installation Guide

Welcome to WeChatMemories! This guide will walk you through setting up the entire system, which allows you to create a searchable, personal AI assistant for your WeChat chat history, all running locally on your own machines.

**System Overview:**
*   **Windows Machine (Client):** Handles WeChat log decryption, runs the Ollama LLM/Embedding service, and provides a configuration wizard.
*   **Linux Machine (Server):** Hosts the `mem0` vector store service, a Langchain agent for data processing, and the web-based Chatbot interface.

## Prerequisites

**General:**
*   Two machines (one Windows, one Linux) on the same local network.
*   Basic familiarity with command-line interfaces (CLI) on both Windows (PowerShell/CMD) and Linux (bash).
*   Administrative privileges on both machines for software installation and firewall configuration.
*   Sufficient disk space for WeChat logs, Ollama models, and vector stores.
*   Python 3.8+ on both machines (for some components on Windows, and for all server components on Linux).

**Windows Specific:**
*   Your WeChat desktop application data.
*   `chatlog.exe` (from `sjzar/chatlog` project - you'll download this).
*   Ollama for Windows (you'll download this).

**Linux Specific:**
*   Python 3.8+ and `pip`.
*   `git` (if cloning the project repository).
*   Firewall management tool (`ufw` or `firewalld`).
*   `sysstat` package (optional, for full `monitor.sh` disk I/O stats).
*   `nc` (netcat) and `curl` (for diagnostics, usually pre-installed).

## Installation Steps

The setup process involves configuring both your Windows and Linux machines. It's recommended to follow the steps in order.

### Part 1: Windows Machine Setup

1.  **Prepare Project Files (Windows):**
    *   If you have the complete WeChatMemories project folder, place it in a convenient location on your Windows machine (e.g., `C:\Projects\WeChatMemories`).
    *   If you only have the scripts, ensure they are organized as per the project structure.

2.  **Install `chatlog.exe` (WeChat Log Decryption Tool):**
    *   Go to the `sjzar/chatlog` GitHub releases page: [https://github.com/sjzar/chatlog/releases](https://github.com/sjzar/chatlog/releases)
    *   Download the latest Windows executable (e.g., `chatlog_x.x.x_windows_amd64.exe`).
    *   Rename it to `chatlog.exe`.
    *   Place `chatlog.exe` into the `windows_client/data_processing/` directory within your project structure, or ensure it's in your system's PATH. The `process_chatlogs.ps1` script expects to find it.

3.  **Install and Configure Ollama (LLM & Embedding Service):**
    *   Follow the detailed instructions in: `windows_client/docs/ollama_setup_guide.md`
    *   **Key steps include:**
        *   Downloading and installing Ollama for Windows.
        *   Pulling required models using the Ollama CLI (e.g., `ollama pull llama2`, `ollama pull nomic-embed-text`).
        *   Configuring Windows Defender Firewall to allow inbound connections to Ollama's port (default `11434/TCP`) from your Linux machine's IP.
        *   (Optional but recommended) Configuring Ollama to listen on all network interfaces (`OLLAMA_HOST=0.0.0.0`) if it doesn't by default.

4.  **Configure Windows Network Share (SMB) for Raw Chat Logs:**
    *   The decrypted chat logs need to be accessible by the Linux server.
    *   Follow the detailed instructions in: `windows_client/docs/smb_setup_guide.md`
    *   **Key steps include:**
        *   Creating the target directory if it doesn't exist: `C:\Users\<YourUserName>\Documents\WeChatMemories\RawLogs`.
        *   Sharing this `RawLogs` folder with appropriate permissions (read-only for a specific user account that the Linux machine will use).

### Part 2: Linux Machine Setup

1.  **Prepare Project Files (Linux):**
    *   Transfer or clone the WeChatMemories project repository to your Linux machine (e.g., `/home/your_user/WeChatMemories`).

2.  **Set up Python Environment:**
    *   It's highly recommended to use a Python virtual environment.
    *   Navigate to the `linux_server` directory of the project.
        ```bash
        cd /path/to/WeChatMemories/linux_server
        python3 -m venv .venv
        source .venv/bin/activate
        pip install --upgrade pip
        ```

3.  **Install Dependencies for Linux Services:**
    *   **Mem0 Service:**
        ```bash
        # Assuming you are in linux_server directory and venv is active
        pip install -r mem0_service/requirements.txt
        ```
    *   **Langchain Agent:**
        ```bash
        pip install -r langchain_agent/requirements.txt
        ```
    *   **Chatbot Backend:**
        ```bash
        pip install -r chatbot_backend/requirements.txt
        ```
    *   *(Note: If you encounter issues, you might need to install system build dependencies for some Python packages, e.g., `python3-dev`, `build-essential`)*

4.  **Configure Linux Firewall:**
    *   Allow incoming connections to the ports used by the `mem0_service` (default: `8000/TCP`) and the `chatbot_backend` (default: `5000/TCP`) from your Windows machine's IP.
    *   Follow the detailed instructions in: `linux_server/docs/firewall_setup_guide.md` (covers `ufw` and `firewalld`).

### Part 3: Configuration Using the Windows Wizard

1.  **Run the Windows Configuration Wizard:**
    *   On your Windows machine, navigate to the `windows_client/config_wizard/` directory.
    *   Ensure you have Python installed and necessary libraries (like `requests`, `tkinter` is usually built-in). If `requests` is missing: `pip install requests`.
    *   Run the wizard: `python config_wizard_app.py`
    *   The wizard will guide you through:
        *   Confirming your Windows IP.
        *   Entering your Linux machine's IP address.
        *   Specifying the path to your shared `RawLogs` folder on Windows and the credentials for SMB access.
        *   Selecting the Ollama LLM and Embedding models you downloaded.
        *   Generating/confirming a Shared Secret Key (used for `mem0_service` authentication).
    *   **Save the Configuration:** The wizard will prompt you to save a `linux_config.json` file. Save this file.

2.  **Transfer `linux_config.json` to Linux:**
    *   Securely transfer the generated `linux_config.json` file from your Windows machine to your Linux machine.
    *   Place it in one of the following locations on the Linux server so the services can find it:
        *   `linux_server/linux_config.json` (recommended general location)
        *   Or, inside specific service directories like `linux_server/langchain_agent/` or `linux_server/chatbot_backend/` if you prefer.
        *   Alternatively, set the `WECHATMEMORIES_CONFIG` environment variable on Linux to the full path of this file.

3.  **Configure `mem0_service` Environment:**
    *   On your Linux machine, navigate to `linux_server/mem0_service/`.
    *   Create or edit the `.env` file (`linux_server/mem0_service/.env`).
    *   Ensure the following values in `.env` match those from your `linux_config.json` or your setup:
        *   `SHARED_SECRET_KEY`: Must match the one in `linux_config.json`.
        *   `MEM0_STORAGE_PATH`: Define where `mem0` will store its data (e.g., `./mem0_data`).
        *   `OLLAMA_BASE_URL`: The URL of your Windows Ollama service (e.g., `http://<WINDOWS_IP>:11434`).
        *   `OLLAMA_EMBEDDING_MODEL`: The name of the embedding model in your Windows Ollama (e.g., `nomic-embed-text:latest`).
    *   A template is provided at `linux_server/mem0_service/.env`.

### Part 4: Starting Services on Linux

Ensure your Python virtual environment is active (`source /path/to/WeChatMemories/linux_server/.venv/bin/activate`).

1.  **Start the Mem0 Service:**
    *   Navigate to `linux_server/mem0_service/`.
    *   Run using Gunicorn (recommended for stability):
        ```bash
        gunicorn --workers 2 --bind 0.0.0.0:8000 app:app
        ```
        (Adjust port `8000` if changed in `linux_config.json` and firewall rules).
    *   For persistent operation, set it up as a `systemd` service as described in `linux_server/docs/mem0_setup_guide.md`.

2.  **Start the Chatbot Backend Service:**
    *   Navigate to `linux_server/chatbot_backend/`.
    *   Run using Gunicorn:
        ```bash
        gunicorn --workers 2 --bind 0.0.0.0:5000 app:app
        ```
        (Adjust port `5000` if you plan to use a different one and update firewall rules).
    *   This can also be set up as a `systemd` service.

3.  **Run the Langchain Agent (Initial Data Ingestion):**
    *   Navigate to `linux_server/langchain_agent/`.
    *   Run the agent script:
        ```bash
        python agent.py
        ```
    *   This script will connect to the Windows share, process chat log files, and store them in the `mem0_service`. It's currently designed for a single pass. For continuous monitoring, the script would need to be adapted or run periodically (e.g., via cron).

### Part 5: Initial Data Processing on Windows

1.  **Run the WeChat Log Decryption Script:**
    *   On your Windows machine, open PowerShell.
    *   Navigate to the `windows_client/data_processing/` directory.
    *   Run the script:
        ```powershell
        .\process_chatlogs.ps1
        ```
    *   This script will attempt to find your WeChat data, use `chatlog.exe` to decrypt it, and store the plain text logs in the `RawLogs` folder you shared earlier.
    *   *(Note: `chatlog.exe` might require WeChat to be running or have had a successful login to obtain decryption keys. Refer to `sjzar/chatlog` documentation for specifics if you encounter issues with key acquisition.)*

## Next Steps

Once all services are running and initial data is processed:
*   The Langchain agent on Linux should start picking up files from the Windows `RawLogs` share and ingesting them into the `mem0` service. You can monitor its logs.
*   You can access the Chatbot UI by opening a web browser and navigating to `http://<LINUX_IP>:5000` (or the configured chatbot port).

Refer to the **User Manual** (`docs/user_manual.md`) for instructions on using the chatbot and monitoring.
Refer to the **Troubleshooting Guide** (`docs/troubleshooting_guide.md`) if you encounter issues.
```
