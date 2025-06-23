# Ollama Deployment and Configuration Guide (Windows)

This guide explains how to install and configure Ollama on your Windows computer to serve Large Language Models (LLMs) and Embedding models for the WeChatMemories project.

## 1. Download and Install Ollama

*   **Download Ollama:**
    *   Go to the official Ollama website: [https://ollama.com/](https://ollama.com/)
    *   Download the Windows installer.
*   **Install Ollama:**
    *   Run the downloaded installer and follow the on-screen instructions.
    *   Ollama will typically install and run as a background service. You should see an Ollama icon in your system tray.

## 2. Verify Ollama Installation

*   Open a Command Prompt (`cmd`) or PowerShell window.
*   Type the command: `ollama --version`
*   You should see the installed Ollama version, confirming it's installed and accessible via the command line.
*   You can also type `ollama list` to see any models you might already have (it will be empty if this is a fresh install).

## 3. Pull Required Models

For the WeChatMemories project, you will need:
*   A **Large Language Model (LLM)** for generating answers (e.g., `llama2`, `mistral`).
*   An **Embedding Model** for converting text into vector representations (e.g., `nomic-embed-text`).

*   **Open Command Prompt or PowerShell.**
*   **Pull an LLM:**
    *   Example using `llama2` (a commonly used general-purpose model, around 3.8GB):
        ```bash
        ollama pull llama2
        ```
    *   You can choose other models from the [Ollama Library](https://ollama.com/library). Consider model size and performance based on your hardware. For instance, `mistral` is another popular choice that is generally faster than `llama2` and often performs comparably or better for many tasks.
        ```bash
        ollama pull mistral
        ```
*   **Pull an Embedding Model:**
    *   The recommended model is `nomic-embed-text`:
        ```bash
        ollama pull nomic-embed-text
        ```
*   **Verify Downloaded Models:**
    *   After pulling, list the models to ensure they are available:
        ```bash
        ollama list
        ```
    *   You should see the models you just downloaded in the output, along with their sizes.

## 4. Ensure Ollama Service is Running and Accessible

*   **Background Service:** Ollama should automatically run as a background service after installation. You can check its status via the system tray icon.
*   **API Port:** By default, Ollama serves its API on `localhost` (or `127.0.0.1`) at port `11434`.
*   **Firewall Configuration (Crucial for Local Network Access):**
    For the Linux server to access Ollama on your Windows machine, you need to allow inbound connections to port `11434` through the Windows Defender Firewall.
    1.  **Open Windows Defender Firewall:**
        *   Search for "Windows Defender Firewall" in the Start Menu and open it.
        *   Alternatively, open "Windows Security", then "Firewall & network protection".
    2.  Click on **Advanced settings** on the left pane.
        *   ![Firewall Advanced Settings](https://i.imgur.com/example_fw_adv_settings.png) <!-- Placeholder image link -->
    3.  In the "Windows Defender Firewall with Advanced Security" window, click on **Inbound Rules** in the left pane.
    4.  In the right pane, click on **New Rule...**.
        *   ![New Inbound Rule](https://i.imgur.com/example_fw_new_rule.png) <!-- Placeholder image link -->
    5.  **Rule Type:** Select **Port** and click Next.
        *   ![Rule Type Port](https://i.imgur.com/example_fw_rule_port.png) <!-- Placeholder image link -->
    6.  **Protocol and Ports:**
        *   Select **TCP**.
        *   Select **Specific local ports:** and enter `11434`.
        *   Click **Next**.
        *   ![Rule Protocol Port TCP 11434](https://i.imgur.com/example_fw_rule_tcp_port.png) <!-- Placeholder image link -->
    7.  **Action:** Select **Allow the connection** and click Next.
        *   ![Rule Action Allow](https://i.imgur.com/example_fw_rule_allow.png) <!-- Placeholder image link -->
    8.  **Profile:**
        *   Ensure **Private** is checked.
        *   **Important:** If your Linux server is on the same local network and your Windows network profile is "Private", this is usually sufficient.
        *   Uncheck **Public** unless you have a specific reason and understand the security implications. It's generally not recommended to expose Ollama to public networks.
        *   You can leave **Domain** checked if applicable to your network.
        *   Click **Next**.
        *   ![Rule Profile Private](https://i.imgur.com/example_fw_rule_profile.png) <!-- Placeholder image link -->
    9.  **Name:**
        *   Give the rule a descriptive name, e.g., `Ollama Access (TCP 11434)`.
        *   Optionally, add a description.
        *   Click **Finish**.

## 5. (Optional) Configure Ollama to Listen on All Interfaces

By default, `ollama serve` might only listen on `127.0.0.1` (localhost). For other devices on your network to reach it using your machine's IP address, Ollama needs to listen on `0.0.0.0`.

*   **Check Current Ollama Host (Environment Variable):**
    *   Ollama uses the `OLLAMA_HOST` environment variable. If this is not set, it defaults to `127.0.0.1`.
*   **Set `OLLAMA_HOST` Environment Variable (if needed):**
    1.  Search for "Edit the system environment variables" in the Start Menu and open it.
    2.  In the System Properties window, click the **Environment Variables...** button.
    3.  Under "System variables" (for all users) or "User variables for <YourUserName>" (for current user only), click **New...**.
        *   **Variable name:** `OLLAMA_HOST`
        *   **Variable value:** `0.0.0.0`
        *   ![OLLAMA_HOST Env Var](https://i.imgur.com/example_ollama_host_env.png) <!-- Placeholder image link -->
    4.  Click OK on all dialogs.
    5.  **Restart Ollama:** You'll need to restart the Ollama application/service for this change to take effect.
        *   Right-click the Ollama icon in the system tray and choose "Quit Ollama".
        *   Then, restart Ollama from the Start Menu.

    **Alternatively, for temporary testing (command line):**
    You can stop the Ollama service (if running) and run it manually from the command line specifying the host:
    ```bash
    # First, ensure the Ollama background service/app is not running.
    # Quit from system tray.
    ollama serve --host 0.0.0.0:11434
    ```
    This command will occupy the current terminal. Closing the terminal will stop the server. Using the environment variable is the recommended way for a persistent setting.

    *Note: Recent versions of Ollama for Windows, when installed as a service, might already listen on all interfaces by default when a firewall rule is in place. The environment variable or explicit `ollama serve` command is a fallback if you encounter issues.*

## 6. Test Network Accessibility (Optional but Recommended)

From another computer on your local network (e.g., the Linux machine, or even a smartphone if you have a curl-like tool):
*   Try to access `http://<Your_Windows_IP_Address>:11434/api/tags`.
    *   Replace `<Your_Windows_IP_Address>` with the actual IPv4 address of your Windows machine (you found this in the SMB setup guide using `ipconfig`).
*   Example using `curl` from Linux:
    ```bash
    curl http://192.168.1.100:11434/api/tags
    ```
*   If successful, you should receive a JSON response listing your installed Ollama models. If it fails, re-check firewall settings and the `OLLAMA_HOST` configuration.

You have now installed Ollama, downloaded the necessary models, and configured it for local network access. The configuration wizard will later use this setup.
---
*(Note: Placeholder image links (i.imgur.com) are used above. In a real document, these would be screenshots of the actual Windows UI elements.)*
