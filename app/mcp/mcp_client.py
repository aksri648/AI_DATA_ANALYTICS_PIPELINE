import json
import subprocess
from typing import Any

import requests

from app.utils.logging import logger


class MCPClient:
    def __init__(self, transport: str = "stdio", command: str | None = None, url: str | None = None):
        self.transport = transport
        self.command = command
        self.url = url
        self._process = None

    def start_stdio(self):
        if not self.command:
            raise ValueError("Command required for stdio transport")
        self._process = subprocess.Popen(
            self.command.split(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def send_request(self, request: dict[str, Any]) -> dict[str, Any]:
        if self.transport == "stdio":
            return self._send_stdio(request)
        elif self.transport == "http":
            return self._send_http(request)
        raise ValueError(f"Unknown transport: {self.transport}")

    def _send_stdio(self, request: dict[str, Any]) -> dict[str, Any]:
        if not self._process:
            self.start_stdio()
        self._process.stdin.write(json.dumps(request) + "\n")
        self._process.stdin.flush()
        response = self._process.stdout.readline()
        return json.loads(response.strip())

    def _send_http(self, request: dict[str, Any]) -> dict[str, Any]:
        resp = requests.post(self.url, json=request, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def list_tools(self) -> list[dict[str, Any]]:
        response = self.send_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        })
        return response.get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        response = self.send_request({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        })
        content = response.get("result", {}).get("content", [])
        if content:
            text = content[0].get("text", "{}")
            return json.loads(text)
        return {"error": "No content in response"}

    def close(self):
        if self._process:
            self._process.terminate()
            self._process = None
