"""Generate enhanced household data with additional dimensions."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List
import logging

from models.enhanced_mpi import (
    EnhancedDeprivationScore,
    EnhancedHouseholdData,
    EnhancedHousingDeprivation,
    DigitalDeprivation,
    TransportDeprivation,
    EconomicVulnerability,
    EnvironmentalDeprivation,
)

logger = logging.getLogger(__name__)


class EnhancedDataGenerator:
    """Generate enhanced household data with realistic correlations."""
    
    def __init__(self, data_dir: str = './data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_enhanced_households(
        self,
        census_df: pd.DataFrame,
        households_per_ward: int = 30,
        digital_economy_intensity: float = 0.6,  # South Africa is moderately digital
    ) -> List[EnhancedHouseholdData]:
        """
        Generate enhanced household data from ward statistics.
        
        Args:
            census_df: Ward-level census data
            households_per_ward: Number of households per ward
            digital_economy_intensity: How digitized the economy is (0-1)
        """
        households = []
        
        for _, ward in census_df.iterrows():
            cell_id = ward['ward_id']
            
            # Ward-level context
            base_deprivation = (
                ward['pct_no_electricity'] + 
                ward['pct_inadequate_sanitation'] + 
                ward['pct_no_piped_water']
            ) / 3
            
            urbanization = ward['urban_rural_index']
            sprawl = 1 - urbanization  # More rural = more sprawl
            
            # Rental market tightness (higher near coast/CBD)
            coast_distance = ward['longitude'] - 30.7
            rental_tightness = np.clip(1 - coast_distance * 2, 0.3, 1.0)
            
            # Generate households
            for hh_num in range(households_per_ward):
                household_id = f"{cell_id}_HH{hh_num:03d}"
                
                # Household characteristics
                hh_size = max(1, int(np.random.poisson(3.5)))
                num_children = int(np.random.binomial(hh_size - 1, 0.3)) if hh_size > 1 else 0
                num_elderly = int(np.random.binomial(hh_size, 0.15))
                
                # Income (correlated with deprivation)
                # Using rough South African household income distribution
                income_mean = 8000 * (1 - base_deprivation)  # ZAR per month
                income_std = income_mean * 0.4
                monthly_income = max(1000, np.random.lognormal(
                    np.log(income_mean), 
                    0.6
                ))
                
                # Income volatility (higher for informal work)
                informal_work_prob = base_deprivation * 0.7
                is_informal = np.random.random() < informal_work_prob
                income_volatility = 0.5 if is_informal else 0.15
                
                # === HOUSING ===
                
                # Tenure type
                ownership_prob = 0.7 * (1 - base_deprivation)  # Wealthier = more owners
                if np.random.random() < ownership_prob:
                    tenure_type = 'owner'
                    tenure_security = 0.0
                    monthly_housing_cost = monthly_income * 0.05  # Property tax, maintenance
                elif np.random.random() < 0.7:
                    tenure_type = 'secure_rental'
                    tenure_security = 0.3
                    # Rental cost varies by area
                    base_rent = 2000 * rental_tightness * (1 + urbanization * 0.5)
                    monthly_housing_cost = np.random.normal(base_rent, base_rent * 0.2)
                else:
                    tenure_type = 'informal'
                    tenure_security = 1.0
                    monthly_housing_cost = monthly_income * 0.10  # Informal settlements
                
                # Structure quality (correlated with deprivation)
                structure_quality = np.random.beta(
                    2 * (1 - base_deprivation) + 0.5,
                    2 * base_deprivation + 0.5
                )
                
                # Cost burden
                housing_cost_ratio = monthly_housing_cost / monthly_income
                cost_burden = min(1.0, housing_cost_ratio / 0.30)  # 30% threshold
                
                housing = EnhancedHousingDeprivation(
                    structure_quality=structure_quality,
                    tenure_security=tenure_security,
                    cost_burden=cost_burden,
                )
                
                # === DIGITAL ===
                
                # Internet access (function of income and urbanization)
                internet_prob = 0.4 + 0.4 * (1 - base_deprivation) + 0.2 * urbanization
                no_internet = float(np.random.random() > internet_prob)
                
                # Device ownership (correlated with internet)
                device_prob = internet_prob * 0.9  # Slightly higher
                no_device = float(np.random.random() > device_prob)
                
                # Digital literacy (correlated with education and age)
                edu_deprived = np.random.random() < ward['pct_no_schooling']
                literacy_prob = 0.6 if not edu_deprived else 0.2
                if num_elderly > 0:
                    literacy_prob *= 0.6  # Elderly less digitally literate
                digital_illiteracy = float(np.random.random() > literacy_prob)
                
                digital = DigitalDeprivation(
                    no_internet_access=no_internet,
                    no_device=no_device,
                    digital_illiteracy=digital_illiteracy,
                )
                
                # === TRANSPORT ===
                
                # Vehicle ownership
                vehicle_prob = 0.3 + 0.5 * (1 - base_deprivation)
                has_vehicle = np.random.random() < vehicle_prob
                
                # Public transit access (better in urban areas)
                transit_prob = 0.3 + 0.6 * urbanization
                has_transit = np.random.random() < transit_prob
                
                no_transport_access = float(not has_vehicle and not has_transit)
                
                # Commute time (worse in sprawl without vehicle)
                base_commute = 30 + 60 * sprawl  # Minutes
                if not has_vehicle:
                    base_commute *= 1.5
                excessive_commute = float(base_commute > 90)
                
                # Transport cost
                if has_vehicle:
                    transport_cost = monthly_income * 0.15  # Fuel, maintenance
                elif has_transit:
                    transport_cost = monthly_income * 0.10  # Public transit
                else:
                    transport_cost = monthly_income * 0.20  # Taxis, informal
                
                transport_cost_burden = min(1.0, (transport_cost / monthly_income) / 0.20)
                
                transport = TransportDeprivation(
                    excessive_commute_time=excessive_commute,
                    transport_cost_burden=transport_cost_burden,
                    no_transport_access=no_transport_access,
                )
                
                # === ECONOMIC SECURITY ===
                
                # Emergency savings
                savings_prob = 0.5 * (1 - base_deprivation) * (1 - income_volatility)
                no_emergency_savings = float(np.random.random() > savings_prob)
                
                # Social protection (formal employment = more protection)
                protection_prob = 0.3 + 0.4 * (1 - informal_work_prob)
                no_social_protection = float(np.random.random() > protection_prob)
                
                # Debt burden (more likely if high costs)
                debt_prob = 0.2 + 0.3 * cost_burden + 0.2 * transport_cost_burden
                high_debt_burden = float(np.random.random() < debt_prob)
                
                economic_security = EconomicVulnerability(
                    income_volatility=min(1.0, income_volatility),
                    no_emergency_savings=no_emergency_savings,
                    no_social_protection=no_social_protection,
                    high_debt_burden=high_debt_burden,
                )
                
                # === ENVIRONMENT ===
                
                # Air quality (worse near industrial areas, in urban sprawl)
                pollution_risk = 0.3 * urbanization + 0.3 * base_deprivation
                poor_air_quality = float(np.random.random() < pollution_risk)
                
                # Flood risk (informal settlements more vulnerable)
                flood_prob = 0.1 if tenure_type != 'informal' else 0.4
                flood_risk = float(np.random.random() < flood_prob)
                
                # Heat exposure (function of climate and lack of cooling)
                no_electricity = float(np.random.random() < ward['pct_no_electricity'])
                heat_exposure = no_electricity  # If no electricity, can't cool
                
                # Toxic proximity (more common in poor areas)
                toxic_prob = 0.2 * base_deprivation
                toxic_proximity = float(np.random.random() < toxic_prob)
                
                environment = EnvironmentalDeprivation(
                    poor_air_quality=poor_air_quality,
                    flood_risk=flood_risk,
                    heat_exposure=heat_exposure,
                    toxic_proximity=toxic_proximity,
                )
                
                # === ORIGINAL MPI INDICATORS ===
                
                deprivations = EnhancedDeprivationScore(
                    # Health
                    nutrition=float(np.random.random() < ward['pct_malnourished']),
                    child_mortality=float(np.random.random() < ward['child_mortality_rate']),
                    
                    # Education
                    years_schooling=float(np.random.random() < ward['pct_no_schooling']),
                    school_attendance=float(np.random.random() < ward['pct_child_not_attending']) if num_children > 0 else 0.0,
                    
                    # Living standards (original)
                    electricity=no_electricity,
                    sanitation=float(np.random.random() < ward['pct_inadequate_sanitation']),
                    drinking_water=float(np.random.random() < ward['pct_no_piped_water']),
                    cooking_fuel=float(np.random.random() < ward['pct_wood_fuel']),
                    assets=float(np.random.random() < ward['pct_no_assets']),
                    
                    # Enhanced dimensions
                    housing=housing,
                    digital=digital,
                    transport=transport,
                    economic_security=economic_security,
                    environment=environment,
                )
                
                household = EnhancedHouseholdData(
                    household_id=household_id,
                    cell_id=cell_id,
                    deprivations=deprivations,
                    household_size=hh_size,
                    num_children=num_children,
                    num_elderly=num_elderly,
                    monthly_income=monthly_income,
                    monthly_housing_cost=monthly_housing_cost,
                    monthly_transport_cost=transport_cost,
                    tenure_type=tenure_type,
                    urban_sprawl_index=sprawl,
                    local_rental_index=rental_tightness,
                )
                
                households.append(household)
        
        logger.info(f"Generated {len(households)} enhanced households")
        return households
