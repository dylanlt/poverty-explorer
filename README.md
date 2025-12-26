# Climate-Adjusted Multidimensional Poverty Index (MPI)

A proof-of-concept tool demonstrating how climate and geographic context should influence poverty measurement. Traditional MPI uses fixed global weights - this approach adjusts weights based on objectively measurable local conditions.

## Case Study: Durban, South Africa

Durban has significant microclimate variation:
- Coastal areas vs inland suburbs can differ by 10-20°C
- Urban density varies dramatically
- Real poverty gradients from informal settlements to affluent suburbs

## The Problem

Current poverty measurements use one-size-fits-all approaches:
- **Same weights globally**: Electricity counts equally in mild climates and harsh ones
- **No context**: Doesn't account for whether you live where 40°C heat or -30°C cold is common
- **Currency-based**: Poverty lines in unstable currencies don't reflect real purchasing power

## The Solution

**Single formula, context-sensitive parameters:**

```python
weight = base_weight + (climate_harshness × adjustment_factor)
```

Where climate_harshness is objectively measured from weather data:
- Degree-days from thermal comfort zone (18-24°C)
- Temperature extremes
- Precipitation patterns

## Installation

### Prerequisites
- Python 3.9+
- For real ERA5 climate data: [CDS API account](https://cds.climate.copernicus.eu/api-how-to)

### Setup

```bash
# Clone/download this repository
cd durban-mpi-poc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configure ERA5 Climate Data

To use real ERA5 climate data from Copernicus:

1. Register at https://cds.climate.copernicus.eu/how-to-api
2. Get your API key from your account page
3. Accept the ERA5 license terms at https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels
4. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
5. Edit `.env` and add your API key:
   ```
   COPERNICUS_API_KEY=your-api-key-here
   ```
   Example: `COPERNICUS_API_KEY=abcdef01-2345-6789-abcd-ef0123456789`

**Note**: The app will fall back to synthetic data if the API key is not configured.

## Usage

### Run the Streamlit App

```bash
streamlit run app.py
```

Then:
1. Click "Load Data" in the sidebar
2. Explore the tabs:
   - **Map View**: Geographic distribution of poverty and climate
   - **Analysis**: Statistical comparisons
   - **Cell Deep-Dive**: Detailed look at individual wards
   - **Comparison**: Standard vs adjusted MPI

### Using Real Data

The POC currently uses synthetic data that mirrors real Durban patterns. To use real data:

1. **Climate**: Set `force_download=True` in `app.py` line with `fetch_era5_data()`
2. **Census**: Place Stats SA data in `data/` and update `load_census_data()` path
3. **DHS**: Add household survey data via `load_or_generate_data()`

## Architecture

```
durban-mpi-poc/
├── app.py                    # Main Streamlit application
├── models/
│   ├── cells.py             # GeographicCell, ClimateProfile, ContextFactors
│   └── mpi.py               # MPI calculation (standard & adjusted)
├── data/
│   ├── climate.py           # ERA5 data fetching & processing
│   └── socioeconomic.py     # Census & household data
└── requirements.txt
```

## Key Concepts

### Climate Harshness Index (0-1)

Combines:
- Deviation from thermal comfort (18-24°C)
- Heating/cooling degree-days
- Normalized to 0 (mild) to 1 (extreme)

### Context-Adjusted Weights

**Electricity**:
```python
weight = 0.08 + (0.12 × climate_harshness)
```
- Mild climate: 8% of total weight
- Harsh climate: up to 20% of total weight

**Sanitation/Water**:
```python
weight = 0.08 + (0.07 × urbanization)
```
- Rural: 8% weight
- Dense urban: 15% weight

**Core indicators** (nutrition, mortality) remain relatively constant.

## Example Insights

From synthetic Durban data:

1. **Coastal vs Inland**: Households 15km inland may be classified as poor due to extreme heat (need electricity for cooling), while identical deprivations on the coast are below poverty threshold

2. **Classification Changes**: ~5-10% of households switch poverty status when climate is considered

3. **Policy Implications**: Different wards need different interventions - inland areas prioritize electricity/housing, coastal areas prioritize water/sanitation

## Data Sources (for production use)

**Climate**:
- ERA5 Reanalysis: https://cds.climate.copernicus.eu
- Resolution: 0.25° (~25km grid)
- Variables: 2m temperature, precipitation, dewpoint

**Socioeconomic**:
- Stats SA Census: http://www.statssa.gov.za/
- OPHI South Africa MPI: https://ophi.org.uk/
- DHS Surveys: https://dhsprogram.com/

**Geographic**:
- eThekwini Ward Boundaries: Municipal GIS
- SRTM Elevation: https://earthexplorer.usgs.gov/
- OpenStreetMap: https://www.openstreetmap.org/

## Extensions

### Multi-City Comparison
Add cities with different climates (e.g., Cape Town, Johannesburg) to demonstrate weight variation

### Temporal Analysis
Track how climate change affects poverty measurement over time

### Other Context Factors
- Disease environment (malaria risk, water-borne illness)
- Conflict/stability
- Market access

### Integration with Policy
Link to actual intervention targeting - show ROI of different programs by ward

## Technical Notes

### Weight Normalization
Adjusted weights always sum to 1.0 to maintain comparability

### Deprivation Scoring
Binary indicators (0 or 1) following standard MPI methodology

### Poverty Cutoff
Uses standard 33.3% threshold (adjustable in code)

### Performance
- Loads 50 wards × 30 households = 1,500 households in <5s
- Climate grid: ~200 cells at 0.25° resolution
- Interactive map renders in <2s

## Contributing

This is a POC - suggestions welcome:
- Better weight functions (empirical calibration)
- Additional context factors
- Real data integration
- UI/UX improvements

## References

- Alkire, S., & Foster, J. (2011). Counting and multidimensional poverty measurement. *Journal of Public Economics*.
- OPHI (2024). Global Multidimensional Poverty Index. https://ophi.org.uk/multidimensional-poverty-index/
- Hersbach et al. (2020). The ERA5 global reanalysis. *Quarterly Journal of the Royal Meteorological Society*.

## License

MIT - use freely, attribution appreciated

## Contact

Questions/feedback welcome via GitHub issues or pull requests
