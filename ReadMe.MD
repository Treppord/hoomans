# Hoomans - 2D Survival Simulation Game

A retro-style 2D survival simulation game built with a custom Python game engine using Pygame. Experience life as a "hooman" in a procedurally generated world where you must manage your needs, interact with NPCs, and build structures to survive.

## 🎮 Game Overview

Hoomans is a top-down 2D survival game that combines classic retro aesthetics with modern gameplay mechanics. Players control a character in a tile-based world, managing hunger, thirst, and comfort while interacting with AI-driven NPCs and exploring a living, breathing environment.

## 🧬 CNA System - Computerized Neural Attributes

### Revolutionary Entity System

Hoomans features a groundbreaking **CNA (Computerized Neural Attributes)** system that brings NPCs to life with DNA-inspired characteristics:

- **Genetic-Style Attributes**: Each entity has unique genetic markers, personality traits, and inherited characteristics
- **Binary File Format**: Efficient .cna file format for storing complex entity data
- **Heredity System**: Generate child entities that inherit traits from parent NPCs
- **Cultural Identity**: Entities belong to different cultures (Red, Blue, Green, etc.) affecting their appearance and behavior
- **Persistent Memory**: NPCs remember their experiences and relationships across game sessions

### CNA Editor Suite

A complete standalone editor for creating and managing entities:

- **PyQt5 GUI Application**: Professional interface for entity creation and editing
- **Visual Entity Designer**: Real-time preview of entity attributes and appearance
- **Batch Generation**: Create multiple entities with realistic genetic variation
- **Parent-Child Relationships**: Generate offspring with inherited traits and mutations
- **Binary Hex Viewer**: Inspect the raw binary data of CNA files
- **Import/Export System**: Save and load entity collections

### CNA File Format Features

- **Compact Binary Storage**: Optimized bitfield packing for minimal file size
- **Version Compatibility**: Backward compatibility with legacy CNA formats
- **Cross-Platform**: Works seamlessly between the game and editor
- **Validation System**: Built-in data integrity checks and error handling

## 🤖 Advanced AI System

### AI Universe Controller

Hoomans features a sophisticated AI system that creates truly intelligent and autonomous NPCs:

- **Centralized AI Management**: Single controller manages all NPC decision-making
- **Multi-threaded Processing**: AI decisions processed in separate threads for smooth gameplay
- **State-Based Decision Making**: NPCs make decisions based on comprehensive world state
- **Memory-Driven Behavior**: NPCs remember locations, interactions, and experiences
- **Dynamic Response System**: Real-time chat responses and contextual interactions

### Local LLM Integration

- **Local Model Support**: Integration with llama-cpp-python for offline AI
- **Fallback AI System**: Rule-based AI ensures gameplay continues if LLM unavailable
- **Adaptive Prompting**: Dynamic prompt generation based on NPC state and needs
- **Context-Aware Responses**: NPCs respond intelligently to player messages and world events
- **Personality-Driven Dialogue**: CNA attributes influence conversation style and content

### Intelligent NPC Behaviors

- **Need-Based Decision Making**: NPCs prioritize actions based on hunger, thirst, and comfort
- **Exploration and Mapping**: NPCs actively explore and remember world locations
- **Social Interactions**: Complex relationship systems and memory of past conversations
- **Advice Following**: NPCs can understand and act on player suggestions
- **Emergency Responses**: Smart reactions to dangerous situations (e.g., escaping water)

### AI Technical Features

- **Agent State Management**: Comprehensive tracking of NPC internal states
- **World State Collection**: Efficient gathering of environmental information
- **Decision Validation**: AI decisions validated against game rules and physics
- **Batch Processing**: Multiple NPC decisions processed efficiently
- **Memory Optimization**: Smart caching and cleanup of AI memory systems

## 🛠️ Custom Game Engine Features

### Core Engine Architecture

- **Modular Design**: Clean separation between engine systems (physics, rendering, audio, UI)
- **Entity-Component System**: Flexible entity management with component-based architecture
- **Game State Management**: Seamless transitions between menu, gameplay, and pause states
- **Delta Time Support**: Frame-rate independent updates for smooth gameplay
- **CNA Integration**: Native support for loading and displaying CNA-based entities

### 2D Rendering & Graphics

- **Tile-Based World**: 16x16 pixel tiles for authentic retro feel
- **Sprite Animation System**: Multi-frame animations with idle and walking states
- **Camera System**: Smooth camera movement with zoom, pan, and follow capabilities
- **Layered Rendering**: Proper depth sorting for terrain, entities, and UI elements
- **Transparency Support**: Alpha blending for visual effects and overlays
- **Dynamic Entity Coloring**: Visual representation based on CNA cultural attributes

### World Generation & Management

- **Procedural Map Generation**: Wave Function Collapse-inspired biome generation
- **Realistic Biomes**: Ocean, forest, plains, mountains, desert, and more
- **Entity Tiles**: Interactive world objects like trees and houses
- **World Persistence**: Save/load world state with comprehensive caching system
- **Dynamic Weather**: Environmental effects and particle systems
- **Seed-Based Generation**: Reproducible worlds with deterministic generation

### Physics & Movement

- **Grid-Based Movement**: Precise tile-based positioning with smooth interpolation
- **Collision Detection**: Comprehensive collision system for walls, water, and structures
- **Pathfinding**: A\* pathfinding for NPCs with terrain cost consideration
- **Entity Interactions**: Complex interaction system between entities and world objects

### AI & NPC System

- **CNA-Driven Behavior**: AI decisions influenced by genetic attributes and personality
- **Advanced AI Controllers**: Multiple AI behaviors (wandering, following, seeking)
- **Need-Based Behavior**: NPCs manage hunger, thirst, and comfort autonomously
- **Memory System**: NPCs remember locations and past interactions
- **Social Interactions**: Chat system with context-aware responses
- **Exploration Behavior**: NPCs actively explore and map their environment
- **Cultural Behaviors**: Different cultures exhibit unique behavioral patterns

### Audio System

- **Multi-Channel Audio**: Separate volume controls for SFX and music
- **Spatial Audio**: Distance-based volume for immersive experience
- **Dynamic Sound Effects**: Context-sensitive audio (footsteps, drinking, eating)
- **Audio Asset Management**: Efficient loading and caching of sound files

### User Interface

- **Retro-Styled UI**: Pixel-perfect interface elements with transparency
- **Modular UI System**: Reusable components (buttons, panels, text inputs)
- **Interactive Menus**: Main menu, pause menu, and in-game interaction systems
- **Chat System**: Real-time communication with scrollable history
- **Inventory Management**: Drag-and-drop item system with visual feedback
- **Entity Information Panels**: Detailed CNA attribute display

### Input & Controls

- **Flexible Input Mapping**: Customizable key bindings
- **Multi-Input Support**: Keyboard and mouse with context-sensitive controls
- **Chat Mode**: Dedicated text input system with clipboard support
- **Camera Controls**: Mouse-based panning and zooming

### Data Management

- **Save System**: Comprehensive world and entity state persistence
- **Statistics Tracking**: Player stats with min/max constraints and observers
- **Configuration Management**: Settings persistence and runtime modification
- **Asset Pipeline**: Efficient loading and caching of game assets
- **CNA File Integration**: Seamless loading of entity data from .cna files

## 🎨 Retro Aesthetic Features

### Visual Style

- **16x16 Pixel Art**: Authentic retro tile-based graphics
- **Limited Color Palette**: Carefully chosen colors for nostalgic feel
- **Pixel-Perfect Rendering**: No anti-aliasing for crisp, clean pixels
- **Sprite Animations**: Classic frame-based character animations
- **Cultural Color Coding**: Entities display colors based on their CNA cultural attributes

### Audio Design

- **Retro Sound Effects**: 8-bit inspired audio for actions and interactions
- **Ambient Soundscapes**: Environmental audio that enhances immersion
- **Classic UI Sounds**: Satisfying click and confirmation sounds

### Typography

- **Pixel Fonts**: Custom bitmap fonts for authentic retro text rendering
- **Consistent Styling**: Unified visual language throughout the interface

## 🏗️ Current Game Features

### Survival Mechanics

- **Hunger System**: Eat food to maintain energy levels
- **Thirst System**: Find and drink water to stay hydrated
- **Comfort System**: Rest in houses to restore comfort levels
- **CNA-Influenced Needs**: Entity attributes affect survival requirements

### World Interaction

- **Resource Gathering**: Collect materials from the environment
- **Construction System**: Build houses and structures using schematics
- **Tool Usage**: Craft and use tools for various tasks

### NPC Interactions

- **Dynamic Conversations**: Chat with NPCs who remember past interactions
- **Social Relationships**: Build relationships with other characters
- **Collaborative Survival**: NPCs have their own needs and goals
- **Genetic Diversity**: Each NPC has unique CNA-based characteristics
- **Cultural Interactions**: Different cultures interact in unique ways

### Exploration

- **Procedural Worlds**: Each playthrough features a unique world
- **Biome Diversity**: Explore forests, deserts, mountains, and more
- **Hidden Secrets**: Discover special locations and resources
- **Persistent NPCs**: Entities remember their exploration and discoveries

## 🛠️ Development Tools

### CNA Editor Suite

- **Standalone Entity Editor**: Complete PyQt5 application for CNA management
- **Visual Attribute Editor**: Real-time editing of genetic and personality traits
- **Batch Entity Generation**: Create populations with realistic genetic diversity
- **Heredity Simulator**: Generate offspring with inherited and mutated traits
- **Binary Data Viewer**: Inspect and debug CNA file contents
- **Asset Integration**: Direct integration with game sprite systems

### Item Creator Tool

- **Visual Item Editor**: Create and modify game items with a GUI
- **Aseprite Integration**: Direct sprite editing workflow
- **Property Management**: Configure item behaviors and attributes
- **Asset Pipeline**: Automated icon generation and management

### Debug Features

- **Map Visualization**: Debug overlays for biome and height maps
- **Performance Monitoring**: Frame rate and system performance tracking
- **Console Commands**: Runtime debugging and testing commands
- **CNA Debug Tools**: Inspect entity attributes and behaviors in real-time

## 🚀 Technical Specifications

### Engine Requirements

- **Python 3.7+**: Modern Python with type hints support
- **Pygame 2.0+**: Hardware-accelerated 2D graphics
- **PyQt5**: Professional GUI framework for CNA editor
- **NumPy**: Efficient array operations for world generation
- **llama-cpp-python**: Optional local LLM support for advanced AI
- **Optional Dependencies**: Aseprite for asset creation

### Performance Features

- **Efficient Rendering**: Frustum culling and dirty rectangle optimization
- **Memory Management**: Smart caching and garbage collection
- **Scalable Architecture**: Supports worlds up to 256x256 tiles
- **Cross-Platform**: Runs on Windows, macOS, and Linux
- **Optimized CNA Storage**: Bitfield packing for minimal memory usage

### File Formats

- **CNA Files**: Custom binary format for entity data with version control
- **JSON Configuration**: Human-readable settings and data files
- **PNG Graphics**: Standard image format with transparency support
- **Custom Cache Format**: Optimized binary format for world persistence

### CNA Technical Details

- **Bitfield Optimization**: Health values packed into single bytes
- **Enum Compression**: Multiple enums stored in optimized bit patterns
- **Version Compatibility**: Automatic handling of legacy file formats
- **Data Validation**: Comprehensive error checking and recovery
- **Cross-Platform Binary**: Consistent format across all operating systems

### AI Technical Architecture

- **Modular AI Design**: Separate interfaces for different AI backends
- **State Management**: Comprehensive agent state tracking and persistence
- **Decision Pipeline**: Multi-stage decision validation and execution
- **Memory Systems**: Efficient storage and retrieval of NPC memories
- **Prompt Engineering**: Dynamic prompt generation for context-aware responses

## 🎯 Future Development

The engine is designed for extensibility and future enhancements:

- **Multiplayer Support**: Network architecture foundation in place
- **Mod Support**: Plugin system for community content
- **Advanced AI**: Machine learning integration for smarter NPCs
- **Enhanced Graphics**: Shader support and lighting effects
- **Mobile Platforms**: Touch-friendly interface adaptations
- **CNA Evolution**: Advanced genetic algorithms and trait inheritance
- **Community Sharing**: Online CNA entity marketplace

## 🎮 Getting Started

### Main Game

1. **Install Dependencies**: `pip install pygame numpy`
2. **Optional AI Setup**: `pip install llama-cpp-python` for local LLM support
3. **Run the Game**: `python game_engine.py`
4. **Create Items**: Use the built-in item creator tool
5. **Explore**: Generate new worlds with different seeds
6. **Survive**: Manage your needs and build your settlement

### CNA Editor

1. **Install PyQt5**: `pip install PyQt5`
2. **Launch Editor**: `python cna/main.py`
3. **Create Entities**: Design unique NPCs with custom attributes
4. **Generate Families**: Create parent-child relationships
5. **Export to Game**: Save .cna files for use in the main game

### Command Line Options

- `--seed <number>`: Start with a specific world seed
- `--fullscreen`: Launch in fullscreen mode
- `--skip-menu`: Skip main menu and start directly
- `--width <pixels>` / `--height <pixels>`: Set window dimensions

Experience the charm of retro gaming with modern conveniences in this lovingly crafted 2D survival simulation featuring revolutionary genetic-based NPCs!

## 🧬 CNA System Deep Dive

The Computerized Neural Attributes system represents a breakthrough in NPC design, bringing biological realism to digital entities:

### Genetic Architecture

- **10 Genetic Markers**: Simulated DNA-like data affecting behavior
- **5 Personality Traits**: Floating-point values defining character
- **Cultural Heritage**: 11 distinct cultures with unique characteristics
- **Nation Affiliations**: Geographic and political identity systems

### Inheritance Mechanics

- **Realistic Breeding**: Child entities inherit traits from both parents
- **Genetic Mutation**: Small random variations ensure diversity
- **Trait Blending**: Weighted averages with random variation
- **Cultural Mixing**: Children can inherit culture from either parent

### Visual Representation

- **Color-Coded Cultures**: Each culture has distinct visual appearance
- **Age-Based Brightness**: Younger entities appear brighter
- **Dynamic Coloring**: Real-time color calculation based on CNA data

## 🤖 AI System Deep Dive

The AI system in Hoomans represents a sophisticated approach to NPC intelligence:

### Decision Making Process

- **World State Analysis**: NPCs analyze their environment, needs, and memories
- **Priority-Based Actions**: Critical needs (thirst, hunger) override other behaviors
- **Context-Aware Responses**: NPCs understand and respond to player communication
- **Memory Integration**: Past experiences influence current decisions

### Local LLM Integration

- **Offline Intelligence**: No internet required for advanced AI behaviors
- **Fallback Systems**: Rule-based AI ensures gameplay continuity
- **Prompt Engineering**: Dynamic prompts based on NPC state and personality
- **Response Validation**: AI outputs validated against game rules

### Behavioral Complexity

- **Exploration Patterns**: NPCs map their world and remember important locations
- **Social Dynamics**: Complex relationship systems with other NPCs and players
- **Emergency Responses**: Smart reactions to dangerous or unusual situations
- **Cultural Behaviors**: AI decisions influenced by CNA cultural attributes

This innovative system creates a living, evolving world where every NPC has a unique genetic identity and behavioral profile powered by advanced AI!
