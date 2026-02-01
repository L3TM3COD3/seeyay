"""
Development script to run both backend and bot
"""
import subprocess
import sys
import os
from pathlib import Path


def main():
    print("🚀 Starting СИЯЙ AI Development Environment")
    print("=" * 50)
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found!")
        print("Please create .env file with the following variables:")
        print("""
BOT_TOKEN=your_telegram_bot_token
GOOGLE_AI_API_KEY=your_google_ai_api_key
BACKEND_URL=http://localhost:8000
MINI_APP_URL=https://your-domain.com
DATABASE_URL=sqlite+aiosqlite:///./seeyay.db
        """)
        return
    
    print("\n📦 Starting Backend (FastAPI)...")
    print("   URL: http://localhost:8000")
    print("   Docs: http://localhost:8000/docs")
    
    print("\n🤖 Starting Telegram Bot...")
    print("   Make sure BOT_TOKEN is set in .env")
    
    print("\n📱 To start Mini App development server:")
    print("   cd mini-app && npm install && npm run dev")
    print("   URL: http://localhost:3000")
    
    print("\n" + "=" * 50)
    print("Press Ctrl+C to stop all services")
    print("=" * 50 + "\n")
    
    # Start backend
    try:
        # Run backend
        backend_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            cwd=os.getcwd()
        )
        
        # Run bot
        bot_process = subprocess.Popen(
            [sys.executable, "-m", "bot.main"],
            cwd=os.getcwd()
        )
        
        # Wait for processes
        backend_process.wait()
        bot_process.wait()
        
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        backend_process.terminate()
        bot_process.terminate()
        print("✅ All services stopped")


if __name__ == "__main__":
    main()
