# backend/scripts/init_chroma.py
import chromadb
from chromadb.config import Settings
import os

def init_chroma_db():
    """初始化Chroma数据库"""

    # 创建数据目录
    db_path = "./chroma_db"
    os.makedirs(db_path, exist_ok=True)

    # 配置Chroma客户端
    client = chromadb.PersistentClient(
        path=db_path,
        settings=Settings(
            allow_reset=True,
            anonymized_telemetry=False
        )
    )

    # 创建集合
    collection = client.get_or_create_collection(
        name="longterm_memory_local",
        metadata={"description": "长期记忆本地向量存储"}
    )

    print(f"✅ Chroma数据库初始化完成")
    print(f"📁 存储路径: {os.path.abspath(db_path)}")
    print(f"📊 集合名称: {collection.name}")
    print(f"📈 当前文档数: {collection.count()}")

    return client, collection

if __name__ == "__main__":
    init_chroma_db()
