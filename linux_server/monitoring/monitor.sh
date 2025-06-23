#!/bin/bash

# monitor.sh
# Basic system and service monitoring script for WeChatMemories Linux server.

LOG_FILE="system_monitor.log"
CONFIG_FILE_PATH="${WECHATMEMORIES_CONFIG:-../linux_config.json}" # Default relative to linux_server/ if not set

# --- Configuration (Attempt to load from JSON config) ---
MEM0_PORT="8000" # Default
CHATBOT_PORT="5000" # Default
WINDOWS_OLLAMA_URL="" # To be loaded from config

# Function to safely parse JSON with grep and sed (basic)
# More robust parsing would use `jq`
get_json_value() {
    local json_file="$1"
    local key="$2"
    # Basic parser: handles simple key: "value" patterns
    # Might fail with complex JSON structures, escaping, etc.
    grep -oP "\"${key}\":\s*\"?\K[^\",]+" "$json_file" | head -n 1
}

if [ -f "$CONFIG_FILE_PATH" ]; then
    echo "INFO: Loading configuration from $CONFIG_FILE_PATH"
    MEM0_PORT_FROM_CONFIG=$(get_json_value "$CONFIG_FILE_PATH" "mem0_port")
    # Assuming chatbot port is not in linux_config.json, but could be added.
    # For now, CHATBOT_PORT remains default or can be passed as env var.

    OLLAMA_BASE_URL_FROM_CONFIG=$(get_json_value "$CONFIG_FILE_PATH" "ollama_base_url")

    if [ -n "$MEM0_PORT_FROM_CONFIG" ]; then
        MEM0_PORT="$MEM0_PORT_FROM_CONFIG"
    fi
    if [ -n "$OLLAMA_BASE_URL_FROM_CONFIG" ]; then
        WINDOWS_OLLAMA_URL="$OLLAMA_BASE_URL_FROM_CONFIG"
    else
        # If ollama_base_url is not in config, try to get windows_ip and construct it
        WINDOWS_IP_FROM_CONFIG=$(get_json_value "$CONFIG_FILE_PATH" "windows_ip")
        if [ -n "$WINDOWS_IP_FROM_CONFIG" ]; then
            WINDOWS_OLLAMA_URL="http://${WINDOWS_IP_FROM_CONFIG}:11434" # Default Ollama port
        fi
    fi
    echo "INFO: Mem0 Port: $MEM0_PORT"
    echo "INFO: Chatbot Port (default): $CHATBOT_PORT" # Assuming fixed or env var for chatbot's own port
    echo "INFO: Windows Ollama URL: $WINDOWS_OLLAMA_URL"
else
    echo "WARNING: Configuration file $CONFIG_FILE_PATH not found. Using default ports and no Ollama URL."
fi


# --- Logging Function ---
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# --- Start Monitoring ---
log_message "===== Starting System Monitor Run ====="

# 1. System Performance Metrics
log_message "--- System Performance ---"
log_message "CPU Usage (top 5 processes):"
top -b -n 1 | head -n 12 | tail -n 6 >> "$LOG_FILE"
log_message "Memory Usage (free -h):"
free -h >> "$LOG_FILE"
log_message "Disk I/O (iostat -xz 1 2, brief):" # Needs sysstat package
if command -v iostat &> /dev/null; then
    iostat -xz 1 2 | grep -vE '^$' | grep -A 1000 -e '^avg-cpu:' -e '^Device:' >> "$LOG_FILE" || log_message "iostat data collection had issues."
else
    log_message "iostat command not found. Skipping disk I/O stats. (Install sysstat package)"
fi
log_message "Disk Usage (df -h /):" # Root filesystem, adjust if data is elsewhere
df -h / >> "$LOG_FILE"
log_message "Network Stats (ss -s):"
if command -v ss &> /dev/null; then
    ss -s >> "$LOG_FILE"
else
    netstat -s >> "$LOG_FILE" # Fallback for older systems
fi
log_message "--------------------------"

# 2. Check Service Port Listening Status
log_message "--- Service Port Status ---"
# Check mem0 service port
if netstat -tulnp | grep -q ":${MEM0_PORT}.*LISTEN"; then
    log_message "Mem0 Service (Port $MEM0_PORT): Listening"
else
    log_message "Mem0 Service (Port $MEM0_PORT): NOT LISTENING"
fi

# Check Chatbot service port (assuming it runs on this Linux server)
if netstat -tulnp | grep -q ":${CHATBOT_PORT}.*LISTEN"; then
    log_message "Chatbot Service (Port $CHATBOT_PORT): Listening"
else
    log_message "Chatbot Service (Port $CHATBOT_PORT): NOT LISTENING"
fi
log_message "---------------------------"

# 3. Check Connection to Windows Ollama Service
log_message "--- Windows Ollama Connectivity ---"
if [ -n "$WINDOWS_OLLAMA_URL" ]; then
    # Basic check - can we connect to the port?
    # Extract host and port from URL (e.g., http://192.168.1.101:11434)
    OLLAMA_HOST=$(echo "$WINDOWS_OLLAMA_URL" | sed -E 's_^[a-zA-Z]+://([^:/]+).*_\1_')
    OLLAMA_PORT=$(echo "$WINDOWS_OLLAMA_URL" | sed -E 's_^[a-zA-Z]+://[^:/]+:?([0-9]*).*_\1_')
    if [ -z "$OLLAMA_PORT" ]; then # Default HTTP/HTTPS ports if not specified
        if [[ "$WINDOWS_OLLAMA_URL" == http://* ]]; then OLLAMA_PORT="80";
        elif [[ "$WINDOWS_OLLAMA_URL" == https://* ]]; then OLLAMA_PORT="443";
        else OLLAMA_PORT="11434"; # Default if scheme missing and no port
        fi
    fi


    if nc -z -w5 "$OLLAMA_HOST" "$OLLAMA_PORT"; then # 5 second timeout
        log_message "Windows Ollama ($OLLAMA_HOST:$OLLAMA_PORT): Connection successful (port reachable)"
        # Optional: Deeper check with curl if jq is available for nice output
        if command -v curl &> /dev/null; then
            API_TAGS_URL="${WINDOWS_OLLAMA_URL%/}/api/tags" # Ensure no double slash
            log_message "Attempting to query Ollama API tags at $API_TAGS_URL..."
            if curl --silent --fail --connect-timeout 5 -X GET "$API_TAGS_URL" > /dev/null; then
                 log_message "Windows Ollama API (/api/tags): Responsive"
                 # curl_output=$(curl --silent --connect-timeout 5 -X GET "$API_TAGS_URL")
                 # if command -v jq &> /dev/null; then
                 #    echo "$curl_output" | jq . >> "$LOG_FILE"
                 # else
                 #    echo "$curl_output" >> "$LOG_FILE"
                 # fi
            else
                 log_message "Windows Ollama API (/api/tags): NOT RESPONSIVE or error during curl"
            fi
        else
            log_message "curl command not found. Skipping API deep check."
        fi
    else
        log_message "Windows Ollama ($OLLAMA_HOST:$OLLAMA_PORT): Connection FAILED (port not reachable)"
    fi
else
    log_message "Windows Ollama URL not configured. Skipping connectivity test."
fi
log_message "-------------------------------"

log_message "===== System Monitor Run Finished ====="
echo "Monitoring data logged to $LOG_FILE"

# Potential enhancements:
# - Use `jq` for robust JSON parsing if available.
# - Check status of systemd services for mem0 and chatbot.
# - More detailed network error diagnostics.
# - Rotate log file.
# - Send alerts on failures (e.g., via email or a messaging service if configured).
```

This script:
*   Defines a log file.
*   Attempts to load `mem0_port` and `ollama_base_url` from the `linux_config.json` (with a very basic JSON parsing method; `jq` would be more robust).
*   Logs CPU usage (top processes), memory usage, basic disk I/O (if `iostat` is available), disk usage, and network summary.
*   Checks if `mem0_service` and `chatbot_service` ports are listening.
*   Attempts to connect to the Windows Ollama service port and optionally queries its `/api/tags` endpoint.
*   Writes all output to `system_monitor.log`.

The user will need to make it executable (`chmod +x monitor.sh`) and can run it manually or via cron.

Finally, the **Linux Firewall Configuration Guide (`linux_server/docs/firewall_setup_guide.md`)**.
This was planned to be in `docs/firewall_setup_guide_linux.md` at the root `docs` level, but the plan step says `linux_server/docs/firewall_setup_guide.md`. I will stick to the plan step's location. If this is a duplication, we can consolidate later.
Given I already created `docs/firewall_setup_guide_linux.md`, I will create this one specific to the `linux_server` context, perhaps focusing more on the ports used by services within `linux_server`.
