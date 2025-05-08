# CNA Editor - Computerized Neural Attributes

CNA Editor is a tool for creating, editing, and generating CNA (Computerized Neural Attributes) files. CNA is a custom binary format designed to efficiently store entity attributes for AI virtual worlds, inspired by human DNA.

## Features

- Create and edit CNA entities with a user-friendly GUI
- Generate random entities with realistic attributes
- Create child entities by combining attributes from parent entities
- View the binary representation of CNA files
- Batch generate and save multiple entities

## CNA Format

The CNA format is a binary file format that efficiently stores the following attributes:

### Basic Attributes

- Name (First and Last name)
- Age (0-60 minutes in virtual time)
- Gender (Male or Female)
- Culture (Red or Blue)
- Nation (NL or PL)
- Physical Health (0-5 scale)
- Generational Health (0-5 scale)
- Mental Health (0-5 scale)

### Extended Attributes

- Genetic Markers (Simulated genetic information)
- Personality Traits (Behavioral tendencies)
- Intelligence Factor (Learning capacity)
- Adaptability (Environmental adaptation capability)
- Immunity Strength (Resistance to negative influences)

## Installation

1. Clone this repository:

```bash
git clone https://github.com/yourusername/cna-editor.git
cd cna-editor
```

2. Run the application:

```bash
python main.py
```

## Requirements

- Python 3.7 or higher
- Tkinter (usually included with Python)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

````

## 7. Let's create a requirements.txt file

```text:requirements.txt
# No external dependencies required beyond standard library
````

## Summary

I've created a complete application for working with the CNA (Computerized Neural Attributes) file format. Here's what each component does:

1. **cna_format.py**: Defines the data structure for CNA attributes, including basic information like name, age, gender, and health metrics, as well as extended DNA-inspired attributes.

2. **cna_codec.py**: Provides encoding and decoding functionality to convert between CNA objects and binary data, optimizing storage efficiency.

3. **cna_generator.py**: Generates random CNA entities and can create child entities by combining attributes from parent entities.

4. **cna_gui.py**: A full-featured GUI application with:

   - An editor for viewing and modifying CNA attributes
   - A generator for creating random entities and child entities
   - A binary viewer for examining the raw CNA data
   - File operations for saving and loading CNA files

5. **main.py**: The entry point for running the application.

The CNA format efficiently stores entity data in a binary format, making it suitable for use in AI virtual worlds where performance is important. The application provides a user-friendly interface for working with this data.

To run the application, execute:

```bash
python main.py
```
