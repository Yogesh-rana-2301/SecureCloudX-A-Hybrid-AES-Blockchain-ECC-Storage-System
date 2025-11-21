# SecureCloudX API Examples

This document provides practical examples for using the SecureCloudX API.

## Base Configuration

```bash
export BASE_URL="http://localhost:8000"
```

## 1. User Registration Examples

### Register Alice

```bash
curl -X POST $BASE_URL/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice"
  }'
```

**Expected Response:**

```json
{
  "user_id": 1,
  "username": "alice",
  "public_key": "-----BEGIN PUBLIC KEY-----\nMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...\n-----END PUBLIC KEY-----\n",
  "message": "User 'alice' registered successfully"
}
```

### Register Bob

```bash
curl -X POST $BASE_URL/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "bob"
  }'
```

## 2. File Upload Examples

### Upload a Text File

```bash
# Create a test file
echo "This is a confidential document" > secret.txt

# Upload the file
curl -X POST $BASE_URL/upload \
  -F "file=@secret.txt" \
  -F "owner_id=1"
```

**Expected Response:**

```json
{
  "file_id": 1,
  "filename": "secret.txt",
  "block_index": 1,
  "message": "File 'secret.txt' uploaded and encrypted successfully"
}
```

### Upload a Binary File

```bash
curl -X POST $BASE_URL/upload \
  -F "file=@document.pdf" \
  -F "owner_id=1"
```

## 3. File Download Examples

### Download Your Own File

```bash
curl -X GET "$BASE_URL/download/1?user_id=1" \
  --output downloaded_file.txt
```

### Download with Headers

```bash
curl -X GET "$BASE_URL/download/1?user_id=1" \
  -v \
  --output downloaded_file.txt
```

## 4. File Sharing Examples

### Share a File with Another User

```bash
curl -X POST $BASE_URL/share \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": 1,
    "owner_id": 1,
    "recipient_username": "bob"
  }'
```

**Expected Response:**

```json
{
  "share_id": 1,
  "block_index": 2,
  "message": "File 'secret.txt' shared with 'bob' successfully"
}
```

### Recipient Downloads Shared File

```bash
curl -X GET "$BASE_URL/download/1?user_id=2" \
  --output shared_file.txt
```

## 5. Blockchain Examples

### View Entire Blockchain

```bash
curl -X GET $BASE_URL/chain | jq '.'
```

### Check Blockchain Validity

```bash
curl -X GET $BASE_URL/chain | jq '.is_valid'
```

### Get Block Count

```bash
curl -X GET $BASE_URL/chain | jq '.length'
```

### View Latest Block

```bash
curl -X GET $BASE_URL/chain | jq '.chain[-1]'
```

## 6. User Management Examples

### List All Users

```bash
curl -X GET $BASE_URL/users | jq '.'
```

### Get Specific User's Files

```bash
curl -X GET $BASE_URL/files/1 | jq '.'
```

### Count User's Files

```bash
curl -X GET $BASE_URL/files/1 | jq '.owned_count'
```

## 7. Health Check Examples

### Simple Health Check

```bash
curl -X GET $BASE_URL/health
```

### Monitor Server Status

```bash
watch -n 5 'curl -s http://localhost:8000/health | jq .'
```

## 8. Complete Workflow Example

```bash
#!/bin/bash
# Complete SecureCloudX Workflow

BASE_URL="http://localhost:8000"

echo "=== SecureCloudX Complete Workflow ==="

# 1. Register users
echo "1. Registering users..."
ALICE=$(curl -s -X POST $BASE_URL/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice"}')
ALICE_ID=$(echo $ALICE | jq -r '.user_id')
echo "   Alice ID: $ALICE_ID"

BOB=$(curl -s -X POST $BASE_URL/register \
  -H "Content-Type: application/json" \
  -d '{"username": "bob"}')
BOB_ID=$(echo $BOB | jq -r '.user_id')
echo "   Bob ID: $BOB_ID"

# 2. Create and upload file
echo "2. Uploading file..."
echo "Confidential Business Plan" > business_plan.txt
UPLOAD=$(curl -s -X POST $BASE_URL/upload \
  -F "file=@business_plan.txt" \
  -F "owner_id=$ALICE_ID")
FILE_ID=$(echo $UPLOAD | jq -r '.file_id')
echo "   File ID: $FILE_ID"

# 3. Share file
echo "3. Sharing file with Bob..."
SHARE=$(curl -s -X POST $BASE_URL/share \
  -H "Content-Type: application/json" \
  -d "{
    \"file_id\": $FILE_ID,
    \"owner_id\": $ALICE_ID,
    \"recipient_username\": \"bob\"
  }")
echo "   Share complete"

# 4. Bob downloads
echo "4. Bob downloading shared file..."
curl -s -X GET "$BASE_URL/download/$FILE_ID?user_id=$BOB_ID" \
  --output bob_received.txt
echo "   Downloaded: bob_received.txt"

# 5. Verify blockchain
echo "5. Verifying blockchain..."
CHAIN=$(curl -s -X GET $BASE_URL/chain)
IS_VALID=$(echo $CHAIN | jq -r '.is_valid')
BLOCKS=$(echo $CHAIN | jq -r '.length')
echo "   Blocks: $BLOCKS"
echo "   Valid: $IS_VALID"

echo "=== Workflow Complete ==="
```

## 9. Python Examples

### Using requests library

```python
import requests

BASE_URL = "http://localhost:8000"

# Register user
response = requests.post(
    f"{BASE_URL}/register",
    json={"username": "alice"}
)
user = response.json()
print(f"User ID: {user['user_id']}")

# Upload file
with open("document.txt", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/upload",
        files={"file": f},
        data={"owner_id": user['user_id']}
    )
file_info = response.json()
print(f"File ID: {file_info['file_id']}")

# Download file
response = requests.get(
    f"{BASE_URL}/download/{file_info['file_id']}",
    params={"user_id": user['user_id']}
)
with open("downloaded.txt", "wb") as f:
    f.write(response.content)
```

### Async with httpx

```python
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        # Register user
        response = await client.post(
            "http://localhost:8000/register",
            json={"username": "alice"}
        )
        user = response.json()

        # View blockchain
        response = await client.get(
            "http://localhost:8000/chain"
        )
        chain = response.json()
        print(f"Blockchain has {chain['length']} blocks")

asyncio.run(main())
```

## 10. JavaScript/Node.js Examples

### Using axios

```javascript
const axios = require("axios");
const FormData = require("form-data");
const fs = require("fs");

const BASE_URL = "http://localhost:8000";

// Register user
async function registerUser(username) {
  const response = await axios.post(`${BASE_URL}/register`, {
    username: username,
  });
  return response.data;
}

// Upload file
async function uploadFile(filePath, ownerId) {
  const form = new FormData();
  form.append("file", fs.createReadStream(filePath));
  form.append("owner_id", ownerId);

  const response = await axios.post(`${BASE_URL}/upload`, form, {
    headers: form.getHeaders(),
  });
  return response.data;
}

// Main workflow
async function main() {
  try {
    const user = await registerUser("alice");
    console.log(`User registered: ${user.user_id}`);

    const file = await uploadFile("document.txt", user.user_id);
    console.log(`File uploaded: ${file.file_id}`);
  } catch (error) {
    console.error("Error:", error.message);
  }
}

main();
```

## 11. Error Handling Examples

### Handle User Already Exists

```bash
curl -X POST $BASE_URL/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice"}'

# If alice already exists:
# {"detail": "Username already exists"}
```

### Handle File Not Found

```bash
curl -X GET "$BASE_URL/download/999?user_id=1"

# Response:
# {"detail": "File not found"}
```

### Handle Access Denied

```bash
curl -X GET "$BASE_URL/download/1?user_id=999"

# Response:
# {"detail": "Access denied"}
```

## 12. Advanced Examples

### Batch File Upload

```bash
for file in *.txt; do
    echo "Uploading $file..."
    curl -X POST $BASE_URL/upload \
      -F "file=@$file" \
      -F "owner_id=1"
    sleep 1
done
```

### Monitor Blockchain Growth

```bash
while true; do
    curl -s $BASE_URL/chain | jq '{blocks: .length, valid: .is_valid}'
    sleep 10
done
```

### Export Blockchain to File

```bash
curl -s $BASE_URL/chain | jq '.' > blockchain_backup.json
```

## 13. Testing with Postman

Import this collection:

```json
{
  "info": {
    "name": "SecureCloudX API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Register User",
      "request": {
        "method": "POST",
        "header": [{ "key": "Content-Type", "value": "application/json" }],
        "body": {
          "mode": "raw",
          "raw": "{\"username\": \"alice\"}"
        },
        "url": "{{base_url}}/register"
      }
    },
    {
      "name": "Upload File",
      "request": {
        "method": "POST",
        "body": {
          "mode": "formdata",
          "formdata": [
            { "key": "file", "type": "file", "src": "" },
            { "key": "owner_id", "value": "1", "type": "text" }
          ]
        },
        "url": "{{base_url}}/upload"
      }
    }
  ],
  "variable": [{ "key": "base_url", "value": "http://localhost:8000" }]
}
```

## Need Help?

- View interactive docs: http://localhost:8000/docs
- Check server health: http://localhost:8000/health
- Report issues: GitHub Issues
