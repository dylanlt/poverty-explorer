"""Geographic cell model for climate-adjusted MPI calculation."""

from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np


@dataclass
class ClimateProfile:
    """Climate characteristics for a geographic cell."""
    avg_temp_range: float  # Daily/seasonal temperature variance in °C
    heating_degree_days: float  # Annual HDD (base 18°C)
    cooling_degree_days: float  # Annual CDD (base 24°C)
    annual_precipitation: float  # mm
    avg_humidity: float  # %
    temp_min: float  # Annual minimum temperature
    temp_max: float  # Annual maximum temperature
    
    @property
    def climate_harshness(self) -> float:
        """
        Calculate climate harshness index (0-1 scale).
        Based on deviation from thermal comfort zone and temperature extremes.
        """
        # Temperature extremes beyond comfort zone
        comfort_deviation = (
            max(0, 18 - self.temp_min) + 
            max(0, self.temp_max - 24)
        ) / 50  # Normalize to ~0-1
        
        # Degree days indicate heating/cooling needs
        degree_days_factor = (self.heating_degree_days + self.cooling_degree_days) / 3000
        
        # Combine factors
        harshness = np.clip(0.5 * comfort_deviation + 0.5 * degree_days_factor, 0, 1)
        return harshness


@dataclass
class ContextFactors:
    """Socioeconomic and infrastructure context for a geographic cell."""
    population_density: float  # People per km²
    urban_rural_index: float  # 0 = rural, 1 = urban
    infrastructure_index: float  # 0-1 composite score
    elevation: float  # Meters above sea level
    distance_to_services: float  # km to nearest healthcare/education
    
    @property
    def urbanization_level(self) -> float:
        """
        Urbanization level (0-1) based on density and infrastructure.
        """
        # Log scale for density (up to 10,000 per km²)
        density_factor = np.clip(np.log10(max(1, self.population_density)) / 4, 0, 1)
        return 0.5 * density_factor + 0.5 * self.urban_rural_index


@dataclass
class GeographicCell:
    """Represents a geographic cell with climate and context data."""
    cell_id: str
    lat: float
    lon: float
    name: Optional[str] = None
    
    climate: Optional[ClimateProfile] = None
    context: Optional[ContextFactors] = None
    
    def __post_init__(self):
        """Validate coordinates."""
        if not -90 <= self.lat <= 90:
            raise ValueError(f"Invalid latitude: {self.lat}")
        if not -180 <= self.lon <= 180:
            raise ValueError(f"Invalid longitude: {self.lon}")
    
    @property
    def has_complete_data(self) -> bool:
        """Check if cell has all required data."""
        return self.climate is not None and self.context is not None
    
    def get_climate_weights(self) -> Dict[str, float]:
        """
        Calculate climate-adjusted weights for MPI indicators.
        Returns weights that sum to 1.0 across all indicators.
        """
        if not self.climate:
            raise ValueError("Climate data required to calculate weights")
        
        harshness = self.climate.climate_harshness
        urbanization = self.context.urbanization_level if self.context else 0.5
        
        # Base weights (sum to 1.0)
        weights = {
            # Energy needs scale with climate harshness
            'electricity': 0.08 + (0.12 * harshness),
            'cooking_fuel': 0.05 + (0.05 * harshness),
            
            # Sanitation/water more critical in dense urban areas
            'sanitation': 0.08 + (0.07 * urbanization),
            'drinking_water': 0.08 + (0.07 * urbanization),
            
            # Shelter quality matters more in harsh climates
            'flooring': 0.08 + (0.07 * harshness),
            
            # Universal needs - relatively constant
            'nutrition': 0.15,
            'child_mortality': 0.15,
            'years_schooling': 0.08,
            'school_attendance': 0.08,
            'assets': 0.07,
        }
        
        # Normalize to ensure sum = 1.0
        total = sum(weights.values())
        return {k: v/total for k, v in weights.items()}
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'cell_id': self.cell_id,
            'lat': self.lat,
            'lon': self.lon,
            'name': self.name,
            'climate': {
                'harshness': self.climate.climate_harshness if self.climate else None,
                'heating_degree_days': self.climate.heating_degree_days if self.climate else None,
                'cooling_degree_days': self.climate.cooling_degree_days if self.climate else None,
                'temp_range': self.climate.avg_temp_range if self.climate else None,
            } if self.climate else None,
            'context': {
                'urbanization': self.context.urbanization_level if self.context else None,
                'population_density': self.context.population_density if self.context else None,
            } if self.context else None,
        }