import json
import re
from pathlib import Path
from typing import Any

import requests
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM, OllamaEmbeddings

from app.config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_EMBEDDING_MODEL, BASE_DIR
from app.utils.logging import logger

PERSIST_FILE = BASE_DIR / "ollama_config.json"


def load_persisted_url() -> str | None:
    try:
        if PERSIST_FILE.exists():
            data = json.loads(PERSIST_FILE.read_text())
            return data.get("base_url")
    except Exception:
        pass
    return None


def persist_url(url: str):
    try:
        PERSIST_FILE.write_text(json.dumps({"base_url": url}))
    except Exception as e:
        logger.warning(f"Failed to persist Ollama URL: {e}")


class OllamaService:
    def __init__(self, base_url: str | None = None):
        persisted = load_persisted_url()
        self.base_url = base_url or persisted or OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        self.embedding_model = OLLAMA_EMBEDDING_MODEL
        self._llm = None
        self._embeddings = None

    @property
    def llm(self) -> OllamaLLM:
        if self._llm is None:
            self._llm = OllamaLLM(
                model=self.model,
                base_url=self.base_url,
                temperature=0,
            )
        return self._llm

    @property
    def embeddings(self) -> OllamaEmbeddings:
        if self._embeddings is None:
            self._embeddings = OllamaEmbeddings(
                model=self.embedding_model,
                base_url=self.base_url,
            )
        return self._embeddings

    def update_url(self, url: str):
        self.base_url = url
        self._llm = None
        self._embeddings = None
        persist_url(url)

    def set_model(self, model_name: str):
        self.model = model_name
        self._llm = None

    def invoke(self, prompt: str, system_prompt: str | None = None) -> str:
        if system_prompt:
            template = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}"),
            ])
            chain = template | self.llm
            return chain.invoke({"input": prompt})
        return self.llm.invoke(prompt)

    def invoke_json(self, prompt: str, system_prompt: str | None = None) -> dict[str, Any]:
        response = self.invoke(prompt, system_prompt)
        cleaned = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)
        cleaned = re.sub(r"```json\s*", "", cleaned)
        cleaned = re.sub(r"\s*```", "", cleaned)
        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}. Response: {cleaned[:500]}")
            return {"error": "Failed to parse response", "raw": cleaned[:500]}

    def check_health(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    def list_models(self) -> list[str]:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to list models: {e}")
        return []

    def embed_text(self, text: str) -> list[float]:
        return self.embeddings.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embeddings.embed_documents(texts)


ollama_service = OllamaService()
