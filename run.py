#!/usr/bin/env python3
"""
Start the BigQuery SQL Agent
"""

import os
import sys
import uvicorn
import argparse
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🚀 Starting BigQuery SQL Agent")
    print("=" * 50)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    
    # Set default values for BigQuery (update these for your project)
    os.environ.setdefault("BIGQUERY_PROJECT_ID", "cogent-tine-87309")
    os.environ.setdefault("BIGQUERY_DATASET", "usheru_data_mart")
    
    # Check required environment variables
    required = ["OPENAI_API_KEY"]  # Only OpenAI key is truly required now
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("📝 Set your OpenAI API key:")
        print("   - Windows: set OPENAI_API_KEY=your-key")
        print("   - Linux/Mac: export OPENAI_API_KEY=your-key")
        print("   - Or create a .env file with OPENAI_API_KEY=your-key")
        sys.exit(1)
    
    # Check service account file in project root
    if not os.path.exists("service_account.json"):
        print("❌ service_account.json file not found")
        print()
        print("📁 Place your BigQuery service account JSON file here:")
        print(f"   {os.path.abspath('.')}/service_account.json")
        print()
        print("💡 How to get the service account file:")
        print("   1. Go to Google Cloud Console")
        print("   2. Navigate to IAM & Admin > Service Accounts")
        print("   3. Create or select a service account")
        print("   4. Click 'Keys' > 'Add Key' > 'Create New Key'")
        print("   5. Choose JSON format and download")
        print("   6. Rename the file to 'service_account.json'")
        print("   7. Place it in the project root directory")
        sys.exit(1)
    
    print(f"✅ Environment variables configured")
    print(f"✅ Service account file found")
    print(f"📊 Project: {os.getenv('BIGQUERY_PROJECT_ID')}")
    print(f"📋 Dataset: {os.getenv('BIGQUERY_DATASET')}")
    print()
    print("🌐 Starting server on http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=args.port,
        reload=True
    )

if __name__ == "__main__":
    main() 