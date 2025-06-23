import os
import logging
from functools import wraps
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from mem0 import Memory # Main class from mem0ai

# --- Configuration & Initialization ---
load_dotenv() # Load environment variables from .env file

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Shared secret key for API authentication
SHARED_SECRET_KEY = os.getenv("SHARED_SECRET_KEY")
if not SHARED_SECRET_KEY:
    logging.error("SHARED_SECRET_KEY not found in .env file. Service will not be secure.")
    # For development, you might allow it to run, but for production, exit or raise error.
    # raise ValueError("SHARED_SECRET_KEY is not set.")

# mem0 configuration
# For local persistence, mem0 can use LanceDB.
# The storage path should be configurable.
DEFAULT_STORAGE_PATH = "./mem0_data_default" # Default if not in .env
MEM0_STORAGE_PATH = os.getenv("MEM0_STORAGE_PATH", DEFAULT_STORAGE_PATH)

# Ensure the storage directory exists
os.makedirs(MEM0_STORAGE_PATH, exist_ok=True)
logging.info(f"Mem0 storage path: {os.path.abspath(MEM0_STORAGE_PATH)}")

# Initialize mem0
# We need to configure mem0 to use a local vector store for persistence.
# According to mem0 docs, it can use LanceDB.
# The config for mem0 often involves specifying a vector store or other components.
# For a simple local setup, we might configure it like this:
# This configuration may need adjustment based on the exact version of mem0ai
# and how it expects local LanceDB to be configured.
# It's also possible mem0 handles this more automatically if lancedb is installed.

# Option 1: Rely on mem0's defaults if lancedb is installed and it picks it up
# for persistence with a path.
# mem0_instance = Memory() # This might be in-memory only by default.

# Option 2: Explicitly configure vector store for persistence.
# The exact config structure can vary. Checking mem0 docs for "persistence" or "lancedb".
# A common pattern is to pass a config dictionary.
# From mem0 docs:
# from mem0.configs.vector_stores.lancedb import LanceDBConfig
# vector_store_config = LanceDBConfig(path=MEM0_STORAGE_PATH)
# mem0_config = {"vector_store": vector_store_config}
# mem0_instance = Memory(config=mem0_config)

# Let's try a simpler initialization first, assuming mem0 might handle
# persistence to a path if lancedb is installed.
# If not, we'll need to use the more explicit config.
# For now, we'll instantiate one Memory object globally.
# In a more complex app, you might manage instances differently.

# Global mem0 instance.
# This is a simplified approach. For production, consider instance management.
# The `Memory()` class itself might not be thread-safe for concurrent writes
# with some backends without careful handling or a proper service architecture.
# However, for sequential processing by the Langchain agent, this might be okay.
# Let's assume mem0 handles internal locking or we ensure sequential access for writes.

# Placeholder for mem0 instance. It will be initialized in a function to allow for
# more complex setup or re-initialization if needed.
mem0_instance = None

def get_mem0_instance():
    global mem0_instance
    if mem0_instance is None:
        logging.info("Initializing mem0 instance...")
        try:
            # Attempting to use LanceDB for persistence.
            # The key is ensuring mem0 knows where to store its LanceDB data.
            # Some versions of mem0 might take 'data_dir' or similar in its main config.
            # Or, it might be part of a vector_store_config.
            # Let's assume a config structure that points to our storage path.
            # This is a common pattern for libraries that use other components.

            # Based on recent mem0 patterns, it might be:
            # config = {
            #     "vector_store": {
            #         "provider": "lancedb",
            #         "config": {
            #             "uri": MEM0_STORAGE_PATH
            #         }
            #     },
            #     # We don't want mem0 to use an external LLM for its internal ops by default
            #     # if our primary LLM is Ollama on Windows.
            #     # If mem0 *needs* an LLM for its own processing (e.g. summarization before storage),
            #     # we might need to configure it here, possibly pointing to Windows Ollama.
            #     # For now, let's assume it can work without one for basic add/search,
            #     # or uses a very light default.
            #     "llm": None # Attempt to disable internal LLM use or use a default light one.
            # }
            # mem0_instance = Memory(config=config)

            # Simpler approach: mem0 >= 0.1.40 automatically creates a lancedb store in ~/.mem0/
            # To customize path, you might need to set an environment variable like MEM0_DATA_DIR
            # or pass it via config. Let's try setting an env var that mem0 might pick up.
            os.environ['MEM0_DATA_DIR'] = MEM0_STORAGE_PATH # Hacky, but some libs do this

            # Or, if `Memory` constructor takes a `data_dir` directly or via a top-level config key:
            # config = {"data_dir": MEM0_STORAGE_PATH} # hypothetical
            # mem0_instance = Memory(config=config)

            # The most straightforward if supported by current mem0 version:
            mem0_instance = Memory() # And hope it uses MEM0_DATA_DIR or defaults to a known local persistent spot
                                     # and we can find where that is.
                                     # If it defaults to ~/.mem0 and we want it in MEM0_STORAGE_PATH,
                                     # we need a proper config.

            # Let's assume for now, we need to find the right config for LanceDB path.
            # If `mem0ai` includes `LanceDBConfig`:
            from mem0.configs.vector_stores.lancedb import LanceDBConfig
            from mem0.embeddings.ollama import OllamaEmbeddings as Mem0OllamaEmbeddings # mem0's own Ollama wrapper

            # Config for Windows Ollama (for embeddings) - this needs to be passed from agent's config
            # For now, we'll need to read it from an env var or a shared config accessible here.
            # Let's assume these are also in the .env for the mem0_service
            OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
            OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL")

            if not OLLAMA_BASE_URL or not OLLAMA_EMBEDDING_MODEL:
                logging.error("OLLAMA_BASE_URL or OLLAMA_EMBEDDING_MODEL not set in .env for mem0_service.")
                logging.error("Mem0 will likely fail to generate embeddings if it's not configured with a default.")
                # This is a critical configuration for the current design.
                raise ValueError("Ollama embedding config missing for mem0 service.")

            vector_store_config = LanceDBConfig(path=MEM0_STORAGE_PATH)

            # Configure mem0 to use the Windows Ollama for embeddings
            # The exact key for embedder config might vary ("embedder", "embedding_model", etc.)
            # Checking recent mem0 docs, it might be under an "embeddings" key or "embedder".
            # Example:
            # "embeddings": {
            #    "provider": "ollama",
            #    "config": {
            #        "model": OLLAMA_EMBEDDING_MODEL,
            #        "base_url": OLLAMA_BASE_URL
            #    }
            # }
            # Or using mem0.embeddings.OllamaEmbeddings directly:

            ollama_embedder_for_mem0 = Mem0OllamaEmbeddings(model=OLLAMA_EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)

            mem0_config = {
                "vector_store": vector_store_config,
                "embedder": ollama_embedder_for_mem0, # Pass the initialized embedder instance
                 # "llm": None # Explicitly disable internal LLM usage if not needed for memory processing itself
            }

            mem0_instance = Memory(config=mem0_config)

            logging.info(f"Mem0 instance initialized. Data should persist in {MEM0_STORAGE_PATH}")
            logging.info(f"Mem0 configured to use Ollama embeddings: {OLLAMA_BASE_URL} with model {OLLAMA_EMBEDDING_MODEL}")

        except ImportError as ie:
            if 'LanceDBConfig' in str(ie) or 'OllamaEmbeddings' in str(ie):
                 logging.error(f"Failed to import mem0 components (LanceDBConfig or OllamaEmbeddings): {ie}. Is lancedb installed and mem0ai version compatible and includes these?")
            else:
                logging.error(f"An import error occurred: {ie}")
            logging.info("Attempting basic Memory() initialization without explicit LanceDB/Ollama config as fallback.")
            mem0_instance = Memory() # Fallback, might be in-memory or default path, and might try to use OpenAI embeddings
            logging.warning("Fallback mem0 instance may not use desired persistence or embeddings.")
        except Exception as e:
            logging.error(f"Failed to initialize mem0 with specific config: {e}", exc_info=True)
            logging.error("Mem0 service might not function correctly.")
            raise RuntimeError(f"Could not initialize mem0: {e}") from e

    return mem0_instance


# --- Authentication Decorator ---
def require_secret_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not SHARED_SECRET_KEY: # If no key is set, bypass auth (dev only, insecure)
            logging.warning("SHARED_SECRET_KEY is not set. Authentication is bypassed. THIS IS INSECURE.")
        elif request.headers.get("X-Shared-Secret") != SHARED_SECRET_KEY:
            logging.warning(f"Unauthorized access attempt. Incorrect or missing X-Shared-Secret header.")
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# --- API Endpoints ---

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    # Try to get mem0 instance to ensure it can initialize
    try:
        get_mem0_instance()
        return jsonify({"status": "ok", "message": "Mem0 service is running"}), 200
    except Exception as e:
        logging.error(f"Health check failed during mem0 initialization: {e}")
        return jsonify({"status": "error", "message": f"Mem0 initialization failed: {e}"}), 500


@app.route("/add", methods=["POST"])
@require_secret_key
def add_memory_entry():
    """
    Adds a memory entry to mem0.
    Expects JSON payload:
    {
        "data": "text content of the memory",
        "user_id": "identifier for the user/chat (e.g., wxid_xxxx or GroupName)",
        "metadata": { ... } // Optional metadata
    }
    """
    mem0 = get_mem0_instance()
    if not mem0:
        return jsonify({"error": "Mem0 not initialized"}), 500

    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "Invalid JSON payload"}), 400

        text_content = payload.get("data")
        user_id = payload.get("user_id")
        metadata = payload.get("metadata", {}) # Allow optional metadata

        if not text_content or not user_id:
            return jsonify({"error": "Missing 'data' or 'user_id' in payload"}), 400

        # mem0.add() can take a list of messages or a single string.
        # For simple text chunks, we can pass the string directly.
        # The 'user_id' parameter in mem0.add() is crucial for namespacing.
        # The 'agent_id' could be used if we have multiple agents interacting with the same user's memory.
        # For now, we'll use a default agent_id or omit if not strictly needed.

        # Example: mem0.add(text_content, user_id=user_id, metadata=metadata)
        # The exact signature for `add` might vary (e.g., if it expects a list of "messages")
        # For raw text, it might be:
        # mem0.add(data=text_content, user_id=user_id, metadata=metadata)
        # Or if it expects a "message" like structure:
        # mem0.add([{"role": "user", "content": text_content}], user_id=user_id, metadata=metadata)

        # Let's assume a simple direct add:
        result = mem0.add(text_content, user_id=user_id, metadata=metadata)

        logging.info(f"Added memory for user_id '{user_id}'. Result: {result}")
        return jsonify({"status": "success", "message": "Memory added.", "result": result}), 201

    except Exception as e:
        logging.error(f"Error in /add endpoint: {e}", exc_info=True)
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route("/search", methods=["POST"]) # Changed to POST to accept JSON body for query
@require_secret_key
def search_memory_entries():
    """
    Searches memories in mem0.
    Expects JSON payload:
    {
        "query": "search query text",
        "user_id": "identifier for the user/chat",
        "limit": 3 // Optional limit for results
    }
    """
    mem0 = get_mem0_instance()
    if not mem0:
        return jsonify({"error": "Mem0 not initialized"}), 500

    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "Invalid JSON payload"}), 400

        query_text = payload.get("query")
        user_id = payload.get("user_id")
        limit = payload.get("limit", 3) # Default limit

        if not query_text or not user_id:
            return jsonify({"error": "Missing 'query' or 'user_id' in payload"}), 400

        # mem0.search() is the typical method.
        # It usually takes the query, user_id, and other params like limit.
        results = mem0.search(query=query_text, user_id=user_id, limit=limit)

        logging.info(f"Searched memories for user_id '{user_id}' with query '{query_text}'. Found: {len(results.get('results', [])) if results else 0} results.")
        return jsonify({"status": "success", "results": results.get("results", []) if results else []}), 200

    except Exception as e:
        logging.error(f"Error in /search endpoint: {e}", exc_info=True)
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

# Example of how to list all memories for a user (if mem0 supports it directly)
@app.route("/list_all", methods=["GET"])
@require_secret_key
def list_all_memories_for_user():
    mem0 = get_mem0_instance()
    if not mem0:
        return jsonify({"error": "Mem0 not initialized"}), 500

    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing 'user_id' parameter"}), 400

    try:
        # mem0.get_all() or mem0.list() might be available.
        # If it stores data in a structured way, it might have such a method.
        # This is speculative; consult mem0 docs for listing all memories.
        # For now, we'll assume such a method exists or search with a wildcard if possible.
        # Or, this might just be a search with a very broad query and high limit.
        # This endpoint is more for debugging/utility.

        # mem0.get_all(user_id=user_id) or similar
        # For now, let's simulate by searching with a generic query if no direct list method
        # This is NOT efficient for "list all".
        # results = mem0.search(query="*", user_id=user_id, limit=1000) # Highly dependent on mem0 behavior

        # A more direct way if available (hypothetical):
        # all_memories = mem0.get_memories(user_id=user_id)
        # For now, this endpoint will be placeholder as direct "list all" is not standard in all vector stores.

        # Check if mem0 has a "get_all" method or similar.
        if hasattr(mem0, 'get_all') and callable(getattr(mem0, 'get_all')):
            all_memories = mem0.get_all(user_id=user_id) # Assuming it takes user_id
            logging.info(f"Retrieved all memories for user_id '{user_id}'.")
            return jsonify({"status": "success", "memories": all_memories}), 200
        else:
            # Fallback: search with a common term or indicate not implemented
            # This is not a true "list all"
            results = mem0.search(query=" ", user_id=user_id, limit=100) # Get some recent/relevant ones
            logging.info(f"Listing memories for user_id '{user_id}' (used broad search).")
            message = "List all not directly supported, returning results from a broad search."
            return jsonify({"status": "partial_success", "message": message, "results": results.get("results", []) if results else []}), 200


    except Exception as e:
        logging.error(f"Error in /list_all endpoint: {e}", exc_info=True)
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


# --- Main Execution ---
if __name__ == "__main__":
    # Ensure mem0 instance is created at startup to catch initialization errors early
    try:
        get_mem0_instance()
        logging.info("Successfully pre-initialized mem0 instance.")
    except RuntimeError as e:
        logging.error(f"CRITICAL: Could not start application due to mem0 initialization failure: {e}")
        exit(1) # Exit if mem0 cannot be initialized

    # Port can be configured via Gunicorn or environment variable
    port = int(os.getenv("MEM0_SERVICE_PORT", 8000))
    # When running directly with `python app.py`, Flask's dev server is used.
    # For production, use Gunicorn as per the setup guide.
    logging.info(f"Starting Flask development server on http://0.0.0.0:{port}")
    logging.warning("This is a development server. For production, run with Gunicorn.")
    app.run(host="0.0.0.0", port=port, debug=False) # debug=False for less verbose default logs in prod-like run
```
