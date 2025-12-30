#!/usr/bin/env python
"""
Compare Standard MPI vs Climate-Adjusted MPI vs Enhanced MPI.
Demonstrates how additional dimensions (housing tenure/cost, digital, transport, etc.) 
affect poverty measurement.
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from models.cells import GeographicCell, ClimateProfile, ContextFactors
from models.mpi import MPICalculator, DeprivationScore, HouseholdData
from models.enhanced_mpi import (
    EnhancedMPICalculator,
    EnhancedDeprivationScore,
    EnhancedHouseholdData,
    EnhancedHousingDeprivation,
    DigitalDeprivation,
    TransportDeprivation,
    EconomicVulnerability,
    EnvironmentalDeprivation,
)


def create_example_household(scenario: str) -> EnhancedHouseholdData:
    """Create example household for different scenarios."""
    
    if scenario == "renter_high_cost":
        # Household with adequate structure but high rent burden
        return EnhancedHouseholdData(
            household_id="RENTER_HIGH",
            cell_id="TEST",
            deprivations=EnhancedDeprivationScore(
                # Original MPI - Not severely deprived
                nutrition=0.0,
                child_mortality=0.0,
                years_schooling=0.0,
                school_attendance=0.0,
                electricity=0.0,  # Has electricity
                sanitation=0.0,
                drinking_water=0.0,
                cooking_fuel=0.0,
                assets=0.0,
                
                # Enhanced housing - PROBLEM: high rent burden
                housing=EnhancedHousingDeprivation(
                    structure_quality=0.2,  # Decent structure
                    tenure_security=0.3,  # Secure rental
                    cost_burden=0.9,  # 50% of income to rent!
                ),
                
                # Digital - Has access
                digital=DigitalDeprivation(
                    no_internet_access=0.0,
                    no_device=0.0,
                    digital_illiteracy=0.0,
                ),
                
                # Transport - Car owner, manageable
                transport=TransportDeprivation(
                    excessive_commute_time=0.0,
                    transport_cost_burden=0.3,
                    no_transport_access=0.0,
                ),
                
                # Economic - Vulnerable due to rent
                economic_security=EconomicVulnerability(
                    income_volatility=0.3,
                    no_emergency_savings=0.8,  # Can't save due to rent
                    no_social_protection=0.0,
                    high_debt_burden=0.6,
                ),
                
                # Environment - OK
                environment=EnvironmentalDeprivation(
                    poor_air_quality=0.0,
                    flood_risk=0.0,
                    heat_exposure=0.0,
                    toxic_proximity=0.0,
                ),
            ),
            household_size=3,
            monthly_income=6000,
            monthly_housing_cost=3000,  # 50% of income!
            monthly_transport_cost=900,
            tenure_type='secure_rental',
            local_rental_index=1.5,  # Expensive area
        )
    
    elif scenario == "owner_poor_structure":
        # Homeowner with poor structure but no ongoing costs
        return EnhancedHouseholdData(
            household_id="OWNER_POOR",
            cell_id="TEST",
            deprivations=EnhancedDeprivationScore(
                # Original MPI - Some deprivation
                nutrition=0.3,
                child_mortality=0.0,
                years_schooling=0.5,
                school_attendance=0.0,
                electricity=1.0,  # No electricity
                sanitation=1.0,
                drinking_water=0.0,
                cooking_fuel=1.0,
                assets=0.8,
                
                # Enhanced housing - poor structure but OWNED
                housing=EnhancedHousingDeprivation(
                    structure_quality=0.8,  # Poor structure
                    tenure_security=0.0,  # Owns it - secure!
                    cost_burden=0.1,  # Minimal ongoing cost
                ),
                
                # Digital - No access
                digital=DigitalDeprivation(
                    no_internet_access=1.0,
                    no_device=0.8,
                    digital_illiteracy=0.9,
                ),
                
                # Transport - No vehicle, poor transit
                transport=TransportDeprivation(
                    excessive_commute_time=1.0,
                    transport_cost_burden=0.8,
                    no_transport_access=0.7,
                ),
                
                # Economic - Stable but low
                economic_security=EconomicVulnerability(
                    income_volatility=0.2,  # Pension - stable
                    no_emergency_savings=0.9,
                    no_social_protection=0.3,  # Some pension
                    high_debt_burden=0.1,  # Low debt due to ownership
                ),
                
                # Environment - Exposed
                environment=EnvironmentalDeprivation(
                    poor_air_quality=0.6,
                    flood_risk=0.8,
                    heat_exposure=1.0,  # No electricity = no cooling
                    toxic_proximity=0.5,
                ),
            ),
            household_size=4,
            monthly_income=3000,
            monthly_housing_cost=200,  # Just maintenance
            monthly_transport_cost=600,
            tenure_type='owner',
        )
    
    elif scenario == "digital_excluded":
        # Household with basic services but digitally excluded
        return EnhancedHouseholdData(
            household_id="DIGITAL_EXCLUDED",
            cell_id="TEST",
            deprivations=EnhancedDeprivationScore(
                # Original MPI - Adequate
                nutrition=0.0,
                child_mortality=0.0,
                years_schooling=0.3,
                school_attendance=0.0,
                electricity=0.0,
                sanitation=0.0,
                drinking_water=0.0,
                cooking_fuel=0.0,
                assets=0.3,
                
                # Housing - OK
                housing=EnhancedHousingDeprivation(
                    structure_quality=0.2,
                    tenure_security=0.0,
                    cost_burden=0.3,
                ),
                
                # Digital - COMPLETELY EXCLUDED
                digital=DigitalDeprivation(
                    no_internet_access=1.0,
                    no_device=1.0,
                    digital_illiteracy=1.0,
                ),
                
                # Transport - Adequate
                transport=TransportDeprivation(
                    excessive_commute_time=0.3,
                    transport_cost_burden=0.4,
                    no_transport_access=0.0,
                ),
                
                # Economic - OK
                economic_security=EconomicVulnerability(
                    income_volatility=0.3,
                    no_emergency_savings=0.5,
                    no_social_protection=0.3,
                    high_debt_burden=0.2,
                ),
                
                # Environment - OK
                environment=EnvironmentalDeprivation(
                    poor_air_quality=0.2,
                    flood_risk=0.1,
                    heat_exposure=0.0,
                    toxic_proximity=0.0,
                ),
            ),
            household_size=2,
            monthly_income=5000,
            monthly_housing_cost=1500,
            monthly_transport_cost=800,
            tenure_type='owner',
        )


def main():
    print("=" * 70)
    print("MPI Comparison: Standard vs Climate-Adjusted vs Enhanced")
    print("=" * 70)
    
    # Create test climate context
    harsh_climate = ClimateProfile(
        avg_temp_range=15.0,
        heating_degree_days=100,
        cooling_degree_days=800,
        annual_precipitation=800,
        avg_humidity=70,
        temp_min=10,
        temp_max=38,
    )
    
    urban_context = ContextFactors(
        population_density=5000,
        urban_rural_index=0.9,
        infrastructure_index=0.7,
        elevation=50,
        distance_to_services=3,
    )
    
    cell = GeographicCell(
        cell_id="URBAN_HARSH",
        lat=-29.9,
        lon=30.9,
        name="Urban Inland Ward",
        climate=harsh_climate,
        context=urban_context,
    )
    
    print(f"\nTest Context:")
    print(f"  Climate Harshness: {cell.climate.climate_harshness:.2f}")
    print(f"  Urbanization: {cell.context.urbanization_level:.2f}")
    
    # Test scenarios
    scenarios = [
        ("renter_high_cost", "Renter with High Rent Burden"),
        ("owner_poor_structure", "Homeowner with Poor Structure"),
        ("digital_excluded", "Digitally Excluded Household"),
    ]
    
    for scenario_id, scenario_name in scenarios:
        print("\n" + "=" * 70)
        print(f"SCENARIO: {scenario_name}")
        print("=" * 70)
        
        household = create_example_household(scenario_id)
        
        # 1. Standard MPI (backward compatible)
        standard_deprivations = DeprivationScore(
            **household.deprivations.to_standard_mpi_compatible()
        )
        standard_hh = HouseholdData(
            household_id=household.household_id,
            cell_id=household.cell_id,
            deprivations=standard_deprivations,
            household_size=household.household_size,
        )
        standard_result = MPICalculator.calculate_household_mpi(standard_hh)
        
        # 2. Climate-Adjusted MPI
        climate_weights = cell.get_climate_weights()
        climate_result = MPICalculator.calculate_household_mpi(standard_hh, weights=climate_weights)
        
        # 3. Enhanced MPI (with all new dimensions)
        enhanced_weights = EnhancedMPICalculator.get_context_adjusted_weights(
            climate_harshness=cell.climate.climate_harshness,
            urbanization=cell.context.urbanization_level,
            sprawl_index=household.urban_sprawl_index or 0.1,
            digital_economy_intensity=0.6,
            rental_market_tightness=household.local_rental_index or 0.5,
        )
        
        housing_weights = EnhancedMPICalculator.calculate_housing_subcomponent_weights(
            climate_harshness=cell.climate.climate_harshness,
            rental_market_tightness=household.local_rental_index or 0.5,
        )
        
        enhanced_result = EnhancedMPICalculator.calculate_household_mpi(
            household,
            weights=enhanced_weights,
            housing_weights=housing_weights,
        )
        
        # Display results
        print(f"\n{'Method':<25} {'Score':>10} {'Poor?':>10} {'Difference':>12}")
        print("-" * 70)
        
        print(f"{'Standard MPI':<25} {standard_result['deprivation_score']:>10.3f} "
              f"{'YES' if standard_result['is_poor'] else 'NO':>10} {'-':>12}")
        
        climate_diff = climate_result['deprivation_score'] - standard_result['deprivation_score']
        print(f"{'Climate-Adjusted MPI':<25} {climate_result['deprivation_score']:>10.3f} "
              f"{'YES' if climate_result['is_poor'] else 'NO':>10} {climate_diff:>+12.3f}")
        
        enhanced_diff = enhanced_result['deprivation_score'] - standard_result['deprivation_score']
        print(f"{'Enhanced MPI':<25} {enhanced_result['deprivation_score']:>10.3f} "
              f"{'YES' if enhanced_result['is_poor'] else 'NO':>10} {enhanced_diff:>+12.3f}")
        
        # Key insight for this scenario
        print(f"\n📊 Key Insight:")
        
        if scenario_id == "renter_high_cost":
            print(f"   Standard MPI: {'POOR' if standard_result['is_poor'] else 'NOT POOR'} - "
                  "misses 50% rent burden")
            print(f"   Enhanced MPI: {'POOR' if enhanced_result['is_poor'] else 'NOT POOR'} - "
                  "captures housing cost crisis")
            print(f"   Housing cost: {household.monthly_housing_cost:.0f} / "
                  f"{household.monthly_income:.0f} ({household.housing_cost_burden:.1%})")
        
        elif scenario_id == "owner_poor_structure":
            print(f"   Standard MPI: {'POOR' if standard_result['is_poor'] else 'NOT POOR'} - "
                  "sees deprivations")
            print(f"   Enhanced MPI: {'POOR' if enhanced_result['is_poor'] else 'NOT POOR'} - "
                  "considers housing security")
            print(f"   Owns home (secure) but poor structure + digital/transport excluded")
        
        elif scenario_id == "digital_excluded":
            print(f"   Standard MPI: {'POOR' if standard_result['is_poor'] else 'NOT POOR'} - "
                  "basic needs met")
            print(f"   Enhanced MPI: {'POOR' if enhanced_result['is_poor'] else 'NOT POOR'} - "
                  "sees digital exclusion")
            print(f"   Digital economy participation impossible without connectivity")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY: What Each Method Captures")
    print("=" * 70)
    
    print("\n📌 Standard MPI:")
    print("   ✓ Basic health, education, utilities")
    print("   ✗ Misses: rent burden, digital exclusion, transport access")
    print("   ✗ Housing treated as binary (adequate/inadequate)")
    
    print("\n📌 Climate-Adjusted MPI:")
    print("   ✓ Everything in standard MPI")
    print("   ✓ Weights electricity/housing by climate need")
    print("   ✗ Still misses: new forms of deprivation")
    
    print("\n📌 Enhanced MPI:")
    print("   ✓ Everything in climate-adjusted MPI")
    print("   ✓ Housing tenure + cost burden (solves rent/ownership issue)")
    print("   ✓ Digital connectivity (essential in modern economy)")
    print("   ✓ Transportation access (mobility critical)")
    print("   ✓ Economic vulnerability (captures instability)")
    print("   ✓ Environmental hazards (quality of life + health)")
    
    print("\n" + "=" * 70)
    print("The enhanced MPI provides a more complete picture of poverty")
    print("in modern, digitizing economies with tight housing markets.")
    print("=" * 70)


if __name__ == "__main__":
    main()
