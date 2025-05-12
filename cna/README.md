# CNA - Computerized Neural Attributes

## Overview

CNA (Computerized Neural Attributes) is a custom binary format designed to efficiently store entity attributes for AI virtual worlds. Inspired by human DNA, it provides a compact way to represent various characteristics of virtual entities, including basic information, health metrics, and DNA-inspired attributes that influence behavior and capabilities.

## What is CNA?

CNA serves as a genetic blueprint for virtual entities in simulation environments. Each CNA file contains:

- **Basic Attributes**: Core information like name, age, gender, culture, and nation
- **Health Metrics**: Physical, mental, and generational health indicators
- **Extended DNA-inspired Attributes**: Genetic markers, personality traits, intelligence, adaptability, and immunity

The format is optimized for efficient storage and retrieval, making it suitable for large-scale simulations where many entities need to be processed quickly.

## File Format Specification

CNA files use a binary format with the following structure:

1. **File Signature**: `CNA1` (4 bytes) - Identifies the file as a CNA format
2. **Basic Attributes**:
   - First Name: Length (2 bytes) + UTF-8 encoded string
   - Last Name: Length (2 bytes) + UTF-8 encoded string
   - Age: Minutes (1 byte, range 0-60)
   - Gender: Enum value (1 byte)
   - Culture: Enum value (1 byte)
   - Nation: Enum value (1 byte)
   - Physical Health: Value (1 byte, range 0-5)
   - Generational Health: Value (1 byte, range 0-5)
   - Mental Health: Value (1 byte, range 0-5)
3. **Extended Attributes**:
   - Intelligence Factor: Float (4 bytes)
   - Adaptability: Float (4 bytes)
   - Immunity Strength: Float (4 bytes)
   - Genetic Markers: Count (1 byte) + Markers (2 bytes each)
   - Personality Traits: Count (1 byte) + Traits (4 bytes each, float)

## Components

### Core Classes

- **CNAAttributes**: Data class that holds all entity attributes
- **CNACodec**: Handles encoding/decoding between CNA objects and binary data
- **CNAGenerator**: Creates random entities and simulates genetic inheritance

### Enumerations

- **Gender**: MALE (0), FEMALE (1)
- **Culture**: RED (0), BLUE (1), GREEN (2), YELLOW (3), PURPLE (4), ORANGE (5), PINK (6), BROWN (7), GRAY (8), BLACK (9), WHITE (10)
- **Nation**: NL (0), PL (1), AL (2), FL (3), CL (4), SL (5), DL (6), VL (7), ML (8), GL (9), HL (10)

## Genetic Inheritance

CNA supports simulating genetic inheritance through the `generate_child` function:

- Children inherit attributes from both parents with natural variation
- Genetic markers have a 50% chance to come from either parent with a 10% mutation chance
- Personality traits are created through weighted averages of parent traits with random variation
- Health attributes are influenced by both parents with some randomness
- Last name is typically inherited from one parent

## CNA Editor Application

The included CNA Editor provides a GUI for working with CNA files:

- **Entity Editor**: Create and modify CNA entities
- **Generator**: Create random entities or child entities from parents
- **Binary Viewer**: Examine the raw binary representation of CNA data
- **Batch Operations**: Generate and save multiple entities at once

## Usage

### Running the Application

```bash
python main.py
```

### Programmatic Usage

```python
# Create a new entity
from cna_format import CNAAttributes, Gender, Culture, Nation
from cna_generator import CNAGenerator
from cna_codec import CNACodec

# Generate a random entity
entity = CNAGenerator.generate_random()

# Save to file
CNACodec.save_to_file(entity, "entity.cna")

# Load from file
loaded_entity = CNACodec.load_from_file("entity.cna")

# Create a child from two parents
parent1 = CNAGenerator.generate_random()
parent2 = CNAGenerator.generate_random()
child = CNAGenerator.generate_child(parent1, parent2)
```

## Applications

CNA can be used in:

- AI-driven virtual worlds and simulations
- Genetic algorithm research
- Game development for character attributes
- Educational tools demonstrating genetic inheritance
- Procedural generation of diverse populations

## Requirements

- Python 3.7 or higher
- PyQt5 (for the GUI application)
