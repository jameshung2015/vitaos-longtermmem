#!/bin/bash
# backend/scripts/maintenance.sh

# Determine script's own directory to reliably find other scripts/files
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# Assuming PROJECT_ROOT_DIR is the parent of the 'backend' directory
PROJECT_ROOT_DIR=$(dirname "$(dirname "$SCRIPT_DIR")")
LOG_DIR="$PROJECT_ROOT_DIR/logs" # Define where logs are stored, e.g., project_root/logs

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Daily maintenance task
daily_maintenance() {
    echo "📅 Executing daily maintenance tasks... $(date)"

    # Clean up old log files (e.g., older than 7 days)
    echo "🧹 Cleaning up old log files from $LOG_DIR (older than 7 days)..."
    find "$LOG_DIR/" -name "*.log" -mtime +7 -print -delete

    # Database optimization (placeholder call)
    echo " optimizing Chroma database..."
    if [ -f "$SCRIPT_DIR/optimize_chroma.py" ]; then
        python "$SCRIPT_DIR/optimize_chroma.py" >> "$LOG_DIR/maintenance_daily.log" 2>&1
    else
        echo "⚠️ optimize_chroma.py not found." >> "$LOG_DIR/maintenance_daily.log"
    fi

    # Generate performance report (placeholder call)
    echo "📊 Generating performance report..."
    if [ -f "$SCRIPT_DIR/performance_report.py" ]; then
        python "$SCRIPT_DIR/performance_report.py" >> "$LOG_DIR/maintenance_daily.log" 2>&1
    else
        echo "⚠️ performance_report.py not found." >> "$LOG_DIR/maintenance_daily.log"
    fi

    # Health check (placeholder call)
    echo "🩺 Performing health check..."
    if [ -f "$SCRIPT_DIR/health_check.py" ]; then
        python "$SCRIPT_DIR/health_check.py" >> "$LOG_DIR/maintenance_daily.log" 2>&1
    else
        echo "⚠️ health_check.py not found." >> "$LOG_DIR/maintenance_daily.log"
    fi

    echo "✅ Daily maintenance completed. Log: $LOG_DIR/maintenance_daily.log"
}

# Weekly maintenance task
weekly_maintenance() {
    echo "📅 Executing weekly maintenance tasks... $(date)"

    # Full data backup (using service_manager.sh)
    echo "💾 Performing full data backup..."
    if [ -f "$SCRIPT_DIR/service_manager.sh" ]; then
        "$SCRIPT_DIR/service_manager.sh" backup >> "$LOG_DIR/maintenance_weekly.log" 2>&1
    else
        echo "⚠️ service_manager.sh not found. Cannot perform backup." >> "$LOG_DIR/maintenance_weekly.log"
    fi

    # Clean temporary files (example for Chroma, adjust if needed)
    echo "🧹 Cleaning temporary Chroma files..."
    # This is a generic example; actual temp files for Chroma might differ or be managed internally.
    # The doc had /tmp/chroma* which is system-wide. Be cautious with system /tmp.
    # For now, let's assume Chroma places temp files within its own db directory or a known temp location.
    # If specific paths are known, use them. Otherwise, this step might be too risky or unnecessary.
    # find /tmp -name "chroma*" -mtime +7 -print -delete # Original from doc, commented out for safety.
    echo "   (Skipping system-wide /tmp cleanup for now - requires specific paths for safety)" >> "$LOG_DIR/maintenance_weekly.log"

    # System update check (Debian/Ubuntu example)
    echo "🔄 Checking for system updates (apt list --upgradable)..."
    if command -v apt &> /dev/null; then
        apt list --upgradable >> "$LOG_DIR/maintenance_weekly.log" 2>&1
    else
        echo "   apt command not found. Skipping system update check." >> "$LOG_DIR/maintenance_weekly.log"
    fi

    echo "✅ Weekly maintenance completed. Log: $LOG_DIR/maintenance_weekly.log"
}

case $1 in
    "daily")
        daily_maintenance
        ;;
    "weekly")
        weekly_maintenance
        ;;
    *)
        echo "Usage: $0 [daily|weekly]"
        exit 1
        ;;
esac
