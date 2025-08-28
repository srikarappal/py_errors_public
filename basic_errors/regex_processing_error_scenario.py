try:
    import thinking_sdk_client as thinking
    print("✅ ThinkingSDK Client imported successfully")
except ImportError:
    print("❌ ThinkingSDK Client not found. Run: pip install -r requirements.txt")
    sys.exit(1)

thinking.start(config_file="thinkingsdk.yaml")



import re
m = re.match(r"id=(\d+)", "prefix id=42")  # match anchors at start of string
print(m.group(1))  # AttributeError: 'NoneType' object has no attribute 'group'

