# Contributing to SecureCloudX

Thank you for your interest in contributing to SecureCloudX! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [How to Contribute](#how-to-contribute)
4. [Development Setup](#development-setup)
5. [Coding Standards](#coding-standards)
6. [Pull Request Process](#pull-request-process)
7. [Testing Guidelines](#testing-guidelines)
8. [Documentation](#documentation)
9. [Community](#community)

## 📜 Code of Conduct

This project adheres to the Contributor Covenant [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to dakshk9999@gmail.com.

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Basic understanding of cryptography concepts
- Familiarity with FastAPI (optional but helpful)

### Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/yogesh-rana-2301/SecureCloudX-A-Hybrid-AES-Blockchain-ECC-Storage-System.git
cd SecureCloudX-A-Hybrid-AES-Blockchain-ECC-Storage-System

# Add upstream remote
git remote add upstream https://github.com/Yogesh-rana-2301/SecureCloudX-A-Hybrid-AES-Blockchain-ECC-Storage-System.git
```

## 🤝 How to Contribute

### Types of Contributions

We welcome various types of contributions:

#### 🐛 Bug Reports

Found a bug? Please create an issue with:

- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version)
- Screenshots (if applicable)

**Template:**

```markdown
**Bug Description:**
[Clear description of the bug]

**To Reproduce:**
1. Step 1
2. Step 2
3. See error

**Expected Behavior:**
[What should happen]

**Environment:**
- OS: [e.g., macOS 13.0]
- Python: [e.g., 3.10.5]
- SecureCloudX version: [e.g., 1.0.0]

**Additional Context:**
[Any other relevant information]
```

#### ✨ Feature Requests

Have an idea? Create an issue with:

- Use case description
- Proposed solution
- Alternative solutions considered
- Additional context

**Template:**

```markdown
**Feature Description:**
[Clear description of the feature]

**Use Case:**
[Why is this feature needed?]

**Proposed Solution:**
[How should it work?]

**Alternatives:**
[Other approaches considered]

**Additional Context:**
[Mockups, examples, etc.]
```

#### 🔧 Code Contributions

Areas where we need help:

- **Core Features**
  - Enhanced encryption algorithms
  - Additional blockchain features
  - Performance optimizations
  
- **Infrastructure**
  - CI/CD improvements
  - Docker enhancements
  - Deployment scripts
  
- **Documentation**
  - Tutorial improvements
  - API documentation
  - Code comments
  
- **Testing**
  - Unit tests
  - Integration tests
  - Security tests

#### 📚 Documentation

- Fix typos or clarify explanations
- Add examples
- Translate documentation
- Create tutorials or blog posts

## 💻 Development Setup

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available

# Or install in development mode
pip install -e .
```

### 3. Create Development Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 4. Set Up Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

## 🎨 Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

```python
# ✅ Good
def encrypt_file(file_path: str, key: bytes) -> bytes:
    """
    Encrypt a file using AES-256-CBC.
    
    Args:
        file_path: Path to the file to encrypt
        key: 32-byte AES encryption key
        
    Returns:
        Encrypted file content in bytes
        
    Raises:
        ValueError: If key length is invalid
    """
    if len(key) != 32:
        raise ValueError("AES key must be 32 bytes")
    
    # Implementation
    pass

# ❌ Bad
def encryptFile(filePath,key):
    # No docstring, no type hints, poor naming
    pass
```

### Code Formatting

```bash
# Use Black for code formatting
pip install black
black modules/ app/

# Use isort for import sorting
pip install isort
isort modules/ app/

# Use flake8 for linting
pip install flake8
flake8 modules/ app/
```

### Type Hints

Always use type hints:

```python
from typing import Dict, List, Optional

def get_user_files(user_id: int) -> List[Dict[str, str]]:
    """Get all files for a user."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def encrypt_aes_key_with_ecc(aes_key: bytes, public_key_pem: str) -> str:
    """
    Encrypt an AES key using ECC public key.
    
    Args:
        aes_key: The 32-byte AES key to encrypt
        public_key_pem: Recipient's ECC public key in PEM format
        
    Returns:
        Base64-encoded encrypted key package
        
    Raises:
        ValueError: If key formats are invalid
        
    Example:
        >>> keypair = generate_ecc_keypair()
        >>> aes_key = generate_aes_key()
        >>> encrypted = encrypt_aes_key_with_ecc(aes_key, keypair['public_key'])
    """
    pass
```

### Naming Conventions

```python
# Variables and functions: snake_case
user_id = 1
def get_user_info():
    pass

# Classes: PascalCase
class UserManager:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Private methods: _leading_underscore
def _internal_helper():
    pass
```

## 🔄 Pull Request Process

### 1. Update Your Branch

```bash
# Sync with upstream
git fetch upstream
git rebase upstream/main
```

### 2. Make Your Changes

```bash
# Make changes, then:
git add .
git commit -m "feat: add new encryption algorithm"

# Follow conventional commits:
# feat: new feature
# fix: bug fix
# docs: documentation changes
# style: formatting changes
# refactor: code refactoring
# test: adding tests
# chore: maintenance tasks
```

### 3. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 4. Create Pull Request

Go to GitHub and create a PR with:

**Title:** Clear, descriptive summary (50 chars max)

**Description:**
```markdown
## Description
[What does this PR do?]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated

## Related Issues
Closes #123
```

### 5. Code Review

- Address reviewer feedback
- Push new commits to the same branch
- Request re-review when ready

### 6. Merge

Once approved, a maintainer will merge your PR.

## 🧪 Testing Guidelines

### Running Tests

```bash
# Run all tests
python test_system.py

# Run specific module tests
python -m pytest tests/test_aes.py

# Run with coverage
pip install pytest-cov
pytest --cov=modules tests/
```

### Writing Tests

```python
# tests/test_aes_encryption.py
import pytest
from modules.aes_encryption import generate_aes_key, encrypt_file, decrypt_file

def test_generate_aes_key():
    """Test AES key generation."""
    key = generate_aes_key()
    assert len(key) == 32
    assert isinstance(key, bytes)

def test_encrypt_decrypt_roundtrip(tmp_path):
    """Test encryption and decryption."""
    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, SecureCloudX!")
    
    # Generate key and encrypt
    key = generate_aes_key()
    encrypted = encrypt_file(str(test_file), key)
    
    # Decrypt and verify
    decrypted = decrypt_file(encrypted, key)
    assert decrypted == b"Hello, SecureCloudX!"

def test_invalid_key_length():
    """Test error handling for invalid key."""
    with pytest.raises(ValueError):
        encrypt_file("test.txt", b"shortkey")
```

### Test Coverage

Aim for >80% code coverage:

```bash
pytest --cov=modules --cov-report=html
open htmlcov/index.html
```

## 📖 Documentation

### Code Comments

```python
# Good: Explain WHY, not WHAT
# Use ECDH instead of RSA for better performance on embedded devices
shared_secret = private_key.exchange(ec.ECDH(), public_key)

# Bad: States the obvious
# Perform key exchange
shared_secret = private_key.exchange(ec.ECDH(), public_key)
```

### README Updates

If your change affects usage:

1. Update relevant sections in README.md
2. Add examples if introducing new features
3. Update API documentation

### Changelog

Add your changes to CHANGELOG.md:

```markdown
## [Unreleased]

### Added
- New feature description (#PR_NUMBER)

### Fixed
- Bug fix description (#PR_NUMBER)

### Changed
- Breaking change description (#PR_NUMBER)
```

## 👥 Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community support
- **Email**: dakshk9999@gmail.com for private matters

### Getting Help

Stuck? Here's how to get help:

1. Check existing [issues](https://github.com/Yogesh-rana-2301/SecureCloudX-A-Hybrid-AES-Blockchain-ECC-Storage-System/issues)
2. Read the [documentation](README.md)
3. Ask in [GitHub Discussions](https://github.com/Yogesh-rana-2301/SecureCloudX-A-Hybrid-AES-Blockchain-ECC-Storage-System/discussions)
4. Contact maintainers

### Recognition

Contributors will be:

- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in relevant documentation

## 🏅 Contribution Levels

### 🌱 First-Time Contributor

Good first issues tagged with `good-first-issue`:

- Documentation improvements
- Simple bug fixes
- Adding tests
- Typo fixes

### 🌿 Regular Contributor

After 3+ merged PRs:

- Review other PRs
- Help triage issues
- Mentor new contributors

### 🌳 Maintainer

Trusted contributors may become maintainers with:

- Merge access
- Release responsibilities
- Architecture decisions

## 📋 Checklist Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added (if applicable)
- [ ] Documentation updated
- [ ] Commit messages follow conventions
- [ ] PR description is complete
- [ ] Linked to relevant issues
- [ ] Self-review completed

## ⚖️ License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

## 🙏 Thank You!

Every contribution, no matter how small, makes SecureCloudX better. We appreciate your time and effort!

---

**Questions?** Open an issue or contact us at dakshk9999@gmail.com

**Happy Contributing!** 🎉
