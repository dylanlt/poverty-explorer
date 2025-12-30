"""Enhanced MPI calculation with additional dimensions beyond standard MPI."""

from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np


@dataclass
class EnhancedHousingDeprivation:
    """
    Enhanced housing deprivation that separates structure, tenure, and cost.
    Addresses the rent/ownership issue.
    """
    structure_quality: float  # 0-1: physical adequacy (walls, roof, space)
    tenure_security: float  # 0-1: 0=owner, 0.3=secure rental, 1.0=informal/precarious
    cost_burden: float  # 0-1: housing cost as % of income, normalized
    
    @property
    def composite_score(self) -> float:
        """
        Calculate composite housing deprivation.
        Weighted: structure 40%, tenure 30%, cost 30%
        """
        return 0.4 * self.structure_quality + 0.3 * self.tenure_security + 0.3 * self.cost_burden


@dataclass
class DigitalDeprivation:
    """Digital connectivity and literacy deprivation."""
    no_internet_access: float  # 0-1: lacks reliable internet
    no_device: float  # 0-1: lacks smartphone/computer
    digital_illiteracy: float  # 0-1: cannot perform essential digital tasks
    
    @property
    def composite_score(self) -> float:
        """Average across digital indicators."""
        return (self.no_internet_access + self.no_device + self.digital_illiteracy) / 3


@dataclass
class TransportDeprivation:
    """Transportation access and cost deprivation."""
    excessive_commute_time: float  # 0-1: >90 min to work/services
    transport_cost_burden: float  # 0-1: >20% income on transport
    no_transport_access: float  # 0-1: lacks vehicle AND no public transit
    
    @property
    def composite_score(self) -> float:
        """
        Weighted composite: access 40%, time 30%, cost 30%
        """
        return 0.4 * self.no_transport_access + 0.3 * self.excessive_commute_time + 0.3 * self.transport_cost_burden


@dataclass
class EconomicVulnerability:
    """Economic security and vulnerability indicators."""
    income_volatility: float  # 0-1: coefficient of variation in monthly income
    no_emergency_savings: float  # 0-1: cannot handle $400 emergency
    no_social_protection: float  # 0-1: no unemployment insurance or safety net
    high_debt_burden: float  # 0-1: debt service >40% of income
    
    @property
    def composite_score(self) -> float:
        """Average across vulnerability indicators."""
        return (self.income_volatility + self.no_emergency_savings + 
                self.no_social_protection + self.high_debt_burden) / 4


@dataclass
class EnvironmentalDeprivation:
    """Environmental hazards and climate exposure."""
    poor_air_quality: float  # 0-1: PM2.5 > WHO threshold
    flood_risk: float  # 0-1: in flood zone without protection
    heat_exposure: float  # 0-1: dangerous heat days without cooling
    toxic_proximity: float  # 0-1: near industrial/waste sites
    
    @property
    def composite_score(self) -> float:
        """
        Weighted: air quality 30%, heat 30%, flood 25%, toxic 15%
        """
        return (0.3 * self.poor_air_quality + 0.3 * self.heat_exposure + 
                0.25 * self.flood_risk + 0.15 * self.toxic_proximity)


@dataclass
class EnhancedDeprivationScore:
    """
    Enhanced deprivation scores including original MPI plus new dimensions.
    Maintains backwards compatibility with standard MPI.
    """
    # Original MPI - Health (1/3 of standard MPI)
    nutrition: float
    child_mortality: float
    
    # Original MPI - Education (1/3 of standard MPI)
    years_schooling: float
    school_attendance: float
    
    # Original MPI - Living Standards (1/3 of standard MPI)
    # But now with enhanced housing
    electricity: float
    sanitation: float
    drinking_water: float
    cooking_fuel: float
    assets: float
    
    # Enhanced housing (replaces simple 'flooring' indicator)
    housing: EnhancedHousingDeprivation
    
    # New dimensions
    digital: DigitalDeprivation
    transport: TransportDeprivation
    economic_security: EconomicVulnerability
    environment: EnvironmentalDeprivation
    
    def __post_init__(self):
        """Validate all basic scores are between 0 and 1."""
        for field_name, value in self.__dict__.items():
            if isinstance(value, float) and not 0 <= value <= 1:
                raise ValueError(f"{field_name} must be between 0 and 1, got {value}")
    
    def to_standard_mpi_compatible(self) -> Dict[str, float]:
        """
        Convert to standard MPI format for backwards compatibility.
        Uses housing structure quality as 'flooring' equivalent.
        """
        return {
            'nutrition': self.nutrition,
            'child_mortality': self.child_mortality,
            'years_schooling': self.years_schooling,
            'school_attendance': self.school_attendance,
            'electricity': self.electricity,
            'sanitation': self.sanitation,
            'drinking_water': self.drinking_water,
            'flooring': self.housing.structure_quality,  # Approximate
            'cooking_fuel': self.cooking_fuel,
            'assets': self.assets,
        }


@dataclass
class EnhancedHouseholdData:
    """Enhanced household data with additional context."""
    household_id: str
    cell_id: str
    deprivations: EnhancedDeprivationScore
    household_size: int
    
    # Demographics
    num_children: Optional[int] = None
    num_elderly: Optional[int] = None
    
    # Economic context
    monthly_income: Optional[float] = None  # Local currency
    monthly_housing_cost: Optional[float] = None
    monthly_transport_cost: Optional[float] = None
    
    # Housing context
    tenure_type: Optional[str] = None  # 'owner', 'secure_rental', 'informal'
    
    # Location context
    urban_sprawl_index: Optional[float] = None  # 0-1: how spread out the area is
    local_rental_index: Optional[float] = None  # Relative cost of housing in area
    
    @property
    def housing_cost_burden(self) -> Optional[float]:
        """Calculate housing cost as % of income."""
        if self.monthly_income and self.monthly_housing_cost and self.monthly_income > 0:
            return self.monthly_housing_cost / self.monthly_income
        return None
    
    @property
    def transport_cost_burden(self) -> Optional[float]:
        """Calculate transport cost as % of income."""
        if self.monthly_income and self.monthly_transport_cost and self.monthly_income > 0:
            return self.monthly_transport_cost / self.monthly_income
        return None


class EnhancedMPICalculator:
    """Calculate Enhanced Multidimensional Poverty Index."""
    
    # Enhanced MPI weights with new dimensions
    # Core MPI dimensions reduced from 100% to 70% to make room for new dimensions
    ENHANCED_WEIGHTS = {
        # Health: 15% (was 33%)
        'nutrition': 0.075,
        'child_mortality': 0.075,
        
        # Education: 15% (was 33%)
        'years_schooling': 0.075,
        'school_attendance': 0.075,
        
        # Core Living Standards: 40% (was 33%, but now more detailed)
        'electricity': 0.06,
        'sanitation': 0.06,
        'drinking_water': 0.06,
        'cooking_fuel': 0.05,
        'assets': 0.05,
        'housing': 0.12,  # Enhanced housing gets more weight
        
        # New Dimensions: 30%
        'digital': 0.08,  # Digital connectivity increasingly critical
        'transport': 0.08,  # Mobility access
        'economic_security': 0.07,  # Vulnerability
        'environment': 0.07,  # Environmental hazards
    }
    
    POVERTY_CUTOFF = 0.33  # Keep standard threshold for comparability
    
    @classmethod
    def get_context_adjusted_weights(
        cls,
        climate_harshness: float,
        urbanization: float,
        sprawl_index: float = 0.5,
        digital_economy_intensity: float = 0.5,
        rental_market_tightness: float = 0.5,
    ) -> Dict[str, float]:
        """
        Calculate context-adjusted weights for enhanced MPI.
        
        Args:
            climate_harshness: 0-1 scale
            urbanization: 0-1 scale
            sprawl_index: 0-1, how spread out the area is
            digital_economy_intensity: 0-1, how digitized the economy is
            rental_market_tightness: 0-1, housing market pressure
        """
        weights = cls.ENHANCED_WEIGHTS.copy()
        
        # Climate adjustments (electricity, cooking fuel, housing)
        weights['electricity'] += 0.04 * climate_harshness
        weights['cooking_fuel'] += 0.02 * climate_harshness
        weights['housing'] += 0.03 * climate_harshness
        
        # Urbanization adjustments (sanitation, water)
        weights['sanitation'] += 0.04 * urbanization
        weights['drinking_water'] += 0.04 * urbanization
        
        # Sprawl adjustments (transport becomes critical in sprawl)
        weights['transport'] += 0.06 * sprawl_index
        
        # Digital economy (digital access more important in digital economies)
        weights['digital'] += 0.05 * digital_economy_intensity
        
        # Rental market (housing cost matters more in tight markets)
        # This is captured in the housing sub-components weight calculation
        
        # Normalize to sum to 1.0
        total = sum(weights.values())
        return {k: v/total for k, v in weights.items()}
    
    @classmethod
    def calculate_housing_subcomponent_weights(
        cls,
        climate_harshness: float,
        rental_market_tightness: float,
    ) -> Dict[str, float]:
        """
        Calculate weights for housing sub-components.
        
        Returns:
            Dict with weights for structure, tenure, cost
        """
        # Base weights
        structure_weight = 0.40
        tenure_weight = 0.30
        cost_weight = 0.30
        
        # In harsh climates, structure quality matters more
        structure_weight += 0.10 * climate_harshness
        
        # In tight rental markets, cost burden matters more
        cost_weight += 0.15 * rental_market_tightness
        
        # Normalize
        total = structure_weight + tenure_weight + cost_weight
        return {
            'structure': structure_weight / total,
            'tenure': tenure_weight / total,
            'cost': cost_weight / total,
        }
    
    @classmethod
    def calculate_deprivation_score(
        cls,
        deprivations: EnhancedDeprivationScore,
        weights: Optional[Dict[str, float]] = None,
        housing_weights: Optional[Dict[str, float]] = None,
    ) -> float:
        """
        Calculate weighted deprivation score.
        
        Args:
            deprivations: Enhanced deprivation scores
            weights: Overall dimension weights
            housing_weights: Sub-component weights for housing
        """
        if weights is None:
            weights = cls.ENHANCED_WEIGHTS
        
        if housing_weights is None:
            housing_weights = {'structure': 0.4, 'tenure': 0.3, 'cost': 0.3}
        
        score = 0.0
        
        # Simple indicators
        for indicator in ['nutrition', 'child_mortality', 'years_schooling', 
                          'school_attendance', 'electricity', 'sanitation',
                          'drinking_water', 'cooking_fuel', 'assets']:
            score += weights[indicator] * getattr(deprivations, indicator)
        
        # Enhanced housing (use sub-component weights)
        housing_deprivation = (
            housing_weights['structure'] * deprivations.housing.structure_quality +
            housing_weights['tenure'] * deprivations.housing.tenure_security +
            housing_weights['cost'] * deprivations.housing.cost_burden
        )
        score += weights['housing'] * housing_deprivation
        
        # Composite dimensions
        score += weights['digital'] * deprivations.digital.composite_score
        score += weights['transport'] * deprivations.transport.composite_score
        score += weights['economic_security'] * deprivations.economic_security.composite_score
        score += weights['environment'] * deprivations.environment.composite_score
        
        return score
    
    @classmethod
    def calculate_household_mpi(
        cls,
        household: EnhancedHouseholdData,
        weights: Optional[Dict[str, float]] = None,
        housing_weights: Optional[Dict[str, float]] = None,
        cutoff: Optional[float] = None,
    ) -> Dict[str, float]:
        """Calculate enhanced MPI for a household."""
        score = cls.calculate_deprivation_score(
            household.deprivations, 
            weights, 
            housing_weights
        )
        
        if cutoff is None:
            cutoff = cls.POVERTY_CUTOFF
        
        is_poor = score >= cutoff
        intensity = score if is_poor else 0.0
        
        return {
            'deprivation_score': score,
            'is_poor': is_poor,
            'intensity': intensity,
        }
