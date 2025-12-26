#!/usr/bin/env python
"""Quick start script to test the MPI calculation without Streamlit."""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from models.cells import GeographicCell, ClimateProfile, ContextFactors
from models.mpi import MPICalculator, DeprivationScore, HouseholdData


def main():
    """Run a simple test of the MPI calculation."""
    print("=" * 60)
    print("Climate-Adjusted MPI - Quick Test")
    print("=" * 60)
    
    # Create a sample cell with harsh climate (inland Durban)
    print("\n1. Creating sample geographic cell...")
    
    harsh_climate = ClimateProfile(
        avg_temp_range=15.0,  # Large daily variation
        heating_degree_days=100,
        cooling_degree_days=800,  # Hot climate
        annual_precipitation=800,
        avg_humidity=70,
        temp_min=10,
        temp_max=38,  # Hot summers
    )
    
    urban_context = ContextFactors(
        population_density=3000,
        urban_rural_index=0.8,
        infrastructure_index=0.6,
        elevation=100,
        distance_to_services=5,
    )
    
    harsh_cell = GeographicCell(
        cell_id="TEST_HARSH",
        lat=-29.9,
        lon=30.9,
        name="Inland Urban Ward",
        climate=harsh_climate,
        context=urban_context,
    )
    
    print(f"   Climate Harshness: {harsh_cell.climate.climate_harshness:.2f}")
    print(f"   Urbanization: {harsh_cell.context.urbanization_level:.2f}")
    
    # Create a sample cell with mild climate (coastal Durban)
    print("\n2. Creating mild climate cell...")
    
    mild_climate = ClimateProfile(
        avg_temp_range=8.0,
        heating_degree_days=50,
        cooling_degree_days=200,
        annual_precipitation=1000,
        avg_humidity=75,
        temp_min=15,
        temp_max=28,
    )
    
    mild_cell = GeographicCell(
        cell_id="TEST_MILD",
        lat=-29.85,
        lon=31.03,
        name="Coastal Ward",
        climate=mild_climate,
        context=urban_context,
    )
    
    print(f"   Climate Harshness: {mild_cell.climate.climate_harshness:.2f}")
    print(f"   Urbanization: {mild_cell.context.urbanization_level:.2f}")
    
    # Create a sample household with moderate deprivations
    print("\n3. Creating sample household with deprivations...")
    
    deprivations = DeprivationScore(
        nutrition=0.0,
        child_mortality=0.0,
        years_schooling=0.0,
        school_attendance=0.0,
        electricity=1.0,  # Deprived
        sanitation=1.0,   # Deprived
        drinking_water=0.0,
        flooring=1.0,     # Deprived
        cooking_fuel=1.0, # Deprived
        assets=0.5,       # Partially deprived
    )
    
    household = HouseholdData(
        household_id="HH001",
        cell_id="TEST_HARSH",
        deprivations=deprivations,
        household_size=4,
        num_children=2,
    )
    
    print("   Deprivations:")
    print(f"     - Electricity: {deprivations.electricity}")
    print(f"     - Sanitation: {deprivations.sanitation}")
    print(f"     - Housing: {deprivations.flooring}")
    print(f"     - Cooking fuel: {deprivations.cooking_fuel}")
    
    # Calculate standard MPI
    print("\n4. Calculating Standard MPI...")
    
    standard = MPICalculator.calculate_household_mpi(household, weights=None)
    print(f"   Deprivation Score: {standard['deprivation_score']:.3f}")
    print(f"   Is Poor: {standard['is_poor']}")
    print(f"   Intensity: {standard['intensity']:.3f}")
    
    # Calculate climate-adjusted MPI for harsh climate
    print("\n5. Calculating Climate-Adjusted MPI (Harsh Climate)...")
    
    harsh_weights = harsh_cell.get_climate_weights()
    harsh_adjusted = MPICalculator.calculate_household_mpi(household, weights=harsh_weights)
    
    print(f"   Deprivation Score: {harsh_adjusted['deprivation_score']:.3f}")
    print(f"   Is Poor: {harsh_adjusted['is_poor']}")
    print(f"   Difference: {harsh_adjusted['deprivation_score'] - standard['deprivation_score']:+.3f}")
    
    # Calculate climate-adjusted MPI for mild climate
    print("\n6. Calculating Climate-Adjusted MPI (Mild Climate)...")
    
    mild_weights = mild_cell.get_climate_weights()
    mild_adjusted = MPICalculator.calculate_household_mpi(household, weights=mild_weights)
    
    print(f"   Deprivation Score: {mild_adjusted['deprivation_score']:.3f}")
    print(f"   Is Poor: {mild_adjusted['is_poor']}")
    print(f"   Difference: {mild_adjusted['deprivation_score'] - standard['deprivation_score']:+.3f}")
    
    # Show weight differences
    print("\n7. Weight Comparison (Harsh vs Mild Climate)...")
    print(f"\n   {'Indicator':<20} {'Standard':>10} {'Harsh':>10} {'Mild':>10}")
    print("   " + "-" * 54)
    
    standard_weights = MPICalculator.STANDARD_WEIGHTS
    for indicator in ['electricity', 'sanitation', 'housing', 'cooking_fuel']:
        if indicator == 'housing':
            indicator_key = 'flooring'
        else:
            indicator_key = indicator
        
        std = standard_weights[indicator_key]
        harsh = harsh_weights[indicator_key]
        mild = mild_weights[indicator_key]
        
        print(f"   {indicator:<20} {std:>10.3f} {harsh:>10.3f} {mild:>10.3f}")
    
    # Key insight
    print("\n" + "=" * 60)
    print("KEY INSIGHT:")
    print("=" * 60)
    print(f"\nSame household, same deprivations:")
    print(f"  • In harsh climate: MPI = {harsh_adjusted['deprivation_score']:.3f} ({'POOR' if harsh_adjusted['is_poor'] else 'NOT POOR'})")
    print(f"  • In mild climate:  MPI = {mild_adjusted['deprivation_score']:.3f} ({'POOR' if mild_adjusted['is_poor'] else 'NOT POOR'})")
    print(f"  • Standard method:  MPI = {standard['deprivation_score']:.3f} ({'POOR' if standard['is_poor'] else 'NOT POOR'})")
    
    print("\nLack of electricity matters MORE in harsh climates (heating/cooling needs).")
    print("This is captured by climate-adjusted weights, missed by standard MPI.")
    
    print("\n" + "=" * 60)
    print("\nTo explore interactively, run: streamlit run app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()