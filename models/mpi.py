"""MPI calculation logic - standard and climate-adjusted versions."""

from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np


@dataclass
class DeprivationScore:
    """Individual deprivation scores for each MPI indicator (0-1 scale)."""
    # Health (1/3 of total)
    nutrition: float  # 0 = not deprived, 1 = deprived
    child_mortality: float
    
    # Education (1/3 of total)
    years_schooling: float
    school_attendance: float
    
    # Living Standards (1/3 of total)
    electricity: float
    sanitation: float
    drinking_water: float
    flooring: float
    cooking_fuel: float
    assets: float
    
    def __post_init__(self):
        """Validate all scores are between 0 and 1."""
        for field_name, value in self.__dict__.items():
            if not 0 <= value <= 1:
                raise ValueError(f"{field_name} must be between 0 and 1, got {value}")


@dataclass
class HouseholdData:
    """Household-level poverty data."""
    household_id: str
    cell_id: str
    deprivations: DeprivationScore
    household_size: int
    
    # Optional demographics
    num_children: Optional[int] = None
    num_elderly: Optional[int] = None


class MPICalculator:
    """Calculate Multidimensional Poverty Index."""
    
    # Standard MPI weights (Alkire-Foster methodology)
    STANDARD_WEIGHTS = {
        # Health: 1/3 total, split equally
        'nutrition': 1/6,
        'child_mortality': 1/6,
        
        # Education: 1/3 total, split equally
        'years_schooling': 1/6,
        'school_attendance': 1/6,
        
        # Living Standards: 1/3 total, split across 6 indicators
        'electricity': 1/18,
        'sanitation': 1/18,
        'drinking_water': 1/18,
        'flooring': 1/18,
        'cooking_fuel': 1/18,
        'assets': 1/18,
    }
    
    POVERTY_CUTOFF = 0.33  # 33.3% - standard MPI threshold
    
    @classmethod
    def calculate_deprivation_score(
        cls, 
        deprivations: DeprivationScore, 
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate weighted deprivation score for a household.
        
        Args:
            deprivations: Deprivation scores for each indicator
            weights: Custom weights dict, or None for standard weights
            
        Returns:
            Weighted deprivation score (0-1)
        """
        if weights is None:
            weights = cls.STANDARD_WEIGHTS
        
        score = 0.0
        for indicator, weight in weights.items():
            deprivation_value = getattr(deprivations, indicator)
            score += weight * deprivation_value
        
        return score
    
    @classmethod
    def is_poor(cls, deprivation_score: float, cutoff: Optional[float] = None) -> bool:
        """Determine if household is multidimensionally poor."""
        if cutoff is None:
            cutoff = cls.POVERTY_CUTOFF
        return deprivation_score >= cutoff
    
    @classmethod
    def calculate_intensity(
        cls, 
        deprivation_score: float, 
        cutoff: Optional[float] = None
    ) -> float:
        """
        Calculate intensity of poverty (average deprivation among the poor).
        Returns 0 if not poor.
        """
        if cutoff is None:
            cutoff = cls.POVERTY_CUTOFF
        
        if deprivation_score >= cutoff:
            return deprivation_score
        return 0.0
    
    @classmethod
    def calculate_household_mpi(
        cls,
        household: HouseholdData,
        weights: Optional[Dict[str, float]] = None,
        cutoff: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate MPI metrics for a single household.
        
        Returns:
            Dict with deprivation_score, is_poor, intensity
        """
        score = cls.calculate_deprivation_score(household.deprivations, weights)
        is_poor = cls.is_poor(score, cutoff)
        intensity = cls.calculate_intensity(score, cutoff)
        
        return {
            'deprivation_score': score,
            'is_poor': is_poor,
            'intensity': intensity,
        }
    
    @classmethod
    def calculate_population_mpi(
        cls,
        households: list[HouseholdData],
        weights: Optional[Dict[str, float]] = None,
        cutoff: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate MPI for a population (incidence × intensity).
        
        Returns:
            Dict with MPI, headcount_ratio (H), intensity (A), and other metrics
        """
        if not households:
            return {
                'MPI': 0.0,
                'headcount_ratio': 0.0,
                'intensity': 0.0,
                'num_poor': 0,
                'total_population': 0,
            }
        
        results = [
            cls.calculate_household_mpi(hh, weights, cutoff) 
            for hh in households
        ]
        
        num_poor = sum(1 for r in results if r['is_poor'])
        total = len(households)
        
        # Headcount ratio (H): proportion poor
        headcount_ratio = num_poor / total if total > 0 else 0
        
        # Average intensity (A): average deprivation among the poor
        if num_poor > 0:
            avg_intensity = np.mean([
                r['intensity'] for r in results if r['is_poor']
            ])
        else:
            avg_intensity = 0.0
        
        # MPI = H × A
        mpi = headcount_ratio * avg_intensity
        
        return {
            'MPI': mpi,
            'headcount_ratio': headcount_ratio,
            'intensity': avg_intensity,
            'num_poor': num_poor,
            'total_population': total,
            'avg_deprivation_score': np.mean([r['deprivation_score'] for r in results]),
        }
    
    @classmethod
    def compare_standard_vs_adjusted(
        cls,
        household: HouseholdData,
        adjusted_weights: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare standard MPI vs climate-adjusted MPI for a household.
        
        Returns:
            Dict with 'standard' and 'adjusted' results
        """
        standard = cls.calculate_household_mpi(household, weights=None)
        adjusted = cls.calculate_household_mpi(household, weights=adjusted_weights)
        
        return {
            'standard': standard,
            'adjusted': adjusted,
            'difference': {
                'deprivation_score': adjusted['deprivation_score'] - standard['deprivation_score'],
                'classification_changed': standard['is_poor'] != adjusted['is_poor'],
            }
        }