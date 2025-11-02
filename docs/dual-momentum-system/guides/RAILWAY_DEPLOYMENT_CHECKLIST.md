# Railway Deployment Checklist ✅

Quick reference for deploying this Streamlit app to Railway.

## Pre-Deployment Verification ✅

All checks passed:

- ✅ **Procfile exists** - Uses `$PORT` correctly
- ✅ **runtime.txt exists** - Specifies Python 3.11.0
- ✅ **requirements.txt exists** - All dependencies listed
- ✅ **Python syntax valid** - All `.py` files compile without errors
- ✅ **File handling safe** - Uses `mkdir(parents=True, exist_ok=True)`
- ✅ **Environment variables** - Properly handled with fallbacks
- ✅ **Port configuration** - Procfile overrides .streamlit/config.toml

## Deployment Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Deploy to Railway"
git push origin main
```

### 2. Create Railway Project
1. Go to https://railway.app
2. Sign in with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose this repository
6. Railway auto-detects Python and deploys

### 3. Set Environment Variables (Optional)
In Railway dashboard → Variables:
- `ALPHAVANTAGE_API_KEY` = your_key_here (optional)
- `TWELVEDATA_API_KEY` = your_key_here (optional)

### 4. Deploy
- Railway builds automatically
- First build: ~5-10 minutes (compiling dependencies)
- Subsequent builds: ~2-3 minutes
- App will be live at: `https://your-app.railway.app`

## Testing After Deployment

### Essential Tests
- [ ] Homepage loads
- [ ] All navigation pages accessible
- [ ] Run a simple backtest (e.g., SPY)
- [ ] Download CSV/JSON export
- [ ] Test with custom asset universe

### Optional Tests
- [ ] Test Alpha Vantage integration (if API key set)
- [ ] Test Twelve Data integration (if API key set)
- [ ] Run memory-intensive backtest
- [ ] Test on mobile device

## Monitoring

### What to Watch
1. **Memory Usage** - Check Railway metrics
   - Normal: 200-500 MB
   - High: 1-2 GB (heavy backtests)
   - Limit: 512 MB (Hobby), 8 GB (Developer)

2. **Build Times**
   - Initial: 5-10 minutes (normal)
   - Rebuilds: 2-3 minutes (normal)

3. **Logs** - Check Railway logs for errors
   ```bash
   # Common log patterns to watch
   # ✅ Good: "You can now view your Streamlit app"
   # ⚠️  Warning: "MemoryError"
   # ❌ Error: "ModuleNotFoundError"
   ```

## Known Limitations

### Ephemeral Storage ⚠️
- Custom asset universes **reset on redeploy**
- Data in `data/asset_universes.json` is **not persistent**
- Workaround: Re-create universes or use environment variables

### Memory Constraints
- Hobby plan (512 MB): May fail on large backtests
- Solution: Upgrade to Developer plan (8 GB)

### Build Time
- Heavy dependencies (`vectorbt`, `scipy`): Slow first build
- Solution: Be patient; subsequent builds are faster

## Troubleshooting

### App Won't Start
```bash
# Check Railway logs for:
1. Missing dependencies → Add to requirements.txt
2. Port binding issues → Verify Procfile uses $PORT
3. Import errors → Check Python version compatibility
```

### Memory Errors
```bash
# Solutions:
1. Reduce backtest date range
2. Use fewer assets in universe
3. Upgrade Railway plan
```

### Slow Performance
```bash
# Possible causes:
1. Cold start (first request after idle)
2. Large dataset downloads
3. Complex calculations

# Solutions:
1. Wait for warm-up
2. Cache frequently-used data
3. Optimize backtest parameters
```

## Cost Estimates

### Hobby Plan ($5 free credit/month)
- Good for: Testing, demos, light use
- Limits: 512 MB RAM, may hit memory issues
- Cost: Free (uses monthly credit)

### Developer Plan ($20/month)
- Good for: Production, heavy backtests
- Limits: 8 GB RAM, plenty of headroom
- Cost: $20/month flat

**Recommendation**: Start with Hobby, upgrade if needed

## Success Criteria

Your deployment is successful when:
- ✅ App loads without errors
- ✅ All pages render correctly
- ✅ Backtests can be executed
- ✅ Results can be downloaded
- ✅ No memory errors in logs

## Quick Commands

### View Logs
```bash
# In Railway dashboard: Deployments → View Logs
```

### Redeploy
```bash
# Push any commit to GitHub
git commit --allow-empty -m "Trigger redeploy"
git push
```

### Rollback
```bash
# In Railway dashboard: Deployments → Select previous → Rollback
```

## Support Resources

- Railway Docs: https://docs.railway.app
- Streamlit Docs: https://docs.streamlit.io
- Community: https://discord.gg/railway
- This App: See `RAILWAY_COMPATIBILITY_REPORT.md`

---

**Status**: ✅ READY FOR DEPLOYMENT
**Last Verified**: 2025-10-21
**Confidence**: 95%
