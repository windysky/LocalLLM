# LocalLLM System Administrator Guide

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Service Management](#service-management)
5. [Model Management](#model-management)
6. [Security Considerations](#security-considerations)
7. [Monitoring & Logging](#monitoring--logging)
8. [Performance Tuning](#performance-tuning)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements

- **OS**: Linux (Ubuntu 18.04+, CentOS 7+), macOS (10.15+), or Windows 10+
- **CPU**: 4+ cores for 7B models, 8+ cores for 9B models
- **RAM**: 16GB minimum, 32GB+ recommended
- **Storage**: 100GB+ free disk space for models
- **Network**: 1Gbps+ for model downloads

### Recommended Production Setup

- **OS**: Ubuntu 22.04 LTS or CentOS 8+
- **CPU**: 16+ cores (Intel i7/i9 or AMD Ryzen 7/9)
- **RAM**: 64GB+ DDR4
- **Storage**: 500GB+ NVMe SSD
- **GPU**: NVIDIA RTX 3080/4080 or equivalent with 16GB+ VRAM (optional)
- **Network**: 10Gbps for multi-user access

## Installation

### 1. Install System Dependencies

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip git curl wget
sudo apt install -y build-essential python3-dev
```

#### CentOS/RHEL:
```bash
sudo yum update
sudo yum install -y python3.11 python3-pip git curl wget
sudo yum groupinstall -y "Development Tools"
sudo yum install -y python3-devel
```

### 2. Create Service Account

```bash
sudo useradd -m -s /bin/bash locallm
sudo usermod -aG sudo locallm
```

### 3. Install LocalLLM

```bash
# Clone repository
cd /opt
sudo git clone https://github.com/your-org/LocalLLM.git
sudo chown -R locallm:locallm LocalLLM
cd LocalLLM

# Create virtual environment
sudo -u locallm python3.11 -m venv venv
sudo -u locallm ./venv/bin/pip install --upgrade pip

# Install dependencies
sudo -u locallm ./venv/bin/pip install -r requirements.txt

# Create required directories
sudo -u locallm mkdir -p models logs
```

### 4. Install Ollama

```bash
# As root or with sudo
curl -fsSL https://ollama.ai/install.sh | sh

# Enable and start Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama
sudo systemctl status ollama
```

### 5. Create Systemd Service

Create `/etc/systemd/system/locallm.service`:

```ini
[Unit]
Description=LocalLLM API Server
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=forking
User=locallm
Group=locallm
WorkingDirectory=/opt/LocalLLM
Environment=PATH=/opt/LocalLLM/venv/bin
ExecStart=/opt/LocalLLM/venv/bin/python /opt/LocalLLM/cli/start_server.py --daemon
ExecStop=/opt/LocalLLM/venv/bin/python /opt/LocalLLM/cli/stop_server.py
PIDFile=/opt/LocalLLM/locallm_server.pid
Restart=always
RestartSec=10

# Performance tuning
LimitNOFILE=65536
LimitNPROC=4096

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/LocalLLM/models /opt/LocalLLM/logs

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable locallm
sudo systemctl start locallm
sudo systemctl status locallm
```

## Configuration

### 1. Basic Configuration

Edit `/opt/LocalLLM/config.yaml`:

```yaml
# Server settings
server:
  host: "0.0.0.0"  # Listen on all interfaces
  port: 8000
  workers: 2  # Number of worker processes

# Model settings
models:
  storage_dir: "/opt/LocalLLM/models"
  default_model: ""  # Auto-load on startup
  max_loaded_models: 2  # Adjust based on RAM
  auto_download: true  # Allow auto-download
  supported_formats:
    - "gguf"
    - "safetensors"

# Inference settings
inference:
  device: "auto"  # auto, cpu, cuda, mps
  max_memory: 32  # GB
  context_size: 4096
  temperature: 0.7
  max_tokens: 2048

# Web interface
web:
  enabled: true
  port: 8080
  host: "0.0.0.0"

# Logging
logging:
  level: "INFO"  # DEBUG for detailed logs
  file: "/opt/LocalLLM/logs/locallm.log"
  max_size: "100MB"
  backup_count: 10

# API settings
api:
  openai_compatible: true
  rate_limit: 120  # requests per minute
  cors_enabled: true
  cors_origins:
    - "http://localhost:3000"
    - "http://yourdomain.com"
```

### 2. Environment Variables

Create `/opt/LocalLLM/.env`:

```bash
# Server configuration
DEFAULT_HOST=0.0.0.0
DEFAULT_PORT=8000

# Model directory (ensure sufficient disk space)
MODEL_DIR=/opt/LocalLLM/models

# Device selection
DEVICE=auto  # or cpu, cuda, mps

# Memory limit (GB)
MAX_MEMORY=32

# Hugging Face token (for private models)
HUGGINGFACE_TOKEN=your_token_here

# Logging
LOG_LEVEL=INFO

# Security
API_KEY=your_api_key_here  # Optional: if implementing auth
```

### 3. Network Configuration

#### Firewall Settings (Ubuntu UFW):

```bash
# Allow API and web ports
sudo ufw allow 8000/tcp
sudo ufw allow 8080/tcp
sudo ufw reload
```

#### Nginx Reverse Proxy (Optional but Recommended):

Create `/etc/nginx/sites-available/locallm`:

```nginx
upstream locallm_api {
    server 127.0.0.1:8000;
}

upstream locallm_web {
    server 127.0.0.1:8080;
}

server {
    listen 80;
    server_name llm.yourdomain.com;

    # API endpoints
    location /v1/ {
        proxy_pass http://locallm_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Management endpoints
    location /models/ {
        proxy_pass http://locallm_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health endpoint
    location /health {
        proxy_pass http://locallm_api;
        access_log off;
    }

    # Web interface
    location / {
        proxy_pass http://locallm_web;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/locallm /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Service Management

### Starting/Stopping the Service

```bash
# Using systemd
sudo systemctl start locallm
sudo systemctl stop locallm
sudo systemctl restart locallm
sudo systemctl status locallm

# Using scripts
sudo -u locallm /opt/LocalLLM/venv/bin/python /opt/LocalLLM/cli/start_server.py
sudo -u locallm /opt/LocalLLM/venv/bin/python /opt/LocalLLM/cli/stop_server.py
```

### Checking Logs

```bash
# Systemd logs
sudo journalctl -u locallm -f

# Application logs
sudo tail -f /opt/LocalLLM/logs/locallm.log

# Ollama logs
sudo journalctl -u ollama -f
```

### Configuration Updates

```bash
# After modifying config.yaml
sudo systemctl restart locallm

# Or for hot reload (if implemented)
sudo -u locallm kill -HUP $(cat /opt/LocalLLM/locallm_server.pid)
```

## Model Management

### Downloading Models

```bash
# List available models
sudo -u locallm /opt/LocalLLM/venv/bin/python /opt/LocalLLM/cli/manage_models.py --list

# Download specific model
sudo -u locallm /opt/LocalLLM/venv/bin/python /opt/LocalLLM/cli/manage_models.py --download gemma-2-9b

# Download multiple models
for model in gemma-2-9b qwen2.5-7b mistral-7b; do
    sudo -u locallm /opt/LocalLLM/venv/bin/python /opt/LocalLLM/cli/manage_models.py --download $model
done
```

### Model Storage Management

```bash
# Check disk usage
sudo du -sh /opt/LocalLLM/models/*

# Remove unused models
sudo -u locallm /opt/LocalLLM/venv/bin/python /opt/LocalLLM/cli/manage_models.py --remove old-model

# Move models to external storage (if needed)
sudo mv /opt/LocalLLM/models /mnt/nvme/locallm_models
sudo ln -s /mnt/nvme/locallm_models /opt/LocalLLM/models
```

### Model Pre-loading

Edit `config.yaml` to auto-load models:

```yaml
models:
  default_model: "gemma-2-9b"  # Auto-load on startup
```

Or use CLI:

```bash
sudo -u locallm /opt/LocalLLM/venv/bin/python /opt/LocalLLM/cli/manage_models.py --load gemma-2-9b
```

## Security Considerations

### 1. Network Security

- **Firewall**: Only expose necessary ports (8000, 8080)
- **VPN/Private Network**: Restrict access to trusted networks
- **Reverse Proxy**: Use Nginx for SSL termination and rate limiting

### 2. SSL/TLS Configuration

Generate SSL certificates:

```bash
# Self-signed (for testing)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/locallm.key \
    -out /etc/ssl/certs/locallm.crt

# Let's Encrypt (for production)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d llm.yourdomain.com
```

Update Nginx config for HTTPS:

```nginx
server {
    listen 443 ssl;
    server_name llm.yourdomain.com;

    ssl_certificate /etc/ssl/certs/locallm.crt;
    ssl_certificate_key /etc/ssl/private/locallm.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... rest of configuration
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name llm.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### 3. API Authentication (Optional)

Implement API key authentication:

```python
# Add to src/server.py
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != config.api.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
```

### 4. Resource Limits

Set up cgroups to limit resource usage:

```bash
# Create service limits
sudo systemctl edit locallm

# Add these lines:
[Service]
MemoryLimit=32G
CPUQuota=200%
IOReadBandwidthMax=/opt/LocalLLM/models 100M
IOWriteBandwidthMax=/opt/LocalLLM/models 100M
```

## Monitoring & Logging

### 1. Log Rotation

Create `/etc/logrotate.d/locallm`:

```
/opt/LocalLLM/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 locallm locallm
    postrotate
        systemctl reload locallm
    endscript
}
```

### 2. Monitoring Scripts

Create `/opt/LocalLLM/scripts/monitor.sh`:

```bash
#!/bin/bash
# Monitor script for LocalLLM

API_URL="http://localhost:8000"
LOG_FILE="/opt/LocalLLM/logs/monitor.log"

# Check API health
response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL/health)
if [ $response != "200" ]; then
    echo "$(date): API health check failed (HTTP $response)" >> $LOG_FILE
    systemctl restart locallm
fi

# Check disk space
usage=$(df /opt/LocalLLM/models | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $usage -gt 90 ]; then
    echo "$(date): Model storage at ${usage}%" >> $LOG_FILE
    # Send alert email or notification
fi

# Check memory usage
mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ $mem_usage -gt 90 ]; then
    echo "$(date): Memory usage at ${mem_usage}%" >> $LOG_FILE
fi
```

Make it executable and add to crontab:

```bash
sudo chmod +x /opt/LocalLLM/scripts/monitor.sh
sudo crontab -e
# Add: */5 * * * * /opt/LocalLLM/scripts/monitor.sh
```

### 3. Prometheus Metrics (Optional)

Add metrics endpoint to server:

```python
# Add to src/server.py
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('locallm_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('locallm_request_duration_seconds', 'Request latency')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Performance Tuning

### 1. System Optimization

```bash
# Optimize kernel parameters for high concurrency
echo 'net.core.somaxconn = 65536' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_max_syn_backlog = 65536' >> /etc/sysctl.conf
echo 'vm.swappiness = 10' >> /etc/sysctl.conf
sysctl -p

# Optimize file limits
echo 'locallm soft nofile 65536' >> /etc/security/limits.conf
echo 'locallm hard nofile 65536' >> /etc/security/limits.conf
```

### 2. Database Optimization (if using caching)

```yaml
# Add to config.yaml
cache:
  enabled: true
  backend: "redis"
  redis_url: "redis://localhost:6379/0"
  ttl: 3600  # 1 hour
```

### 3. GPU Acceleration (if available)

```yaml
# Update config.yaml
inference:
  device: "cuda"  # For NVIDIA GPUs
  # or
  device: "mps"   # For Apple Silicon
```

Install CUDA:

```bash
# NVIDIA CUDA
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda
```

## Backup & Recovery

### 1. Configuration Backup

```bash
#!/bin/bash
# backup_config.sh

BACKUP_DIR="/backup/locallm"
DATE=$(date +%Y%m%d)

mkdir -p $BACKUP_DIR

# Backup configurations
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    /opt/LocalLLM/config.yaml \
    /opt/LocalLLM/.env \
    /etc/systemd/system/locallm.service \
    /etc/nginx/sites-available/locallm

# Keep last 30 days
find $BACKUP_DIR -name "config_*.tar.gz" -mtime +30 -delete
```

### 2. Model Backup (Optional)

```bash
#!/bin/bash
# backup_models.sh

SOURCE="/opt/LocalLLM/models"
DEST="/backup/locallm/models"

# Use rsync for incremental backup
rsync -av --delete $SOURCE/ $DEST/

# Compress old models
find $DEST -name "*.safetensors" -mtime +30 -exec gzip {} \;
```

### 3. Recovery Procedure

```bash
# Restore configuration
sudo systemctl stop locallm
tar -xzf /backup/locallm/config_YYYYMMDD.tar.gz -C /
sudo systemctl daemon-reload
sudo systemctl start locallm

# Verify service
sudo systemctl status locallm
curl http://localhost:8000/health
```

## Troubleshooting

### Common Issues

1. **Service Won't Start**
   ```bash
   # Check logs
   sudo journalctl -u locallm -n 50

   # Check port conflicts
   sudo netstat -tulpn | grep :8000

   # Check permissions
   sudo -u locallm ls -la /opt/LocalLLm/
   ```

2. **Model Loading Fails**
   ```bash
   # Check Ollama status
   sudo systemctl status ollama

   # Check disk space
   df -h /opt/LocalLLM/models

   # Check model files
   sudo -u locallm ls -la /opt/LocalLLM/models/
   ```

3. **High Memory Usage**
   ```bash
   # Check loaded models
   sudo -u locallm /opt/LocalLLM/venv/bin/python /opt/LocalLLM/cli/manage_models.py --loaded

   # Unload unused models
   sudo -u locallm /opt/LocalLLM/venv/bin/python /opt/LocalLLM/cli/manage_models.py --unload model-name
   ```

4. **Slow Performance**
   ```bash
   # Check system resources
   htop
   iotop

   # Check API response time
   curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
   ```

### Performance Debugging

Create `curl-format.txt`:

```
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
```

### Emergency Procedures

1. **Full System Reset**
   ```bash
   # Stop all services
   sudo systemctl stop locallm ollama

   # Clear PID files
   rm -f /opt/LocalLLM/*.pid

   # Clear logs if full
   > /opt/LocalLLM/logs/locallm.log

   # Restart services
   sudo systemctl start ollama
   sudo systemctl start locallm
   ```

2. **Model Corruption Recovery**
   ```bash
   # Remove corrupted model
   sudo -u locallm /opt/LocalLLM/venv/bin/python /opt/LocalLLM/cli/manage_models.py --remove corrupted-model

   # Re-download
   sudo -u locallm /opt/LocalLLM/venv/bin/python /opt/LocalLLM/cli/manage_models.py --download model-name
   ```

### Support and Maintenance

- Regular maintenance window: Sunday 2-4 AM
- Monitoring alerts: Email admin@yourdomain.com
- Emergency contact: +1-555-0123
- Documentation: https://docs.yourdomain.com/locallm
- Source repository: https://github.com/your-org/LocalLLM