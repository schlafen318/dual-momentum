#!/bin/bash
# Start the REST API server

cd "$(dirname "$0")"

echo "Starting Dual Momentum Backtesting API..."
echo ""
echo "API will be available at:"
echo "  - API: http://localhost:8000"
echo "  - Docs: http://localhost:8000/api/docs"
echo "  - ReDoc: http://localhost:8000/api/redoc"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

