# EC2 Deployment Guide

## Prerequisites

1. **EC2 Instance**: Ubuntu 22.04 LTS (t3.medium or larger recommended)
2. **Security Group**: Allow inbound traffic on ports 22 (SSH) and 80 (HTTP)
3. **Credentials**: OpenAI API key and BigQuery service account JSON

## Quick Deployment

### Step 1: Connect to your EC2 instance
```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

### Step 2: Upload your code
```bash
# Option A: Using git (if your repo is public)
git clone https://github.com/your-username/usheru-sql-agent.git /tmp/usheru-sql-agent

# Option B: Using SCP to upload from local machine
# Run this from your local machine:
scp -i your-key.pem -r . ubuntu@your-ec2-public-ip:/tmp/usheru-sql-agent
```

### Step 3: Run the deployment script
```bash
# Copy files to the deployment location
sudo cp -r /tmp/usheru-sql-agent /opt/
sudo chown -R $USER:$USER /opt/usheru-sql-agent
cd /opt/usheru-sql-agent

# Make the deployment script executable and run it
chmod +x deploy.sh
./deploy.sh
```

### Step 4: Configure credentials
```bash
# Edit environment variables
nano /opt/usheru-sql-agent/.env

# Upload your service account JSON
# From your local machine:
scp -i your-key.pem service_account.json ubuntu@your-ec2-public-ip:/opt/usheru-sql-agent/
```

### Step 5: Start services
```bash
sudo systemctl start usheru-sql-agent
sudo systemctl start nginx
```

### Step 6: Verify deployment
```bash
# Check service status
sudo systemctl status usheru-sql-agent
sudo systemctl status nginx

# Test the application
curl http://localhost/
```

## Environment Variables

Create `/opt/usheru-sql-agent/.env` with:

```env
# Model settings
LLM_MODEL=gpt-4o-mini
LLM_PROVIDER=openai
LLM_TEMPERATURE=0

# BigQuery settings
BIGQUERY_PROJECT_ID=your-actual-project-id
BIGQUERY_DATASET=your-actual-dataset

# API settings
OPENAI_API_KEY=your-actual-openai-api-key

# Query settings
MAX_BYTES_BILLED=1000000000
QUERY_TIMEOUT=30
```

## Service Management

```bash
# Start/stop/restart the application
sudo systemctl start usheru-sql-agent
sudo systemctl stop usheru-sql-agent
sudo systemctl restart usheru-sql-agent

# View logs
sudo journalctl -u usheru-sql-agent -f

# Nginx management
sudo systemctl restart nginx
sudo nginx -t  # Test configuration
```

## Troubleshooting

### Application won't start
```bash
# Check logs
sudo journalctl -u usheru-sql-agent -n 50

# Check if port is in use
sudo netstat -tlnp | grep :8000

# Test manually
cd /opt/usheru-sql-agent
source venv/bin/activate
python wsgi.py
```

### Permission issues
```bash
# Fix ownership
sudo chown -R $USER:$USER /opt/usheru-sql-agent

# Check service account file
ls -la /opt/usheru-sql-agent/service_account.json
```

### BigQuery connection issues
```bash
# Test BigQuery connection
cd /opt/usheru-sql-agent
source venv/bin/activate
python -c "from app.db.connection import get_bigquery_client; print(get_bigquery_client().project)"
```

## SSL/HTTPS Setup (Optional)

For production, consider setting up SSL with Let's Encrypt:

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com

# Auto-renewal is handled by systemd timer
sudo systemctl status certbot.timer
```

## Performance Optimization

For higher traffic:

1. Increase Gunicorn workers in `gunicorn_config.py`
2. Use a larger EC2 instance type
3. Add load balancing with Application Load Balancer
4. Consider using Redis for caching query results 