#!/bin/bash

# Quick EC2 Deployment - assumes code is on GitHub
# Run this on your EC2 instance

echo "🚀 Quick deployment from GitHub..."

# Update system and install essentials
sudo apt update && sudo apt install -y python3-pip python3-venv git

# Clone your repository (replace with your actual repo URL)
echo "📥 Cloning from GitHub..."
read -p "Enter your GitHub repo URL: " REPO_URL
git clone $REPO_URL /opt/usheru-sql-agent
cd /opt/usheru-sql-agent

# Create virtual environment and install dependencies
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create environment file
echo "⚙️ Creating environment file..."
cat > .env << EOF
LLM_MODEL=gpt-4o-mini
LLM_PROVIDER=openai
LLM_TEMPERATURE=0
BIGQUERY_PROJECT_ID=your-project-id
BIGQUERY_DATASET=your-dataset
OPENAI_API_KEY=your-openai-api-key
MAX_BYTES_BILLED=1000000000
QUERY_TIMEOUT=30
EOF

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file: nano .env"
echo "2. Upload service_account.json to this directory"
echo "3. Run the app: source venv/bin/activate && python run.py"
echo ""
echo "For production, you can set up nginx/systemd later if needed." 