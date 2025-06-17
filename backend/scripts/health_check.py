# backend/scripts/health_check.py
import time
import requests # For Ollama and potentially backend app
import chromadb # For ChromaDB
# from backend.code.ollama_embedder import OllamaEmbedder # If using its health_check

def check_ollama_status_basic():
    ollama_base_url = "http://localhost:11434"
    try:
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            return True, f"Ollama service running. Models available: {len(response.json().get('models', []))}"
        return False, f"Ollama service error. Status: {response.status_code}"
    except requests.RequestException as e:
        return False, f"Ollama service connection failed: {e}"

def check_chroma_status_basic():
    try:
        # Assuming chroma_db is in the project root or a known path
        # The path for PersistentClient should be consistent with its usage elsewhere (e.g., init_chroma.py, config.py)
        # Let's assume it's './chroma_db' relative to where health_check might be run from (e.g. project root)
        # Or, more robustly, use an absolute path or path derived from config.
        client = chromadb.PersistentClient(path="./chroma_db") # Adjust path if needed
        # Try to get a known collection, or list collections
        client.get_or_create_collection("longterm_memory_local") # As used in init_chroma
        return True, "ChromaDB service appears responsive (collection accessible)."
    except Exception as e:
        return False, f"ChromaDB connection/access failed: {e}"

def check_backend_app_status_basic():
    # This is highly dependent on how the backend app exposes its health.
    # Assuming it runs on a specific port and might have a /health endpoint.
    # For now, this is a very basic placeholder.
    # backend_url = "http://localhost:8000" # Example, if backend runs on 8000
    # try:
    #     response = requests.get(f"{backend_url}/health", timeout=5) # Hypothetical health endpoint
    #     if response.status_code == 200:
    #         return True, "Backend application is healthy."
    #     return False, f"Backend application unhealthy. Status: {response.status_code}"
    # except requests.RequestException as e:
    #     return False, f"Backend application connection failed: {e}"
    return None, "Backend app health check not implemented yet."


def perform_full_health_check():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Performing System Health Check...")

    overall_healthy = True

    ollama_ok, ollama_msg = check_ollama_status_basic()
    print(f"Ollama Status: {'OK' if ollama_ok else 'FAIL'} - {ollama_msg}")
    if not ollama_ok: overall_healthy = False

    chroma_ok, chroma_msg = check_chroma_status_basic()
    print(f"ChromaDB Status: {'OK' if chroma_ok else 'FAIL'} - {chroma_msg}")
    if not chroma_ok: overall_healthy = False

    backend_ok, backend_msg = check_backend_app_status_basic()
    if backend_ok is not None: # If implemented
        print(f"Backend App Status: {'OK' if backend_ok else 'FAIL'} - {backend_msg}")
        if not backend_ok: overall_healthy = False
    else:
        print(f"Backend App Status: {backend_msg}")


    if overall_healthy:
        print("✅ System Health Check: All components appear nominal.")
    else:
        print("❌ System Health Check: One or more components reported issues.")

    return overall_healthy

if __name__ == "__main__":
    perform_full_health_check()
    print("Health check script executed.")
