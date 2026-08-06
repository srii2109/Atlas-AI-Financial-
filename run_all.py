# Python 3.14 compatibility monkeypatch for protobuf upb c-extension
import builtins
import importlib

original_import = builtins.__import__
def custom_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name and "google._upb" in name:
        raise ImportError("google._upb is disabled for Python 3.14 compatibility")
    if fromlist:
        for f in fromlist:
            if f == "_upb":
                raise ImportError("google._upb is disabled for Python 3.14 compatibility")
    return original_import(name, globals, locals, fromlist, level)
builtins.__import__ = custom_import

original_import_module = importlib.import_module
def custom_import_module(name, package=None):
    if name and "google._upb" in name:
        raise ImportError("google._upb is disabled for Python 3.14 compatibility")
    return original_import_module(name, package)
importlib.import_module = custom_import_module

import subprocess
import sys
import time

def main():
    print("==================================================")
    print("Starting Atlas AI Financial Assistant System...")
    print("==================================================")

    # 1. Start FastAPI Web Server
    print("Launching FastAPI Web Server (server.py)...")
    server_process = subprocess.Popen([sys.executable, "server.py"])

    # Give the server 3 seconds to bind to the port
    time.sleep(3)

    # 2. Start Telegram Bot Poller
    print("Launching Telegram Bot Poller (bot.py)...")
    bot_process = subprocess.Popen([sys.executable, "bot.py"])

    print("Both processes are running. Monitoring status...")
    print("==================================================")

    try:
        # Keep main process alive and monitor subprocesses
        while True:
            # Check if any process has terminated
            server_status = server_process.poll()
            bot_status = bot_process.poll()

            if server_status is not None:
                print(f"Warning: FastAPI server stopped with code {server_status}. Restarting...")
                server_process = subprocess.Popen([sys.executable, "server.py"])
                time.sleep(3)

            if bot_status is not None:
                print(f"Warning: Telegram bot stopped with code {bot_status}. Restarting...")
                bot_process = subprocess.Popen([sys.executable, "bot.py"])
                time.sleep(3)

            time.sleep(5)
            
    except KeyboardInterrupt:
        print("Shutting down subprocesses...")
        server_process.terminate()
        bot_process.terminate()
        server_process.wait()
        bot_process.wait()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
