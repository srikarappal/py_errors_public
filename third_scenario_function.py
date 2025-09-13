try:
    import thinking_sdk_client as thinking
    print("✅ ThinkingSDK Client imported successfully")
except ImportError:
    print("❌ ThinkingSDK Client not found. Run: pip install -r requirements.txt")
    sys.exit(1)

thinking.start(config_file="thinkingsdk.yaml")

def test_none_type_error():
    names = []
    names = names.append("Ada")   # .append returns None
    print(len(names))             # TypeError: object of type 'NoneType' has no len()

test_none_type_error()