# Setting Up API Key with GitHub Secrets

## ⚠️ Important: Never Commit .env Files to Git

The `.env` file with your real API key should **NEVER** be committed to the GitHub repository. This is why it's in `.gitignore`.

## ✅ Correct Method: GitHub Secrets

For GitHub Actions and CI/CD, use GitHub Secrets instead.

### Step 1: Add Secret to GitHub Repository

1. **Go to your repository on GitHub**
   - Navigate to: `https://github.com/YOUR_USERNAME/YOUR_REPO`

2. **Open Settings**
   - Click `Settings` tab (top right)

3. **Navigate to Secrets**
   - Click `Secrets and variables` → `Actions` (left sidebar)

4. **Add New Secret**
   - Click `New repository secret` button
   - **Name:** `ALPHAVANTAGE_API_KEY`
   - **Value:** `your_api_key_here` (paste your actual API key)
   - Click `Add secret`

### Step 2: Secret is Now Available

The GitHub workflow file (`.github/workflows/test-alpha-vantage.yml`) will automatically use this secret:

```yaml
env:
  ALPHAVANTAGE_API_KEY: ${{ secrets.ALPHAVANTAGE_API_KEY }}
```

### Step 3: Verify Setup

After adding the secret:

1. Go to `Actions` tab
2. Click on `Test Alpha Vantage Integration` workflow
3. Click `Run workflow` → `Run workflow`
4. Watch it run - should complete successfully

## For Local Development

### Create Local .env File (NOT Committed)

```bash
cd dual_momentum_system

# Copy the example
cp .env.example .env

# Edit .env and add your API key
nano .env  # or use your preferred editor
```

Your `.env` file should look like:
```bash
ALPHAVANTAGE_API_KEY=your_actual_api_key_here
```

**This file is already in `.gitignore` and will NOT be committed.**

### Verify Local Setup

```bash
# Load environment variables
source .env  # or: export $(cat .env | xargs)

# Test
python3 examples/quick_alpha_vantage_test.py
```

## Security Checklist

- [ ] ✅ API key stored in GitHub Secrets
- [ ] ✅ `.env` file is in `.gitignore`
- [ ] ✅ Local `.env` file created (not committed)
- [ ] ❌ **NEVER** commit `.env` to repository
- [ ] ❌ **NEVER** hardcode API keys in code

## File Structure

```
dual_momentum_system/
├── .env.example          ✅ Safe - Uses placeholder (committed to git)
├── .env                  🔒 Secret - Real key (NOT committed, in .gitignore)
├── .gitignore            ✅ Protects .env from being committed
└── .github/
    └── workflows/
        └── test-alpha-vantage.yml  ✅ Uses GitHub Secrets
```

## What Gets Committed vs Not

### ✅ Safe to Commit (Already in Repo)
- `.env.example` - Template with placeholders
- `.gitignore` - Protects sensitive files
- `*.py` files - No hardcoded keys
- Workflow files - Uses `${{ secrets.* }}`
- Documentation

### 🔒 NEVER Commit (Protected by .gitignore)
- `.env` - Your actual API keys
- `.env.local` - Local overrides
- Any file with real credentials

## Troubleshooting

### "Secret not found" in GitHub Actions

**Solution:**
1. Check secret name is exactly `ALPHAVANTAGE_API_KEY`
2. Verify it's a repository secret (not environment secret)
3. Make sure you have permissions to add secrets

### Local .env file not working

**Solution:**
```bash
# Check file exists
ls -la .env

# Check it's not empty
cat .env

# Load manually
export ALPHAVANTAGE_API_KEY=your_key_here

# Or use direnv (recommended)
echo "source .env" >> ~/.bashrc
```

### I accidentally committed .env file

**Solution:**
```bash
# Remove from git but keep local file
git rm --cached .env

# Commit the removal
git commit -m "Remove .env from repository"

# Push
git push

# IMPORTANT: Rotate your API key immediately!
# Get a new key from: https://www.alphavantage.co/support/#api-key
```

## Alternative: Environment Variables

Instead of .env file, set directly:

```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export ALPHAVANTAGE_API_KEY=your_key_here' >> ~/.bashrc
source ~/.bashrc
```

## Production Deployment

### Heroku
```bash
heroku config:set ALPHAVANTAGE_API_KEY=your_key_here
```

### Docker
```bash
docker run -e ALPHAVANTAGE_API_KEY=your_key_here myapp
```

### AWS / GCP / Azure
Use their respective secret management services:
- AWS: Secrets Manager
- GCP: Secret Manager
- Azure: Key Vault

## Summary

✅ **GitHub Secrets** - For CI/CD workflows  
✅ **Local .env** - For development (not committed)  
✅ **Environment Variables** - For production  
❌ **NEVER** commit .env to repository  
❌ **NEVER** hardcode keys in code  

Your API key is now secure and available for both GitHub Actions and local development!
