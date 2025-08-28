"""
Command line code to process JSON data.
"""
import sys
import os

try:
    import thinking_sdk_client as thinking
    print("✅ ThinkingSDK Client imported successfully")
except ImportError:
    print("❌ ThinkingSDK Client not found. Run: pip install -r requirements.txt")
    sys.exit(1)

thinking.start(config_file="thinkingsdk.yaml")

import json
import os
import argparse
import logging
from pathlib import Path

def main():
    """
    Main function to execute the script logic.
    """
    print("Hello, World!")

    data = {}
    p = Path("first_scenario_parsing_config.json")
    if not p.exists():
        print(f"File {p} does not exist.")
        sys.exit(1)

    try:
        # Load JSON data from the file
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"🔥 Exception occurred: {e}")
        print("🔄 Stopping ThinkingSDK to flush events...")
        thinking.stop()  # Stop and flush events
        print("⏳ ThinkingSDK stopped - events should be sent")
        raise  # Re-raise the exception

    

if __name__ == "__main__":
    # Entry point of the script
    main()
