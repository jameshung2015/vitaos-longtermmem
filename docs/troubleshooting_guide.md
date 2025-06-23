# WeChatMemories - Troubleshooting Guide

This guide helps you diagnose and resolve common issues you might encounter while setting up or using WeChatMemories.

## General Troubleshooting Steps

1.  **Check Logs:** This is often the first and most important step.
    *   **Windows `process_chatlogs.ps1`:** Check PowerShell console output for errors during decryption.
    *   **Windows Ollama:** Look for Ollama logs (location might vary, check Ollama documentation or system tray icon options).
    *   **Linux `mem0_service`:** If run directly with Gunicorn, check terminal output. If run as a `systemd` service, use `journalctl -u mem0svc -f` (or your service name).
    *   **Linux `langchain_agent`:** Check terminal output of `agent.py`.
    *   **Linux `chatbot_backend`:** If run directly with Gunicorn, check terminal output. If run as a `systemd` service, use `journalctl -u chatbotsvc -f` (or your service name).
    *   **Linux `monitor.sh`:** Output is logged to `linux_server/monitoring/system_monitor.log`.

2.  **Verify Configuration (`linux_config.json` and `mem0_service/.env`):**
    *   Ensure `linux_config.json` (transferred from Windows to Linux) has the correct IP addresses, share paths, credentials, model names, and shared secret key.
    *   Ensure `linux_server/mem0_service/.env` on the Linux machine has the correct `SHARED_SECRET_KEY`, `OLLAMA_BASE_URL`, and `OLLAMA_EMBEDDING_MODEL` that align with `linux_config.json` and your Windows Ollama setup.

3.  **Network Connectivity:**
    *   **Ping:** Can the Windows machine ping the Linux machine and vice-versa?
    *   **Port Reachability:** Use tools like `nc` (netcat), `telnet`, or the tests in the Windows Configuration Wizard.
        *   From Windows, can it reach Linux on ports for `mem0_service` (e.g., 8000) and `chatbot_backend` (e.g., 5000)?
        *   From Linux, can it reach Windows on the Ollama port (e.g., 11434) and SMB port (445)?
    *   **Firewalls:** Double-check firewall rules on both Windows and Linux. Ensure they allow traffic from the specific IP addresses on the required ports. Temporarily disabling the firewall (for testing ONLY on a safe local network) can help isolate if it's a firewall issue. **Remember to re-enable it!**

4.  **Service Status (Linux):**
    *   If using `systemd`: `sudo systemctl status <servicename>`.
    *   Check if processes are running: `ps aux | grep gunicorn` or `ps aux | grep python`.

## Specific Issues

### Windows Side

1.  **`chatlog.exe` Fails to Decrypt or Get Keys:**
    *   **Cause:** `chatlog.exe` might need WeChat to be running and logged in, or have specific files accessible from a recent login. It may also have compatibility issues with certain WeChat versions.
    *   **Solution:**
        *   Ensure WeChat is running on Windows.
        *   Try restarting WeChat.
        *   Check the `sjzar/chatlog` GitHub page for issues related to your WeChat version or error messages.
        *   Ensure `chatlog.exe` is the correct version for your system.

2.  **Ollama Models Not Downloading or Ollama Service Not Starting:**
    *   **Cause:** Network issues, lack of disk space, incorrect Ollama installation.
    *   **Solution:**
        *   Check your internet connection.
        *   Verify available disk space.
        *   Reinstall Ollama.
        *   Check Ollama logs for specific errors.
        *   Try pulling a very small model first (e.g., `ollama pull orca-mini`) to test basic functionality.

3.  **Cannot Access Windows SMB Share from Linux:**
    *   **Cause:** Incorrect share path, incorrect permissions, firewall blocking SMB, SMB service not running on Windows, incorrect credentials in `linux_config.json`.
    *   **Solution:**
        *   Verify the share path and name carefully.
        *   Re-check share permissions and NTFS permissions on the `RawLogs` folder (refer to `windows_client/docs/smb_setup_guide.md`).
        *   Ensure "File and Printer Sharing" is allowed in Windows Firewall for your network profile (Private).
        *   Ensure the "Server" service is running on Windows (`services.msc`).
        *   Double-check username (include domain if necessary, e.g., `COMPUTERNAME\User` or `user@domain.com`) and password in `linux_config.json`.
        *   Try accessing the share from another Windows machine first to isolate if it's a general Windows share issue.

### Linux Side

1.  **Python Dependencies Installation Fails:**
    *   **Cause:** Missing system development libraries (like `python3-dev`, `gcc`), `pip` issues, network problems.
    *   **Solution:**
        *   Ensure your system is updated: `sudo apt update && sudo apt upgrade` (Debian/Ubuntu) or `sudo dnf update` (Fedora).
        *   Install common build tools: `sudo apt install python3-dev build-essential libgssapi-krb5-2` (Debian/Ubuntu) or `sudo dnf groupinstall "Development Tools"` and `sudo dnf install python3-devel krb5-devel` (Fedora). `krb5-devel` or `libgssapi-krb5-2` can sometimes be needed by SMB libraries.
        *   Ensure your virtual environment is active.
        *   Check network connectivity.

2.  **`mem0_service` or `chatbot_backend` Fails to Start:**
    *   **Cause:** Port conflict (another service using the port), errors in the Python script (`app.py`), missing/incorrect configuration in `.env` or `linux_config.json`.
    *   **Solution:**
        *   Check logs for specific Python errors.
        *   Use `netstat -tulnp | grep <port>` to see if the port is already in use.
        *   Verify all required environment variables / config values are correctly set.

3.  **Langchain Agent (`agent.py`) Cannot Connect to SMB Share:**
    *   **Cause:** Same as "Cannot Access Windows SMB Share from Linux" (see above). Also, the SMB client library used in `agent.py` (`smbclient`) might have authentication quirks.
    *   **Solution:**
        *   Focus on SMB server-side configuration first.
        *   Ensure `smbclient` (the command-line tool) works from Linux if installed.
        *   The Python `smbclient` library might require global credential setup or specific environment variables. Consider switching to `pysmbclient` or `smbprotocol` in `agent.py` if `smbclient` remains problematic, as these often offer more direct credential handling in code.
        *   Check agent logs for SMB-related error messages.

4.  **Langchain Agent or Chatbot Backend Cannot Connect to Windows Ollama:**
    *   **Cause:** Windows Firewall blocking, Ollama not listening on the correct interface or port, incorrect Ollama URL in `linux_config.json`.
    *   **Solution:**
        *   Verify Windows Firewall rule for Ollama port (e.g., 11434).
        *   Ensure `OLLAMA_HOST` is set to `0.0.0.0` on Windows if Ollama doesn't listen on all interfaces by default.
        *   Use `curl http://<WINDOWS_IP>:11434/api/tags` from the Linux terminal to test basic connectivity and API response.

5.  **`mem0_service` Reports "Unauthorized" (401 Error):**
    *   **Cause:** The `X-Shared-Secret` header sent by the client (Langchain Agent or Chatbot Backend) does not match the `SHARED_SECRET_KEY` in the `mem0_service/.env` file.
    *   **Solution:** Ensure the shared secret key is identical in `linux_config.json` (used by clients) and `mem0_service/.env`.

6.  **Chatbot Returns Errors or "Cannot connect to LLM/mem0":**
    *   **Cause:** Underlying services (`mem0_service`, Windows Ollama) are down or unreachable. Configuration errors.
    *   **Solution:** Check the status and logs of `mem0_service` and Windows Ollama. Verify network connectivity and configuration as per other troubleshooting steps.

### Chatbot Specific

1.  **No Relevant Context Found / Answers are Generic:**
    *   **Cause:** Data might not be ingested into `mem0` correctly. The `chat_context_id` selected in the UI might not match the `user_id`s used during `mem0` ingestion. The search query might be too vague. Embedding model issues.
    *   **Solution:**
        *   Verify Langchain agent successfully processed and added data to `mem0`. Check `mem0_service` logs for add operations.
        *   Ensure the `chat_context_id` logic is working. (Future enhancement: populate the dropdown dynamically from `mem0` `user_id`s).
        *   Try more specific queries.
        *   Ensure the `OLLAMA_EMBEDDING_MODEL` configured for `mem0_service` in its `.env` is correct and working on the Windows Ollama instance.

2.  **Chatbot UI Issues (e.g., messages not appearing, buttons not working):**
    *   **Cause:** JavaScript errors in the browser.
    *   **Solution:** Open your browser's developer console (usually F12) and check for JavaScript errors on the "Console" tab.

This guide is not exhaustive. If you encounter an issue not listed here, carefully check all relevant logs and configurations.
```

With the User Installation Guide, User Manual, and Troubleshooting Guide created, the documentation aspect of this step is largely covered.

The other items (Error Handling, UX, Performance, Security) are principles that have been incorporated to a baseline degree during development or documented. Further enhancements in these areas would typically occur during a testing and refinement phase.

For example, a review of logging:
*   `windows_client/config_wizard/config_wizard_app.py`: Uses `messagebox` for user feedback; logging to a file is not implemented but could be added. Test results are logged to its UI.
*   `windows_client/data_processing/process_chatlogs.ps1`: Uses `Write-Host`, `Write-Warning`, `Write-Error`. Could be enhanced to log to a file.
*   `linux_server/mem0_service/app.py`: Uses Python's `logging` module. Configured with a basic format.
*   `linux_server/langchain_agent/agent.py`: Uses Python's `logging` module. Configured with a basic format.
*   `linux_server/chatbot_backend/app.py`: Uses Python's `logging` module. Configured with a basic format.

The current logging is generally sufficient for diagnosing issues as per the troubleshooting guide. Standardization of log formats or centralized logging are more advanced features.

I will now mark this plan step as complete.
