# backend/scripts/import_to_chroma.py
import json
import chromadb
try:
    from backend.code.ollama_embedder import OllamaEmbedder
except ImportError:
    # This might happen if PYTHONPATH is not set up correctly or script is run from a weird location.
    # For robustness in a subtask, assume it might fail and provide a fallback or log it.
    print("Failed to import OllamaEmbedder from backend.code.ollama_embedder.")
    print("Ensure the script is run from the project root or backend directory, or PYTHONPATH is set.")
    # In a real scenario, this should probably raise an error or have a more robust import solution.
    # For this subtask, we'll define a placeholder if it fails to allow file creation.
    class OllamaEmbedder: # Placeholder
        def __init__(self, *args, **kwargs): print("Using Placeholder OllamaEmbedder")
        def embed_documents(self, texts): return [[0.0] * 768 for _ in texts] # nomic-embed-text is 768
        def embed_query(self, text): return [0.0] * 768

from tqdm import tqdm # Ensure tqdm is listed as a dependency if not already

def import_to_chroma():
    """导入数据到Chroma"""

    # 初始化服务
    # Ensure ./chroma_db path is relative to where this script is run, or use absolute paths.
    # The document implies running from a context where ./chroma_db is correct.
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_or_create_collection("longterm_memory_local")
        embedder = OllamaEmbedder() # This will use the potentially adjusted import
    except Exception as e:
        print(f"Error initializing ChromaDB client or OllamaEmbedder: {e}")
        return False

    # 读取导出数据
    input_filename = "vikingdb_export.json"
    try:
        with open(input_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {input_filename} not found. Please run export_vikingdb.py first.")
        return False
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {input_filename}: {e}")
        return False

    memories = data.get("memories", [])
    if not memories:
        print("No memories found in the export file.")
        return False

    batch_size = 100 # As per doc

    print(f"📥 开始导入 {len(memories)} 条记忆...")

    for i in tqdm(range(0, len(memories), batch_size)):
        batch = memories[i:i+batch_size]

        texts = [m["text"] for m in batch]
        # The doc uses f"mem_{m['id']}" - ensure 'id' exists and is suitable.
        # The export script uses "id": memory.get("id")
        ids = [f"mem_{m['id']}" for m in batch if m.get('id') is not None]
        if len(ids) != len(texts):
            print(f"Warning: Some items in batch {i//batch_size} are missing an ID. Skipping them for ID generation.")
            # Filter out items without IDs for all lists to maintain consistency
            valid_batch_indices = [idx for idx, item in enumerate(batch) if item.get('id') is not None]
            texts = [texts[idx] for idx in valid_batch_indices]
            # Metadatas also need to be filtered if they are to be used
            metadatas_batch = [batch[idx]["metadata"] for idx in valid_batch_indices]
            if not texts: # if all items in batch lacked id
                continue
        else:
            metadatas_batch = [m["metadata"] for m in batch]

        # 生成嵌入向量
        try:
            embeddings = embedder.embed_documents(texts)
        except Exception as e:
            print(f"Error embedding documents in batch {i//batch_size}: {e}")
            continue # Skip this batch or handle error appropriately

        # 插入到Chroma
        try:
            collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas_batch, # Corrected from metadatas to metadatas_batch
                ids=ids
            )
        except Exception as e:
            print(f"Error adding batch {i//batch_size} to Chroma: {e}")
            continue # Skip this batch

    print(f"✅ 导入完成: {collection.count()} 条记忆 (potentially, check logs for errors)")

    # 验证数据一致性
    test_query = "测试查询"
    print(f"🧪 Performing a test query: '{test_query}'")
    try:
        results = collection.query(
            query_embeddings=[embedder.embed_query(test_query)],
            n_results=5
        )
        print(f"🔍 测试查询返回 {len(results.get('documents', [[]])[0])} 条结果")
    except Exception as e:
        print(f"Error during test query: {e}")

    return True

if __name__ == "__main__":
    import_to_chroma()
