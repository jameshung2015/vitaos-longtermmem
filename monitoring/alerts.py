# monitoring/alerts.py
import smtplib
from email.mime.text import MIMEText
from typing import Dict, List, Any
import time
import json # Added for the __main__ example

class AlertManager:
    def __init__(self, mail_config: Dict = None):
        self.alert_rules = {
            "cpu_high": {"threshold": 90, "severity": "warning", "metric": "system_metrics.cpu_percent"},
            "memory_high": {"threshold": 95, "severity": "critical", "metric": "system_metrics.memory_percent"},
            "disk_high": {"threshold": 95, "severity": "critical", "metric": "system_metrics.disk_percent"},
            "ollama_down": {"threshold": "error", "severity": "critical", "metric": "ollama_health.status"},
            "chroma_error": {"threshold": "error", "severity": "critical", "metric": "chroma_health.status"},
            "ollama_embedding_latency": {"threshold": 1.0, "severity": "warning", "metric": "ollama_health.response_time_seconds"}
        }
        self.mail_config = mail_config if mail_config else {
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "smtp_user": "user@example.com",
            "smtp_password": "password",
            "from_email": "system_alerts@example.com",
            "to_email": "admin@example.com"
        }

    def _get_metric_value(self, metrics_report: Dict, metric_path: str) -> Any:
        keys = metric_path.split('.')
        value = metrics_report
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return None

    def check_alerts(self, metrics_report: Dict) -> List[Dict]:
        alerts = []
        for rule_name, rule_config in self.alert_rules.items():
            metric_value = self._get_metric_value(metrics_report, rule_config["metric"])
            if metric_value is None:
                continue
            triggered = False
            if isinstance(metric_value, (int, float)) and isinstance(rule_config["threshold"], (int, float)):
                if metric_value > rule_config["threshold"]:
                    triggered = True
            elif isinstance(metric_value, str) and metric_value == rule_config["threshold"]:
                triggered = True
            if triggered:
                alerts.append({
                    "rule_name": rule_name,
                    "severity": rule_config["severity"],
                    "metric_path": rule_config["metric"],
                    "threshold": rule_config["threshold"],
                    "current_value": metric_value,
                    "message": f"Alert: {rule_name} - {rule_config['metric']} ({metric_value}) exceeded threshold ({rule_config['threshold']}). Severity: {rule_config['severity']}"
                })
        return alerts

    def send_alert_email(self, alert: Dict):
        subject = f"[Monitoring Alert] {alert['severity'].upper()}: {alert['rule_name']}"
        body = f"""
        Dear Admin,
        An alert has been triggered by the monitoring system:
        Rule Name: {alert['rule_name']}
        Severity: {alert['severity']}
        Metric: {alert['metric_path']}
        Threshold: {alert['threshold']}
        Current Value: {alert['current_value']}
        Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}
        Message: {alert['message']}
        Please investigate this issue.
        Regards,
        Automated Monitoring System
        """
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.mail_config["from_email"]
        msg['To'] = self.mail_config["to_email"]
        print(f"INFO: Attempting to send email alert: Subject: {subject}")
        print(f"      Body: {body[:200].replace(chr(10), ' ')}...") # Replaced newline for cleaner log
        print(f"SIMULATED_EMAIL_SENT: Alert for {alert['rule_name']} to {self.mail_config['to_email']}")

if __name__ == "__main__":
    dummy_metrics_report = {
        "report_generated_at": time.time(),
        "system_metrics": {
            "cpu_percent": 95, "memory_percent": 80, "disk_percent": 70,
            "timestamp": time.time()
        },
        "ollama_health": {
            "status": "healthy", "response_time_seconds": 0.5, "models_count": 1
        },
        "chroma_health": {
            "status": "error", "error": "Connection failed", "collection_count": 0
        }
    }
    alert_manager = AlertManager()
    triggered_alerts = alert_manager.check_alerts(dummy_metrics_report)
    if triggered_alerts:
        print(f"\n--- Triggered Alerts ({len(triggered_alerts)}) ---")
        for alert_item in triggered_alerts:
            print(json.dumps(alert_item, indent=2))
            alert_manager.send_alert_email(alert_item)
    else:
        print("\n--- No Alerts Triggered ---")
