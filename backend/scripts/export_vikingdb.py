# backend/scripts/export_vikingdb.py
import json
# Assuming config.py is in backend.code and this script is run from a context where backend.code is accessible
# Or that mem0 is installed and configured appropriately to find its config
# For now, let's assume a direct import if the structure allows, or this might need adjustment
try:
    from backend.code.config import mem0_config
except ImportError:
    # Fallback if the script is run from a different path, though this is less ideal
    # This part is speculative and depends on how mem0 library loads its config
    print("Warning: Could not import mem0_config directly. Ensure mem0 is configured.")
    mem0_config = {} # Placeholder

from mem0 import Memory # Assuming mem0 is an installed library

def export_vikingdb_data():
    """导出VikingDB数据"""

    # 连接现有VikingDB
    # The Memory.from_config might fail if VOLC_ACCESSKEY/SECRETKEY are commented out
    # and if the library strictly requires them for "vikingdb" provider
    # This script is for a future state where it might be run BEFORE config changes,
    # or mem0 library handles this gracefully.
    print("Attempting to connect to VikingDB. This may require valid cloud credentials in config.")
    try:
        memory_client = Memory.from_config(mem0_config) # This will use the config.py
    except Exception as e:
        print(f"Error initializing Memory client: {e}")
        print("Please ensure your config.py is set up for VikingDB for this script to work.")
        print("This script is intended to be run BEFORE migrating to local ChromaDB.")
        return None

    # 获取所有记忆数据
    print("Fetching all memories from VikingDB...")
    try:
        all_memories = memory_client.get_all(limit=100000) # Default limit in doc
    except Exception as e:
        print(f"Error fetching memories from VikingDB: {e}")
        return None

    # 导出格式
    export_data = {
        "version": "1.0",
        "timestamp": "2025-06-17T10:00:00Z", # Doc timestamp
        "total_count": len(all_memories),
        "memories": []
    }

    for memory in all_memories:
        export_data["memories"].append({
            "id": memory.get("id"),
            "text": memory.get("memory"), # Changed from "text" to "memory" as per doc's example usage of memory_client.get_all
            "metadata": memory.get("metadata", {}),
            "user_id": memory.get("user_id"),
            "agent_id": memory.get("agent_id"),
            "created_at": memory.get("created_at")
        })

    # 保存到文件
    output_filename = "vikingdb_export.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 导出完成: {len(all_memories)} 条记忆 to {output_filename}")
    return export_data

if __name__ == "__main__":
    export_vikingdb_data()
