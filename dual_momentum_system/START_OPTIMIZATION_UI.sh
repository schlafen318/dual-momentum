#!/bin/bash
#
# Quick start script for Portfolio Optimization UI
#

cd "$(dirname "$0")"

echo "════════════════════════════════════════════════════════════════"
echo "  🚀 Starting Dual Momentum Backtest Dashboard"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "The app has TWO optimization features:"
echo ""
echo "  1️⃣  HYPERPARAMETER OPTIMIZATION (Backtest Parameters)"
echo "      → Navigate to: 🎯 Hyperparameter Tuning"
echo "      → Click tab: 🔬 Compare Methods"
echo "      → Compare: Grid Search, Random Search, Bayesian"
echo ""
echo "  2️⃣  PORTFOLIO OPTIMIZATION (Asset Allocation)"
echo "      → Navigate to: 💼 Portfolio Optimization"
echo "      → Compare: 7 portfolio construction methods"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Starting Streamlit app in 3 seconds..."
sleep 3

# Start streamlit
streamlit run frontend/app.py
