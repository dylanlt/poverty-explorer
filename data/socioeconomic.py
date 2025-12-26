"""Socioeconomic data loading and generation for Durban."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List
import logging
from models.mpi import DeprivationScore, HouseholdData

logger = logging.getLogger(__name__)


class SocioeconomicDataLoader:
    """Load and process socioeconomic data for Durban."""
    
    def __init__(self, data_dir: str = './data'):
        """Initialize loader with data directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_census_data(self, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Load census data for Durban wards.
        
        Expected columns:
        - ward_id, ward_name
        - population, households
        - latitude, longitude
        - Various deprivation indicators
        
        If filepath is None, generates synthetic data based on real patterns.
        """
        if filepath and Path(filepath).exists():
            logger.info(f"Loading census data from {filepath}")
            return pd.read_csv(filepath)
        
        logger.warning("Generating synthetic census data")
        return self._generate_synthetic_census()
    
    def _generate_synthetic_census(self) -> pd.DataFrame:
        """
        Generate synthetic census data for Durban wards.
        Based on actual Durban socioeconomic patterns:
        - Coastal areas: more affluent
        - Western inland areas: higher deprivation
        - Northern areas: mixed
        """
        # eThekwini has ~110 wards, we'll create a simplified version
        num_wards = 50

        wards = []

        # Generate random points within Durban's actual land area
        # Use a more realistic approach that avoids ocean coordinates
        # Durban coastline runs roughly NE-SW at longitude ~31.0
        np.random.seed(42)  # For reproducibility

        ward_id = 1
        attempts = 0
        max_attempts = 200

        while ward_id <= num_wards and attempts < max_attempts:
            attempts += 1

            # Generate candidate coordinate
            lat = np.random.uniform(-30.2, -29.6)
            lon = np.random.uniform(30.5, 31.1)

            # Filter out ocean coordinates (rough approximation)
            # Durban's coast runs approximately: lon > 30.7 + 0.5 * (lat + 29.9)
            # This creates a diagonal boundary representing the coastline
            coast_boundary_lon = 30.7 + 0.5 * (lat + 29.9)

            # Skip if point is likely in the ocean (too far east)
            if lon > coast_boundary_lon + 0.15:
                continue

            # Distance from coast (proxy for affluence)
            coast_distance = max(0, lon - coast_boundary_lon) / 0.15  # 0 = at coast, 1 = far inland

            # Distance from city center (Durban CBD ~-29.85, 31.03)
            cbd_distance = np.sqrt((lat - (-29.85))**2 + (lon - 31.03)**2)

            # Population density higher near coast and CBD
            density = 5000 * (1 - coast_distance) * (1 - cbd_distance * 2)
            density = max(100, min(10000, density))

            # Number of households
            num_households = int(density * 2 + np.random.normal(0, 100))
            num_households = max(50, num_households)

            # Deprivation correlates with distance from coast/CBD
            # Add some randomness
            base_deprivation = coast_distance * 0.6 + cbd_distance * 0.2
            base_deprivation = np.clip(base_deprivation + np.random.normal(0, 0.15), 0, 1)

            ward = {
                'ward_id': f'W{ward_id:03d}',
                'ward_name': f'Ward {ward_id}',
                'latitude': lat,
                'longitude': lon,
                'population': int(num_households * 3.5),  # Avg household size
                'num_households': num_households,
                'population_density': density,

                # Deprivation indicators (higher = more deprived)
                'pct_no_electricity': base_deprivation * 0.3 + np.random.normal(0, 0.05),
                'pct_inadequate_sanitation': base_deprivation * 0.4 + np.random.normal(0, 0.08),
                'pct_no_piped_water': base_deprivation * 0.35 + np.random.normal(0, 0.06),
                'pct_inadequate_housing': base_deprivation * 0.5 + np.random.normal(0, 0.1),
                'pct_dirt_floor': base_deprivation * 0.25 + np.random.normal(0, 0.05),
                'pct_wood_fuel': base_deprivation * 0.2 + np.random.normal(0, 0.04),
                'pct_no_assets': base_deprivation * 0.35 + np.random.normal(0, 0.07),

                # Education
                'pct_no_schooling': base_deprivation * 0.3 + np.random.normal(0, 0.05),
                'pct_child_not_attending': base_deprivation * 0.15 + np.random.normal(0, 0.03),

                # Health
                'pct_malnourished': base_deprivation * 0.2 + np.random.normal(0, 0.04),
                'child_mortality_rate': base_deprivation * 0.25 + np.random.normal(0, 0.05),

                # Context
                'urban_rural_index': 1 - coast_distance * 0.5,  # More urban near coast
                'distance_to_hospital_km': coast_distance * 15 + np.random.normal(0, 2),
            }

            # Clip percentages to [0, 1]
            for key in ward:
                if key.startswith('pct_') or key.endswith('_rate'):
                    ward[key] = np.clip(ward[key], 0, 1)

            wards.append(ward)
            ward_id += 1
        
        return pd.DataFrame(wards)
    
    def generate_household_data(
        self, 
        census_df: pd.DataFrame,
        households_per_ward: int = 20
    ) -> List[HouseholdData]:
        """
        Generate individual household data from ward-level statistics.
        
        Args:
            census_df: Ward-level census data
            households_per_ward: Number of synthetic households per ward
            
        Returns:
            List of HouseholdData objects
        """
        households = []
        
        for _, ward in census_df.iterrows():
            cell_id = ward['ward_id']
            
            # Generate households with deprivations sampled from ward distributions
            for hh_num in range(households_per_ward):
                household_id = f"{cell_id}_HH{hh_num:03d}"
                
                # Sample household size (Poisson distribution)
                hh_size = max(1, int(np.random.poisson(3.5)))
                num_children = int(np.random.binomial(hh_size - 1, 0.3)) if hh_size > 1 else 0
                
                # Sample deprivations based on ward percentages
                # Binary: deprived or not (using ward percentage as probability)
                deprivations = DeprivationScore(
                    # Health
                    nutrition=float(np.random.random() < ward['pct_malnourished']),
                    child_mortality=float(np.random.random() < ward['child_mortality_rate']),
                    
                    # Education
                    years_schooling=float(np.random.random() < ward['pct_no_schooling']),
                    school_attendance=float(np.random.random() < ward['pct_child_not_attending']) if num_children > 0 else 0.0,
                    
                    # Living standards
                    electricity=float(np.random.random() < ward['pct_no_electricity']),
                    sanitation=float(np.random.random() < ward['pct_inadequate_sanitation']),
                    drinking_water=float(np.random.random() < ward['pct_no_piped_water']),
                    flooring=float(np.random.random() < ward['pct_dirt_floor']),
                    cooking_fuel=float(np.random.random() < ward['pct_wood_fuel']),
                    assets=float(np.random.random() < ward['pct_no_assets']),
                )
                
                household = HouseholdData(
                    household_id=household_id,
                    cell_id=cell_id,
                    deprivations=deprivations,
                    household_size=hh_size,
                    num_children=num_children,
                )
                
                households.append(household)
        
        logger.info(f"Generated {len(households)} households across {len(census_df)} wards")
        return households
    
    def load_or_generate_data(
        self,
        census_filepath: Optional[str] = None,
        households_per_ward: int = 20
    ) -> tuple[pd.DataFrame, List[HouseholdData]]:
        """
        Convenience method to load or generate both census and household data.
        
        Returns:
            Tuple of (census_dataframe, households_list)
        """
        census_df = self.load_census_data(census_filepath)
        households = self.generate_household_data(census_df, households_per_ward)
        return census_df, households
    
    def export_sample_data(self, output_dir: str = './data/samples'):
        """Export sample data for inspection."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        census_df, households = self.load_or_generate_data(households_per_ward=10)
        
        # Export census data
        census_df.to_csv(output_path / 'census_data.csv', index=False)
        logger.info(f"Exported census data to {output_path / 'census_data.csv'}")
        
        # Export sample households
        hh_records = []
        for hh in households[:100]:  # First 100 households
            record = {
                'household_id': hh.household_id,
                'cell_id': hh.cell_id,
                'household_size': hh.household_size,
                'num_children': hh.num_children,
            }
            # Add deprivation scores
            for field in hh.deprivations.__dataclass_fields__:
                record[f'deprived_{field}'] = getattr(hh.deprivations, field)
            hh_records.append(record)
        
        pd.DataFrame(hh_records).to_csv(
            output_path / 'sample_households.csv', 
            index=False
        )
        logger.info(f"Exported sample households to {output_path / 'sample_households.csv'}")