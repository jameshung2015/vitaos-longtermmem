import os
import time
import json
import hashlib
import logging
import requests # For Ollama and mem0 service
from smbclient import listdir, open_file # Using smbclient as it's often simpler for basic ops
# from smbprotocol.connection import Connection # Alternative if more control needed

from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_core.documents import Document # If creating Document objects

# --- Configuration Loading ---
CONFIG_FILE_PATH = os.getenv("WECHATMEMORIES_CONFIG", "linux_config.json") # Allow override

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

class WeChatLangchainAgent:
    def __init__(self, config_path):
        self.config = self.load_config(config_path)
        if not self.config:
            raise ValueError("Failed to load or validate configuration.")

        self.ollama_llm = Ollama(
            base_url=self.config["ollama_base_url"],
            model=self.config["ollama_llm_model"]
        )
        self.ollama_embeddings = OllamaEmbeddings(
            base_url=self.config["ollama_base_url"],
            model=self.config["ollama_embedding_model"]
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Adjust as needed
            chunk_overlap=200   # Adjust as needed
        )

        self.processed_files_log = "processed_files.log" # Simple log for incremental processing
        self.processed_files = self._load_processed_files()

        # SMB connection details
        self.smb_server = self.config["windows_ip"]
        # SMB share path needs to be just the share name for listdir/open_file
        # e.g., if full path is \\server\share\folder -> server='server', share_path='share\\folder'
        # The config provides "windows_smb_share_path" like "C:/Users/User/Documents/WeChatMemories/RawLogs"
        # We need to parse this into share name and path within share.
        # For now, assume "windows_smb_share_path" is the *share name* like "RawLogs"
        # and files are directly under it. This might need refinement.
        # If "windows_smb_share_path" is "C:/.../RawLogs", and "RawLogs" is the share name.
        self.smb_share_name = os.path.basename(self.config["windows_smb_share_path"].replace("\\", "/"))
        self.smb_user = self.config["windows_smb_username"]
        self.smb_password = self.config["windows_smb_password"]

        # Configure smbclient (globally or per call)
        # smbclient.ClientConfig(username=self.smb_user, password=self.smb_password)
        # For simplicity, pass credentials in each call if needed, or ensure they are set globally if library supports.
        # `smbclient` functions will try to use current user or prompt if not configured.
        # It's better to pass them explicitly or ensure smbclient is configured.
        # For now, we will rely on them being passed if the library supports it per call,
        # or pre-configure if necessary. The plan is to use `smbprotocol` which might be more explicit.
        # Switching to smbclient for now, will pass auth.

        self.mem0_service_url = f"http://{self.config['linux_ip']}:{self.config['mem0_port']}"
        self.shared_secret_key = self.config["shared_secret_key"]

        logging.info("Langchain Agent initialized.")
        logging.info(f"Monitoring SMB Share: \\\\{self.smb_server}\\{self.smb_share_name}")
        logging.info(f"Ollama Service: {self.config['ollama_base_url']}")
        logging.info(f"Mem0 Service: {self.mem0_service_url}")


    def load_config(self, config_path):
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            # Basic validation (add more as needed)
            required_keys = [
                "windows_ip", "windows_smb_share_path", "windows_smb_username", "windows_smb_password",
                "ollama_base_url", "ollama_llm_model", "ollama_embedding_model",
                "linux_ip", "mem0_port", "shared_secret_key"
            ]
            for key in required_keys:
                if key not in config_data:
                    logging.error(f"Missing key '{key}' in configuration file: {config_path}")
                    return None
            return config_data
        except FileNotFoundError:
            logging.error(f"Configuration file not found: {config_path}")
            return None
        except json.JSONDecodeError:
            logging.error(f"Error decoding JSON from configuration file: {config_path}")
            return None

    def _load_processed_files(self):
        processed = {}
        try:
            if os.path.exists(self.processed_files_log):
                with open(self.processed_files_log, 'r') as f:
                    for line in f:
                        parts = line.strip().split(":", 1)
                        if len(parts) == 2:
                            processed[parts[0]] = parts[1]
        except Exception as e:
            logging.warning(f"Could not load processed files log: {e}")
        return processed

    def _log_processed_file(self, file_path_on_share, file_hash):
        self.processed_files[file_path_on_share] = file_hash
        try:
            with open(self.processed_files_log, 'a') as f:
                f.write(f"{file_path_on_share}:{file_hash}\n")
        except Exception as e:
            logging.error(f"Could not write to processed files log: {e}")

    def get_file_content_and_hash_smb(self, file_path_on_share):
        """
        Reads a file from SMB share and returns its content and MD5 hash.
        file_path_on_share is relative to the share root.
        """
        full_smb_path = f"\\\\{self.smb_server}\\{self.smb_share_name}\\{file_path_on_share}"
        content_bytes = b""
        try:
            # Note: smbclient.open_file requires path to be relative to share root if server/share specified,
            # or full \\server\share\path if not.
            # For listdir, it's `listdir(r"\\server\share")`
            # For open_file, it's `open_file(r"\\server\share\file.txt")`

            # We need to handle authentication. smbclient might try to use kinit or prompt.
            # It's better to explicitly pass credentials.
            # According to smbclient docs, set username/password with `smbclient.ClientConfig()`
            # or ensure they are available through other means (e.g. Kerberos ticket).
            # Let's assume ClientConfig needs to be set once.
            # This should ideally be done during init, but smbclient's global config is tricky.
            # For this example, we'll assume it's configured or we try to pass them if the function allows.
            # `smbclient.open_file` itself doesn't take username/password directly.
            # One must call `smbclient.ClientConfig(username=..., password=...)` before operations.
            # This is a global setting.

            # A more robust way for smbclient might be setting it before the loop:
            # smbclient.ClientConfig(username=self.smb_user, password=self.smb_password)
            # However, this is global state which is not ideal for libraries.
            # Let's proceed with this for now for `smbclient`.
            # If issues, `pysmbclient` or `smbprotocol` might offer better credential handling per connection.

            with open_file(full_smb_path, mode='rb', username=self.smb_user, password=self.smb_password) as fd:
                content_bytes = fd.read()

            content_str = content_bytes.decode('utf-8', errors='replace') # Assuming UTF-8 logs
            file_hash = hashlib.md5(content_bytes).hexdigest()
            return content_str, file_hash
        except Exception as e:
            logging.error(f"Error accessing SMB file {full_smb_path}: {e}")
            return None, None

    def process_single_file(self, file_path_on_share, file_content):
        """
        Processes a single file's content: splits, embeds, and stores in mem0.
        file_path_on_share is used as part of the user_id for mem0.
        """
        logging.info(f"Processing file: {file_path_on_share}")

        # Use filename or a hash of it as user_id for mem0
        # Or perhaps the "talker" if the filename contains it.
        # For now, let's use the filename (without extension) as the primary user_id context.
        user_id_for_mem0 = os.path.splitext(os.path.basename(file_path_on_share))[0]
        logging.info(f"Using user_id '{user_id_for_mem0}' for mem0 entries from this file.")

        texts = self.text_splitter.split_text(file_content)
        logging.info(f"Split file into {len(texts)} chunks.")

        # Embeddings are done by mem0 if it's configured with an embedding model,
        # OR we can pre-embed and send embeddings to mem0.
        # The current plan: "In calling mem0's client API,將對 Embedding 或 LLM 的請求直接發送給 Windows 本地 Ollama 服務"
        # This implies the Langchain agent does NOT directly ask mem0 to generate embeddings.
        # Instead, mem0 is used as a vector store for *externally generated* embeddings.
        # However, mem0's `add` function usually takes text and handles embedding itself.

        # Re-evaluating: If mem0.add(text, ...) is used, mem0 will try to embed it.
        # If mem0 is initialized with an embedding model (e.g. from Ollama), it could work.
        # The plan: "將對 Embedding 或 LLM 的請求直接發送給 Windows 本地 Ollama 服務"
        # This could mean:
        #   1. Langchain agent gets text -> Calls Windows Ollama for embedding -> Sends text + embedding to mem0.
        #      (This requires mem0 to support adding pre-computed vectors).
        #   2. Langchain agent gets text -> Calls mem0.add(text) -> mem0 internally calls Windows Ollama for embedding.
        #      (This requires mem0 to be configured with the Windows Ollama embedding model).

        # Let's assume Option 2 for now, as it's simpler for mem0's API.
        # This means the `mem0_service/app.py` needs to initialize `Memory` with
        # an embedding model that points to Windows Ollama.
        # This was NOT explicitly done in mem0_service/app.py yet.
        # It tried `llm: None`. This needs to be revisited.
        # For now, the agent will just call `mem0_service.add(text_chunk, user_id)`

        # If `mem0_service` is indeed configured to use Windows Ollama for embeddings:
        for i, chunk in enumerate(texts):
            payload = {
                "data": chunk,
                "user_id": user_id_for_mem0, # Group all chunks from same file under same user_id
                "metadata": {
                    "source_file": file_path_on_share,
                    "chunk_index": i,
                    # Add other relevant metadata, e.g., timestamp if available from log
                }
            }
            try:
                response = requests.post(
                    f"{self.mem0_service_url}/add",
                    json=payload,
                    headers={"X-Shared-Secret": self.shared_secret_key, "Content-Type": "application/json"}
                )
                response.raise_for_status()
                logging.debug(f"Stored chunk {i} for {file_path_on_share} in mem0. Response: {response.json()}")
            except requests.exceptions.RequestException as e:
                logging.error(f"Failed to store chunk {i} for {file_path_on_share} in mem0: {e}")
                if e.response is not None:
                    logging.error(f"Mem0 service response: {e.response.text}")
                # Optionally, implement retry or dead-letter queue for failed chunks

        logging.info(f"Finished processing file {file_path_on_share}")


    def monitor_and_process_share(self):
        """Monitors the SMB share and processes new or updated files."""
        logging.info(f"Starting SMB share monitoring: \\\\{self.smb_server}\\{self.smb_share_name}")

        # Configure smbclient globally (if this is the chosen way)
        # This is not ideal, but how smbclient often works without explicit session objects.
        # Consider using a library that supports explicit credential passing per operation or session.
        # For now, setting it with a warning.
        logging.warning("Attempting to set global smbclient username/password. This has global effect.")
        try:
            from smbclient import ClientConfig # Delay import to ensure it's available
            ClientConfig(username=self.smb_user, password=self.smb_password)
            logging.info("Global smbclient credentials set.")
        except Exception as e:
            logging.error(f"Failed to set global smbclient credentials: {e}. SMB operations might fail.")
            # This is a critical failure for smbclient if it can't authenticate.

        try:
            # Path for listdir should be \\server\share (or \\server\share\subfolder)
            share_root_path = f"\\\\{self.smb_server}\\{self.smb_share_name}"

            # List files in the root of the share.
            # If RawLogs are in subdirectories within the share, this needs to be recursive.
            # For now, assume .txt files are directly in the share specified by `smb_share_name`.
            files_on_share = listdir(share_root_path)

            logging.info(f"Found {len(files_on_share)} items in {share_root_path}")

            for filename in files_on_share:
                # Assuming we are only interested in .txt files (or other relevant log extensions)
                if not filename.lower().endswith(".txt"): # Adjust if other extensions
                    logging.debug(f"Skipping non-txt file: {filename}")
                    continue

                file_path_relative_to_share = filename # Since we listed the root

                # Check if file was processed and if it changed
                content, current_hash = self.get_file_content_and_hash_smb(file_path_relative_to_share)

                if content is None or current_hash is None:
                    logging.warning(f"Could not read or hash {file_path_relative_to_share}. Skipping.")
                    continue

                previous_hash = self.processed_files.get(file_path_relative_to_share)
                if previous_hash == current_hash:
                    logging.debug(f"File {file_path_relative_to_share} has not changed. Skipping.")
                    continue

                logging.info(f"New or updated file detected: {file_path_relative_to_share} (Hash: {current_hash})")
                self.process_single_file(file_path_relative_to_share, content)
                self._log_processed_file(file_path_relative_to_share, current_hash)

        except Exception as e:
            logging.error(f"Error during SMB share monitoring or processing: {e}", exc_info=True)
            # Depending on the error, might need to handle SMB authentication issues, share not found, etc.

    def run(self):
        logging.info("Langchain Agent starting run loop.")
        # Initial check
        try:
            self.monitor_and_process_share()
        except Exception as e:
            logging.critical(f"Unhandled exception during initial processing run: {e}", exc_info=True)

        # In a real agent, this would be a loop with a sleep, or use watchdog for event-based monitoring
        # For this project, a periodic scan might be sufficient.
        # while True:
        #     try:
        #         self.monitor_and_process_share()
        #     except Exception as e:
        #         logging.error(f"Error in monitoring loop: {e}", exc_info=True)
        #     logging.info(f"Waiting for {self.config.get('scan_interval_seconds', 300)} seconds before next scan.")
        #     time.sleep(self.config.get('scan_interval_seconds', 300)) # e.g., 5 minutes

        # For now, let's make it a one-shot run for simplicity in this phase.
        # Later, it can be converted to a continuous service.
        logging.info("Langchain Agent run finished (single pass).")


if __name__ == "__main__":
    logging.info("Starting Langchain Agent script.")
    # Load config path from environment or use default
    config_file = os.getenv("WECHATMEMORIES_CONFIG", "linux_config.json")

    # Check if config file exists in common locations if not specified absolutely
    if not os.path.isabs(config_file):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Check relative to script, then parent (linux_server), then current dir
        potential_paths = [
            os.path.join(script_dir, config_file),
            os.path.join(script_dir, "..", config_file), # If config is in linux_server/
            config_file
        ]
        found_config = False
        for p_path in potential_paths:
            if os.path.exists(p_path):
                config_file = p_path
                found_config = True
                logging.info(f"Using configuration file: {os.path.abspath(config_file)}")
                break
        if not found_config:
            logging.error(f"Configuration file '{config_file}' not found in standard locations. Please set WECHATMEMORIES_CONFIG or place it correctly.")
            exit(1)

    try:
        agent = WeChatLangchainAgent(config_path=config_file)
        agent.run()
    except ValueError as ve: # Config loading error
        logging.critical(f"Agent initialization failed: {ve}")
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}", exc_info=True)

```

**Key considerations and placeholders in this initial `agent.py`:**

1.  **SMB Client Choice and Authentication (`smbclient`):**
    *   I've used `smbclient` for now as it's part of Samba.
    *   Authentication with `smbclient` can be tricky. It often relies on global configuration (`smbclient.ClientConfig`) or system-level Kerberos/NTLM setup. The code includes a warning and an attempt to set `ClientConfig`. This is a common pain point and might need to be switched to `pysmbclient` or `smbprotocol` if `smbclient` proves too difficult to manage credentials with cleanly from Python without external config. The plan originally mentioned `smbprotocol`. If `smbclient` is problematic, I will switch.
    *   The share path construction (`smb_share_name`) assumes the `windows_smb_share_path` from the config is the *actual share name*. This detail needs to be precise.

2.  **`mem0` Embedding Strategy:**
    *   The current agent code calls `mem0_service/add` with text chunks. This implies that the `mem0_service` itself is responsible for generating embeddings.
    *   For this to work with Windows Ollama, the `mem0_service/app.py` must initialize `mem0.Memory` in a way that it uses the Windows Ollama instance for embeddings (e.g., by configuring `mem0` with an `OllamaEmbeddings` instance pointing to the Windows machine).
    *   The placeholder in `mem0_service/app.py` for `mem0` initialization needs to be updated to reflect this. If `mem0` cannot be easily configured to use a *remote* Ollama instance for its *internal* embedding generation, then the agent would have to:
        1.  Get text chunk.
        2.  Call `self.ollama_embeddings.embed_query(chunk)` (or `embed_documents`).
        3.  Send the text chunk *and its pre-computed vector* to `mem0_service`. This would require the `/add` endpoint in `mem0_service` to accept pre-computed vectors. This is a more complex pattern.
    *   **Decision for now:** Assume `mem0_service` will be configured to use Windows Ollama for embeddings. This means the `mem0_service/app.py` will need an `OllamaEmbeddings` instance.

3.  **Incremental Processing:**
    *   Uses a simple `processed_files.log` storing `filepath:hash`.
    *   Reads the whole file to hash it. For very large, frequently appended files, this might be inefficient, but for typical chat logs (which are new files or fully rewritten), it's okay.

4.  **Error Handling:** Basic error handling is in place, but real-world SMB/network issues can be varied.

5.  **Run Loop:** Currently, it's a single pass. A `while True` loop with `time.sleep()` or `watchdog` would be for continuous operation.

Next, I will create a placeholder `linux_config.json` that the agent expects, to facilitate testing and understanding of the structure. This file would normally be generated by the Windows `config_wizard_app.py`.
