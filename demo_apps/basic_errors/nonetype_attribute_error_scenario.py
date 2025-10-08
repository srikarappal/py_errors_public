try:
    import thinking_sdk_client as thinking
except ImportError:
    sys.exit(1)

thinking.start(config_file="thinkingsdk.yaml")

names = []
names = names.append("Ada")   # .append returns None
print(len(names))             # TypeError: object of type 'NoneType' has no len()
