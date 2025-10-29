"""
Portfolio Optimization Results Viewer

Simple script to visualize and analyze portfolio optimization results.
Can be used to view results from saved files or generate new comparisons.
"""

import sys
from pathlib import Path
import argparse
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def view_saved_results(results_dir: str = './portfolio_optimization_results'):
    """
    View results from saved portfolio optimization comparison.
    
    Args:
        results_dir: Directory containing saved results
    """
    results_path = Path(results_dir)
    
    if not results_path.exists():
        print(f"❌ Results directory not found: {results_dir}")
        print("   Run the demo first: python examples/portfolio_optimization_comparison_demo.py")
        return
    
    # Find latest results files
    comparison_files = list(results_path.glob('*_comparison.csv'))
    weights_files = list(results_path.glob('*_weights.csv'))
    summary_files = list(results_path.glob('*_summary.json'))
    
    if not comparison_files:
        print(f"❌ No results found in {results_dir}")
        print("   Run the demo first: python examples/portfolio_optimization_comparison_demo.py")
        return
    
    # Use most recent files
    comparison_file = sorted(comparison_files)[-1]
    weights_file = sorted(weights_files)[-1]
    summary_file = sorted(summary_files)[-1]
    
    print("="*80)
    print("PORTFOLIO OPTIMIZATION RESULTS VIEWER")
    print("="*80)
    print(f"\nLoading results from: {results_path}")
    print(f"  Comparison: {comparison_file.name}")
    print(f"  Weights: {weights_file.name}")
    print(f"  Summary: {summary_file.name}")
    print()
    
    # Load data
    comparison_df = pd.read_csv(comparison_file)
    weights_df = pd.read_csv(weights_file, index_col=0)
    
    with open(summary_file, 'r') as f:
        summary = json.load(f)
    
    # Display summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Methods compared: {summary['n_methods_compared']}")
    print(f"Assets: {summary['n_assets']}")
    print(f"Date: {summary['timestamp']}")
    print()
    print(f"🏆 Best Sharpe Ratio: {summary['best_sharpe_method'].replace('_', ' ').title()}")
    print(f"   Score: {summary['best_sharpe_ratio']:.4f}")
    print()
    print(f"📊 Best Diversification: {summary['best_diversification_method'].replace('_', ' ').title()}")
    print(f"   Score: {summary['best_diversification_ratio']:.4f}")
    print()
    print(f"📉 Lowest Volatility: {summary['lowest_volatility_method'].replace('_', ' ').title()}")
    print(f"   Score: {summary['lowest_volatility']:.4f}")
    print()
    
    # Display comparison metrics
    print("="*80)
    print("COMPARISON METRICS")
    print("="*80)
    print()
    
    # Format for display
    display_df = comparison_df.copy()
    for col in ['expected_return', 'expected_volatility', 'sharpe_ratio', 'diversification_ratio']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.4f}" if pd.notnull(x) else "N/A")
    
    print(display_df.to_string(index=False))
    print()
    
    # Display weights
    print("="*80)
    print("PORTFOLIO WEIGHTS")
    print("="*80)
    print()
    
    # Format weights as percentages
    weights_display = weights_df * 100
    print(weights_display.round(2).to_string())
    print()
    
    # Create visualizations
    create_visualizations(comparison_df, weights_df, summary, results_path)


def create_visualizations(comparison_df, weights_df, summary, output_dir):
    """
    Create visualization charts.
    """
    print("="*80)
    print("CREATING VISUALIZATIONS")
    print("="*80)
    print()
    
    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (12, 8)
    
    # 1. Sharpe Ratio Comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    
    methods = comparison_df['method'].tolist()
    sharpe_ratios = comparison_df['sharpe_ratio'].tolist()
    
    # Color best method differently
    colors = ['green' if method == summary['best_sharpe_method'].replace('_', ' ').title() 
              else 'steelblue' for method in methods]
    
    bars = ax.bar(range(len(methods)), sharpe_ratios, color=colors, alpha=0.7)
    ax.set_xticks(range(len(methods)))
    ax.set_xticklabels(methods, rotation=45, ha='right')
    ax.set_ylabel('Sharpe Ratio')
    ax.set_title('Sharpe Ratio by Optimization Method')
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        if pd.notnull(height):
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}',
                   ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    sharpe_path = output_dir / 'sharpe_comparison.png'
    plt.savefig(sharpe_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {sharpe_path.name}")
    plt.close()
    
    # 2. Weights Heatmap
    fig, ax = plt.subplots(figsize=(12, 8))
    
    sns.heatmap(
        weights_df * 100,  # Convert to percentages
        annot=True,
        fmt='.1f',
        cmap='YlOrRd',
        cbar_kws={'label': 'Weight (%)'},
        ax=ax
    )
    ax.set_title('Portfolio Weights by Method (%)')
    ax.set_xlabel('Optimization Method')
    ax.set_ylabel('Asset')
    
    plt.tight_layout()
    heatmap_path = output_dir / 'weights_heatmap.png'
    plt.savefig(heatmap_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {heatmap_path.name}")
    plt.close()
    
    # 3. Volatility vs Return Scatter
    fig, ax = plt.subplots(figsize=(10, 7))
    
    for idx, row in comparison_df.iterrows():
        method = row['method']
        ret = row['expected_return']
        vol = row['expected_volatility']
        
        # Highlight best Sharpe method
        if method == summary['best_sharpe_method'].replace('_', ' ').title():
            ax.scatter(vol, ret, s=200, c='green', marker='*', 
                      label=f'{method} (Best)', zorder=5, edgecolors='black', linewidths=2)
        else:
            ax.scatter(vol, ret, s=100, alpha=0.6)
            ax.annotate(method, (vol, ret), fontsize=8, 
                       xytext=(5, 5), textcoords='offset points')
    
    ax.set_xlabel('Expected Volatility (Risk)')
    ax.set_ylabel('Expected Return')
    ax.set_title('Risk-Return Profile by Method')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    scatter_path = output_dir / 'risk_return_scatter.png'
    plt.savefig(scatter_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {scatter_path.name}")
    plt.close()
    
    # 4. Diversification Comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    
    div_ratios = comparison_df['diversification_ratio'].tolist()
    colors_div = ['green' if method == summary['best_diversification_method'].replace('_', ' ').title() 
                  else 'coral' for method in methods]
    
    bars = ax.bar(range(len(methods)), div_ratios, color=colors_div, alpha=0.7)
    ax.set_xticks(range(len(methods)))
    ax.set_xticklabels(methods, rotation=45, ha='right')
    ax.set_ylabel('Diversification Ratio')
    ax.set_title('Diversification Ratio by Method')
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        if pd.notnull(height):
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}',
                   ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    div_path = output_dir / 'diversification_comparison.png'
    plt.savefig(div_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {div_path.name}")
    plt.close()
    
    # 5. Weight Distribution
    fig, ax = plt.subplots(figsize=(12, 8))
    
    weights_df_pct = weights_df * 100
    weights_df_pct.T.plot(kind='bar', ax=ax, width=0.8)
    
    ax.set_xlabel('Optimization Method')
    ax.set_ylabel('Weight (%)')
    ax.set_title('Portfolio Weight Distribution by Method')
    ax.legend(title='Asset', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    dist_path = output_dir / 'weight_distribution.png'
    plt.savefig(dist_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {dist_path.name}")
    plt.close()
    
    print()
    print("="*80)
    print("VISUALIZATIONS COMPLETE")
    print("="*80)
    print(f"\nAll charts saved to: {output_dir}")
    print("  • sharpe_comparison.png")
    print("  • weights_heatmap.png")
    print("  • risk_return_scatter.png")
    print("  • diversification_comparison.png")
    print("  • weight_distribution.png")
    print()


def create_html_report(results_dir: str = './portfolio_optimization_results'):
    """
    Create an HTML report with all results and visualizations.
    """
    results_path = Path(results_dir)
    
    if not results_path.exists():
        print(f"❌ Results directory not found: {results_dir}")
        return
    
    # Find files
    comparison_files = list(results_path.glob('*_comparison.csv'))
    summary_files = list(results_path.glob('*_summary.json'))
    
    if not comparison_files or not summary_files:
        print(f"❌ No results found in {results_dir}")
        return
    
    comparison_file = sorted(comparison_files)[-1]
    summary_file = sorted(summary_files)[-1]
    
    # Load data
    comparison_df = pd.read_csv(comparison_file)
    with open(summary_file, 'r') as f:
        summary = json.load(f)
    
    # Create HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Portfolio Optimization Results</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .summary {{
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .best-method {{
            background-color: #d5f4e6;
            padding: 15px;
            border-left: 4px solid #27ae60;
            margin: 10px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        img {{
            max-width: 100%;
            height: auto;
            margin: 20px 0;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Portfolio Optimization Results</h1>
        
        <div class="summary">
            <h2>Summary</h2>
            <p><strong>Date:</strong> {summary['timestamp']}</p>
            <p><strong>Methods Compared:</strong> {summary['n_methods_compared']}</p>
            <p><strong>Assets:</strong> {summary['n_assets']}</p>
        </div>
        
        <div class="best-method">
            <h3>🏆 Best Sharpe Ratio</h3>
            <p><strong>Method:</strong> {summary['best_sharpe_method'].replace('_', ' ').title()}</p>
            <p><strong>Sharpe Ratio:</strong> {summary['best_sharpe_ratio']:.4f}</p>
        </div>
        
        <div class="best-method">
            <h3>📊 Best Diversification</h3>
            <p><strong>Method:</strong> {summary['best_diversification_method'].replace('_', ' ').title()}</p>
            <p><strong>Diversification Ratio:</strong> {summary['best_diversification_ratio']:.4f}</p>
        </div>
        
        <div class="best-method">
            <h3>📉 Lowest Volatility</h3>
            <p><strong>Method:</strong> {summary['lowest_volatility_method'].replace('_', ' ').title()}</p>
            <p><strong>Volatility:</strong> {summary['lowest_volatility']:.4f}</p>
        </div>
        
        <h2>Comparison Metrics</h2>
        {comparison_df.to_html(index=False, classes='table')}
        
        <h2>Visualizations</h2>
        <h3>Sharpe Ratio Comparison</h3>
        <img src="sharpe_comparison.png" alt="Sharpe Ratio Comparison">
        
        <h3>Portfolio Weights Heatmap</h3>
        <img src="weights_heatmap.png" alt="Weights Heatmap">
        
        <h3>Risk-Return Profile</h3>
        <img src="risk_return_scatter.png" alt="Risk-Return Scatter">
        
        <h3>Diversification Comparison</h3>
        <img src="diversification_comparison.png" alt="Diversification Comparison">
        
        <h3>Weight Distribution</h3>
        <img src="weight_distribution.png" alt="Weight Distribution">
    </div>
</body>
</html>
"""
    
    # Save HTML report
    html_path = results_path / 'portfolio_optimization_report.html'
    with open(html_path, 'w') as f:
        f.write(html)
    
    print(f"\n✓ HTML report created: {html_path}")
    print(f"  Open in browser: file://{html_path.absolute()}")


def main():
    parser = argparse.ArgumentParser(
        description='View portfolio optimization results'
    )
    parser.add_argument(
        '--dir',
        default='./portfolio_optimization_results',
        help='Results directory (default: ./portfolio_optimization_results)'
    )
    parser.add_argument(
        '--html',
        action='store_true',
        help='Create HTML report'
    )
    
    args = parser.parse_args()
    
    # View results
    view_saved_results(args.dir)
    
    # Create HTML report if requested
    if args.html:
        create_html_report(args.dir)


if __name__ == '__main__':
    main()
