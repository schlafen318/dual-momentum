# Security Notes - API Key Management

## ✅ Security Fix Applied

All hardcoded API keys have been removed from the codebase. API keys must now be provided via environment variables.

## Protected Files

The following files are configured to never be committed to git:

- `.env` - Your local environment variables
- `.env.local` - Local overrides
- `.env.*.local` - Environment-specific local configs

See `.gitignore` for full list.

## Safe API Key Usage

### ✅ CORRECT - Use Environment Variables

```python
import os
from src.data_sources import AlphaVantageSource

# Read from environment variable
api_key = os.environ.get('ALPHAVANTAGE_API_KEY')

source = AlphaVantageSource({'api_key': api_key})
```

### ✅ CORRECT - Use .env File (Not Committed)

Create a `.env` file (already in .gitignore):

```bash
# .env file (NOT committed to git)
ALPHAVANTAGE_API_KEY=your_actual_api_key_here
```

### ❌ WRONG - Hardcoded Keys

```python
# NEVER do this - will fail security checks
source = AlphaVantageSource({'api_key': 'VT0RO0SAME6YV9PC'})
```

## Setting Up Your API Key

### 1. Get Your API Key

Visit: https://www.alphavantage.co/support/#api-key

### 2. Set Environment Variable

**Option A: Command Line (Temporary)**
```bash
export ALPHAVANTAGE_API_KEY=your_api_key_here
```

**Option B: .env File (Persistent, Recommended)**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and replace YOUR_API_KEY_HERE with your actual key
nano .env  # or use your preferred editor
```

**Option C: Shell Profile (Permanent)**
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export ALPHAVANTAGE_API_KEY=your_api_key_here' >> ~/.bashrc
source ~/.bashrc
```

### 3. Verify Setup

```bash
# Check environment variable is set
echo $ALPHAVANTAGE_API_KEY

# Should print your API key (first few chars)
# If empty, it's not set
```

### 4. Test the Integration

```bash
cd dual_momentum_system
python3 examples/quick_alpha_vantage_test.py
```

## CI/CD and Production

### GitHub Actions

Add as repository secret:
1. Go to Settings → Secrets → Actions
2. Add `ALPHAVANTAGE_API_KEY`
3. Reference in workflow:

```yaml
env:
  ALPHAVANTAGE_API_KEY: ${{ secrets.ALPHAVANTAGE_API_KEY }}
```

### Docker

Pass as environment variable:

```bash
docker run -e ALPHAVANTAGE_API_KEY=$ALPHAVANTAGE_API_KEY myapp
```

Or use docker-compose:

```yaml
services:
  app:
    environment:
      - ALPHAVANTAGE_API_KEY=${ALPHAVANTAGE_API_KEY}
```

### Cloud Platforms

- **Heroku**: `heroku config:set ALPHAVANTAGE_API_KEY=your_key`
- **AWS**: Use AWS Secrets Manager or Parameter Store
- **GCP**: Use Secret Manager
- **Azure**: Use Key Vault

## Security Checklist

Before committing code:

- [ ] No API keys in code files
- [ ] `.env` files in `.gitignore`
- [ ] All examples use `os.environ.get()`
- [ ] Documentation uses placeholders (`your_api_key_here`)
- [ ] Test scripts check for missing env vars

## What Was Fixed

1. ✅ Removed hardcoded API key from all Python files
2. ✅ Updated `.env.example` to use placeholder
3. ✅ Modified all examples to read from environment
4. ✅ Added error messages for missing API keys
5. ✅ Created `.gitignore` to prevent `.env` commits
6. ✅ Updated documentation with security best practices

## Files That Were Updated

- `examples/quick_alpha_vantage_test.py` - Now reads from env
- `examples/alpha_vantage_demo.py` - Now reads from env
- `examples/backtest_with_alpha_vantage.py` - Now reads from env
- `.env.example` - Changed to placeholder
- `ALPHA_VANTAGE_SETUP.md` - Updated all examples
- `ALPHA_VANTAGE_FILES.txt` - Removed key references

## Verification

Run security scan:

```bash
# Check for any remaining hardcoded keys
grep -r "VT0RO0SAME6YV9PC" dual_momentum_system/
# Should return: No matches found
```

## Support

If you need help:
1. Check your environment variable is set: `echo $ALPHAVANTAGE_API_KEY`
2. Verify `.env` file exists and has correct format
3. Make sure you're in the right directory when running scripts
4. See `ALPHA_VANTAGE_SETUP.md` for detailed setup guide

## Best Practices

1. **Never commit `.env` files** - They're in `.gitignore` for a reason
2. **Use different keys for dev/prod** - Get separate API keys
3. **Rotate keys regularly** - Change API keys periodically
4. **Limit key permissions** - Use minimum necessary permissions
5. **Monitor usage** - Watch for unusual API call patterns

---

**Last Updated**: Security fix applied - all hardcoded keys removed
**Status**: ✅ SECURE - No hardcoded API keys in repository
