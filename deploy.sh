#!/bin/bash

# EC2 Deployment Script for UsherU SQL Agent
# Run this script on your EC2 instance

set -e  # Exit on any error

echo "🚀 Starting deployment of UsherU SQL Agent..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.11 and required packages
echo "🐍 Installing Python and dependencies..."
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip git nginx supervisor

# Create application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /opt/usheru-sql-agent
sudo chown $USER:$USER /opt/usheru-sql-agent
cd /opt/usheru-sql-agent

# Clone or copy your application
echo "📥 Getting application code..."
# If using git:
# git clone <your-repo-url> .
# If copying files, you'll need to upload them first

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Set up environment variables
echo "⚙️ Setting up environment variables..."
cat > .env << EOF
# Model settings
LLM_MODEL=gpt-4o-mini
LLM_PROVIDER=openai
LLM_TEMPERATURE=0

# BigQuery settings
BIGQUERY_PROJECT_ID=your-project-id
BIGQUERY_DATASET=your-dataset

# API settings
OPENAI_API_KEY=your-openai-api-key

# Query settings
MAX_BYTES_BILLED=1000000000
QUERY_TIMEOUT=30

# Server settings
HOST=0.0.0.0
PORT=8000
EOF

echo "⚠️  Please edit /opt/usheru-sql-agent/.env with your actual credentials"

# Upload service account JSON
echo "🔑 Please upload your service_account.json file to /opt/usheru-sql-agent/"

# Create Gunicorn configuration
echo "🔧 Setting up Gunicorn configuration..."
cat > gunicorn_config.py << EOF
bind = "0.0.0.0:8000"
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 60
keepalive = 5
preload_app = True
capture_output = True
enable_stdio_inheritance = True
EOF

# Create systemd service file
echo "🔧 Setting up systemd service..."
sudo tee /etc/systemd/system/usheru-sql-agent.service > /dev/null << EOF
[Unit]
Description=UsherU SQL Agent
After=network.target

[Service]
Type=exec
User=$USER
Group=$USER
WorkingDirectory=/opt/usheru-sql-agent
Environment=PATH=/opt/usheru-sql-agent/venv/bin
ExecStart=/opt/usheru-sql-agent/venv/bin/gunicorn -c gunicorn_config.py run:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Create Nginx configuration
echo "🔧 Setting up Nginx..."
sudo tee /etc/nginx/sites-available/usheru-sql-agent > /dev/null << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/usheru-sql-agent /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Start and enable services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable usheru-sql-agent
sudo systemctl enable nginx

# Create log directories
sudo mkdir -p /var/log/usheru-sql-agent
sudo chown $USER:$USER /var/log/usheru-sql-agent

echo "✅ Deployment setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit /opt/usheru-sql-agent/.env with your credentials"
echo "2. Upload your service_account.json file to /opt/usheru-sql-agent/"
echo "3. Start the services:"
echo "   sudo systemctl start usheru-sql-agent"
echo "   sudo systemctl start nginx"
echo "4. Check status:"
echo "   sudo systemctl status usheru-sql-agent"
echo "   sudo systemctl status nginx"
echo "5. View logs:"
echo "   sudo journalctl -u usheru-sql-agent -f"
echo ""
echo "Your application will be available at http://your-ec2-public-ip/" 