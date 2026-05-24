import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.utils.logging import logger
from app.llm.ollama_service import ollama_service
from app.mcp.mcp_server import main as mcp_main


def check_environment():
    logger.info("Checking environment...")
    if not ollama_service.check_health():
        logger.warning("Ollama is not running. Start with: ollama serve")
        return False
    models = ollama_service.list_models()
    if not models:
        logger.warning("No Ollama models found. Pull one with: ollama pull qwen2.5:14b")
        return False
    logger.info(f"Available models: {', '.join(models)}")
    return True


def run_streamlit():
    import subprocess, os
    port = os.environ.get("PORT", "8501")
    cmd = ["streamlit", "run", "app/ui/app.py", f"--server.port={port}", "--server.address=0.0.0.0"]
    logger.info(f"Starting Streamlit: {' '.join(cmd)}")
    subprocess.run(cmd)


def run_mcp_server(transport: str = "stdio"):
    logger.info(f"Starting MCP server ({transport})...")
    sys.argv = [sys.argv[0]]
    if transport == "http":
        sys.argv.extend(["http", "9000"])
    mcp_main()


def main():
    parser = argparse.ArgumentParser(description="AI Analytics & ETL Copilot")
    parser.add_argument("mode", nargs="?", default="ui", choices=["ui", "mcp", "check"],
                        help="Run mode: ui (Streamlit), mcp (MCP server), check (environment)")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "http"],
                        help="MCP transport (default: stdio)")
    args = parser.parse_args()

    if args.mode == "check":
        check_environment()
        return

    if args.mode == "mcp":
        run_mcp_server(args.transport)
        return

    check_environment()
    run_streamlit()


if __name__ == "__main__":
    main()
