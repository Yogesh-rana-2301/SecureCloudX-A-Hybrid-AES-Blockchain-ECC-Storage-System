# Setup

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Running Tests](#running-tests)
5. [Production Deployment](#production-deployment)

---

## Prerequisites

### Required Software

- **Python 3.10 or higher**

  ```bash
  python3 --version
  ```

- **pip** (Python package manager)

  ```bash
  pip --version
  ```

- **Docker** (optional, for containerized deployment)

  ```bash
  docker --version
  ```

- **Git**
  ```bash
  git --version
  ```

### Optional Tools

- **jq** - JSON processor for terminal

  ```bash
  # macOS
  brew install jq

  # Ubuntu/Debian
  sudo apt-get install jq
  ```

- **curl** - For API testing (usually pre-installed)

---

## Local Development Setup

### Option 1: Quick Start Script (Recommended)

#### macOS/Linux

```bash
# Clone the repository
git clone https://github.com/Yogesh-rana-2301/SecureCloudX-A-Hybrid-AES-Blockchain-ECC-Storage-System.git
cd SecureCloudX-A-Hybrid-AES-Blockchain-ECC-Storage-System

# Run the quick start script
./start.sh
```

#### Windows

```cmd
REM Clone the repository
git clone https://github.com/Yogesh-rana-2301/SecureCloudX-A-Hybrid-AES-Blockchain-ECC-Storage-System.git
cd SecureCloudX-A-Hybrid-AES-Blockchain-ECC-Storage-System

REM Run the quick start script
start.bat
```

### Option 2: Manual Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/Yogesh-rana-2301/SecureCloudX-A-Hybrid-AES-Blockchain-ECC-Storage-System.git
   cd SecureCloudX-A-Hybrid-AES-Blockchain-ECC-Storage-System
   ```

2. **Create virtual environment**

   ```bash
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Create necessary directories**

   ```bash
   mkdir -p storage/files blockchain
   ```

5. **Run the application**

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Verify installation**
   Open your browser and navigate to:
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

---

## Docker Deployment

### Option 1: Docker Run

1. **Build the image**

   ```bash
   docker build -t securecloudx:latest .
   ```

2. **Run the container**

   ```bash
   docker run -d \
     -p 8000:8000 \
     -v $(pwd)/storage:/app/storage \
     -v $(pwd)/blockchain:/app/blockchain \
     -v $(pwd)/securecloudx.db:/app/securecloudx.db \
     --name securecloudx-app \
     securecloudx:latest
   ```

3. **View logs**

   ```bash
   docker logs -f securecloudx-app
   ```

4. **Stop the container**
   ```bash
   docker stop securecloudx-app
   docker rm securecloudx-app
   ```

### Option 2: Docker Compose (Recommended)

1. **Start the application**

   ```bash
   docker-compose up -d
   ```

2. **View logs**

   ```bash
   docker-compose logs -f
   ```

3. **Stop the application**

   ```bash
   docker-compose down
   ```

4. **Rebuild after changes**
   ```bash
   docker-compose up -d --build
   ```

### Docker Management Commands

```bash
# Check container status
docker ps

# Check health status
docker inspect securecloudx-app | jq '.[0].State.Health'

# Access container shell
docker exec -it securecloudx-app /bin/bash

# Remove all containers and volumes
docker-compose down -v
```

---

## Running Tests

### 1. Automated System Test

```bash
# Make sure the server is running first
# Then run the test script:

python test_system.py
```

This will test:

- ✅ User registration and ECC keypair generation
- ✅ File upload and AES-256 encryption
- ✅ Blockchain key storage and validation
- ✅ File download and decryption
- ✅ Secure file sharing with ECC
- ✅ Access control

### 2. Manual API Testing

```bash
# Test 1: Health check
curl http://localhost:8000/health

# Test 2: Register user
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser"}'

# Test 3: Upload file
echo "Test content" > test.txt
curl -X POST http://localhost:8000/upload \
  -F "file=@test.txt" \
  -F "owner_id=1"

# Test 4: View blockchain
curl http://localhost:8000/chain | jq '.'
```

### 3. Interactive API Testing

Open the Swagger UI in your browser:

```
http://localhost:8000/docs
```

---

## Production Deployment

### Security Considerations

1. **Use HTTPS**

   - Deploy behind a reverse proxy (Nginx/Traefik)
   - Use SSL/TLS certificates (Let's Encrypt)

2. **Environment Variables**
   Create a `.env` file:

   ```env
   DATABASE_PATH=/secure/path/securecloudx.db
   BLOCKCHAIN_PATH=/secure/path/blockchain/chain.json
   STORAGE_PATH=/secure/path/storage
   SECRET_KEY=your-secret-key-here
   ```

3. **Database Security**

   - Use encrypted filesystem for database
   - Regular backups
   - Access controls

4. **Network Security**
   - Firewall rules
   - Rate limiting
   - DDoS protection

### Deployment with Nginx

1. **Install Nginx**

   ```bash
   sudo apt-get update
   sudo apt-get install nginx
   ```

2. **Configure Nginx** (`/etc/nginx/sites-available/securecloudx`)

   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **Enable site**
   ```bash
   sudo ln -s /etc/nginx/sites-available/securecloudx /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### Deployment with Systemd

Create `/etc/systemd/system/securecloudx.service`:

```ini
[Unit]
Description=SecureCloudX API Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/securecloudx
Environment="PATH=/opt/securecloudx/venv/bin"
ExecStart=/opt/securecloudx/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable securecloudx
sudo systemctl start securecloudx
sudo systemctl status securecloudx
```

### Cloud Deployment Examples

#### AWS EC2

```bash
# 1. Launch EC2 instance (Ubuntu 22.04)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# 3. Install dependencies
sudo apt-get update
sudo apt-get install python3.10 python3-pip git

# 4. Clone and setup
git clone https://github.com/Yogesh-rana-2301/SecureCloudX-A-Hybrid-AES-Blockchain-ECC-Storage-System.git
cd SecureCloudX-A-Hybrid-AES-Blockchain-ECC-Storage-System
pip install -r requirements.txt

# 5. Run with systemd (see above)
```

#### Google Cloud Run

```bash
# 1. Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/securecloudx

# 2. Deploy to Cloud Run
gcloud run deploy securecloudx \
  --image gcr.io/PROJECT-ID/securecloudx \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Heroku

```bash
# 1. Create Procfile
echo "web: uvicorn app.main:app --host 0.0.0.0 --port \$PORT" > Procfile

# 2. Deploy
heroku create your-app-name
git push heroku main
```

---

## Troubleshooting

### Issue: Import errors when running

**Solution:**

```bash
# Make sure you're in the virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate      # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Port 8000 already in use

**Solution:**

```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use a different port
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Issue: Database locked error

**Solution:**

```bash
# Close all connections to the database
# Remove lock file if exists
rm securecloudx.db-journal

# Restart the application
```

### Issue: Blockchain validation fails

**Solution:**

```bash
# Backup current chain
cp blockchain/chain.json blockchain/chain.json.backup

# Delete corrupted chain (will create new genesis block)
rm blockchain/chain.json

# Restart application
```

### Issue: Docker container exits immediately

**Solution:**

```bash
# Check logs
docker logs securecloudx-app

# Common causes:
# 1. Port conflict - change port mapping
# 2. Permission issues - check volume permissions
# 3. Missing dependencies - rebuild image
```

### Issue: File upload fails

**Solution:**

```bash
# Check storage directory permissions
ls -la storage/files/

# Create if missing
mkdir -p storage/files

# Fix permissions
chmod 755 storage/files
```

### Issue: Cannot connect to server

**Solution:**

```bash
# Check if server is running
curl http://localhost:8000/health

# Check firewall
sudo ufw status

# Allow port 8000
sudo ufw allow 8000
```

---

## Performance Tuning

### 1. Use Gunicorn for Production

```bash
# Install gunicorn
pip install gunicorn

# Run with multiple workers
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### 2. Database Optimization

```python
# Add indexes to database.py
cursor.execute('CREATE INDEX idx_files_owner ON files(owner_id)')
cursor.execute('CREATE INDEX idx_shares_recipient ON file_shares(recipient_id)')
```

### 3. Enable Caching

Consider adding Redis for caching frequently accessed data.

---

## Monitoring

### Basic Health Monitoring

```bash
# Create monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash
while true; do
    STATUS=$(curl -s http://localhost:8000/health | jq -r '.status')
    if [ "$STATUS" != "healthy" ]; then
        echo "ALERT: Service unhealthy at $(date)"
        # Send notification
    fi
    sleep 60
done
EOF

chmod +x monitor.sh
./monitor.sh &
```

### Log Management

```bash
# Rotate logs with logrotate
sudo nano /etc/logrotate.d/securecloudx

/var/log/securecloudx/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

---

## Backup & Recovery

### Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/securecloudx"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp securecloudx.db "$BACKUP_DIR/db_$DATE.db"

# Backup blockchain
cp blockchain/chain.json "$BACKUP_DIR/chain_$DATE.json"

# Backup encrypted files
tar -czf "$BACKUP_DIR/files_$DATE.tar.gz" storage/files/

echo "Backup completed: $DATE"
```

### Restore Script

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./restore.sh <backup_file>"
    exit 1
fi

# Stop service
docker-compose down

# Restore files
tar -xzf $BACKUP_FILE

# Start service
docker-compose up -d

echo "Restore completed"
```

---

## Support & Resources

- **Documentation**: http://localhost:8000/docs
- **API Examples**: See `API_EXAMPLES.md`
- **GitHub Issues**: https://github.com/Yogesh-rana-2301/SecureCloudX-A-Hybrid-AES-Blockchain-ECC-Storage-System/issues

---

**Last Updated**: November 2025
