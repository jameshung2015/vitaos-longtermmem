# WeChatMemories - User Manual

This manual provides instructions on how to use the WeChatMemories system after it has been successfully installed and configured as per the `user_installation_guide.md`.

## 1. Processing WeChat Chat Logs

The first step to using WeChatMemories is to decrypt your WeChat chat logs and make them available for the system.

**On your Windows Machine:**

1.  **Ensure WeChat is Running (if required by `chatlog.exe`):**
    *   The `chatlog.exe` tool might need WeChat to be running or at least have had a recent successful login to access necessary decryption keys. If decryption fails, try ensuring WeChat is running and logged in.

2.  **Run the Decryption Script:**
    *   Open PowerShell.
    *   Navigate to the `windows_client/data_processing/` directory within your project folder.
    *   Execute the script:
        ```powershell
        .\process_chatlogs.ps1
        ```
    *   **Output:** This script will:
        *   Attempt to locate your WeChat data.
        *   Use `chatlog.exe` to decrypt the chat messages.
        *   Store the decrypted plain text logs in the `C:\Users\<YourUserName>\Documents\WeChatMemories\RawLogs` directory (or the path you configured). This is the folder shared via SMB with your Linux server.
    *   **Frequency:** You'll need to re-run this script whenever you want to process new WeChat messages that have arrived since the last run. The script and the subsequent Langchain agent processing are designed for incremental updates (processing only new or changed files).

## 2. Data Ingestion into `mem0` (Linux Server)

Once new decrypted logs are available in the Windows shared folder, the Langchain Agent on the Linux server will process them.

1.  **Ensure Linux Services are Running:**
    *   **Mem0 Service:** Should be running (e.g., via Gunicorn or systemd).
    *   **Langchain Agent:**
        *   If you set up the Langchain Agent to run periodically (e.g., via cron or a modified script with a loop), it will automatically pick up new files.
        *   If the `agent.py` script is set for a single pass (as in the initial project version), you'll need to run it manually after the Windows `process_chatlogs.ps1` script has completed:
            ```bash
            # On Linux, in the project's linux_server/langchain_agent/ directory
            # (ensure virtual environment is active)
            python agent.py
            ```

2.  **Monitoring Ingestion:**
    *   **Langchain Agent Logs:** Check the console output or log file of the `agent.py` script. It will log which files it's processing and any errors.
    *   **Mem0 Service Logs:** Check the console output or log file of the `mem0_service` (e.g., Gunicorn logs or systemd journal). It will log requests for adding data.
    *   **System Monitoring Script:** You can run the `linux_server/monitoring/monitor.sh` script to get an overview of system performance and service status. Its output is logged to `linux_server/monitoring/system_monitor.log`.

## 3. Using the Chatbot

Once data has been ingested into `mem0`, you can ask questions about your WeChat history using the web chatbot.

1.  **Access the Chatbot:**
    *   Open a web browser on any device on your local network (including your Windows or Linux machine).
    *   Navigate to `http://<LINUX_SERVER_IP>:<CHATBOT_PORT>`.
        *   Replace `<LINUX_SERVER_IP>` with the actual IP address of your Linux server.
        *   Replace `<CHATBOT_PORT>` with the port the chatbot backend is running on (default is `5000`).
        *   Example: `http://192.168.1.102:5000`

2.  **Interacting with the Chatbot:**
    *   **Chat Interface:** You'll see a chat interface with an input box.
    *   **Selecting Chat Context (Optional but Recommended for Specificity):**
        *   Use the dropdown menu (if populated, or if you know the `user_id`s used by `mem0`) to select a specific chat context (e.g., a particular friend or group chat). This helps the chatbot focus its search on relevant conversations.
        *   The `user_id`s in `mem0` typically correspond to the filenames of your chat logs (e.g., contact names or group names, without the `.txt` extension).
        *   If you don't select a context, the chatbot might try a general search or answer without specific chat log context.
    *   **Asking Questions:** Type your question into the input box and press Enter or click "Send."
    *   **Receiving Answers:** The chatbot will:
        1.  Search the `mem0` vector store for relevant information based on your query and selected context.
        2.  Use the retrieved information and your question to query the Ollama LLM (running on your Windows machine).
        3.  Display the LLM's answer.
    *   **Loading Indicator:** A loading indicator will appear while the chatbot is processing your request.

3.  **Example Questions:**
    *   If `chat_context_id` for "John Doe" is selected: "What did we discuss about the project last week?"
    *   If `chat_context_id` for "Family Group" is selected: "When are we planning the next family gathering?"
    *   General query (no context selected, or if a global search is effective): "Summarize my recent important conversations." (Effectiveness depends on how mem0 is searched without specific user_id).

## 4. Stopping Services

*   **Linux Services (`mem0_service`, `chatbot_backend`):**
    *   If running via Gunicorn directly in a terminal: Press `Ctrl+C` in the respective terminals.
    *   If running as `systemd` services:
        ```bash
        sudo systemctl stop mem0svc  # Or your service name for mem0
        sudo systemctl stop chatbotsvc # Or your service name for chatbot
        ```
*   **Windows Ollama Service:**
    *   Usually runs as a background task. You can quit it from the Ollama icon in the system tray.
*   **Windows `process_chatlogs.ps1` and Linux `agent.py`:** These are scripts that run and then exit (unless modified for continuous operation).

## 5. Updating with New Chat Data

1.  Re-run the `process_chatlogs.ps1` script on Windows (Section 1).
2.  Re-run or ensure the `agent.py` script on Linux processes the new files (Section 2).
3.  The chatbot will then have access to the updated information.

This manual provides the basics for operating WeChatMemories. For troubleshooting, please refer to `docs/troubleshooting_guide.md`.
```
