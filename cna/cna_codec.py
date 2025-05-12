"""
CNA Encoder/Decoder with Bitfield Optimization
"""

import struct
import io
from typing import BinaryIO, Tuple
from cna_format import CNAAttributes, Gender, Culture, Nation, HEALTH_MASK_PHYSICAL, HEALTH_MASK_MENTAL, HEALTH_MASK_GENERATIONAL

class CNACodec:
    """Encoder/Decoder for CNA file format"""
    
    # File signature to identify CNA files
    FILE_SIGNATURE = b'CNA2'  # Updated to version 2 for bitfield format
    
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
        
        # Pack age
        buffer.write(struct.pack('<B', attributes.age_minutes))
        
        # Pack enums into a single byte (4 bits each)
        # Gender (1 bit) + Culture (4 bits) + 3 unused bits
        enum_byte1 = (attributes.gender.value & 0x01) | ((attributes.culture.value & 0x0F) << 1)
        buffer.write(struct.pack('<B', enum_byte1))
        
        # Pack Nation (4 bits) + 4 unused bits
        enum_byte2 = attributes.nation.value & 0x0F
        buffer.write(struct.pack('<B', enum_byte2))
        
        # Pack health values (already packed in the object)
        buffer.write(struct.pack('<B', attributes.packed_health))
        
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
        if signature == CNACodec.FILE_SIGNATURE:
            # New format (version 2)
            return CNACodec._decode_v2(buffer)
        elif signature == b'CNA1':
            # Old format (version 1)
            return CNACodec._decode_v1(buffer)
        else:
            raise ValueError(f"Invalid CNA file signature: {signature}")
    
    @staticmethod
    def _decode_v2(buffer: io.BytesIO) -> CNAAttributes:
        """Decode version 2 (bitfield) format"""
        # Read strings
        first_name_len = struct.unpack('<H', buffer.read(2))[0]
        first_name = buffer.read(first_name_len).decode('utf-8')
        
        last_name_len = struct.unpack('<H', buffer.read(2))[0]
        last_name = buffer.read(last_name_len).decode('utf-8')
        
        # Read age
        age_minutes = struct.unpack('<B', buffer.read(1))[0]
        
        # Read packed enums
        enum_byte1 = struct.unpack('<B', buffer.read(1))[0]
        gender = Gender(enum_byte1 & 0x01)
        culture = Culture((enum_byte1 >> 1) & 0x0F)
        
        enum_byte2 = struct.unpack('<B', buffer.read(1))[0]
        nation = Nation(enum_byte2 & 0x0F)
        
        # Read packed health
        packed_health = struct.unpack('<B', buffer.read(1))[0]
        
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
        
        # Create attributes with unpacked health values
        physical_health = packed_health & HEALTH_MASK_PHYSICAL
        mental_health = (packed_health & HEALTH_MASK_MENTAL) >> 3
        generational_health = (packed_health & HEALTH_MASK_GENERATIONAL) >> 6
        
        return CNAAttributes(
            first_name=first_name,
            last_name=last_name,
            age_minutes=age_minutes,
            gender=gender,
            culture=culture,
            nation=nation,
            physical_health=physical_health,
            mental_health=mental_health,
            generational_health=generational_health,
            genetic_markers=genetic_markers,
            personality_traits=personality_traits,
            intelligence_factor=intelligence_factor,
            adaptability=adaptability,
            immunity_strength=immunity_strength,
            _packed_health=packed_health
        )
    
    @staticmethod
    def _decode_v1(buffer: io.BytesIO) -> CNAAttributes:
        """Decode version 1 (original) format for backward compatibility"""
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
        
        # Create attributes object with the old format values
        attributes = CNAAttributes(
            first_name=first_name,
            last_name=last_name,
            age_minutes=age_minutes,
            gender=gender,
            culture=culture,
            nation=nation,
            physical_health=physical_health,
            mental_health=mental_health,
            generational_health=generational_health,
            genetic_markers=genetic_markers,
            personality_traits=personality_traits,
            intelligence_factor=intelligence_factor,
            adaptability=adaptability,
            immunity_strength=immunity_strength
        )
        
        # Pack health values for consistency with new format
        attributes.pack_health_values()
        
        return attributes
    
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
