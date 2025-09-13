#!/usr/bin/env python3
"""
Setup script for ThinkingSDK E2E Testing Environment

This script helps set up the testing environment with proper API keys and configuration.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from dotenv import load_dotenv, set_key

def check_python_version():
    """Ensure Python 3.8+ is being used."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def setup_virtual_environment():
    """Create and activate virtual environment if needed."""
    venv_path = Path("venv")
    
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")
    
    # Provide activation instructions
    if os.name == 'nt':  # Windows
        activate_script = venv_path / "Scripts" / "activate.bat"
    else:  # Unix/macOS
        activate_script = venv_path / "bin" / "activate"
    
    print(f"💡 Activate with: source {activate_script}")

def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e.stderr}")
        sys.exit(1)

def setup_environment_file():
    """Setup .env file with user input."""
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        load_dotenv()
        
        # Check if critical values are set
        api_key = os.getenv('THINKINGSDK_API_KEY')
        if not api_key or api_key.strip() == '':
            print("⚠️  THINKINGSDK_API_KEY not set in .env")
            setup_api_key()
        else:
            print(f"✅ API key configured: {api_key[:20]}...")
    else:
        print("🔧 Setting up .env file...")
        setup_api_key()

def setup_api_key():
    """Interactive API key setup."""
    print("\n🔑 API Key Setup:")
    print("1. Visit http://localhost:3000/dashboard")  
    print("2. Sign in with your Google account")
    print("3. Click 'Generate API Key' in the dashboard")
    print("4. Copy the generated key")
    
    api_key = input("\nPaste your ThinkingSDK API key: ").strip()
    
    if not api_key.startswith('sk_live_'):
        print("⚠️  API key should start with 'sk_live_'")
        print("   Continuing anyway...")
    
    # Save to .env file
    set_key('.env', 'THINKINGSDK_API_KEY', api_key)
    print("✅ API key saved to .env")

def setup_github_token():
    """Setup GitHub token for PR/Issue creation testing."""
    github_token = os.getenv('GITHUB_TEST_TOKEN')
    
    if not github_token:
        print("\n🐙 GitHub Integration Setup (Optional):")
        print("1. Go to https://github.com/settings/tokens")
        print("2. Create token with 'repo' permissions")
        print("3. Paste token below (or press Enter to skip)")
        
        token = input("GitHub Personal Access Token (optional): ").strip()
        
        if token:
            set_key('.env', 'GITHUB_TEST_TOKEN', token)
            
            repo = input("Test repository (format: username/repo): ").strip()
            if repo:
                set_key('.env', 'TEST_GITHUB_REPO', repo)
            
            print("✅ GitHub integration configured")
        else:
            print("ℹ️  GitHub integration skipped")
    else:
        print("✅ GitHub token already configured")

def verify_server_connection():
    """Verify ThinkingSDK server is running."""
    server_url = os.getenv('THINKING_SDK_SERVER_URL', 'http://localhost:8000')
    
    try:
        import requests
        response = requests.get(f"{server_url}/health", timeout=5)
        
        if response.status_code == 200:
            print(f"✅ ThinkingSDK server is running at {server_url}")
            return True
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Cannot connect to ThinkingSDK server: {e}")
        print(f"   Make sure server is running: uvicorn thinking_sdk_server.server:app --reload")
        return False

def main():
    print("🧪 ThinkingSDK E2E Testing Setup")
    print("=" * 50)
    
    check_python_version()
    setup_virtual_environment()
    install_dependencies()
    setup_environment_file()
    setup_github_token()
    
    print("\n🔍 Verifying setup...")
    server_ok = verify_server_connection()
    
    print("\n🎉 Setup Complete!")
    print("\nNext steps:")
    print("1. Start ThinkingSDK server (if not running):")
    print("   cd ../thinkingSDK/thinking_sdk_server")
    print("   uvicorn thinking_sdk_server.server:app --reload")
    print()
    print("2. Run test scenarios:")
    print("   python test_runner.py --list")
    print("   python test_runner.py --scenario payment_processing_error")
    print("   python test_runner.py --all")

if __name__ == "__main__":
    main()
