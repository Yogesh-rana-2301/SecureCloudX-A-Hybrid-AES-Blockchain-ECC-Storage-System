"""
Blockchain Mini-Ledger Module
Implements a simple blockchain for storing and validating AES key records.
"""

import hashlib
import json
import time
from typing import List, Optional
from datetime import datetime


class Block:
    """
    Represents a single block in the blockchain.
    Each block stores encrypted AES key information and links to the previous block.
    """
    
    def __init__(self, index: int, timestamp: float, data: dict, previous_hash: str):
        """
        Initialize a new block.
        
        Args:
            index: Block position in the chain
            timestamp: Unix timestamp when block was created
            data: Dictionary containing encrypted AES key and metadata
            previous_hash: Hash of the previous block in the chain
        """
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """
        Calculate SHA-256 hash of the block's contents.
        
        Returns:
            str: Hexadecimal hash string
        """
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash
        }, sort_keys=True)
        
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def to_dict(self) -> dict:
        """
        Convert block to dictionary format for JSON serialization.
        
        Returns:
            dict: Block data as dictionary
        """
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'hash': self.hash
        }
    
    @staticmethod
    def from_dict(block_dict: dict) -> 'Block':
        """
        Create a Block instance from a dictionary.
        
        Args:
            block_dict: Dictionary containing block data
            
        Returns:
            Block: New Block instance
        """
        block = Block(
            index=block_dict['index'],
            timestamp=block_dict['timestamp'],
            data=block_dict['data'],
            previous_hash=block_dict['previous_hash']
        )
        # Verify the stored hash matches
        if block.hash != block_dict['hash']:
            raise ValueError(f"Block {block.index} has been tampered with!")
        return block


class Blockchain:
    """
    Manages the blockchain ledger of encrypted AES keys.
    """
    
    def __init__(self, chain_file: str = 'blockchain/chain.json', db=None):
        """
        Initialize blockchain, loading existing chain or creating genesis block.
        
        Args:
            chain_file: Path to JSON file for storing the blockchain (fallback)
            db: Database instance for persistent storage (preferred)
        """
        self.chain_file = chain_file
        self.chain: List[Block] = []
        self.db = db
        
        # Try to load from database first, then from file, otherwise create genesis block
        if self.db and self.load_chain_from_database():
            pass  # Successfully loaded from database
        elif not self.load_chain_from_json():
            self.create_genesis_block()
    
    def create_genesis_block(self):
        """
        Create the first block in the blockchain (genesis block).
        """
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            data={'message': 'Genesis Block - SecureCloudX Blockchain Initialized'},
            previous_hash='0'
        )
        self.chain.append(genesis_block)
        self.save_chain_to_json()
    
    def get_latest_block(self) -> Block:
        """
        Get the most recent block in the chain.
        
        Returns:
            Block: The latest block
        """
        return self.chain[-1]
    
    def add_block(self, data: dict) -> Block:
        """
        Add a new block to the blockchain.
        
        Args:
            data: Dictionary containing encrypted AES key and metadata
            
        Returns:
            Block: The newly created block
        """
        previous_block = self.get_latest_block()
        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            data=data,
            previous_hash=previous_block.hash
        )
        
        self.chain.append(new_block)
        
        # Save to database if available, otherwise save to JSON
        if self.db:
            self.save_block_to_database(new_block)
        else:
            self.save_chain_to_json()
        
        return new_block
    
    def validate_chain(self) -> bool:
        """
        Validate the integrity of the entire blockchain.
        
        Returns:
            bool: True if chain is valid, False if tampered
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Check if current block's hash is correct
            if current_block.hash != current_block.calculate_hash():
                print(f"Block {i} has been tampered with!")
                return False
            
            # Check if previous_hash matches
            if current_block.previous_hash != previous_block.hash:
                print(f"Block {i} has invalid previous_hash!")
                return False
        
        return True
    
    def get_block_by_index(self, index: int) -> Optional[Block]:
        """
        Retrieve a block by its index.
        
        Args:
            index: Block index to retrieve
            
        Returns:
            Block or None: The block if found, None otherwise
        """
        if 0 <= index < len(self.chain):
            return self.chain[index]
        return None
    
    def save_chain_to_json(self):
        """
        Save the blockchain to a JSON file.
        """
        import os
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.chain_file), exist_ok=True)
        
        chain_data = [block.to_dict() for block in self.chain]
        
        with open(self.chain_file, 'w') as f:
            json.dump(chain_data, f, indent=2)
    
    def load_chain_from_json(self) -> bool:
        """
        Load the blockchain from a JSON file.
        
        Returns:
            bool: True if chain was loaded successfully, False otherwise
        """
        import os
        
        if not os.path.exists(self.chain_file):
            return False
        
        try:
            with open(self.chain_file, 'r') as f:
                chain_data = json.load(f)
            
            self.chain = [Block.from_dict(block_dict) for block_dict in chain_data]
            
            # Validate loaded chain
            if not self.validate_chain():
                print("WARNING: Loaded blockchain is invalid!")
                return False
            
            return True
        except Exception as e:
            print(f"Error loading blockchain: {e}")
            return False
    
    def get_chain_as_dict(self) -> List[dict]:
        """
        Get the entire blockchain as a list of dictionaries.
        
        Returns:
            List[dict]: List of block dictionaries
        """
        return [block.to_dict() for block in self.chain]
    
    def save_block_to_database(self, block: Block):
        """
        Save a single block to the database.
        
        Args:
            block: Block instance to save
        """
        if self.db:
            self.db.save_blockchain_block(
                block_index=block.index,
                timestamp=block.timestamp,
                data=block.data,
                previous_hash=block.previous_hash,
                block_hash=block.hash
            )
    
    def load_chain_from_database(self) -> bool:
        """
        Load the blockchain from the database.
        
        Returns:
            bool: True if chain was loaded successfully, False otherwise
        """
        if not self.db:
            return False
        
        try:
            blocks_data = self.db.load_blockchain_blocks()
            
            if not blocks_data:
                return False
            
            # Reconstruct blocks from database
            self.chain = []
            for block_data in blocks_data:
                block = Block(
                    index=block_data['block_index'],
                    timestamp=block_data['block_timestamp'],
                    data=block_data['block_data'],
                    previous_hash=block_data['previous_hash']
                )
                # Override the calculated hash with the stored one
                block.hash = block_data['block_hash']
                self.chain.append(block)
            
            # NOTE: We load the chain but don't fail on validation here.
            # The app startup logic will check validity and reset if needed.
            # This prevents worker crashes during deployment.
            
            return True
        except Exception as e:
            print(f"Error loading blockchain from database: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def __len__(self) -> int:
        """Get the number of blocks in the chain."""
        return len(self.chain)
