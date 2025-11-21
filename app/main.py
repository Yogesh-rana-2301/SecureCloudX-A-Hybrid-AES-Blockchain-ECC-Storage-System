"""
SecureCloudX - FastAPI Application
Main application file with REST API endpoints for secure cloud storage.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import Response, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import base64
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add modules to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.aes_encryption import generate_aes_key, encrypt_file, decrypt_file
from modules.ecc_crypto import generate_ecc_keypair, encrypt_aes_key_with_ecc, decrypt_aes_key_with_ecc
from modules.blockchain import Blockchain
from modules.database import Database


# Initialize FastAPI app
app = FastAPI(
    title="SecureCloudX",
    description="Secure cloud storage with AES encryption, blockchain ledger, and ECC key exchange",
    version="1.0.0"
)

# Error handling middleware
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Unhandled exception in {request.method} {request.url}: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(e)}"}
        )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

# Initialize blockchain and database
blockchain = None
db = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global blockchain, db
    try:
        # Use /tmp for blockchain on Render (ephemeral but writable)
        chain_path = '/tmp/blockchain/chain.json' if os.getenv('RENDER') else 'blockchain/chain.json'
        logger.info(f"Initializing blockchain at {chain_path}")
        blockchain = Blockchain(chain_path)
        logger.info(f"Blockchain initialized with {len(blockchain.chain)} blocks")
        
        logger.info("Initializing database connection")
        db = Database('securecloudx.db')
        logger.info(f"✅ Startup successful - Database: {'PostgreSQL' if db.is_postgres else 'SQLite'}")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise  # Re-raise to prevent app from starting with broken state

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        status = {
            "status": "healthy",
            "database": "PostgreSQL" if db and db.is_postgres else "SQLite",
            "blockchain_blocks": len(blockchain.chain) if blockchain else 0
        }
        logger.info(f"Health check: {status}")
        return status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Pydantic models for request/response
class UserRegisterRequest(BaseModel):
    username: str


class UserRegisterResponse(BaseModel):
    user_id: int
    username: str
    public_key: str
    message: str


class FileUploadResponse(BaseModel):
    file_id: int
    filename: str
    block_index: int
    message: str


class FileShareRequest(BaseModel):
    file_id: int
    owner_id: int
    recipient_username: str


class FileShareResponse(BaseModel):
    share_id: int
    block_index: int
    message: str


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint - serve the frontend application."""
    static_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    return FileResponse(static_path)


@app.post("/register", response_model=UserRegisterResponse)
async def register_user(request: UserRegisterRequest):
    """
    Register a new user and generate ECC keypair.
    
    Creates a new user account with unique username and generates
    SECP256R1 ECC public/private keypair for secure key exchange.
    """
    try:
        # Check if database is initialized
        if db is None:
            logger.error("Database not initialized - startup may have failed")
            raise HTTPException(status_code=503, detail="Service not ready - database not initialized")
        
        logger.info(f"Registration attempt for username: {request.username}")
        
        # Check if username already exists
        existing_user = db.get_user_by_username(request.username)
        if existing_user:
            logger.warning(f"Username already exists: {request.username}")
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Generate ECC keypair
        logger.info("Generating ECC keypair")
        keypair = generate_ecc_keypair()
        
        # Save user to database
        logger.info(f"Saving user to database: {request.username}")
        user_id = db.create_user(
            username=request.username,
            public_key=keypair['public_key'],
            private_key=keypair['private_key']
        )
        
        logger.info(f"User registered successfully: {request.username} (ID: {user_id})")
        
        return UserRegisterResponse(
            user_id=user_id,
            username=request.username,
            public_key=keypair['public_key'],
            message=f"User '{request.username}' registered successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed for {request.username}: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    owner_id: int = Form(...)
):
    """
    Upload and encrypt a file with dynamic AES-256 encryption.
    
    Process:
    1. Generate unique AES-256 key
    2. Encrypt file with AES CBC mode
    3. Store encrypted file
    4. Add AES key to blockchain
    5. Save metadata to database
    """
    try:
        # Verify user exists
        user = db.get_user_by_id(owner_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Read file content
        content = await file.read()
        
        # Save temporary file
        temp_path = f"storage/temp_{file.filename}"
        os.makedirs('storage', exist_ok=True)
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        # Generate AES key and encrypt file
        aes_key = generate_aes_key()
        encrypted_result = encrypt_file(temp_path, aes_key)
        
        # Encode AES key for blockchain storage
        aes_key_b64 = base64.b64encode(aes_key).decode('utf-8')
        
        # Add to blockchain
        block_data = {
            'owner_id': owner_id,
            'filename': file.filename,
            'aes_key': aes_key_b64,
            'timestamp': blockchain.get_latest_block().timestamp
        }
        new_block = blockchain.add_block(block_data)
        
        # Save file metadata to database
        stored_path = f"storage/files/{owner_id}_{file.filename}"
        file_id = db.create_file(
            owner_id=owner_id,
            filename=file.filename,
            stored_path=stored_path,
            block_index=new_block.index,
            encrypted_data=encrypted_result['encrypted_data'],
            iv=encrypted_result['iv']
        )
        
        # Clean up temp file
        os.remove(temp_path)
        
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            block_index=new_block.index,
            message=f"File '{file.filename}' uploaded and encrypted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/download/{file_id}")
async def download_file(file_id: int, user_id: int):
    """
    Download and decrypt a file.
    
    Retrieves file from database, fetches AES key from blockchain,
    decrypts the file, and returns it to the user.
    """
    try:
        # Get file metadata
        file_record = db.get_file_by_id(file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if user is the owner
        if file_record['owner_id'] != user_id:
            # Check if file was shared with this user
            share = db.get_file_share(file_id, user_id)
            if not share:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Get recipient's private key to decrypt AES key
            user = db.get_user_by_id(user_id)
            encrypted_aes_key = share['encrypted_aes_key']
            aes_key = decrypt_aes_key_with_ecc(encrypted_aes_key, user['ecc_private_key'])
        else:
            # Owner accessing their own file - get AES key from blockchain
            block = blockchain.get_block_by_index(file_record['block_index'])
            if not block:
                raise HTTPException(status_code=500, detail="Blockchain block not found")
            
            aes_key_b64 = block.data['aes_key']
            aes_key = base64.b64decode(aes_key_b64)
        
        # Decrypt file
        decrypted_content = decrypt_file(
            encrypted_data=file_record['encrypted_data'],
            key=aes_key,
            iv=file_record['iv']
        )
        
        # Return file
        return Response(
            content=decrypted_content,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={file_record['filename']}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@app.post("/share", response_model=FileShareResponse)
async def share_file(request: FileShareRequest):
    """
    Share a file with another user using ECC encryption.
    
    Process:
    1. Retrieve original AES key from blockchain
    2. Get recipient's ECC public key
    3. Encrypt AES key with recipient's public key
    4. Add encrypted key to blockchain
    5. Create share record in database
    """
    try:
        # Verify file exists and requester is owner
        file_record = db.get_file_by_id(request.file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        if file_record['owner_id'] != request.owner_id:
            raise HTTPException(status_code=403, detail="Only file owner can share")
        
        # Get recipient user
        recipient = db.get_user_by_username(request.recipient_username)
        if not recipient:
            raise HTTPException(status_code=404, detail="Recipient user not found")
        
        if recipient['id'] == request.owner_id:
            raise HTTPException(status_code=400, detail="Cannot share file with yourself")
        
        # Check if already shared
        existing_share = db.get_file_share(request.file_id, recipient['id'])
        if existing_share:
            raise HTTPException(status_code=400, detail="File already shared with this user")
        
        # Get original AES key from blockchain
        block = blockchain.get_block_by_index(file_record['block_index'])
        if not block:
            raise HTTPException(status_code=500, detail="Blockchain block not found")
        
        aes_key_b64 = block.data['aes_key']
        aes_key = base64.b64decode(aes_key_b64)
        
        # Encrypt AES key with recipient's public key
        encrypted_aes_key = encrypt_aes_key_with_ecc(
            aes_key=aes_key,
            recipient_public_key_pem=recipient['ecc_public_key']
        )
        
        # Add to blockchain
        share_block_data = {
            'action': 'share',
            'file_id': request.file_id,
            'owner_id': request.owner_id,
            'recipient_id': recipient['id'],
            'encrypted_aes_key': encrypted_aes_key,
            'filename': file_record['filename']
        }
        new_block = blockchain.add_block(share_block_data)
        
        # Create share record in database
        share_id = db.create_file_share(
            file_id=request.file_id,
            owner_id=request.owner_id,
            recipient_id=recipient['id'],
            encrypted_aes_key=encrypted_aes_key,
            block_index=new_block.index
        )
        
        return FileShareResponse(
            share_id=share_id,
            block_index=new_block.index,
            message=f"File '{file_record['filename']}' shared with '{recipient['username']}' successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Share failed: {str(e)}")


@app.get("/chain")
async def get_blockchain():
    """
    Retrieve the entire blockchain ledger.
    
    Returns the complete blockchain with all blocks,
    including validation status.
    """
    try:
        is_valid = blockchain.validate_chain()
        
        return {
            "chain": blockchain.get_chain_as_dict(),
            "length": len(blockchain),
            "is_valid": is_valid,
            "message": "Blockchain is valid" if is_valid else "WARNING: Blockchain has been tampered!"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve blockchain: {str(e)}")


@app.get("/users")
async def get_users():
    """
    List all registered users.
    
    Returns list of users (excluding private keys for security).
    """
    try:
        users = db.get_all_users()
        return {
            "users": users,
            "count": len(users)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve users: {str(e)}")


@app.get("/files/{user_id}")
async def get_user_files(user_id: int):
    """
    List all files owned by a specific user.
    
    Returns file metadata for all files belonging to the user.
    """
    try:
        # Verify user exists
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's files
        files = db.get_files_by_owner(user_id)
        
        # Get shared files
        shared_files = db.get_shared_files_for_user(user_id)
        
        return {
            "username": user['username'],
            "owned_files": files,
            "shared_with_me": shared_files,
            "owned_count": len(files),
            "shared_count": len(shared_files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve files: {str(e)}")


@app.get("/health")
async def health_check():
    """
    Health check endpoint for container orchestration.
    """
    return {
        "status": "healthy",
        "blockchain_blocks": len(blockchain),
        "blockchain_valid": blockchain.validate_chain()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
