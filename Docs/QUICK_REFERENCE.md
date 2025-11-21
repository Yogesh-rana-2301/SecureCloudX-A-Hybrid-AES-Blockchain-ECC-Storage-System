# SecureCloudX Reference

## Getting Started (3 Steps)

### Step 1: Install

```bash
git clone https://github.com/Yogesh-rana-2301/SecureCloudX-A-Hybrid-AES-Blockchain-ECC-Storage-System.git
cd SecureCloudX-A-Hybrid-AES-Blockchain-ECC-Storage-System
pip install -r requirements.txt
```

### Step 2: Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Step 3: Test

Open http://localhost:8000/docs

---

## Common Commands

### Register User

```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice"}'
```

### Upload File

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf" \
  -F "owner_id=1"
```

### Download File

```bash
curl "http://localhost:8000/download/1?user_id=1" -o file.pdf
```

### Share File

```bash
curl -X POST http://localhost:8000/share \
  -H "Content-Type: application/json" \
  -d '{"file_id": 1, "owner_id": 1, "recipient_username": "bob"}'
```

### View Blockchain

```bash
curl http://localhost:8000/chain | jq '.'
```

---

## Docker Commands

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild
docker-compose up -d --build
```

---

## Key Files

| File                        | Purpose             |
| --------------------------- | ------------------- |
| `app/main.py`               | FastAPI application |
| `modules/aes_encryption.py` | AES-256 encryption  |
| `modules/ecc_crypto.py`     | ECC key exchange    |
| `modules/blockchain.py`     | Blockchain ledger   |
| `modules/database.py`       | SQLite operations   |
| `requirements.txt`          | Dependencies        |
| `Dockerfile`                | Container config    |
| `test_system.py`            | Automated tests     |

---

## Troubleshooting

### Port in use

```bash
lsof -i :8000
kill -9 <PID>
```

### Reset database

```bash
rm securecloudx.db
# Restart app to recreate
```

### Reset blockchain

```bash
rm blockchain/chain.json
# Restart app to recreate
```

---

## Documentation

- **README.md** - Complete guide
- **API_EXAMPLES.md** - API usage examples
- **PROJECT_SUMMARY.md** - Project overview

---

## API Endpoints

| Endpoint           | Method | Description     |
| ------------------ | ------ | --------------- |
| `/`                | GET    | API info        |
| `/register`        | POST   | Register user   |
| `/upload`          | POST   | Upload file     |
| `/download/{id}`   | GET    | Download file   |
| `/share`           | POST   | Share file      |
| `/chain`           | GET    | View blockchain |
| `/users`           | GET    | List users      |
| `/files/{user_id}` | GET    | User files      |
| `/health`          | GET    | Health check    |

---

## Security Features

AES-256 encryption  
SECP256R1 ECC  
SHA-256 blockchain  
Access control  
Unique keys per file

---

## System Requirements

- Python 3.10+
- 100MB disk space
- 512MB RAM minimum
- Docker (optional)

---

## Test Command

```bash
python test_system.py
```

---

## Access Points

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

---

**Want Help?**  
See README.md or open a GitHub issue

---

_SecureCloudX - Secure Cloud Storage_
