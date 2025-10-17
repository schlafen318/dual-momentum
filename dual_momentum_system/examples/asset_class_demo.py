#!/usr/bin/env python3
"""
Demonstration of the 5 major asset classes.

This script showcases the extensibility of the dual momentum framework
by demonstrating all 5 implemented asset classes and their unique features.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, '/workspace/dual_momentum_system')

from src.asset_classes import (
    EquityAsset,
    CryptoAsset,
    CommodityAsset,
    BondAsset,
    FXAsset
)


def generate_sample_data(symbol, periods=100):
    """Generate sample OHLCV data for demonstration."""
    dates = pd.date_range(end=datetime.now(), periods=periods, freq='D')
    base_price = 100.0
    
    data = pd.DataFrame({
        'Open': base_price + np.random.randn(periods).cumsum(),
        'High': base_price + np.random.randn(periods).cumsum() + 5,
        'Low': base_price + np.random.randn(periods).cumsum() - 5,
        'Close': base_price + np.random.randn(periods).cumsum(),
        'Volume': np.random.randint(1000000, 10000000, periods)
    }, index=dates)
    
    # Ensure high is highest and low is lowest
    data['High'] = data[['Open', 'High', 'Low', 'Close']].max(axis=1)
    data['Low'] = data[['Open', 'High', 'Low', 'Close']].min(axis=1)
    
    return data


def demo_equity():
    """Demonstrate EquityAsset capabilities."""
    print("\n" + "="*80)
    print("1. EQUITY ASSET CLASS - Stocks & Equities")
    print("="*80)
    
    equity = EquityAsset()
    
    # Test various symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'BRK.A', 'invalid123']
    print("\n📊 Symbol Validation:")
    for symbol in symbols:
        valid = equity.validate_symbol(symbol)
        status = "✓" if valid else "✗"
        print(f"  {status} {symbol}: {'Valid' if valid else 'Invalid'}")
    
    # Get metadata
    print("\n📋 Metadata for AAPL:")
    metadata = equity.get_metadata('AAPL')
    print(f"  Name: {metadata.name}")
    print(f"  Exchange: {metadata.exchange}")
    print(f"  Tick Size: ${metadata.tick_size}")
    print(f"  Trading Hours: {metadata.trading_hours['regular']}")
    
    # Process data
    sample_data = generate_sample_data('AAPL')
    price_data = equity.normalize_data(sample_data, 'AAPL')
    
    print(f"\n📈 Price Data Analysis:")
    print(f"  Data Points: {len(price_data.data)}")
    print(f"  Date Range: {price_data.data.index[0].date()} to {price_data.data.index[-1].date()}")
    print(f"  Latest Close: ${price_data.data['close'].iloc[-1]:.2f}")
    
    returns = equity.calculate_returns(price_data)
    print(f"  Average Daily Return: {returns.mean()*100:.2f}%")
    
    volatility = equity.calculate_volatility(price_data, window=20)
    print(f"  Annualized Volatility: {volatility.iloc[-1]*100:.2f}%")


def demo_crypto():
    """Demonstrate CryptoAsset capabilities."""
    print("\n" + "="*80)
    print("2. CRYPTO ASSET CLASS - Cryptocurrencies")
    print("="*80)
    
    crypto = CryptoAsset()
    
    # Test various formats
    symbols = ['BTC/USD', 'ETH-USDT', 'BTCUSD', 'XYZ/ABC']
    print("\n📊 Symbol Validation (supports multiple formats):")
    for symbol in symbols:
        valid = crypto.validate_symbol(symbol)
        status = "✓" if valid else "✗"
        print(f"  {status} {symbol}: {'Valid' if valid else 'Invalid'}")
    
    # Get metadata
    print("\n📋 Metadata for BTC/USD:")
    metadata = crypto.get_metadata('BTC/USD')
    print(f"  Name: {metadata.name}")
    print(f"  Exchange: {metadata.exchange}")
    print(f"  Quote Currency: {metadata.currency}")
    print(f"  Trading: {metadata.trading_hours['note']}")
    print(f"  Decimal Places: {metadata.additional_info['decimal_places']}")
    
    # 24/7 trading
    print(f"\n⏰ 24/7 Trading:")
    test_dates = pd.date_range('2023-10-01', periods=7, freq='D')
    for date in test_dates:
        is_trading = crypto.is_trading_day(date)
        print(f"  {date.strftime('%A')}: {'Open' if is_trading else 'Closed'}")


def demo_commodity():
    """Demonstrate CommodityAsset capabilities."""
    print("\n" + "="*80)
    print("3. COMMODITY ASSET CLASS - Futures & Physical Commodities")
    print("="*80)
    
    commodity = CommodityAsset()
    
    # Test various commodities
    symbols = ['GC', 'CL', 'ZC', 'GCZ23', 'HE']
    print("\n📊 Commodity Symbols:")
    for symbol in symbols:
        if commodity.validate_symbol(symbol):
            metadata = commodity.get_metadata(symbol)
            print(f"  ✓ {symbol:8s} - {metadata.name}")
            print(f"    Type: {metadata.additional_info['commodity_type']}")
            print(f"    Exchange: {metadata.exchange}")
    
    # Contract details
    print("\n📋 Gold Futures (GC) Details:")
    metadata = commodity.get_metadata('GC')
    print(f"  Contract Size: {metadata.additional_info['contract_size']} oz")
    print(f"  Tick Size: ${metadata.tick_size}")
    print(f"  Settlement: {metadata.additional_info['settlement']}")
    
    # Contract month parsing
    print("\n📅 Contract Month Parsing:")
    contract_symbol = 'GCZ23'
    month = commodity.get_contract_month(contract_symbol)
    year = commodity.get_contract_year(contract_symbol)
    print(f"  Symbol: {contract_symbol}")
    print(f"  Contract Month: {month}")
    print(f"  Contract Year: {year}")


def demo_bond():
    """Demonstrate BondAsset capabilities."""
    print("\n" + "="*80)
    print("4. BOND ASSET CLASS - Fixed Income Securities")
    print("="*80)
    
    bond = BondAsset()
    
    # Test bond instruments
    symbols = ['TLT', 'AGG', 'LQD', 'HYG', 'MUB']
    print("\n📊 Bond Instruments:")
    for symbol in symbols:
        if bond.validate_symbol(symbol):
            metadata = bond.get_metadata(symbol)
            duration = metadata.additional_info.get('duration', 'N/A')
            rating = metadata.additional_info.get('credit_rating', 'N/A')
            print(f"  ✓ {symbol:5s} - {metadata.name}")
            print(f"    Duration: {duration:.1f} years | Rating: {rating}")
    
    # Bond-specific calculations
    print("\n📋 Bond Calculations (TLT - 20+ Year Treasury):")
    metadata = bond.get_metadata('TLT')
    print(f"  Bond Type: {metadata.additional_info['bond_type']}")
    print(f"  Duration: {metadata.additional_info['duration']} years")
    print(f"  Coupon Frequency: {metadata.additional_info['coupon_frequency']}")
    
    # Yield to maturity example
    ytm = bond.calculate_yield_to_maturity(
        price=95.0,
        face_value=100.0,
        coupon_rate=0.03,
        years_to_maturity=10
    )
    print(f"\n💰 Sample YTM Calculation:")
    print(f"  Price: $95.00 | Par: $100.00 | Coupon: 3%")
    print(f"  Approximate YTM: {ytm*100:.2f}%")


def demo_fx():
    """Demonstrate FXAsset capabilities."""
    print("\n" + "="*80)
    print("5. FX ASSET CLASS - Foreign Exchange")
    print("="*80)
    
    fx = FXAsset()
    
    # Test currency pairs
    pairs = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'EUR/GBP']
    print("\n📊 Currency Pairs:")
    for pair in pairs:
        if fx.validate_symbol(pair):
            metadata = fx.get_metadata(pair)
            category = metadata.additional_info['pair_category']
            spread = metadata.additional_info['typical_spread_pips']
            print(f"  ✓ {metadata.symbol:8s} - {metadata.name}")
            print(f"    Category: {category.title()} | Typical Spread: {spread} pips")
    
    # Pip calculations
    print("\n📋 EUR/USD Trading Details:")
    metadata = fx.get_metadata('EUR/USD')
    pip_value = fx.calculate_pip_value('EUR/USD', lot_size=100000)
    print(f"  Pip Value (standard lot): ${pip_value:.2f}")
    print(f"  Standard Lot: {metadata.additional_info['standard_lot']:,.0f} units")
    print(f"  Mini Lot: {metadata.additional_info['mini_lot']:,.0f} units")
    print(f"  Micro Lot: {metadata.additional_info['micro_lot']:,.0f} units")
    
    # Position sizing
    print("\n💼 Position Sizing Example:")
    position_size = fx.calculate_position_size(
        account_balance=10000,
        risk_percent=0.02,  # 2% risk
        stop_loss_pips=50,
        symbol='EUR/USD'
    )
    print(f"  Account: $10,000 | Risk: 2% | Stop Loss: 50 pips")
    print(f"  Position Size: {position_size:.2f} lots")
    
    # Trading sessions
    print("\n🌍 Global Trading Sessions:")
    for session, times in fx.trading_sessions.items():
        print(f"  {session.title():12s}: {times['open']} - {times['close']} UTC")


def main():
    """Run all demonstrations."""
    print("\n" + "="*80)
    print("DUAL MOMENTUM FRAMEWORK - ASSET CLASS EXTENSIBILITY DEMONSTRATION")
    print("="*80)
    print("\nThis demonstrates 5 major asset classes, each with unique characteristics")
    print("while conforming to the same BaseAssetClass interface.")
    
    demo_equity()
    demo_crypto()
    demo_commodity()
    demo_bond()
    demo_fx()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("""
✅ All 5 asset classes successfully implemented:
   1. EquityAsset    - Stocks with split/dividend handling
   2. CryptoAsset    - 24/7 trading, fractional shares
   3. CommodityAsset - Futures contracts, expiration dates
   4. BondAsset      - Fixed income, duration, yield calculations
   5. FXAsset        - Currency pairs, pip values, 24/5 trading

🎯 Framework Benefits:
   • Consistent interface across all asset types
   • Easy to add new asset classes
   • Asset-specific features properly encapsulated
   • Extensible plugin architecture
   • Type-safe with proper validation
    """)


if __name__ == '__main__':
    main()
