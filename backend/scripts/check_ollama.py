# backend/scripts/check_ollama.py
import requests
import json

def check_ollama_service():
    """检查Ollama服务状态"""

    base_url = "http://localhost:11434"

    try:
        # 检查服务状态
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama服务运行正常")

            # 列出已安装模型
            models = response.json().get("models", [])
            print(f"📦 已安装模型数量: {len(models)}")

            for model in models:
                name = model.get("name", "unknown")
                size = model.get("size", 0) / (1024**3)  # 转换为GB
                print(f"  - {name} ({size:.2f}GB)")

            return True
        else:
            print("❌ Ollama服务异常")
            return False

    except requests.RequestException as e:
        print(f"❌ Ollama服务连接失败: {e}")
        return False

def test_embedding():
    """测试嵌入功能"""

    base_url = "http://localhost:11434"
    model = "nomic-embed-text" # Ensure this model name matches config
    test_text = "这是一个测试文本"

    payload = {
        "model": model,
        "prompt": test_text
    }

    try:
        response = requests.post(f"{base_url}/api/embeddings", json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            embedding = result.get("embedding", [])
            print(f"✅ 嵌入测试成功")
            print(f"📊 向量维度: {len(embedding)}")
            print(f"🎯 向量范例: {embedding[:5]}...")
            return True
        else:
            print(f"❌ 嵌入测试失败: {response.text}")
            return False

    except requests.RequestException as e:
        print(f"❌ 嵌入服务调用失败: {e}")
        return False

if __name__ == "__main__":
    print("🔍 检查Ollama服务...")
    service_ok = check_ollama_service()

    if service_ok:
        print("\n🧪 测试嵌入功能...")
        test_embedding()
    else:
        print("\n💡 请先启动Ollama服务:")
        print("   systemctl start ollama")
        print("   ollama pull nomic-embed-text") # Or the configured model
