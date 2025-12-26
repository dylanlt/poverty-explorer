"""Test script to verify ERA5 data fetching from Copernicus CDS API."""

import sys
import logging
from data.climate import ClimateDataFetcher

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("=" * 60)
    print("ERA5 Data Fetching Test")
    print("=" * 60)

    fetcher = ClimateDataFetcher()

    # Try to fetch ERA5 data for 2023
    # Note: First download may take several minutes
    print("\nAttempting to fetch ERA5 data for 2023...")
    print("(This may take a few minutes on first download)")

    try:
        climate_ds = fetcher.fetch_era5_data(year=2023, force_download=False)

        print("\n✓ Data fetched successfully!")
        print(f"\nDataset info:")
        print(f"  Variables: {list(climate_ds.data_vars.keys())}")
        print(f"  Coordinates: {list(climate_ds.coords.keys())}")
        print(f"  Latitude range: {float(climate_ds.latitude.min()):.2f} to {float(climate_ds.latitude.max()):.2f}")
        print(f"  Longitude range: {float(climate_ds.longitude.min()):.2f} to {float(climate_ds.longitude.max()):.2f}")

        if 'time' in climate_ds.coords:
            print(f"  Time steps: {len(climate_ds.time)}")

        # Calculate climate statistics
        print("\nCalculating climate statistics...")
        stats = fetcher.calculate_climate_statistics(climate_ds)

        print("\n✓ Climate statistics calculated!")
        print(f"  Available metrics: {list(stats.keys())}")

        # Show some sample values
        if 'temp_mean' in stats:
            mean_temp = float(stats['temp_mean'].mean())
            print(f"\n  Average temperature: {mean_temp:.1f}°C")

        if 'annual_precipitation' in stats:
            mean_precip = float(stats['annual_precipitation'].mean())
            print(f"  Average annual precipitation: {mean_precip:.0f} mm")

        print("\n" + "=" * 60)
        print("SUCCESS: ERA5 integration is working!")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check that COPERNICUS_API_KEY is set in .env file")
        print("2. Verify API key format (new format, no UID prefix)")
        print("3. Accept the ERA5 license terms:")
        print("   https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=download")
        print("   Click 'Licence to use Copernicus Products' and accept")
        print("4. Wait a few minutes after accepting the license before retrying")
        return 1

if __name__ == "__main__":
    sys.exit(main())
