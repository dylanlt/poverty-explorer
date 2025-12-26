# ERA5 Real Data Setup Guide

This guide walks you through setting up real ERA5 climate data from Copernicus for your poverty explorer application.

## Current Status

The application is now configured to use real ERA5 data via environment variables. The synthetic data is used as a fallback if the API is not configured.

## What Was Changed

1. **Updated `data/climate.py`**:
   - Now reads API key from `COPERNICUS_API_KEY` environment variable
   - Updated to new Copernicus API endpoint (https://cds.climate.copernicus.eu/api)
   - Reduced data request to single daily observation (12:00) to avoid quota limits
   - Added proper error handling and fallback to synthetic data

2. **Added Environment Variable Support**:
   - Created `.env.example` template
   - Created `.env` file (with your API key already configured)
   - Added `python-dotenv` to `requirements.txt`
   - Created `.gitignore` to protect sensitive credentials

3. **Updated Documentation**:
   - Updated README.md with new setup instructions
   - Created this setup guide
   - Created `test_era5.py` for testing the integration

## Next Steps

### Step 1: Accept the ERA5 License

**IMPORTANT**: Before you can download ERA5 data, you must accept the license terms.

1. Visit: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=download
2. Scroll to the "Terms of use" section
3. Click on "Licence to use Copernicus Products"
4. Read and accept the license terms
5. Wait 5-10 minutes for the license acceptance to propagate in the system

### Step 2: Test the Integration

Once you've accepted the license, run the test script:

```bash
source venv/bin/activate
python test_era5.py
```

**Expected output** (on first run):
```
============================================================
ERA5 Data Fetching Test
============================================================

Attempting to fetch ERA5 data for 2023...
(This may take a few minutes on first download)

[Download progress messages from Copernicus API...]

✓ Data fetched successfully!

Dataset info:
  Variables: ['t2m', 'tp', 'd2m']
  Coordinates: ['latitude', 'longitude', 'time']
  Latitude range: -30.30 to -29.55
  Longitude range: 30.40 to 31.15
  Time steps: 365

Calculating climate statistics...

✓ Climate statistics calculated!
  Available metrics: dict_keys(['temp_mean', 'temp_min', 'temp_max', ...])

  Average temperature: 20.5°C
  Average annual precipitation: 1009 mm

============================================================
SUCCESS: ERA5 integration is working!
============================================================
```

### Step 3: Run the Application

Once the test passes, run the main application:

```bash
source venv/bin/activate
streamlit run app.py
```

The application will automatically:
1. Try to load cached ERA5 data from `data/cache/era5_durban_2023.nc`
2. If not cached, download from Copernicus API (first run only)
3. Fall back to synthetic data if API fails

## Troubleshooting

### "required licences not accepted"
- Solution: Complete Step 1 above and wait 5-10 minutes

### "cost limits exceeded"
- The data request is too large for your quota
- This shouldn't happen with the updated code (single daily observation)
- If it does, you may need to upgrade your Copernicus account or reduce the date range

### "403 Forbidden"
- Check that your API key is correct in `.env`
- Ensure you've accepted the license terms
- Wait a few minutes and try again

### API key format error
- The new API uses just the API key (UUID format)
- Example: `88bed392-9633-438f-ab66-e72d247fa1a8`
- Do NOT include a UID prefix (old format was `UID:API_KEY`)

### Data downloads slowly
- First download can take 5-15 minutes depending on connection
- Subsequent runs use cached data (loads in <5 seconds)
- Cache stored in `data/cache/era5_durban_2023.nc`

## Understanding the Data

### What Gets Downloaded

- **Variables**:
  - `2m_temperature` (t2m): Air temperature 2 meters above surface
  - `total_precipitation` (tp): Total precipitation
  - `2m_dewpoint_temperature` (d2m): Used to calculate relative humidity

- **Coverage**:
  - Geographic: eThekwini Municipality (Durban)
  - Temporal: Full year (2023 by default)
  - Resolution: 0.25° (~25km grid cells)
  - Frequency: Daily (12:00 UTC observation)

### How It's Used

The application calculates:
1. **Climate Harshness Index**: Based on deviation from thermal comfort zone (18-24°C)
2. **Degree Days**: Heating degree days (HDD) and cooling degree days (CDD)
3. **Context Weights**: Adjusts MPI indicator weights based on climate severity

Example: In areas with extreme heat (high CDD), electricity gets higher weight because it's needed for cooling.

## File Structure

```
poverty-explorer/
├── .env                          # Your API credentials (ignored by git)
├── .env.example                  # Template for API credentials
├── .gitignore                    # Protects .env and cache files
├── data/
│   ├── climate.py               # ERA5 fetching logic (updated)
│   └── cache/                   # Downloaded ERA5 data (auto-created)
│       └── era5_durban_2023.nc # Cached NetCDF file
├── test_era5.py                 # Test script (new)
└── SETUP_ERA5.md               # This file
```

## Performance Notes

- **First run**: 5-15 minutes (downloads ~50MB NetCDF file)
- **Subsequent runs**: <5 seconds (uses cache)
- **Data size**: ~50-100MB for full year, small geographic area
- **API limits**: Free tier allows reasonable academic/research use

## Next Steps

After ERA5 integration works:
1. Consider adding more years of data for trend analysis
2. Expand to other South African cities for comparison
3. Integrate real socioeconomic data (Stats SA, DHS surveys)
4. Add seasonal analysis (wet vs dry season MPI)

## Support

If you encounter issues:
1. Check the Copernicus CDS documentation: https://cds.climate.copernicus.eu/how-to-api
2. Review the test script output for specific error messages
3. Ensure python-dotenv is installed: `pip install python-dotenv`
