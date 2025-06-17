#!/bin/bash
# backend/scripts/service_manager.sh

ACTION=$1
SERVICE=$2

# Determine script's own directory to reliably find other scripts/files
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_ROOT_DIR=$(dirname "$SCRIPT_DIR") # Assumes scripts is one level down from project root (e.g. backend/)
                                          # If scripts is in backend/scripts, then PROJECT_ROOT_DIR is backend/
                                          # Let's adjust to assume PROJECT_ROOT_DIR is parent of backend/
PROJECT_ROOT_DIR=$(dirname "$PROJECT_ROOT_DIR") # Now it's parent of backend/ (e.g. /path/to/project)


start_ollama() {
    echo "🚀 启动Ollama服务..."
    if ! command -v systemctl &> /dev/null; then
        echo "systemctl not found. Assuming Ollama runs some other way or is already managed."
        echo "If Ollama is a docker container, you might use 'docker start ollama_container_name'."
        # ollama serve & # This is an alternative if systemctl is not available
        # For this script, we'll assume user handles Ollama start if systemctl is not present.
    else
        sudo systemctl start ollama # Added sudo as systemctl usually requires it
    fi
    sleep 5 # Keep sleep for service to initialize

    # 检查模型是否加载
    # This check relies on 'ollama list' output format.
    if ollama list | grep -q "nomic-embed-text"; then
        echo "✅ Model 'nomic-embed-text' is available."
    else
        echo "📥 Model 'nomic-embed-text' not found. Attempting to pull..."
        ollama pull nomic-embed-text
        if ollama list | grep -q "nomic-embed-text"; then
            echo "✅ Model 'nomic-embed-text' pulled successfully."
        else
            echo "⚠️ Failed to pull 'nomic-embed-text'. Please ensure Ollama is running and can connect to the internet."
        fi
    fi

    echo "✅ Ollama服务启动/检查完成"
}

stop_ollama() {
    echo "⏹️ 停止Ollama服务..."
    if ! command -v systemctl &> /dev/null; then
        echo "systemctl not found. Assuming Ollama stops some other way or is managed elsewhere."
        # pkill -f "ollama serve" # Alternative if started with 'ollama serve'
    else
        sudo systemctl stop ollama # Added sudo
    fi
    echo "✅ Ollama服务已停止 (attempted)"
}

start_backend() {
    echo "🚀 启动后端服务..."
    # Adjust path to main.py and venv if necessary.
    # Assuming this script is in backend/scripts/ and main.py is in backend/code/
    # and .venv is in backend/
    BACKEND_DIR="$PROJECT_ROOT_DIR/backend"
    echo "Changing to backend directory: $BACKEND_DIR"
    cd "$BACKEND_DIR" || { echo "Failed to cd to $BACKEND_DIR"; exit 1; }

    if [ -f ".venv/bin/activate" ]; then
        echo "Activating Python virtual environment..."
        source .venv/bin/activate
    else
        echo "⚠️ Python virtual environment .venv/bin/activate not found in $BACKEND_DIR."
        echo "    Please ensure it's created and named .venv"
    fi

    # Check if main.py exists
    if [ ! -f "code/main.py" ]; then
        echo "❌ Error: backend/code/main.py not found."
        echo "    Cannot start backend service."
        # Deactivate venv if it was activated
        if type deactivate &>/dev/null; then deactivate; fi
        cd "$SCRIPT_DIR" # Go back to original script dir
        return 1
    fi

    echo "Starting Python backend application: python code/main.py"
    nohup python code/main.py > backend.log 2>&1 &
    echo $! > .backend.pid
    echo "✅ 后端服务启动完成. PID: $(cat .backend.pid). Log: backend.log"

    # Deactivate venv if it was activated
    if type deactivate &>/dev/null; then deactivate; fi
    cd "$SCRIPT_DIR" # Go back to original script dir
}

stop_backend() {
    echo "⏹️ 停止后端服务..."
    BACKEND_DIR="$PROJECT_ROOT_DIR/backend"
    if [ -f "$BACKEND_DIR/.backend.pid" ]; then
        PID_TO_KILL=$(cat "$BACKEND_DIR/.backend.pid")
        echo "Killing process with PID: $PID_TO_KILL"
        if kill "$PID_TO_KILL"; then
            echo "Process $PID_TO_KILL killed."
        else
            echo "⚠️ Failed to kill process $PID_TO_KILL. It might have already stopped."
        fi
        rm "$BACKEND_DIR/.backend.pid"
    else
        echo "⚠️ Backend PID file ($BACKEND_DIR/.backend.pid) not found. Service might not be running or was not started by this script."
    fi
    echo "✅ 后端服务已停止 (attempted)"
}

backup_data() {
    echo "💾 备份数据..."
    timestamp=$(date +%Y%m%d_%H%M%S)
    # Create backup in the project root's backup directory
    BACKUP_ROOT_DIR="$PROJECT_ROOT_DIR/backups" # Changed from relative backup_$timestamp to a backups/ dir
    mkdir -p "$BACKUP_ROOT_DIR"
    ACTUAL_BACKUP_DIR="$BACKUP_ROOT_DIR/backup_$timestamp"
    mkdir -p "$ACTUAL_BACKUP_DIR"

    CHROMA_DB_PATH="$PROJECT_ROOT_DIR/chroma_db" # Path to chroma_db in project root
    CONFIG_PATH="$PROJECT_ROOT_DIR/backend/code/config.py"

    echo "Backing up ChromaDB from $CHROMA_DB_PATH to $ACTUAL_BACKUP_DIR/"
    if [ -d "$CHROMA_DB_PATH" ]; then
        cp -r "$CHROMA_DB_PATH" "$ACTUAL_BACKUP_DIR/"
    else
        echo "⚠️ ChromaDB directory not found at $CHROMA_DB_PATH"
    fi

    echo "Backing up config from $CONFIG_PATH to $ACTUAL_BACKUP_DIR/"
    if [ -f "$CONFIG_PATH" ]; then
        cp "$CONFIG_PATH" "$ACTUAL_BACKUP_DIR/"
    else
        echo "⚠️ Config file not found at $CONFIG_PATH"
    fi

    echo "✅ 数据备份完成: $ACTUAL_BACKUP_DIR"
}

case $ACTION in
    "start")
        case $SERVICE in
            "ollama") start_ollama ;;
            "backend") start_backend ;;
            "all") start_ollama && start_backend ;;
            *) echo "Usage: $0 start [ollama|backend|all]" ;;
        esac
        ;;
    "stop")
        case $SERVICE in
            "ollama") stop_ollama ;;
            "backend") stop_backend ;;
            "all") stop_backend && stop_ollama ;; # Order matters, stop backend first
            *) echo "Usage: $0 stop [ollama|backend|all]" ;;
        esac
        ;;
    "restart")
        $0 stop $SERVICE
        sleep 2
        $0 start $SERVICE
        ;;
    "backup")
        backup_data
        ;;
    *)
        echo "Usage: $0 [start|stop|restart|backup] [service_name or 'all' for start/stop]"
        echo "Service names: ollama, backend"
        exit 1
        ;;
esac
