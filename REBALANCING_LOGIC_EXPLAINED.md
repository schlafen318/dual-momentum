# Complete Rebalancing Logic - Step-by-Step Walkthrough

## Overview

This document explains the **exact** rebalancing logic used in the dual momentum trading system, including how portfolio value is updated and how new positions are sized.

---

## 🔄 PHASE 1: Daily Portfolio Updates

**Location:** `engine.py` lines 165-177

### Every Trading Day:
```python
for current_date in date_index:
    # STEP 1: Update position prices with current market prices
    for symbol, position in positions.items():
        position.current_price = get_market_price(symbol, current_date)
    
    # STEP 2: Recalculate total portfolio value
    portfolio_value = cash + sum(quantity × current_price for each position)
    
    # STEP 3: Record in equity curve
    equity_curve.append(portfolio_value)
    
    # STEP 4: Check if rebalancing needed
    if should_rebalance(current_date):
        # Execute rebalancing (see Phase 2)
```

### Example:
```
Day 1: Portfolio = $50,000 cash + (100 SPY × $400) = $90,000
Day 2: Portfolio = $50,000 cash + (100 SPY × $405) = $90,500 ⬆️
Day 3: Portfolio = $50,000 cash + (100 SPY × $398) = $89,800 ⬇️
```

**Key Point:** Portfolio value updates **daily** to reflect current market prices!

---

## 🎯 PHASE 2: Rebalancing Trigger

**Location:** `engine.py` lines 179-185, `base_strategy.py` lines 323-352

### Rebalancing Frequency Check:
```python
should_rebalance = (
    last_rebalance is None or  # First rebalance
    strategy.should_rebalance(current_date, last_rebalance)
)
```

### Frequency Options:
- **Monthly** (default): `current_date.month != last_rebalance.month`
- **Weekly**: `current_date.week != last_rebalance.week`
- **Daily**: Always true
- **Quarterly/Yearly**: Similar logic

### Data Sufficiency Check:
```python
if should_rebalance and i >= strategy.get_required_history():
    # Have enough data (e.g., 252 days for lookback)
    # Proceed with rebalancing
```

---

## 📊 PHASE 3: Signal Generation (SIMPLIFIED)

**Location:** `dual_momentum.py` lines 189-300

### Step 3.1: Calculate Momentum
```python
for each asset:
    momentum[asset] = price_change(lookback_period=252)
    # Example: (price_today - price_252_days_ago) / price_252_days_ago
```

### Step 3.2: Apply Absolute Momentum Filter
```python
filtered_assets = {
    asset: momentum 
    for asset, momentum in all_assets.items()
    if momentum > absolute_threshold  # default: 0.0
}
```

### Step 3.3: Rank by Relative Momentum
```python
sorted_assets = sorted(filtered_assets, 
                       key=lambda x: momentum[x], 
                       reverse=True)
```

### Step 3.4: Binary Decision

#### **OPTION A: Assets Pass Filter**
```python
if len(sorted_assets) > 0:
    # Select top N assets
    top_assets = sorted_assets[:position_count]
    
    # Generate LONG signals
    for asset in top_assets:
        signals.append(Signal(
            symbol=asset,
            direction=LONG,
            strength=1.0,
            reason=RELATIVE_TOP
        ))
```

#### **OPTION B: No Assets Pass Filter**
```python
else:
    # Simple defensive rotation
    if safe_asset:
        signals.append(Signal(
            symbol=safe_asset,      # e.g., 'AGG', 'TLT'
            direction=LONG,
            strength=1.0,
            reason=DEFENSIVE_ROTATION
        ))
    else:
        # No signals = hold cash
        pass
```

**No more blending!** Just a clean binary decision. ✨

---

## 💰 PHASE 4: Position Sizing & Execution

**Location:** `engine.py` lines 558-769

### Step 4.1: Use UPDATED Portfolio Value
```python
# Portfolio value already updated in Phase 1
portfolio_value = cash + sum(quantity × current_price)
# Example: $105,000 (includes unrealized gains!)
```

### Step 4.2: Separate Risk vs Safe Signals
```python
risk_signals = [s for s in signals if s.symbol != safe_asset]
safe_signal = [s for s in signals if s.symbol == safe_asset]
```

### Step 4.3: Calculate Allocation Weights

#### If Using Multiple Positions:
```python
desired_positions = position_count  # e.g., 3
included_count = len(risk_signals)  # e.g., 2

risk_share = included_count / desired_positions  # 2/3 = 66.7%
safe_share = 1.0 - risk_share                    # 33.3%
```

#### Weight by Strength:
```python
total_strength = sum(signal.strength for signal in risk_signals)

for signal in risk_signals:
    weight[signal.symbol] = (signal.strength / total_strength) × risk_share

if safe_signal:
    weight[safe_asset] = safe_share
```

#### Example:
```
Signals: SPY (strength=1.0), EFA (strength=0.8)
position_count: 3

Calculations:
├─ included_count = 2
├─ risk_share = 2/3 = 0.667
├─ safe_share = 1/3 = 0.333
├─ total_strength = 1.0 + 0.8 = 1.8
├─ SPY weight = (1.0/1.8) × 0.667 = 0.370 (37%)
├─ EFA weight = (0.8/1.8) × 0.667 = 0.297 (30%)
└─ AGG weight = 0.333 (33%)
```

### Step 4.4: Calculate Position Sizes

```python
for signal in signals:
    # Get target allocation
    target_pct = weights[signal.symbol]  # e.g., 0.50 (50%)
    
    # Calculate desired dollars using UPDATED portfolio value
    desired_dollars = portfolio_value × target_pct
    # Example: $105,000 × 50% = $52,500
    
    # Adjust for commissions
    position_size = desired_dollars / (1 + commission)
    # Example: $52,500 / 1.001 = $52,448
    
    # Calculate shares to buy
    shares = position_size / execution_price
    
    # Calculate total cost
    commission_cost = position_size × commission
    total_cost = position_size + commission_cost
```

### Step 4.5: Execute Trades
```python
# Close old positions not in new signals
for symbol in old_positions - new_signals:
    close_position(symbol)
    cash += proceeds - commission

# Open/adjust new positions
for signal in signals:
    if symbol in positions:
        adjust_position(symbol, new_shares, price)
    else:
        open_position(symbol, shares, price)
    
    cash -= total_cost
```

---

## 📈 Complete Example Scenario

### Setup
- **Starting Capital**: $100,000
- **Assets**: SPY, EFA, AGG (safe)
- **Config**: `position_count=1`, `lookback_period=252`, `rebalance_frequency='monthly'`

---

### **Month 1: January 31, 2024**

#### Before Rebalancing:
```
Cash: $100,000
Positions: None
Portfolio Value: $100,000
```

#### Momentum Calculation:
```
SPY: +15.0% ✅ (passes threshold)
EFA: +8.0%  ✅ (passes threshold)
AGG: N/A (safe asset)
```

#### Signal Generation:
```
1. Filter: Both pass absolute momentum
2. Rank: SPY (#1), EFA (#2)
3. Select: Top 1 → SPY
4. Signal: LONG SPY, strength=1.0
```

#### Position Sizing:
```
Portfolio Value: $100,000
Target %: 100% (top 1 asset only)
Desired Dollars: $100,000 × 100% = $100,000
Shares: $100,000 / $400 = 250 shares
Commission: $100,000 × 0.1% = $100
Total Cost: $100,100
```

#### After Rebalancing:
```
Cash: $0
Positions: SPY (250 shares @ $400)
Portfolio Value: $100,000
```

---

### **Daily Updates (Feb 1-28)**

#### Feb 1:
```
SPY: 250 shares × $405 = $101,250
Cash: $0
Portfolio Value: $101,250 ⬆️ (+$1,250)
```

#### Feb 15:
```
SPY: 250 shares × $415 = $103,750
Cash: $0
Portfolio Value: $103,750 ⬆️ (+$3,750)
```

#### Feb 28:
```
SPY: 250 shares × $420 = $105,000
Cash: $0
Portfolio Value: $105,000 ⬆️ (+$5,000)
```

**No rebalancing yet** - still same month!

---

### **Month 2: February 29, 2024** (Rebalancing Day!)

#### Before Rebalancing:
```
Cash: $0
Positions: SPY (250 shares @ $420)
Portfolio Value: $105,000 ✅ (uses UPDATED value!)
```

#### Momentum Calculation:
```
SPY: -8.0% ❌ (fails threshold)
EFA: -5.0% ❌ (fails threshold)
AGG: N/A (safe asset)
```

#### Signal Generation:
```
1. Filter: No assets pass
2. Decision: Rotate to safe asset
3. Signal: LONG AGG, strength=1.0, reason=DEFENSIVE_ROTATION
```

#### Position Sizing:
```
Portfolio Value: $105,000 ✅ (includes $5k gain!)
Target %: 100% (defensive mode)
Desired Dollars: $105,000 × 100% = $105,000

Close SPY:
├─ Sell 250 shares @ $420
├─ Proceeds: $105,000
├─ Commission: $105
└─ Net: $104,895

Open AGG:
├─ Buy with $104,895
├─ Price: $108
├─ Shares: $104,895 / $108 = 971 shares
├─ Cost: $104,868
└─ Commission: $105
```

#### After Rebalancing:
```
Cash: $27
Positions: AGG (971 shares @ $108)
Portfolio Value: $104,895
```

**Key Point:** The $5,000 gain from SPY was **immediately available** for reinvestment in AGG!

---

## 🔑 Critical Insights

### 1. **Mark-to-Market Every Day**
✅ Portfolio value updates daily with current prices
✅ Unrealized gains/losses reflected immediately
✅ No "stale" valuations

### 2. **Rebalancing Uses Updated Value**
✅ Position sizes based on **current** portfolio value
✅ Gains automatically reinvested
✅ Losses automatically reduce exposure

### 3. **Binary Defensive Logic**
✅ No partial allocations
✅ 100% in or 100% out
✅ Simple and clean

### 4. **Transaction Costs Included**
✅ Commission: 0.1% per trade
✅ Slippage: 0.05% price impact
✅ Reduces cash available for next trade

---

## 📊 Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `lookback_period` | 252 | Momentum calculation window (days) |
| `rebalance_frequency` | 'monthly' | How often to check for rebalancing |
| `position_count` | 1 | Max # of risky positions to hold |
| `absolute_threshold` | 0.0 | Minimum momentum to invest (%) |
| `safe_asset` | None | Defensive asset symbol (e.g., 'AGG') |
| `commission` | 0.001 | Transaction cost (0.1%) |
| `slippage` | 0.0005 | Price impact (0.05%) |

---

## 🎯 Summary

The rebalancing logic is now **dramatically simpler**:

1. **Every day**: Update portfolio value with current prices
2. **Every month** (or configured frequency):
   - Calculate momentum for all assets
   - If assets pass filter → Invest in top performers
   - If no assets pass → Rotate to safe asset (or cash)
   - Size positions using **current** portfolio value
3. **Execute trades** with commissions and slippage
4. **Record everything** for performance tracking

**No blending, no complexity, just clean momentum investing!** 🎉
