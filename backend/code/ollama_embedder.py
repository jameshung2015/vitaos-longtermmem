# backend/code/ollama_embedder.py
import requests
import numpy as np
from typing import List, Union

class OllamaEmbedder:
    def __init__(self, model: str = "nomic-embed-text", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/embeddings"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量文档嵌入"""
        embeddings = []
        for text in texts:
            embedding = self._embed_single(text)
            embeddings.append(embedding)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """单个查询嵌入"""
        return self._embed_single(text)

    def _embed_single(self, text: str) -> List[float]:
        """单个文本嵌入"""
        payload = {
            "model": self.model,
            "prompt": text
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result["embedding"]
        except requests.RequestException as e:
            raise Exception(f"Ollama嵌入服务调用失败: {e}")

    def health_check(self) -> bool:
        """健康检查"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
