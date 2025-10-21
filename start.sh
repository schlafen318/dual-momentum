#!/bin/bash
# Railway startup script for Streamlit app

# Navigate to the app directory
cd dual_momentum_system

# Start Streamlit with Railway's dynamic port
streamlit run frontend/app.py --server.port=$PORT --server.headless=true --server.address=0.0.0.0
