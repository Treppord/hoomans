"""
CNA Encoder/Decoder for converting between CNA binary format and Python objects
"""

import struct
import io
from typing import BinaryIO, Tuple
from cna.cna_format import CNAAttributes, Gender, Culture, Nation


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
