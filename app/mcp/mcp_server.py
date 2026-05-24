import json
import sys
import traceback
from typing import Any

from app.mcp.tools import MCPTools
from app.utils.logging import setup_logger

logger = setup_logger("mcp_server", use_stderr=True)


class MCPServer:
    def __init__(self):
        self.tools = MCPTools

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        method = request.get("method")
        req_id = request.get("id")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "0.1.0",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "ai-analytics-mcp", "version": "1.0.0"},
                },
            }

        if method == "notifications/initialized":
            return None

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.tools.get_tool_definitions()},
            }

        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            try:
                result = self.tools.execute_tool(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]
                    },
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": str(e), "data": traceback.format_exc()},
                }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }

    def run_stdio(self):
        logger.info("MCP Server running on stdio transport")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                if response is not None:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
            except json.JSONDecodeError:
                error = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
                sys.stdout.write(json.dumps(error) + "\n")
                sys.stdout.flush()

    def run_http(self, host: str = "0.0.0.0", port: int = 9000):
        from http.server import HTTPServer, BaseHTTPRequestHandler

        class MCPHTTPHandler(BaseHTTPRequestHandler):
            server_instance = self

            def do_POST(self):
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                try:
                    request = json.loads(body)
                    response = self.server_instance.handle_request(request)
                    if response is None:
                        response = {"jsonrpc": "2.0", "id": None, "result": {}}
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())

            def log_message(self, format, *args):
                pass

        server = HTTPServer((host, port), MCPHTTPHandler)
        logger.info(f"MCP HTTP Server running on http://{host}:{port}")
        server.serve_forever()


def main():
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    server = MCPServer()
    if mode == "http":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 9000
        server.run_http(port=port)
    else:
        server.run_stdio()


if __name__ == "__main__":
    main()
