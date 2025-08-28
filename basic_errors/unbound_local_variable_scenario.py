# Load environment variables from .env file
try:
    import thinking_sdk_client as thinking
    print("✅ ThinkingSDK Client imported successfully")
except ImportError:
    print("❌ ThinkingSDK Client not found. Run: pip install -r requirements.txt")
    sys.exit(1)

thinking.start(config_file="thinkingsdk.yaml")



x = 10

def bump():
    x = x + 1      # UnboundLocalError: local variable 'x' referenced before assignment
    return x

bump()  # Let the automatic exit handler flush events
