"""
CNA Generator for creating random CNA entities
"""

import random
import string
from typing import List, Optional
from cna_format import CNAAttributes, Gender, Culture, Nation

class CNAGenerator:
    """Generator for random CNA entities"""
    
    FIRST_NAMES = [
        "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", 
        "Quinn", "Skyler", "Dakota", "Reese", "Emerson", "Finley", "Rowan",
        "Sage", "Kai", "River", "Phoenix", "Remy", "Blair"
    ]
    
    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
        "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"
    ]
    
    @staticmethod
    def generate_random() -> CNAAttributes:
        """Generate a random CNA entity"""
        # Basic attributes
        first_name = random.choice(CNAGenerator.FIRST_NAMES)
        last_name = random.choice(CNAGenerator.LAST_NAMES)
        age_minutes = random.randint(0, 60)
        gender = random.choice(list(Gender))
        culture = random.choice(list(Culture))
        nation = random.choice(list(Nation))
        physical_health = random.randint(0, 5)
        generational_health = random.randint(0, 5)
        mental_health = random.randint(0, 5)
        
        # Extended attributes
        genetic_markers = [random.randint(0, 1023) for _ in range(10)]
        personality_traits = [random.uniform(0.0, 1.0) for _ in range(5)]
        intelligence_factor = random.uniform(0.5, 1.5)
        adaptability = random.uniform(0.5, 1.5)
        immunity_strength = random.uniform(0.5, 1.5)
        
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
    def generate_batch(count: int) -> List[CNAAttributes]:
        """Generate multiple random CNA entities"""
        return [CNAGenerator.generate_random() for _ in range(count)]
    
    @staticmethod
    def generate_child(parent1: CNAAttributes, parent2: CNAAttributes) -> CNAAttributes:
        """Generate a child entity from two parents"""
        # Inherit last name from parent1
        last_name = parent1.last_name
        
        # Generate a random first name
        first_name = random.choice(CNAGenerator.FIRST_NAMES)
        
        # Child starts at age 0
        age_minutes = 0
        
        # Randomly inherit gender
        gender = random.choice(list(Gender))
        
        # Inherit culture and nation (could be randomized for mixed parents)
        culture = parent1.culture if random.random() < 0.5 else parent2.culture
        nation = parent1.nation if random.random() < 0.5 else parent2.nation
        
        # Health attributes are influenced by parents
        # Base value is average of parents with some randomness
        physical_base = (parent1.physical_health + parent2.physical_health) / 2
        physical_health = max(0, min(5, int(physical_base + random.uniform(-1, 1))))
        
        generational_base = (parent1.generational_health + parent2.generational_health) / 2
        generational_health = max(0, min(5, int(generational_base + random.uniform(-1, 1))))
        
        mental_base = (parent1.mental_health + parent2.mental_health) / 2
        mental_health = max(0, min(5, int(mental_base + random.uniform(-1, 1))))
        
        # Extended attributes - mix from parents with some mutation
        genetic_markers = []
        for i in range(min(len(parent1.genetic_markers), len(parent2.genetic_markers))):
            # 50% chance to inherit from either parent, with small mutation chance
            marker = parent1.genetic_markers[i] if random.random() < 0.5 else parent2.genetic_markers[i]
            if random.random() < 0.1:  # 10% mutation chance
                marker = (marker + random.randint(-50, 50)) % 1024
            genetic_markers.append(marker)
        
        # Personality traits - mix from parents with variation
        personality_traits = []
        for i in range(min(len(parent1.personality_traits), len(parent2.personality_traits))):
            # Weighted average with random weight
            weight = random.random()
            trait = weight * parent1.personality_traits[i] + (1-weight) * parent2.personality_traits[i]
            # Add some randomness
            trait = max(0.0, min(1.0, trait + random.uniform(-0.1, 0.1)))
            personality_traits.append(trait)
        
        # Other factors - weighted average with random weight and variation
        intelligence_weight = random.random()
        intelligence_factor = (
            intelligence_weight * parent1.intelligence_factor + 
            (1-intelligence_weight) * parent2.intelligence_factor
        )
        intelligence_factor = max(0.5, min(1.5, intelligence_factor + random.uniform(-0.1, 0.1)))
        
        adaptability_weight = random.random()
        adaptability = (
            adaptability_weight * parent1.adaptability + 
            (1-adaptability_weight) * parent2.adaptability
        )
        adaptability = max(0.5, min(1.5, adaptability + random.uniform(-0.1, 0.1)))
        
        immunity_weight = random.random()
        immunity_strength = (
            immunity_weight * parent1.immunity_strength + 
            (1-immunity_weight) * parent2.immunity_strength
        )
        immunity_strength = max(0.5, min(1.5, immunity_strength + random.uniform(-0.1, 0.1)))
        
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
