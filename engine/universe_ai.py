import random
import time
import threading
import math
import queue
from entities.entity_brain import EntityBrain, Need, Trait

class UniverseAI:
    """Central AI that manages the game universe and entity interactions"""
    
    def __init__(self, max_agents=50):
        self.entities = []
        self.entity_brains = {}
        self.max_agents = max_agents
        self.running = False
        self.last_update_time = time.time()
        
        # Event system
        self.events = []
        self.global_state = {
            'time_of_day': 0.0,  # 0.0 to 1.0 (0 = midnight, 0.5 = noon)
            'weather': 'clear',   # clear, rain, storm
            'temperature': 0.5    # 0.0 (cold) to 1.0 (hot)
        }
        
        # Threading for AI processing
        self.ai_thread = None
        self.ai_queue = queue.Queue()
        self.ai_results = queue.Queue()
    
    def register_entity(self, entity):
        """Register an entity with the universe AI"""
        if len(self.entities) >= self.max_agents:
            print(f"Warning: Maximum number of agents ({self.max_agents}) reached")
            return False
            
        self.entities.append(entity)
        self.entity_brains[entity] = EntityBrain(entity)
        return True
    
    def unregister_entity(self, entity):
        """Unregister an entity from the universe AI"""
        if entity in self.entities:
            self.entities.remove(entity)
            
        if entity in self.entity_brains:
            del self.entity_brains[entity]
    
    def start(self):
        """Start the universe AI processing"""
        if self.running:
            return
            
        self.running = True
        self.last_update_time = time.time()
        
        # Start AI processing thread
        self.ai_thread = threading.Thread(target=self._ai_thread_func)
        self.ai_thread.daemon = True  # Thread will exit when main program exits
        self.ai_thread.start()
    
    def stop(self):
        """Stop the universe AI processing"""
        self.running = False
        if self.ai_thread:
            self.ai_thread.join(timeout=1.0)
            self.ai_thread = None
    
    def update(self):
        """Update the universe state"""
        current_time = time.time()
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Update global state
        self._update_global_state(delta_time)
        
        # Process entity updates in the main thread
        # (AI decisions are processed in a separate thread)
        for entity in self.entities:
            if entity in self.entity_brains:
                brain = self.entity_brains[entity]
                brain.update_needs(delta_time)
                
                # Queue entity for AI processing
                self.ai_queue.put(entity)
        
        # Process AI results
        self._process_ai_results()
        
        # Process interactions between entities
        self._process_entity_interactions()
        
        # Generate random events
        self._generate_events(delta_time)
    
    def _ai_thread_func(self):
        """Background thread for AI processing"""
        while self.running:
            try:
                # Get an entity from the queue
                entity = self.ai_queue.get(timeout=0.1)
                
                # Process AI for this entity
                if entity in self.entity_brains:
                    brain = self.entity_brains[entity]
                    brain.decide_action()
                # Put the result back
                self.ai_results.put(entity)
                
                # Mark task as done
                self.ai_queue.task_done()
            except queue.Empty:
                # No entities to process, sleep briefly
                time.sleep(0.01)
            except Exception as e:
                print(f"Error in AI thread: {e}")
    
    def _process_ai_results(self):
        """Process results from the AI thread"""
        try:
            while True:
                # Get entity from results queue (non-blocking)
                entity = self.ai_results.get_nowait()
                
                # No processing needed here, the entity's brain has already updated
                
                # Mark as done
                self.ai_results.task_done()
        except queue.Empty:
            # No more results to process
            pass
    
    def _update_global_state(self, delta_time):
        """Update the global state of the universe"""
        # Update time of day (full day cycle in 10 minutes of real time)
        day_cycle_duration = 600  # seconds
        self.global_state['time_of_day'] = (self.global_state['time_of_day'] + delta_time / day_cycle_duration) % 1.0
        
        # Update weather occasionally
        if random.random() < 0.001:  # 0.1% chance per update
            weather_options = ['clear', 'rain', 'storm']
            weights = [0.7, 0.2, 0.1]  # Clear weather is more common
            self.global_state['weather'] = random.choices(weather_options, weights=weights)[0]
            
            # Broadcast weather change to all entities
            self._broadcast_event(f"The weather has changed to {self.global_state['weather']}")
        
        # Update temperature based on time of day
        # Coldest at night (time = 0.0), warmest in afternoon (time = 0.6)
        target_temp = 0.3 + 0.5 * math.sin((self.global_state['time_of_day'] - 0.25) * 2 * math.pi)
        # Adjust for weather
        if self.global_state['weather'] == 'rain':
            target_temp -= 0.2
        elif self.global_state['weather'] == 'storm':
            target_temp -= 0.3
            
        # Smooth temperature changes
        self.global_state['temperature'] = self.global_state['temperature'] * 0.99 + target_temp * 0.01
    
    def _process_entity_interactions(self):
        """Process interactions between entities"""
        # Check for entities that are close to each other
        for i, entity1 in enumerate(self.entities):
            if not hasattr(entity1, 'grid_x') or not hasattr(entity1, 'grid_y'):
                continue
                
            for j, entity2 in enumerate(self.entities[i+1:], i+1):
                if not hasattr(entity2, 'grid_x') or not hasattr(entity2, 'grid_y'):
                    continue
                    
                # Calculate Manhattan distance
                distance = abs(entity1.grid_x - entity2.grid_x) + abs(entity1.grid_y - entity2.grid_y)
                
                # If entities are adjacent, they can interact
                if distance <= 1:
                    self._handle_entity_interaction(entity1, entity2)
    
    def _handle_entity_interaction(self, entity1, entity2):
        """Handle interaction between two entities"""
        # Get entity brains
        brain1 = self.entity_brains.get(entity1)
        brain2 = self.entity_brains.get(entity2)
        
        if not brain1 or not brain2:
            return
            
        # Calculate social compatibility based on traits
        compatibility = 0
        for trait in Trait:
            # Similar values for sociability and energy are good
            if trait in [Trait.SOCIABILITY, Trait.ENERGY]:
                similarity = 1 - abs(brain1.traits[trait] - brain2.traits[trait])
                compatibility += similarity * 0.2
            # Complementary values for other traits can be good
            else:
                complementary = 1 - abs(brain1.traits[trait] + brain2.traits[trait] - 1)
                compatibility += complementary * 0.1
        
        # Adjust for aggression - high aggression reduces compatibility
        compatibility -= (brain1.traits[Trait.AGGRESSION] + brain2.traits[Trait.AGGRESSION]) * 0.15
        
        # Clamp to range
        compatibility = max(0, min(1, compatibility))
        
        # Update relationships based on compatibility
        relationship_change = (compatibility - 0.5) * 0.1  # Small changes
        
        brain1.update_relationship(entity2, relationship_change)
        brain2.update_relationship(entity1, relationship_change)
        
        # Satisfy social needs
        brain1.needs[Need.SOCIAL] = min(1.0, brain1.needs[Need.SOCIAL] + 0.05)
        brain2.needs[Need.SOCIAL] = min(1.0, brain2.needs[Need.SOCIAL] + 0.05)
        
        # Generate interaction memory
        if relationship_change > 0:
            interaction = "had a pleasant interaction with"
        else:
            interaction = "had an awkward interaction with"
            
        brain1.add_memory(f"{interaction} {entity2.__class__.__name__}")
        brain2.add_memory(f"{interaction} {entity1.__class__.__name__}")
        
        # Visual feedback - create speech bubbles for player to see
        from engine.core import SimpleGameEngine
        if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
            ui = SimpleGameEngine.instance.ui
            
            # Only show bubbles occasionally
            if random.random() < 0.3:
                if relationship_change > 0:
                    emoji = random.choice(["😊", "👋", "🙂"])
                else:
                    emoji = random.choice(["😐", "🤔", "😕"])
                    
                ui.add_text_bubble(emoji, entity1, duration=1.5)
    
    def _generate_events(self, delta_time):
        """Generate random events in the world"""
        # Chance for random events increases with more entities
        event_chance = 0.001 * len(self.entities)
        
        if random.random() < event_chance:
            event_options = [
                "A cool breeze blows through the area.",
                "Birds can be heard singing in the distance.",
                "The ground trembles slightly for a moment.",
                "A strange smell wafts through the air.",
                "Clouds form interesting shapes overhead."
            ]
            
            # Weather-specific events
            if self.global_state['weather'] == 'rain':
                event_options.extend([
                    "Rain falls steadily from the sky.",
                    "A puddle forms on the ground.",
                    "The sound of raindrops is soothing."
                ])
            elif self.global_state['weather'] == 'storm':
                event_options.extend([
                    "Lightning flashes in the distance.",
                    "Thunder booms overhead.",
                    "The wind howls fiercely."
                ])
                
            # Time-specific events
            if self.global_state['time_of_day'] < 0.25:  # Night
                event_options.extend([
                    "The stars twinkle in the night sky.",
                    "An owl hoots somewhere nearby.",
                    "The moonlight casts eerie shadows."
                ])
            elif 0.25 <= self.global_state['time_of_day'] < 0.75:  # Day
                event_options.extend([
                    "The sun shines brightly overhead.",
                    "A butterfly flutters past.",
                    "The day is full of activity."
                ])
            else:  # Evening
                event_options.extend([
                    "The sun begins to set, painting the sky.",
                    "Long shadows stretch across the ground.",
                    "The air grows cooler as evening approaches."
                ])
                
            # Select and broadcast an event
            event = random.choice(event_options)
            self._broadcast_event(event)
    
    def _broadcast_event(self, event_text):
        """Broadcast an event to all entities"""
        # Add to event list
        self.events.append({
            'text': event_text,
            'time': time.time()
        })
        
        # Limit event history
        if len(self.events) > 10:
            self.events.pop(0)
            
        # Add to entity memories (only some entities will remember)
        for entity in self.entities:
            if entity in self.entity_brains:
                brain = self.entity_brains[entity]
                # Higher intelligence means more likely to notice events
                if random.random() < brain.traits[Trait.INTELLIGENCE]:
                    brain.add_memory(event_text)
        
        # Display event in UI
        from engine.core import SimpleGameEngine
        if hasattr(SimpleGameEngine, 'instance') and hasattr(SimpleGameEngine.instance, 'ui'):
            SimpleGameEngine.instance.ui.add_event_message(event_text)
