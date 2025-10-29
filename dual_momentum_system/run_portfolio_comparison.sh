#!/bin/bash

# Portfolio Optimization Comparison Runner
# Easy script to run and view portfolio optimization results

echo "========================================================================"
echo "PORTFOLIO OPTIMIZATION COMPARISON"
echo "========================================================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

# Show menu
echo "What would you like to do?"
echo ""
echo "1) Run full comparison (all 7 methods)"
echo "2) Run quick comparison (3 methods, faster)"
echo "3) Run individual method demo"
echo "4) View saved results"
echo "5) View saved results + create visualizations"
echo "6) Create HTML report"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        echo ""
        echo "Running full comparison with all 7 optimization methods..."
        echo ""
        python3 examples/portfolio_optimization_comparison_demo.py
        ;;
    2)
        echo ""
        echo "Running quick comparison (Equal Weight, Risk Parity, Max Sharpe)..."
        echo ""
        python3 examples/portfolio_optimization_comparison_demo.py --quick
        ;;
    3)
        echo ""
        echo "Running individual method demonstrations..."
        echo ""
        python3 examples/portfolio_optimization_comparison_demo.py --individual
        ;;
    4)
        echo ""
        echo "Viewing saved results..."
        echo ""
        python3 examples/view_portfolio_results.py
        ;;
    5)
        echo ""
        echo "Viewing saved results and creating visualizations..."
        echo ""
        python3 examples/view_portfolio_results.py
        ;;
    6)
        echo ""
        echo "Creating HTML report..."
        echo ""
        python3 examples/view_portfolio_results.py --html
        echo ""
        echo "Report created! Open portfolio_optimization_results/portfolio_optimization_report.html"
        ;;
    *)
        echo ""
        echo "Invalid choice. Please run again and select 1-6."
        exit 1
        ;;
esac

echo ""
echo "========================================================================"
echo "COMPLETE"
echo "========================================================================"
echo ""
echo "Results saved to: portfolio_optimization_results/"
echo ""
echo "To view results again, run:"
echo "  python3 examples/view_portfolio_results.py"
echo ""
echo "To create HTML report, run:"
echo "  python3 examples/view_portfolio_results.py --html"
echo ""
