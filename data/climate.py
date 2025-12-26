"""Climate data fetching from ERA5 reanalysis via Copernicus CDS API."""

import os
import cdsapi
import xarray as xr
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import logging
from dotenv import load_dotenv
import zipfile
import tempfile

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class ClimateDataFetcher:
    """Fetch and process ERA5 climate data for Durban region."""
    
    # Durban bounding box (eThekwini Municipality)
    DURBAN_BOUNDS = {
        'north': -29.5,
        'south': -30.3,
        'west': 30.4,
        'east': 31.2,
    }
    
    def __init__(self, cache_dir: str = './data/cache'):
        """Initialize fetcher with cache directory."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_dataset(self, file_path: Path) -> xr.Dataset:
        """
        Load dataset from file, handling ZIP archives from CDS API.

        The Copernicus CDS API sometimes returns ZIP files containing multiple
        NetCDF files (e.g., separate files for instant and accumulated variables).
        """
        # Check if file is a ZIP archive
        try:
            if zipfile.is_zipfile(file_path):
                logger.info(f"Detected ZIP archive, extracting NetCDF files...")
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # List all .nc files in the archive
                    nc_files = [f for f in zip_ref.namelist() if f.endswith('.nc')]

                    if not nc_files:
                        raise ValueError(f"No NetCDF files found in ZIP archive: {file_path}")

                    # Extract to temporary directory and open all datasets
                    datasets = []
                    with tempfile.TemporaryDirectory() as tmpdir:
                        for nc_file in nc_files:
                            zip_ref.extract(nc_file, tmpdir)
                            extracted_path = Path(tmpdir) / nc_file
                            ds = xr.open_dataset(extracted_path, engine='netcdf4')
                            # Rename valid_time to time if present
                            if 'valid_time' in ds.dims:
                                ds = ds.rename({'valid_time': 'time'})
                            datasets.append(ds)

                    # Merge datasets if multiple files
                    if len(datasets) == 1:
                        return datasets[0]
                    else:
                        logger.info(f"Merging {len(datasets)} NetCDF files...")
                        return xr.merge(datasets)
            else:
                # Regular NetCDF file
                ds = xr.open_dataset(file_path, engine='netcdf4')
                # Rename valid_time to time if present
                if 'valid_time' in ds.dims:
                    ds = ds.rename({'valid_time': 'time'})
                return ds
        except Exception as e:
            logger.error(f"Failed to load dataset from {file_path}: {e}")
            raise
        
    def fetch_era5_data(
        self, 
        year: int = 2023,
        variables: Optional[list] = None,
        force_download: bool = False
    ) -> xr.Dataset:
        """
        Fetch ERA5 hourly data for Durban region.
        
        Args:
            year: Year to fetch
            variables: List of variables to fetch (default: temperature, precip)
            force_download: Re-download even if cached
            
        Returns:
            xarray Dataset with climate data
        """
        cache_file = self.cache_dir / f'era5_durban_{year}.nc'

        if cache_file.exists() and not force_download:
            logger.info(f"Loading cached ERA5 data from {cache_file}")
            return self._load_dataset(cache_file)
        
        if variables is None:
            variables = [
                '2m_temperature',
                'total_precipitation',
                '2m_dewpoint_temperature',
            ]
        
        logger.info(f"Fetching ERA5 data for {year}...")

        try:
            # Get API credentials from environment variable
            cds_api_key = os.getenv('COPERNICUS_API_KEY')

            if not cds_api_key:
                logger.warning("COPERNICUS_API_KEY environment variable not set. Using synthetic data.")
                return self._generate_synthetic_data(year)

            # Initialize CDS API client with credentials
            # New CDS API format (as of 2024): API key only, no UID prefix
            c = cdsapi.Client(
                url='https://cds.climate.copernicus.eu/api',
                key=cds_api_key
            )

            c.retrieve(
                'reanalysis-era5-single-levels',
                {
                    'product_type': 'reanalysis',
                    'format': 'netcdf',
                    'variable': variables,
                    'year': str(year),
                    'month': [f'{m:02d}' for m in range(1, 13)],
                    'day': [f'{d:02d}' for d in range(1, 32)],
                    'time': '12:00',  # Request single time per day to reduce data size
                    'area': [
                        self.DURBAN_BOUNDS['north'],
                        self.DURBAN_BOUNDS['west'],
                        self.DURBAN_BOUNDS['south'],
                        self.DURBAN_BOUNDS['east'],
                    ],
                },
                str(cache_file)
            )
            
            logger.info(f"Downloaded ERA5 data to {cache_file}")
            return self._load_dataset(cache_file)
            
        except Exception as e:
            logger.error(f"Failed to fetch ERA5 data: {e}")
            # Return synthetic data for demo if API fails
            return self._generate_synthetic_data(year)
    
    def _generate_synthetic_data(self, year: int) -> xr.Dataset:
        """
        Generate synthetic climate data for demo purposes.
        Based on typical Durban climate patterns.
        """
        logger.warning("Generating synthetic climate data for demo")
        
        # Create grid (0.25 degree resolution, ~25km)
        lats = np.arange(
            self.DURBAN_BOUNDS['south'],
            self.DURBAN_BOUNDS['north'],
            0.25
        )
        lons = np.arange(
            self.DURBAN_BOUNDS['west'],
            self.DURBAN_BOUNDS['east'],
            0.25
        )
        
        # Simplified: daily averages for one year
        days = 365
        
        # Durban has subtropical climate
        # Summer: Dec-Feb (hot, humid, rainy)
        # Winter: Jun-Aug (mild, dry)
        day_of_year = np.arange(days)
        
        # Temperature varies with season and location
        # Coastal areas cooler, inland warmer
        temp_data = np.zeros((len(lats), len(lons), days))
        precip_data = np.zeros((len(lats), len(lons), days))
        
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                # Distance from coast affects temperature
                coast_distance = lon - self.DURBAN_BOUNDS['west']
                
                # Base temperature with seasonal variation
                base_temp = 20 + 8 * np.sin(2 * np.pi * day_of_year / 365 - np.pi/2)
                
                # Inland areas warmer (urban heat island + distance from ocean)
                inland_effect = coast_distance * 15  # Up to 12°C warmer inland
                
                # Elevation effect (cooler at higher elevations)
                # Approximate: western areas higher elevation
                elevation_effect = -coast_distance * 3
                
                temp_data[i, j, :] = base_temp + inland_effect + elevation_effect
                
                # Add daily variation
                temp_data[i, j, :] += np.random.normal(0, 2, days)
                
                # Precipitation higher in summer, lower in winter
                precip_base = 3 + 4 * np.sin(2 * np.pi * day_of_year / 365 - np.pi/2)
                precip_base = np.maximum(0, precip_base)
                
                # More rain inland/western areas
                precip_data[i, j, :] = precip_base * (1 + coast_distance)
                precip_data[i, j, :] = np.maximum(0, precip_data[i, j, :])
        
        # Convert to Kelvin for temperature
        temp_data += 273.15
        
        # Create xarray dataset
        ds = xr.Dataset(
            {
                't2m': (['latitude', 'longitude', 'time'], temp_data),
                'tp': (['latitude', 'longitude', 'time'], precip_data / 1000),  # m
            },
            coords={
                'latitude': lats,
                'longitude': lons,
                'time': np.arange(days),
            }
        )
        
        return ds
    
    def calculate_degree_days(
        self, 
        dataset: xr.Dataset,
        base_heating: float = 18.0,
        base_cooling: float = 24.0
    ) -> Tuple[xr.DataArray, xr.DataArray]:
        """
        Calculate heating and cooling degree days from temperature data.
        
        Args:
            dataset: ERA5 dataset with temperature
            base_heating: Base temperature for HDD (°C)
            base_cooling: Base temperature for CDD (°C)
            
        Returns:
            Tuple of (heating_degree_days, cooling_degree_days) DataArrays
        """
        # Convert from Kelvin to Celsius
        temp_c = dataset['t2m'] - 273.15
        
        # Calculate daily mean temperature
        daily_temp = temp_c.resample(time='1D').mean()
        
        # Heating degree days: sum of (base - temp) when temp < base
        hdd = np.maximum(0, base_heating - daily_temp).sum(dim='time')
        
        # Cooling degree days: sum of (temp - base) when temp > base
        cdd = np.maximum(0, daily_temp - base_cooling).sum(dim='time')
        
        return hdd, cdd
    
    def calculate_climate_statistics(self, dataset: xr.Dataset) -> dict:
        """
        Calculate comprehensive climate statistics for each grid cell.
        
        Returns:
            Dict with DataArrays for various climate metrics
        """
        temp_c = dataset['t2m'] - 273.15
        
        # Temperature statistics
        temp_mean = temp_c.mean(dim='time')
        temp_min = temp_c.min(dim='time')
        temp_max = temp_c.max(dim='time')
        temp_std = temp_c.std(dim='time')
        
        # Daily temperature range
        daily_temp = temp_c.resample(time='1D').mean()
        daily_range = (
            temp_c.resample(time='1D').max() - 
            temp_c.resample(time='1D').min()
        ).mean(dim='time')
        
        # Degree days
        hdd, cdd = self.calculate_degree_days(dataset)
        
        # Precipitation
        total_precip = dataset['tp'].sum(dim='time') * 1000  # Convert to mm
        
        # Relative humidity (if dewpoint available)
        if 'd2m' in dataset:
            dewpoint_c = dataset['d2m'] - 273.15
            # Simplified RH calculation
            rh = 100 * np.exp((17.625 * dewpoint_c) / (243.04 + dewpoint_c)) / \
                 np.exp((17.625 * temp_c) / (243.04 + temp_c))
            avg_humidity = rh.mean(dim='time')
        else:
            avg_humidity = None
        
        return {
            'temp_mean': temp_mean,
            'temp_min': temp_min,
            'temp_max': temp_max,
            'temp_range': daily_range,
            'temp_std': temp_std,
            'heating_degree_days': hdd,
            'cooling_degree_days': cdd,
            'annual_precipitation': total_precip,
            'avg_humidity': avg_humidity,
        }