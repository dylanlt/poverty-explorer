# Enhanced MPI: Addressing Modern Poverty Dimensions

This document describes the enhanced Multidimensional Poverty Index (MPI) that extends the climate-adjusted MPI to include critical modern dimensions of deprivation.

## The Problem with Current Approaches

### 1. **Rent vs Ownership Blind Spot**

**Standard MPI Issue:**
```
Household A: Owns modest home, no ongoing cost
Household B: Rents identical home, 50% of income to rent
Standard MPI: BOTH coded as "adequate housing" = same score
```

**Reality:** Household B is economically vulnerable despite having shelter.

### 2. **Missing Modern Deprivations**

Standard MPI (created 2010) doesn't capture:
- **Digital exclusion**: Can't access services, jobs, education moving online
- **Transportation poverty**: Can't reach work/services due to sprawl + no vehicle
- **Economic vulnerability**: Unstable income, no safety net, debt burden
- **Environmental hazards**: Air pollution, flood risk, heat exposure

### 3. **Dollar-per-Day vs MPI**

- **Dollar-per-day ($2.15 PPP)**: Income-based, misses rent burden issue you identified
- **Standard MPI**: Outcome-based, but housing treated as binary
- **Both miss:** The household with adequate income but 60% going to rent in expensive city

## Enhanced MPI Solution

### Architecture Overview

```
Enhanced MPI = 70% Core MPI + 30% New Dimensions

Core MPI (70%):
  ├─ Health (15%): nutrition, child mortality
  ├─ Education (15%): schooling, attendance
  └─ Living Standards (40%):
      ├─ Electricity, water, sanitation, fuel, assets
      └─ ENHANCED Housing (12%):
          ├─ Structure Quality (40%)
          ├─ Tenure Security (30%)
          └─ Cost Burden (30%)

New Dimensions (30%):
  ├─ Digital Connectivity (8%)
  ├─ Transportation Access (8%)
  ├─ Economic Security (7%)
  └─ Environmental Quality (7%)
```

## Detailed Dimensions

### 1. Enhanced Housing (Solves Rent/Ownership Issue)

**Three Sub-Components:**

#### A. Structure Quality (40%)
Physical adequacy: walls, roof, flooring, space per person
```python
structure_quality = 0/1  # Binary: adequate or not
```

#### B. Tenure Security (30%)
```python
tenure_scores = {
    'owner': 0.0,           # Fully secure
    'secure_rental': 0.3,   # Lease protection
    'informal': 1.0,        # Can be evicted anytime
}
```

#### C. Cost Burden (30%)
```python
# Normalized against local market
cost_burden = (housing_cost / income) / 0.30  # 30% threshold
# Adjusted by local_rental_index to account for market differences
```

**Context Adjustment:**
```python
# In tight housing markets (high rental_tightness), cost matters MORE
housing_subweights = {
    'structure': 0.40 + 0.10 * climate_harshness,
    'cost': 0.30 + 0.15 * rental_tightness,
    'tenure': remainder
}
```

**Example:**
```
Two identical households in structure quality:

Owner in cheap market:
  Structure: 0.2, Tenure: 0.0, Cost: 0.1 → Housing Score: 0.13

Renter in expensive market:
  Structure: 0.2, Tenure: 0.3, Cost: 0.9 → Housing Score: 0.41

Standard MPI would give them similar scores.
Enhanced MPI captures the rent burden crisis.
```

### 2. Digital Connectivity (8%)

**Sub-Components:**
- Internet access (reliable broadband/mobile data)
- Device ownership (smartphone or computer)
- Digital literacy (can perform essential tasks)

**Context Adjustment:**
```python
digital_weight = 0.08 + 0.05 * digital_economy_intensity
```

In highly digitized economies (banking, government services, job applications online), lack of connectivity is severely limiting.

**Example Impacts:**
- Can't apply for jobs (most require online applications)
- Can't access government services (moving to digital-first)
- Children can't do homework (requires internet)
- Can't access cheaper online banking/shopping

### 3. Transportation Access (8%)

**Sub-Components:**
- Physical access (has vehicle OR public transit available)
- Commute time (<90 minutes to work/services)
- Cost burden (<20% of income on transport)

**Context Adjustment:**
```python
transport_weight = 0.08 + 0.06 * sprawl_index
```

In sprawling areas without transit, transport becomes critical bottleneck.

**Example:**
```
Urban with transit: Low transport deprivation
  - Can reach work in 30 min
  - Transit costs 10% of income
  - Score: 0.1

Rural without vehicle: High transport deprivation
  - Takes 2 hours to reach services
  - Must use expensive informal taxis (25% of income)
  - Score: 0.8
```

### 4. Economic Security (7%)

**Sub-Components:**
- Income volatility (stable vs erratic)
- Emergency savings (can handle unexpected $400 expense)
- Social protection (unemployment insurance, safety net)
- Debt burden (<40% of income to debt service)

**Why This Matters:**
Standard MPI is a snapshot. Economic security measures vulnerability to shocks.

**Example:**
```
Household A: $5000/month stable, has savings, insured
  → Can weather job loss, medical emergency
  → Economic security score: 0.2

Household B: $5000/month variable, no savings, informal work
  → One bad month = crisis
  → Economic security score: 0.8
```

### 5. Environmental Quality (7%)

**Sub-Components:**
- Air quality (PM2.5 levels)
- Flood/disaster risk
- Heat exposure (climate + no cooling)
- Toxic proximity (industrial sites, waste)

**Context Adjustment:**
Heat exposure weighted by climate harshness - ties back to original climate adjustment.

## Complete Weight Calculation

### Base Weights (No Context)

```python
ENHANCED_WEIGHTS = {
    # Health: 15%
    'nutrition': 0.075,
    'child_mortality': 0.075,
    
    # Education: 15%
    'years_schooling': 0.075,
    'school_attendance': 0.075,
    
    # Living Standards: 40%
    'electricity': 0.06,
    'sanitation': 0.06,
    'drinking_water': 0.06,
    'cooking_fuel': 0.05,
    'assets': 0.05,
    'housing': 0.12,  # Enhanced with sub-components
    
    # New Dimensions: 30%
    'digital': 0.08,
    'transport': 0.08,
    'economic_security': 0.07,
    'environment': 0.07,
}
```

### Context-Adjusted Weights

```python
def get_adjusted_weights(
    climate_harshness: float,          # 0-1
    urbanization: float,               # 0-1
    sprawl_index: float,               # 0-1
    digital_economy_intensity: float,  # 0-1
    rental_market_tightness: float,    # 0-1
):
    weights = ENHANCED_WEIGHTS.copy()
    
    # Climate adjustments
    weights['electricity'] += 0.04 * climate_harshness
    weights['cooking_fuel'] += 0.02 * climate_harshness
    weights['housing'] += 0.03 * climate_harshness
    
    # Urban density adjustments
    weights['sanitation'] += 0.04 * urbanization
    weights['drinking_water'] += 0.04 * urbanization
    
    # Sprawl adjustments
    weights['transport'] += 0.06 * sprawl_index
    
    # Digital economy adjustments
    weights['digital'] += 0.05 * digital_economy_intensity
    
    # Normalize to sum = 1.0
    total = sum(weights.values())
    return {k: v/total for k, v in weights.items()}
```

## Comparison: Three Approaches

### Scenario 1: Renter in Expensive City

| Dimension | Standard MPI | Climate-Adj | Enhanced MPI |
|-----------|-------------|-------------|--------------|
| Housing | 0.0 (adequate) | 0.0 | **0.41** (high rent) |
| Digital | *(not measured)* | *(not measured)* | 0.0 (has access) |
| Transport | *(not measured)* | *(not measured)* | 0.2 (manageable) |
| **Total Score** | **0.011** | **0.019** | **0.092** |
| **Classification** | NOT POOR | NOT POOR | NOT POOR |

**Insight:** Enhanced MPI reveals the household is rent-burdened (50% of income), even though still below poverty threshold. This household is vulnerable.

### Scenario 2: Rural Homeowner, Poor Structure

| Dimension | Standard MPI | Climate-Adj | Enhanced MPI |
|-----------|-------------|-------------|--------------|
| Housing | 0.8 (inadequate) | 0.9 (harsh climate) | **0.5** (poor but owned) |
| Digital | *(not measured)* | *(not measured)* | **1.0** (no access) |
| Transport | *(not measured)* | *(not measured)* | **0.8** (isolated) |
| Environment | *(not measured)* | *(not measured)* | **0.7** (exposed) |
| **Total Score** | **0.389** | **0.504** | **0.545** |
| **Classification** | POOR | POOR | POOR |

**Insight:** All three methods classify as poor, but Enhanced MPI shows *why* comprehensively: lacks electricity, digital access, transport, faces environmental hazards. Homeownership provides stability but multiple modern deprivations compound.

### Scenario 3: Digitally Excluded

| Dimension | Standard MPI | Climate-Adj | Enhanced MPI |
|-----------|-------------|-------------|--------------|
| Basic needs | 0.05 (mostly adequate) | 0.04 | 0.04 |
| Digital | *(not measured)* | *(not measured)* | **1.0** (fully excluded) |
| **Total Score** | **0.078** | **0.059** | **0.191** |
| **Classification** | NOT POOR | NOT POOR | NOT POOR |

**Insight:** Standard MPI misses digital poverty entirely. Enhanced MPI reveals significant deprivation even though basic needs are met. In a digitizing economy, this household faces barriers to employment, services, education.

## Comparison to Dollar-per-Day

| Aspect | Dollar-per-Day | Standard MPI | Enhanced MPI |
|--------|---------------|--------------|--------------|
| **Income vs Outcomes** | Income only | Outcomes only | Outcomes + costs |
| **Rent burden** | Indirect | No | **YES** |
| **Currency fluctuations** | Vulnerable (even with PPP) | Not affected | Not affected |
| **Digital poverty** | No | No | **YES** |
| **Transport poverty** | No | No | **YES** |
| **Context-aware** | PPP-adjusted | No | **YES** |
| **Vulnerability** | No | No | **YES** |

## Policy Implications

Enhanced MPI enables better targeting:

**Traditional MPI identifies:**
"Ward X has 40% poverty rate"

**Enhanced MPI reveals:**
- "15% are poor due to housing costs" → Housing subsidies
- "10% are poor due to transport" → Transit investment
- "8% are poor due to digital exclusion" → Connectivity programs
- "7% are poor from combined factors" → Comprehensive support

## Run the Demo

```bash
# Test the enhanced MPI
python test_enhanced_mpi.py

# Output shows three scenarios comparing:
# - Standard MPI
# - Climate-Adjusted MPI
# - Enhanced MPI
```