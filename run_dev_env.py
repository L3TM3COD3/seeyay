"""
Development environment script - uses .env.dev configuration
Runs bot and backend with isolated GCP project

Usage:
    1. Create .env.dev file with dev GCP project
    2. Run: python run_dev_env.py
"""
import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv


def main():
    print("=" * 60)
    print("🔧 СИЯЙ AI - Development Environment")
    print("=" * 60)
    
    env_file = Path(".env.dev")
    if not env_file.exists():
        print("\n❌ .env.dev file not found!")
        print("\nCreate .env.dev with:")
        print("-" * 40)
        print("""
BOT_TOKEN=your_dev_bot_token
GCP_PROJECT_ID=seeyay-ai-dev
GCP_LOCATION=europe-west4
BACKEND_URL=http://localhost:8000
MINI_APP_URL=http://localhost:3000
CLOUDPAYMENTS_PUBLIC_ID=test_api_xxx
CLOUDPAYMENTS_API_SECRET=test_secret_xxx
        """)
        print("-" * 40)
        print("\n💡 Don't forget to:")
        print("   1. Create a new bot via @BotFather for development")
        print("   2. Create GCP project 'seeyay-ai-dev'")
        print("   3. Run: gcloud config set project seeyay-ai-dev")
        return 1
    
    # Load environment variables from .env.dev
    load_dotenv(env_file, override=True)
    
    project_id = os.getenv('GCP_PROJECT_ID')
    backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
    
    print(f"\n✅ Loaded dev configuration")
    print(f"   GCP Project: {project_id}")
    print(f"   Backend: {backend_url}")
    print(f"   Mini App: {os.getenv('MINI_APP_URL', 'http://localhost:3000')}")
    
    # Verify it's not production project
    if project_id == "seeyay-ai-tg-bot":
        print("\n⚠️  WARNING: You're using PRODUCTION project!")
        print("   Change GCP_PROJECT_ID in .env.dev to 'seeyay-ai-dev'")
        confirm = input("   Continue anyway? (yes/no): ")
        if confirm.lower() != "yes":
            print("   Aborted.")
            return 1
    
    print("\n🚀 Starting services...")
    print("=" * 60)
    print("\n💡 Press Ctrl+C to stop\n")
    
    try:
        # Create environment copy
        dev_env = os.environ.copy()
        
        # Start backend
        backend_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"],
            cwd=os.getcwd(),
            env=dev_env
        )
        
        # Start bot
        bot_process = subprocess.Popen(
            [sys.executable, "-m", "bot.main"],
            cwd=os.getcwd(),
            env=dev_env
        )
        
        print("✅ Backend started on http://localhost:8000")
        print("✅ Bot started")
        print("\n📱 To start Mini App: cd mini-app && npm run dev")
        
        # Wait for processes
        backend_process.wait()
        bot_process.wait()
        
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("👋 Shutting down dev environment...")
        print("=" * 60)
        backend_process.terminate()
        bot_process.terminate()
        backend_process.wait()
        bot_process.wait()
        print("✅ Services stopped")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
