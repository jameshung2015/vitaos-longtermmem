# monitoring/monitor.py
import psutil
import requests
import time
import logging # Added for logging potential errors
import json # Added for printing the report as in the doc
from typing import Dict, Any
import chromadb # Added chromadb import

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SystemMonitor:
    def __init__(self, ollama_url: str = "http://localhost:11434",
                 chroma_db_path: str = "../chroma_db",
                 chroma_collection_name: str = "longterm_memory_local"):
        self.ollama_url = ollama_url
        self.chroma_db_path = chroma_db_path
        self.chroma_collection_name = chroma_collection_name

    def collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        try:
            disk_io_counters = psutil.disk_io_counters()
            net_io_counters = psutil.net_io_counters()
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "disk_io": disk_io_counters._asdict() if disk_io_counters else {},
                "network_io": net_io_counters._asdict() if net_io_counters else {},
                "timestamp": time.time()
            }
        except Exception as e:
            logging.error(f"Error collecting system metrics: {e}")
            return {"error": str(e)}

    def check_ollama_health(self) -> Dict[str, Any]:
        """检查Ollama服务健康状态"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            response.raise_for_status()
            return {
                "status": "healthy",
                "response_time_seconds": response.elapsed.total_seconds(),
                "models_count": len(response.json().get("models", []))
            }
        except requests.RequestException as e:
            logging.error(f"Ollama health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "response_time_seconds": None
            }

    def check_chroma_health(self) -> Dict[str, Any]:
        """检查Chroma数据库健康状态"""
        start_time = time.time()
        try:
            client = chromadb.PersistentClient(path=self.chroma_db_path)
            collection = client.get_collection(self.chroma_collection_name)
            response_time_seconds = time.time() - start_time
            return {
                "status": "healthy",
                "collection_name": collection.name,
                "collection_count": collection.count(),
                "response_time_seconds": response_time_seconds
            }
        except Exception as e:
            logging.error(f"ChromaDB health check failed: {e}")
            response_time_seconds = time.time() - start_time
            return {
                "status": "error",
                "error": str(e),
                "collection_count": 0,
                "response_time_seconds": response_time_seconds
            }

    def generate_report(self) -> Dict[str, Any]:
        """生成监控报告"""
        report_timestamp = time.time()
        return {
            "report_generated_at": report_timestamp,
            "system_metrics": self.collect_system_metrics(),
            "ollama_health": self.check_ollama_health(),
            "chroma_health": self.check_chroma_health()
        }

if __name__ == "__main__":
    monitor = SystemMonitor(chroma_db_path="../chroma_db")
    report = monitor.generate_report()
    print(json.dumps(report, indent=2))
