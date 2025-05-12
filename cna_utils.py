"""
Utility functions for working with CNA files in the game
"""

import struct
import io
import enum
from dataclasses import dataclass
from typing import Optional, List, Tuple, BinaryIO

# Copy of the necessary CNA classes to avoid import issues

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

class CNACodec:
    """Encoder/Decoder for CNA file format"""
    
    # File signature to identify CNA files
    FILE_SIGNATURE = b'CNA1'
    
    @staticmethod
    def encode(attributes: CNAAttributes) -> bytes:
        """Encode CNAAttributes into binary CNA format"""
        # Validate attributes before encoding
        attributes.validate()
        
        buffer = io.BytesIO()
        
        # Write file signature
        buffer.write(CNACodec.FILE_SIGNATURE)
        
        # Pack basic attributes
        # String format: length (2 bytes) + UTF-8 encoded string
        for name in [attributes.first_name, attributes.last_name]:
            name_bytes = name.encode('utf-8')
            buffer.write(struct.pack('<H', len(name_bytes)))
            buffer.write(name_bytes)
        
        # Pack numeric and enum values
        buffer.write(struct.pack('<B', attributes.age_minutes))
        buffer.write(struct.pack('<B', attributes.gender.value))
        buffer.write(struct.pack('<B', attributes.culture.value))
        buffer.write(struct.pack('<B', attributes.nation.value))
        buffer.write(struct.pack('<B', attributes.physical_health))
        buffer.write(struct.pack('<B', attributes.generational_health))
        buffer.write(struct.pack('<B', attributes.mental_health))
        
        # Pack extended attributes
        buffer.write(struct.pack('<f', attributes.intelligence_factor))
        buffer.write(struct.pack('<f', attributes.adaptability))
        buffer.write(struct.pack('<f', attributes.immunity_strength))
        
        # Pack genetic markers
        buffer.write(struct.pack('<B', len(attributes.genetic_markers)))
        for marker in attributes.genetic_markers:
            buffer.write(struct.pack('<H', marker))
            
        # Pack personality traits
        buffer.write(struct.pack('<B', len(attributes.personality_traits)))
        for trait in attributes.personality_traits:
            buffer.write(struct.pack('<f', trait))
        
        return buffer.getvalue()
    
    @staticmethod
    def decode(data: bytes) -> CNAAttributes:
        """Decode binary CNA format into CNAAttributes"""
        buffer = io.BytesIO(data)
        
        # Check file signature
        signature = buffer.read(4)
        if signature != CNACodec.FILE_SIGNATURE:
            raise ValueError(f"Invalid CNA file signature: {signature}")
        
        # Read strings
        first_name_len = struct.unpack('<H', buffer.read(2))[0]
        first_name = buffer.read(first_name_len).decode('utf-8')
        
        last_name_len = struct.unpack('<H', buffer.read(2))[0]
        last_name = buffer.read(last_name_len).decode('utf-8')
        
        # Read basic attributes
        age_minutes = struct.unpack('<B', buffer.read(1))[0]
        gender = Gender(struct.unpack('<B', buffer.read(1))[0])
        culture = Culture(struct.unpack('<B', buffer.read(1))[0])
        nation = Nation(struct.unpack('<B', buffer.read(1))[0])
        physical_health = struct.unpack('<B', buffer.read(1))[0]
        generational_health = struct.unpack('<B', buffer.read(1))[0]
        mental_health = struct.unpack('<B', buffer.read(1))[0]
        
        # Read extended attributes
        intelligence_factor = struct.unpack('<f', buffer.read(4))[0]
        adaptability = struct.unpack('<f', buffer.read(4))[0]
        immunity_strength = struct.unpack('<f', buffer.read(4))[0]
        
        # Read genetic markers
        marker_count = struct.unpack('<B', buffer.read(1))[0]
        genetic_markers = []
        for _ in range(marker_count):
            marker = struct.unpack('<H', buffer.read(2))[0]
            genetic_markers.append(marker)
            
        # Read personality traits
        trait_count = struct.unpack('<B', buffer.read(1))[0]
        personality_traits = []
        for _ in range(trait_count):
            trait = struct.unpack('<f', buffer.read(4))[0]
            personality_traits.append(trait)
        
        return CNAAttributes(
            first_name=first_name,
            last_name=last_name,
            age_minutes=age_minutes,
            gender=gender,
            culture=culture,
            nation=nation,
            physical_health=physical_health,
            generational_health=generational_health,
            mental_health=mental_health,
            genetic_markers=genetic_markers,
            personality_traits=personality_traits,
            intelligence_factor=intelligence_factor,
            adaptability=adaptability,
            immunity_strength=immunity_strength
        )
    
    @staticmethod
    def save_to_file(attributes: CNAAttributes, filepath: str):
        """Save CNAAttributes to a file"""
        with open(filepath, 'wb') as f:
            f.write(CNACodec.encode(attributes))
    
    @staticmethod
    def load_from_file(filepath: str) -> CNAAttributes:
        """Load CNAAttributes from a file"""
        with open(filepath, 'rb') as f:
            return CNACodec.decode(f.read())
        
# Move this function outside of the class and fix it
def calculate_entity_color(cna_attributes):
    """Calculate entity color based on CNA attributes"""
    # Base colors for different cultures
    culture_colors = {
        Culture.RED: (255, 0, 0),    # Red
        Culture.BLUE: (0, 0, 255),   # Blue
        Culture.GREEN: (0, 255, 0),  # Green
        Culture.YELLOW: (255, 255, 0), # Yellow
        Culture.PURPLE: (128, 0, 128), # Purple
        Culture.ORANGE: (255, 165, 0), # Orange
        Culture.PINK: (255, 192, 203), # Pink
        Culture.BROWN: (165, 42, 42),  # Brown
        Culture.GRAY: (128, 128, 128), # Gray
        Culture.BLACK: (0, 0, 0),      # Black
        Culture.WHITE: (255, 255, 255)  # White
    }
    
    # Get base color for culture
    base_color = culture_colors.get(cna_attributes.culture, (0, 255, 0))  # Default to green if culture not found
    
    # Calculate brightness factor based on age (1.0 for youngest, 0.4 for oldest)
    # Age range is 0-60 minutes
    brightness = 1.0 - (cna_attributes.age_minutes / 60.0 * 0.6)
    
    # Apply brightness to color
    color = tuple(int(c * brightness) for c in base_color)
    
    return color