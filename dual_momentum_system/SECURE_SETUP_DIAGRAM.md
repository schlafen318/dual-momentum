# Secure API Key Setup - Visual Guide

## ❌ WRONG: What NOT to Do

```
GitHub Repository (PUBLIC)
├── .env  ← ❌ NEVER DO THIS!
│   └── ALPHAVANTAGE_API_KEY=VT0RO0... ← EXPOSED TO EVERYONE!
├── script.py
│   └── api_key = "VT0RO0..." ← ❌ HARDCODED! INSECURE!
└── README.md

Result: 🚨 API KEY EXPOSED! Security breach! ⛔
```

## ✅ CORRECT: Secure Setup

```
┌─────────────────────────────────────────────────────────────┐
│                     GITHUB REPOSITORY                        │
│  (Safe to be public - no secrets here)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📁 dual_momentum_system/                                   │
│  ├── .env.example  ← ✅ Template only (YOUR_API_KEY_HERE)  │
│  ├── .gitignore    ← ✅ Protects .env from commits         │
│  ├── *.py files    ← ✅ Use os.environ.get()               │
│  └── .github/workflows/                                      │
│      └── test.yml  ← ✅ Uses ${{ secrets.* }}              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                          │
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
        ▼                                   ▼
┌───────────────────┐            ┌──────────────────────┐
│  GITHUB SECRETS   │            │  YOUR LOCAL COMPUTER │
│  (Repository)     │            │  (Not committed)     │
├───────────────────┤            ├──────────────────────┤
│                   │            │                      │
│  Settings →       │            │  📁 dual_momentum/   │
│  Secrets →        │            │  ├── .env  🔒        │
│  Actions          │            │  │   ALPHAVANTAGE_  │
│                   │            │  │   API_KEY=real   │
│  Name:            │            │  │                  │
│  ALPHAVANTAGE_    │            │  └── (Protected by  │
│  API_KEY          │            │       .gitignore)    │
│                   │            │                      │
│  Value:           │            │  OR just export:     │
│  your_real_key    │            │  $ export ALPHA...  │
│                   │            │                      │
└───────────────────┘            └──────────────────────┘
        │                                   │
        │ Used by GitHub Actions            │ Used locally
        ▼                                   ▼
┌───────────────────┐            ┌──────────────────────┐
│  CI/CD WORKFLOW   │            │  LOCAL DEVELOPMENT   │
│  (Automated)      │            │  (Your machine)      │
├───────────────────┤            ├──────────────────────┤
│                   │            │                      │
│  env:             │            │  $ python3 test.py   │
│    ALPHAVANTAGE_  │            │                      │
│    API_KEY: ${{   │            │  Script reads:       │
│    secrets.* }}   │            │  os.environ.get()    │
│                   │            │                      │
│  ✅ Secure!       │            │  ✅ Secure!          │
│                   │            │                      │
└───────────────────┘            └──────────────────────┘
```

## How It Works

### 1️⃣ GitHub Repository (Public)
- Contains **only safe files**
- `.env.example` has placeholder text
- `.gitignore` prevents `.env` from being committed
- Python scripts use `os.environ.get()`

### 2️⃣ GitHub Secrets (Encrypted)
- Navigate: `Settings → Secrets and variables → Actions`
- Add: `ALPHAVANTAGE_API_KEY` = `your_real_key`
- Encrypted and secure
- Only accessible to GitHub Actions

### 3️⃣ Local .env File (Your Computer Only)
- Create: `cp .env.example .env`
- Edit: Add your real API key
- Protected by `.gitignore`
- Never committed to git

### 4️⃣ Scripts Read from Environment
```python
import os

# ✅ CORRECT - Reads from environment
api_key = os.environ.get('ALPHAVANTAGE_API_KEY')

# ❌ WRONG - Hardcoded
# api_key = "VT0RO0SAME6YV9PC"
```

## File Lifecycle

```
┌──────────────────────────────────────────────────────────┐
│ STEP 1: Initial Repository State                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Git Repository                                           │
│ ├── .env.example  ← Committed ✅ (safe placeholder)     │
│ ├── .gitignore    ← Committed ✅ (protects .env)        │
│ └── *.py          ← Committed ✅ (no secrets)           │
│                                                          │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ STEP 2: Clone Repository to Your Computer               │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ $ git clone https://github.com/you/repo.git             │
│                                                          │
│ Your Computer                                            │
│ ├── .env.example  ← Template                            │
│ ├── .gitignore    ← Protection                          │
│ └── *.py          ← Code                                │
│                                                          │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ STEP 3: Create Local .env File                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ $ cp .env.example .env                                   │
│ $ nano .env  # Add your real API key                    │
│                                                          │
│ Your Computer                                            │
│ ├── .env.example  ← Template (committed)                │
│ ├── .env          ← YOUR KEY 🔒 (NOT committed!)        │
│ ├── .gitignore    ← Blocks .env from git                │
│ └── *.py          ← Code                                │
│                                                          │
│ When you run: git add .                                  │
│ Result: .env is IGNORED (protected by .gitignore)       │
│                                                          │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ STEP 4: Verify Protection                               │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ $ git status                                             │
│                                                          │
│ Changes to be committed:                                 │
│   modified: script.py    ✅                             │
│                                                          │
│ Untracked files:                                         │
│   (nothing)              ✅ .env is HIDDEN               │
│                                                          │
│ $ git add .env                                           │
│ The following paths are ignored by .gitignore:           │
│   .env                   ✅ PROTECTED!                   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Testing the Setup

### ✅ Verify .env is Protected

```bash
# Try to add .env (should be blocked)
$ git add .env

# Expected output:
# The following paths are ignored by one of your .gitignore files:
# .env

# Check what will be committed
$ git status

# .env should NOT appear in the list
```

### ✅ Verify Environment Variable Works

```bash
# Set the variable
$ export ALPHAVANTAGE_API_KEY=your_key_here

# Or load from .env
$ export $(cat .env | xargs)

# Test
$ python3 -c "import os; print('Key:', os.environ.get('ALPHAVANTAGE_API_KEY', 'NOT SET'))"

# Expected: Should print your key
```

### ✅ Verify Script Works

```bash
$ cd dual_momentum_system
$ python3 examples/quick_alpha_vantage_test.py

# Expected:
# ✓ AlphaVantageSource initialized
# ✓ API is available
# ✓ SUCCESS - Alpha Vantage is working!
```

## Summary Checklist

### On GitHub
- [ ] Repository has `.gitignore` with `.env` listed
- [ ] Only `.env.example` is committed (with placeholders)
- [ ] Secrets added: Settings → Secrets → Actions
- [ ] GitHub Actions workflow uses `${{ secrets.ALPHAVANTAGE_API_KEY }}`

### On Your Computer
- [ ] Created `.env` from `.env.example`
- [ ] Added real API key to `.env`
- [ ] Verified `.env` is ignored by git
- [ ] Scripts run successfully with environment variable

### In Code
- [ ] All scripts use `os.environ.get('ALPHAVANTAGE_API_KEY')`
- [ ] No hardcoded API keys
- [ ] Error handling for missing keys
- [ ] Tests pass locally and in CI

## 🎯 Result

✅ **API key is secure**  
✅ **Works in GitHub Actions**  
✅ **Works locally**  
✅ **No secrets in repository**  
✅ **Security checks pass**  

Your setup is now **production-ready and secure**! 🎉
