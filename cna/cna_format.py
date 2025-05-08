"""
CNA (Computerized Neural Attributes) Format Specification

A binary format for storing entity attributes in an optimized way.
"""

import struct
import enum
from dataclasses import dataclass
from typing import Optional, List, Tuple

class Gender(enum.Enum):
    MALE = 0
    FEMALE = 1
    
class Culture(enum.Enum):
    RED = 0
    BLUE = 1
    
class Nation(enum.Enum):
    NL = 0
    PL = 1

@dataclass
class CNAAttributes:
    # Basic attributes
    first_name: str
    last_name: str
    age_minutes: int  # 0-60 minutes
    gender: Gender
    culture: Culture
    nation: Nation
    physical_health: int  # 0-5
    generational_health: int  # 0-5
    mental_health: int  # 0-5
    
    # Extended DNA-inspired attributes
    genetic_markers: List[int] = None  # Simulated genetic markers
    personality_traits: List[float] = None  # Personality trait values
    intelligence_factor: float = 1.0  # Base intelligence factor
    adaptability: float = 1.0  # Adaptability to environment
    immunity_strength: float = 1.0  # Immune system strength
    
    def __post_init__(self):
        # Initialize default values for optional fields
        if self.genetic_markers is None:
            self.genetic_markers = [0] * 10  # 10 genetic markers
        if self.personality_traits is None:
            self.personality_traits = [0.5] * 5  # 5 personality traits
            
    def validate(self):
        """Validate that all attributes are within expected ranges"""
        if not (0 <= self.age_minutes <= 60):
            raise ValueError(f"Age must be between 0-60 minutes, got {self.age_minutes}")
        
        for health_attr in [self.physical_health, self.generational_health, self.mental_health]:
            if not (0 <= health_attr <= 5):
                raise ValueError(f"Health attributes must be between 0-5, got {health_attr}")
                
        if not isinstance(self.gender, Gender):
            raise ValueError(f"Gender must be a Gender enum value")
            
        if not isinstance(self.culture, Culture):
            raise ValueError(f"Culture must be a Culture enum value")
            
        if not isinstance(self.nation, Nation):
            raise ValueError(f"Nation must be a Nation enum value")