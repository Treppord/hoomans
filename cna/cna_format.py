"""
CNA (Computerized Neural Attributes) Format Specification with Bitfield Optimization
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
    GREEN = 2
    YELLOW = 3
    PURPLE = 4
    ORANGE = 5
    PINK = 6
    BROWN = 7
    GRAY = 8
    BLACK = 9
    WHITE = 10
    
class Nation(enum.Enum):
    NL = 0
    PL = 1
    AL = 2
    FL = 3
    CL = 4
    SL = 5
    DL = 6
    VL = 7
    ML = 8
    GL = 9
    HL = 10

# Constants for bitfield operations
HEALTH_MASK_PHYSICAL = 0b00000111  # 3 bits for 0-5 range (with room for 0-7)
HEALTH_MASK_MENTAL = 0b00111000    # 3 bits, shifted left by 3
HEALTH_MASK_GENERATIONAL = 0b11000000  # 2 bits, shifted left by 6 (0-3 range)

@dataclass
class CNAAttributes:
    # Basic attributes
    first_name: str
    last_name: str
    age_minutes: int  # 0-60 minutes
    gender: Gender
    culture: Culture
    nation: Nation
    
    # Health attributes (will be stored as a single byte)
    physical_health: int  # 0-5
    mental_health: int  # 0-5
    generational_health: int  # 0-5
    
    # Extended DNA-inspired attributes
    genetic_markers: List[int] = None  # Simulated genetic markers
    personality_traits: List[float] = None  # Personality trait values
    intelligence_factor: float = 1.0  # Base intelligence factor
    adaptability: float = 1.0  # Adaptability to environment
    immunity_strength: float = 1.0  # Immune system strength
    
    # Internal storage for packed health values
    _packed_health: int = 0
    
    def __post_init__(self):
        # Initialize default values for optional fields
        if self.genetic_markers is None:
            self.genetic_markers = [0] * 10  # 10 genetic markers
        if self.personality_traits is None:
            self.personality_traits = [0.5] * 5  # 5 personality traits
            
        # Pack health values
        self.pack_health_values()
            
    def pack_health_values(self):
        """Pack health values into a single byte"""
        # Ensure values are in range
        ph = max(0, min(7, self.physical_health))
        mh = max(0, min(7, self.mental_health))
        gh = max(0, min(3, self.generational_health))
        
        # Pack values
        self._packed_health = (
            (ph & HEALTH_MASK_PHYSICAL) |
            ((mh << 3) & HEALTH_MASK_MENTAL) |
            ((gh << 6) & HEALTH_MASK_GENERATIONAL)
        )
    
    def unpack_health_values(self):
        """Unpack health values from the single byte"""
        self.physical_health = self._packed_health & HEALTH_MASK_PHYSICAL
        self.mental_health = (self._packed_health & HEALTH_MASK_MENTAL) >> 3
        self.generational_health = (self._packed_health & HEALTH_MASK_GENERATIONAL) >> 6
            
    def validate(self):
        """Validate that all attributes are within expected ranges"""
        if not (0 <= self.age_minutes <= 60):
            raise ValueError(f"Age must be between 0-60 minutes, got {self.age_minutes}")
        
        # Health values are now validated during packing
        
        if not isinstance(self.gender, Gender):
            raise ValueError(f"Gender must be a Gender enum value")
            
        if not isinstance(self.culture, Culture):
            raise ValueError(f"Culture must be a Culture enum value")
            
        if not isinstance(self.nation, Nation):
            raise ValueError(f"Nation must be a Nation enum value")
    
    # Property getters and setters to ensure health values are always packed/unpacked correctly
    @property
    def packed_health(self):
        """Get the packed health byte"""
        return self._packed_health
    
    @packed_health.setter
    def packed_health(self, value):
        """Set the packed health byte and unpack values"""
        self._packed_health = value
        self.unpack_health_values()
