"""
Speech constants module - centralizes all speech text used throughout the game
"""

class SpeechConstants:
    # Exploration speeches
    EXPLORING_SPEECHES = [
        # General exploration
        "Explore MODE!"
        
    ]
    
    # Water-related speeches
    WATER_SEEKING_SPEECHES = [
        # Urgent thirst
        "Searching WATER"
    ]
    
    WATER_FOUND_SPEECHES = [
        # Relief at finding water
        "Found WATER"
    ]
    
    WATER_DRINKING_SPEECHES = [
        # Relief at finding water
        "Drinking WATER"
    ]
    
    WATER_ESCAPE_SPEECHES = [
        # Panic about being in water
        "WATER ESCAPE"
    ]
    
    # Food-related speeches
    FOOD_SEEKING_SPEECHES = [
        # Hunger and food spotting
        "I see some food over there!"
    ]
    
    EATING_SPEECHES = [
        # Satisfaction from eating
        "I'll remember where I found this food."
    ]
    
    # Idle/observing speeches
    IDLE_SPEECHES = [
        # When standing still and observing
        "This is a good vantage point to plan my next move."
    ]
    
    # Weather-related speeches
    WEATHER_SPEECHES = {
        "sunny": [
            "What a beautiful sunny day!",
            "The sun feels warm on my skin.",
            "Perfect weather for exploring.",
            "I love days like this.",
            "The sunlight makes everything look more vibrant.",
            "This sunshine is lifting my spirits.",
            "A sunny day makes everything better.",
            "I should make the most of this good weather."
        ],
        "rainy": [
            "This rain is making everything wet.",
            "I should find shelter from this rain.",
            "The sound of raindrops is actually quite soothing.",
            "Rain makes the world smell different.",
            "I hope this rain stops soon.",
            "At least the rain will help plants grow.",
            "Everything looks different in the rain.",
            "I'm getting soaked out here!"
        ],
        "night": [
            "The night sky is beautiful.",
            "It's getting dark, I should be careful.",
            "The stars are coming out.",
            "Night brings different challenges.",
            "I can see better in the moonlight.",
            "The world is so different at night.",
            "I should find a safe place to rest soon.",
            "The darkness holds many secrets."
        ]
    }
    
    # Social speeches (when near other NPCs)
    GREETING_SPEECHES = [
        "Hello there!",
        "Nice to see another person around here.",
        "Greetings, fellow traveler!",
        "How are you doing today?",
        "It's good to see a friendly face.",
        "I hope your day is going well.",
        "Hello! Are you exploring too?",
        "Well met, friend!",
        "I don't see many people around these parts.",
        "It's safer to travel together sometimes.",
        "Have you discovered anything interesting?",
        "I'm glad our paths crossed.",
        "What brings you to this area?",
        "I've been walking alone for too long.",
        "Would you like to share what you've found?"
    ]
    
    # Danger/threat responses
    DANGER_SPEECHES = [
        "That looks dangerous!",
        "I should stay away from there.",
        "I don't like the look of that.",
        "Better safe than sorry.",
        "I'm not risking my life for that.",
        "That's a threat I'd rather avoid.",
        "I need to find a safer path.",
        "My instincts tell me to stay away.",
        "That's not worth the danger.",
        "I value my life too much to go there.",
        "I'll find another way around.",
        "That looks like trouble I don't need.",
        "I'm turning back, it's too risky.",
        "Sometimes courage means knowing when to avoid danger.",
        "I'll come back when I'm better prepared."
    ]
    
    # Discovery speeches (finding something interesting)
    DISCOVERY_SPEECHES = [
        "Look at that!",
        "I've never seen anything like this before!",
        "What an amazing discovery!",
        "This is fascinating!",
        "I should remember this place.",
        "This is worth noting in my memory.",
        "I didn't expect to find this here.",
        "What a remarkable sight!",
        "This discovery was worth the journey.",
        "I wonder what this means.",
        "This changes what I know about this area.",
        "I need to investigate this further.",
        "This is a significant find!",
        "I should tell others about this.",
        "This place is special, I can feel it."
    ]
    
    # Frustration speeches
    FRUSTRATION_SPEECHES = [
        "This isn't working.",
        "I'm getting nowhere.",
        "There must be a better way.",
        "This is more difficult than I thought.",
        "I'm starting to get frustrated.",
        "I need to try a different approach.",
        "Why is this so challenging?",
        "I thought this would be easier.",
        "I'm not giving up, but this is tough.",
        "I need to be more patient.",
        "This is testing my limits.",
        "I'll figure this out eventually.",
        "Sometimes the hardest paths lead to the best discoveries.",
        "I won't let this defeat me.",
        "One more try, I can do this."
    ]
    
    # Returning home speeches
    RETURNING_HOME_SPEECHES = [
        "Time to head back home.",
        "I've explored enough for now.",
        "Home is calling me.",
        "I should return to my base.",
        "I've gathered enough information for today.",
        "I miss the comfort of my home.",
        "I'll continue exploring another day.",
        "It's good to return home after an adventure.",
        "I need to organize what I've discovered.",
        "Home is where I can rest and recover.",
        "I've wandered far enough for today.",
        "The journey out is only half the adventure.",
        "I'll bring back what I've learned.",
        "My home base awaits my return.",
        "I look forward to the familiar comfort of home."
    ]
    
    # Memory-related speeches (remembering locations)
    MEMORY_SPEECHES = [
        "I remember this place.",
        "I've been here before.",
        "This location is familiar.",
        "I should mark this in my memory.",
        "I won't forget this spot.",
        "This is worth remembering for later.",
        "I'm creating a mental map of this area.",
        "I'll need to recall this location.",
        "My memory of this place is clear.",
        "I'm getting better at remembering landmarks.",
        "This will be an important reference point.",
        "I'm building a picture of this world in my mind.",
        "Each remembered location helps me navigate better.",
        "This place stands out in my memory.",
        "I'll use this memory to guide my future explorations."
    ]
    
    # Health-related speeches
    HEALTH_SPEECHES = {
        "good": [
            "I'm feeling strong and healthy.",
            "My body feels great today.",
            "I'm in peak condition.",
            "Nothing can slow me down when I feel this good.",
            "I'm ready for whatever challenges come my way.",
            "Being healthy makes everything easier.",
            "I feel like I could run for miles.",
            "My health has never been better."
        ],
        "injured": [
            "I need to be careful with this injury.",
            "I'm not at my best right now.",
            "This wound is slowing me down.",
            "I should rest and recover.",
            "I need to find something to heal this injury.",
            "I'll push through the pain for now.",
            "This injury is worse than I thought.",
            "I hope this heals quickly."
        ]
    }
    
    # Mood-related speeches
    MOOD_SPEECHES = {
        "happy": [
            "What a wonderful day!",
            "I'm in such a good mood right now.",
            "Life feels full of possibilities.",
            "I can't help but smile today.",
            "Everything seems brighter when I'm happy.",
            "This joy makes me want to explore more.",
            "My spirits are high today.",
            "Happiness makes the journey worthwhile."
        ],
        "sad": [
            "I'm feeling a bit down today.",
            "Sometimes the journey gets lonely.",
            "I wish I had someone to talk to.",
            "This sadness weighs on me.",
            "I need to find something to lift my spirits.",
            "Even in sadness, I must continue forward.",
            "This melancholy will pass eventually.",
            "I'll find joy again, I just need to keep going."
        ],
        "tired": [
            "I need to rest soon.",
            "My feet are getting tired.",
            "I've been walking for so long.",
            "A short break would do me good.",
            "I can't keep going at this pace.",
            "My energy is running low.",
            "I should find a safe place to rest.",
            "Even explorers need to sleep sometimes."
        ]
    }
    