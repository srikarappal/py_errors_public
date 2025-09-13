# Load environment variables from .env file
try:
    import thinking_sdk_client as thinking
except ImportError:
    sys.exit(1)

thinking.start(config_file="thinkingsdk.yaml")

x = 10

def bump():
    x = x + 1
    return x

bump()
