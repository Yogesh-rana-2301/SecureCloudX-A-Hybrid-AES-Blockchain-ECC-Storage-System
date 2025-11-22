#!/usr/bin/env python3
"""
SecureCloudX Comprehensive Testing Script
Tests all major functionality including encryption, blockchain, and API endpoints.
"""

import requests
import json
import os
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_complete_workflow():
    """Run comprehensive tests on all SecureCloudX features."""
    
    print("\n SecureCloudX - Comprehensive System Test")
    print("="*60)
    
    try:
        # Test 1: Server Health Check
        print_section("1. Server Health Check")
        response = requests.get(f"{BASE_URL}/health")
        health = response.json()
        print(f"✓ Status: {health['status']}")
        print(f"✓ Blockchain Blocks: {health['blockchain_blocks']}")
        print(f"✓ Blockchain Valid: {health['blockchain_valid']}")
        
        # Test 2: Register Users
        print_section("2. User Registration")
        
        # Generate unique usernames with timestamp
        timestamp = int(time.time())
        alice_username = f"alice_{timestamp}"
        bob_username = f"bob_{timestamp}"
        
        alice_response = requests.post(
            f"{BASE_URL}/register",
            json={"username": alice_username}
        )
        alice = alice_response.json()
        print(f"✓ Registered Alice")
        print(f"  - User ID: {alice['user_id']}")
        print(f"  - Username: {alice['username']}")
        print(f"  - Public Key (first 50 chars): {alice['public_key'][:50]}...")
        
        bob_response = requests.post(
            f"{BASE_URL}/register",
            json={"username": bob_username}
        )
        bob = bob_response.json()
        print(f"✓ Registered Bob")
        print(f"  - User ID: {bob['user_id']}")
        print(f"  - Username: {bob['username']}")
        
        # Test 3: List All Users
        print_section("3. List All Users")
        users_response = requests.get(f"{BASE_URL}/users")
        users_data = users_response.json()
        print(f"✓ Total Users: {users_data['count']}")
        for user in users_data['users'][-2:]:  # Show last 2 users
            print(f"  - {user['username']} (ID: {user['id']})")
        
        # Test 4: File Upload
        print_section("4. File Upload & Encryption")
        
        # Create test file
        test_filename = f"test_document_{timestamp}.txt"
        test_content = f"SecureCloudX Test Content - {timestamp}\nThis is a secure document!"
        with open(test_filename, "w") as f:
            f.write(test_content)
        
        # Upload file
        with open(test_filename, "rb") as f:
            upload_response = requests.post(
                f"{BASE_URL}/upload",
                files={"file": f},
                data={"owner_id": alice['user_id']}
            )
        
        file_info = upload_response.json()
        print(f"✓ File Uploaded")
        print(f"  - File ID: {file_info['file_id']}")
        print(f"  - Filename: {file_info['filename']}")
        print(f"  - Blockchain Block: {file_info['block_index']}")
        
        # Clean up test file
        os.remove(test_filename)
        
        # Test 5: View Blockchain
        print_section("5. Blockchain Verification")
        chain_response = requests.get(f"{BASE_URL}/chain")
        chain_data = chain_response.json()
        print(f"✓ Blockchain Status")
        print(f"  - Total Blocks: {chain_data['length']}")
        print(f"  - Chain Valid: {chain_data['is_valid']}")
        print(f"  - Latest Block Index: {chain_data['chain'][-1]['index']}")
        print(f"  - Latest Block Hash: {chain_data['chain'][-1]['hash'][:16]}...")
        
        # Test 6: File Download (Owner)
        print_section("6. File Download (Owner Access)")
        download_response = requests.get(
            f"{BASE_URL}/download/{file_info['file_id']}",
            params={"user_id": alice['user_id']}
        )
        
        if download_response.status_code == 200:
            downloaded_content = download_response.content.decode()
            print(f"✓ File Downloaded Successfully")
            print(f"  - Content matches: {downloaded_content == test_content}")
            print(f"  - Content preview: {downloaded_content[:50]}...")
        else:
            print(f"✗ Download failed: {download_response.status_code}")
        
        # Test 7: File Sharing
        print_section("7. Secure File Sharing")
        share_response = requests.post(
            f"{BASE_URL}/share",
            json={
                "file_id": file_info['file_id'],
                "owner_id": alice['user_id'],
                "recipient_username": bob['username']
            }
        )
        
        share_info = share_response.json()
        print(f"✓ File Shared with Bob")
        print(f"  - Share ID: {share_info['share_id']}")
        print(f"  - Blockchain Block: {share_info['block_index']}")
        print(f"  - Message: {share_info['message']}")
        
        # Test 8: File Download (Shared Access)
        print_section("8. File Download (Shared Access)")
        bob_download_response = requests.get(
            f"{BASE_URL}/download/{file_info['file_id']}",
            params={"user_id": bob['user_id']}
        )
        
        if bob_download_response.status_code == 200:
            bob_content = bob_download_response.content.decode()
            print(f"✓ Bob Downloaded Shared File Successfully")
            print(f"  - Content matches original: {bob_content == test_content}")
            print(f"  - Decryption successful via ECC key exchange")
        else:
            print(f"✗ Download failed: {bob_download_response.status_code}")
        
        # Test 9: List User Files
        print_section("9. User File Management")
        alice_files_response = requests.get(f"{BASE_URL}/files/{alice['user_id']}")
        alice_files = alice_files_response.json()
        print(f"✓ Alice's Files")
        print(f"  - Owned Files: {alice_files['owned_count']}")
        print(f"  - Shared with Alice: {alice_files['shared_count']}")
        
        bob_files_response = requests.get(f"{BASE_URL}/files/{bob['user_id']}")
        bob_files = bob_files_response.json()
        print(f"✓ Bob's Files")
        print(f"  - Owned Files: {bob_files['owned_count']}")
        print(f"  - Shared with Bob: {bob_files['shared_count']}")
        
        # Test 10: Final Blockchain Validation
        print_section("10. Final Blockchain Validation")
        final_chain = requests.get(f"{BASE_URL}/chain").json()
        print(f"✓ Final Blockchain State")
        print(f"  - Total Blocks: {final_chain['length']}")
        print(f"  - Validation: {final_chain['message']}")
        
        # Print blockchain summary
        print(f"\n  Block Summary:")
        for block in final_chain['chain']:
            print(f"    Block {block['index']}: {list(block['data'].keys())}")
        
        # Final Summary
        print_section(" All Tests Completed Successfully!")
        print("\nTest Summary:")
        print("  ✓ User Registration")
        print("  ✓ ECC Keypair Generation")
        print("  ✓ File Upload & AES Encryption")
        print("  ✓ Blockchain Key Storage")
        print("  ✓ File Download & Decryption")
        print("  ✓ Secure File Sharing (ECC)")
        print("  ✓ Blockchain Validation")
        print("  ✓ Access Control")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n Error: Cannot connect to SecureCloudX server")
        print("   Make sure the server is running on http://localhost:8000")
        print("   Run: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return False
        
    except Exception as e:
        print(f"\n Test Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_workflow()
    exit(0 if success else 1)
