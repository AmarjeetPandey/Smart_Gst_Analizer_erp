# SmartGST AI ERP - Deployment Guide

## Deployment Options

### 1. Local Development
### 2. Docker Deployment
### 3. Cloud Deployment (AWS, GCP, Azure)
### 4. Manual Server Deployment

---

## Option 1: Local Development

### Requirements
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- Redis 6+

### Installation Steps

#### Backend Setup
```bash
cd backend
python -m venv venv

# Activate virtual environment
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env with your settings

# Run migrations (when available)
alembic upgrade head

# Start server
uvicorn main:app --reload --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev  # Port 3000
```

---

## Option 2: Docker Deployment (Recommended)

### Prerequisites
- Docker 20+
- Docker Compose 2+

### Quick Start

#### 1. Clone Repository
```bash
git clone <repository-url>
cd smartgst-erp
```

#### 2. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env

# Set important values:
# - DATABASE_URL
# - REDIS_URL
# - SECRET_KEY
# - SMTP credentials
```

#### 3. Build Images
```bash
cd docker
docker-compose build
```

#### 4. Start Services
```bash
docker-compose up -d
```

#### 5. Check Status
```bash
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### 6. Access Application
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

### Docker Commands Reference

```bash
# Start containers
docker-compose up -d

# Stop containers
docker-compose down

# View logs
docker-compose logs -f

# Rebuild images
docker-compose build --no-cache

# Execute command in container
docker-compose exec backend python script.py

# Backup database
docker-compose exec postgres pg_dump smartgst_db > backup.sql

# Restore database
docker-compose exec postgres psql smartgst_db < backup.sql
```

---

## Option 3: Cloud Deployment

### AWS Deployment

#### Using EC2

**1. Launch EC2 Instance**
- AMI: Ubuntu 22.04 LTS
- Instance Type: t3.medium (minimum)
- Storage: 50GB EBS
- Security Group: Allow 80, 443, 8000, 3000

**2. SSH into Instance**
```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

**3. Install Docker**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
```

**4. Deploy Application**
```bash
# Clone repository
git clone <repository-url>
cd smartgst-erp

# Configure environment
nano .env

# Start with Docker Compose
cd docker
docker-compose up -d
```

#### Using ECS (Elastic Container Service)

**1. Create ECR Repositories**
```bash
aws ecr create-repository --repository-name smartgst-backend
aws ecr create-repository --repository-name smartgst-frontend
```

**2. Build and Push Images**
```bash
# Build backend
docker build -t smartgst-backend -f docker/Dockerfile.backend .
docker tag smartgst-backend:latest <account>.dkr.ecr.<region>.amazonaws.com/smartgst-backend:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/smartgst-backend:latest

# Build frontend
docker build -t smartgst-frontend -f docker/Dockerfile.frontend .
docker tag smartgst-frontend:latest <account>.dkr.ecr.<region>.amazonaws.com/smartgst-frontend:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/smartgst-frontend:latest
```

**3. Create ECS Cluster and Services**
```bash
# Create cluster
aws ecs create-cluster --cluster-name smartgst

# Register task definitions and create services
# Use AWS Console for more control
```

### Google Cloud Platform (GCP)

**1. Create Compute Engine Instance**
```bash
gcloud compute instances create smartgst \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --machine-type=e2-medium \
  --zone=us-central1-a
```

**2. SSH and Deploy**
```bash
gcloud compute ssh smartgst --zone=us-central1-a

# Follow Docker deployment steps
```

### Azure Deployment

**1. Create Resource Group**
```bash
az group create \
  --name smartgst-rg \
  --location eastus
```

**2. Create Container Instance**
```bash
az container create \
  --resource-group smartgst-rg \
  --name smartgst \
  --image smartgst-backend:latest \
  --cpu 2 \
  --memory 4
```

---

## Option 4: Manual Server Deployment

### Production Checklist

- [ ] Server setup (Linux)
- [ ] Install dependencies
- [ ] Configure firewall
- [ ] Setup SSL/TLS
- [ ] Configure reverse proxy (Nginx)
- [ ] Setup systemd services
- [ ] Configure monitoring
- [ ] Setup backups

### Step-by-Step

#### 1. Server Setup (Ubuntu 22.04)

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y \
  python3.11 \
  python3-pip \
  nodejs \
  npm \
  postgresql \
  postgresql-contrib \
  redis-server \
  nginx \
  certbot \
  python3-certbot-nginx

# Create application user
sudo useradd -m -s /bin/bash smartgst
sudo su - smartgst
```

#### 2. Clone Repository
```bash
git clone <repository-url>
cd smartgst-erp
```

#### 3. Backend Setup
```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
nano .env

# Create systemd service
sudo tee /etc/systemd/system/smartgst-backend.service << EOF
[Unit]
Description=SmartGST Backend
After=network.target postgresql.service redis-server.service

[Service]
User=smartgst
WorkingDirectory=/home/smartgst/smartgst-erp/backend
Environment="PATH=/home/smartgst/smartgst-erp/backend/venv/bin"
ExecStart=/home/smartgst/smartgst-erp/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable smartgst-backend
sudo systemctl start smartgst-backend
```

#### 4. Frontend Setup
```bash
cd ../frontend

# Install dependencies
npm ci

# Build
npm run build

# Create systemd service for serving
sudo tee /etc/systemd/system/smartgst-frontend.service << EOF
[Unit]
Description=SmartGST Frontend
After=network.target

[Service]
User=smartgst
WorkingDirectory=/home/smartgst/smartgst-erp/frontend
ExecStart=/usr/bin/npx serve -s dist -l 3000

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable smartgst-frontend
sudo systemctl start smartgst-frontend
```

#### 5. Nginx Reverse Proxy
```bash
sudo tee /etc/nginx/sites-available/smartgst << EOF
upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # API
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/smartgst /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

#### 6. SSL Certificate
```bash
sudo certbot certonly --nginx -d your-domain.com
```

#### 7. Database Setup
```bash
# Create database
sudo -u postgres createdb smartgst_db

# Run migrations
cd backend
source venv/bin/activate
alembic upgrade head
```

---

## Performance Optimization

### Database Optimization
```bash
# Connection pooling
SQLALCHEMY_POOL_SIZE=20
SQLALCHEMY_MAX_OVERFLOW=40

# Query optimization
Enable query logging
Add indexes
```

### Caching
```bash
# Redis cache
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### CDN Setup
- CloudFront (AWS)
- Cloudflare
- Bunny CDN

---

## Monitoring & Logging

### Application Monitoring
```bash
# Install monitoring tools
pip install prometheus-client grafana-api

# Configure in app
```

### Log Management
```bash
# Centralized logging
Install ELK Stack or Splunk
Configure log forwarding
```

### Performance Monitoring
```bash
# Monitor with
New Relic
Datadog
CloudWatch
```

---

## Backup & Recovery

### Automated Backups

**Database Backup**
```bash
# Daily backup script
0 2 * * * pg_dump smartgst_db | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz
```

**File Backup**
```bash
# Weekly backup
0 3 * * 0 tar -czf /backups/app_$(date +\%Y\%m\%d).tar.gz /home/smartgst/smartgst-erp
```

### Recovery Procedure
```bash
# Restore database
gunzip /backups/db_backup.sql.gz
psql smartgst_db < /backups/db_backup.sql

# Restore files
tar -xzf /backups/app_backup.tar.gz
```

---

## Security Hardening

### Firewall Setup
```bash
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### SSH Security
```bash
# Disable password authentication
PermitRootLogin no
PasswordAuthentication no

# Use SSH keys only
```

### Environment Variables
```bash
# Never commit .env
# Store secrets in:
# - AWS Secrets Manager
# - Google Secret Manager
# - Azure Key Vault
```

### HTTPS/TLS
```bash
# Use strong certificates
# Update certbot frequently
sudo certbot renew --dry-run
```

---

## Scaling Strategies

### Horizontal Scaling
- Load balancer (Nginx, HAProxy)
- Multiple backend instances
- Database replication

### Vertical Scaling
- Increase server resources
- Optimize database
- Cache more aggressively

### Microservices
- Separate ML models
- Async tasks with Celery
- API gateway pattern

---

## Troubleshooting

### Backend Issues
```bash
# Check service status
sudo systemctl status smartgst-backend

# View logs
sudo journalctl -u smartgst-backend -f

# Database connection
psql -h localhost -U postgres -d smartgst_db
```

### Frontend Issues
```bash
# Check frontend service
sudo systemctl status smartgst-frontend

# Build logs
npm run build

# Check Nginx
sudo nginx -t
sudo systemctl status nginx
```

### Common Issues
- Port already in use
- Database connection refused
- Permission denied
- Out of disk space
- Memory issues

---

## Maintenance

### Regular Tasks
- Database optimization
- Log rotation
- Security patches
- Dependency updates
- Backup verification

### Updates
```bash
# Update Python packages
pip list --outdated
pip install --upgrade package-name

# Update Node packages
npm outdated
npm update
```

---

## Support & Documentation

- **API Docs**: http://your-domain.com/api/docs
- **GitHub**: Your repository
- **Issues**: Issue tracker
- **Documentation**: Online docs

---

For questions or issues, refer to the main [README.md](../README.md).
