import random
from typing import Dict, Optional

def create_adaptive_system_prompt(has_critical_thirst, has_critical_hunger, actions):
    """Create a concise system prompt based on agent's needs"""
    
    # Start with available actions
    action_list = ", ".join(actions.keys())
    base_prompt = f"You control an NPC in a game. Respond with JSON: {{\"action\": \"[action]\", \"speech\": \"[optional speech]\", \"reason\": \"[brief explanation]\"}}. Available actions: {action_list}."
    
    # Add specific guidance based on critical needs
    if has_critical_thirst and has_critical_hunger:
        base_prompt += " NPC is CRITICALLY THIRSTY AND HUNGRY. Prioritize finding water first. Use fast movement actions. Speech should express URGENT need for water."
    elif has_critical_thirst:
        base_prompt += " NPC is CRITICALLY THIRSTY. Prioritize finding water. Use fast movement actions. Speech should express URGENT need for water."
    elif has_critical_hunger:
        base_prompt += " NPC is CRITICALLY HUNGRY. Prioritize finding food. Use fast movement actions. Speech should express URGENT need for food."
    else:
        base_prompt += " NPC is fine. Focus on exploration and personality. Use regular movement actions. Never mention thirst/hunger/water/food."
    
    # Add guidance for player advice
    base_prompt += " If player gives advice, consider following it, especially if it helps with critical needs. Include in your reason if you're following advice."
    
    return base_prompt

def generate_player_advice_section(state):
    """Generate the player advice section for the prompt"""
    if "player_advice" not in state:
        return ""
        
    advice = state["player_advice"]
    advice_type = advice["type"]
    
    if advice_type == "direction":
        return f"""
PLAYER ADVICE:
- The player told you there is {advice['what']} about {advice['distance']} tiles to the {advice['direction']} of you.
- You can choose to follow this advice if you believe it will help you.
- If you want to follow this advice, you should move in the {advice['direction']} direction.
- Include in your reason if you're following the player's advice.
"""
    elif advice_type == "location":
        return f"""
PLAYER ADVICE:
- The player told you there is {advice['what']} near the {advice['landmark']}.
- You can choose to follow this advice if you believe it will help you.
- Include in your reason if you're following the player's advice.
"""
    return ""

def create_attribute_aware_prompt(agent, player_message, attribute_query=None):
    """Create a prompt that includes CNA attributes for more accurate responses"""
    if not hasattr(agent, 'cna_data') or not agent.cna_data:
        return f"Player: {player_message}\n\nRespond as an NPC in a game. Keep it short and natural."
    
    cna = agent.cna_data
    name = cna.first_name
    
    # Build a character profile based on CNA attributes
    profile = f"You are {name}, an NPC with the following attributes:\n"
    
    # Add mental health if available
    if hasattr(cna, 'mental_health'):
        profile += f"- Mental health: {cna.mental_health}/5 "
        if cna.mental_health <= 1:
            profile += "(poor, struggling mentally)\n"
        elif cna.mental_health <= 3:
            profile += "(average mental state)\n"
        else:
            profile += "(excellent mental health)\n"
    
    # Add physical health if available
    if hasattr(cna, 'physical_health'):
        profile += f"- Physical health: {cna.physical_health}/5 "
        if cna.physical_health <= 1:
            profile += "(poor, physically weak)\n"
        elif cna.physical_health <= 3:
            profile += "(average physical condition)\n"
        else:
            profile += "(excellent physical condition)\n"
    
    # Add intelligence if available
    if hasattr(cna, 'intelligence_factor'):
        profile += f"- Intelligence: {cna.intelligence_factor:.1f} "
        if cna.intelligence_factor < 0.8:
            profile += "(below average)\n"
        elif cna.intelligence_factor < 1.2:
            profile += "(average)\n"
        else:
            profile += "(above average)\n"
    
    # Add culture and nation
    profile += f"- Culture: {cna.culture.name}\n"
    profile += f"- Nation: {cna.nation.name}\n"
    
    # Add personality traits if available - fix for float values
    if hasattr(cna, 'personality_traits') and cna.personality_traits:
        # Convert float values to strings with descriptive labels
        if len(cna.personality_traits) > 0 and isinstance(cna.personality_traits[0], float):
            # Assuming the traits follow the Big Five model
            trait_names = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]
            trait_descriptions = []
            
            for i, trait_value in enumerate(cna.personality_traits):
                if i < len(trait_names):
                    trait_name = trait_names[i]
                    if trait_value > 0.7:
                        trait_descriptions.append(f"High {trait_name}")
                    elif trait_value < 0.3:
                        trait_descriptions.append(f"Low {trait_name}")
                    else:
                        trait_descriptions.append(f"Moderate {trait_name}")
            
            profile += f"- Personality traits: {', '.join(trait_descriptions)}\n"
        else:
            # If they're already strings, join them directly
            profile += f"- Personality traits: {', '.join(str(trait) for trait in cna.personality_traits)}\n"
    
    # Add current needs
    if hasattr(agent, 'thirst'):
        profile += f"- Current thirst: {agent.thirst}/10 "
        if agent.thirst <= 2:
            profile += "(very thirsty, this is a priority)\n"
        elif agent.thirst <= 5:
            profile += "(somewhat thirsty)\n"
        else:
            profile += "(not thirsty)\n"
    
    if hasattr(agent, 'hunger'):
        profile += f"- Current hunger: {agent.hunger}/10 "
        if agent.hunger <= 2:
            profile += "(very hungry, this is a priority)\n"
        elif agent.hunger <= 5:
            profile += "(somewhat hungry)\n"
        else:
            profile += "(not hungry)\n"
    
    # Add specific instructions based on the attribute being queried
    query_instructions = ""
    if attribute_query:
        if attribute_query == "mental_health":
            query_instructions = f"\nIMPORTANT: The player is asking about your mental health. Your mental health is {cna.mental_health}/5. Your response MUST accurately reflect this level of mental well-being. DO NOT say you're just a game character or that you're here to help on a journey."
        elif attribute_query == "physical_health":
            query_instructions = f"\nIMPORTANT: The player is asking about your physical health. Your physical health is {cna.physical_health}/5. Your response MUST accurately reflect this level of physical condition. DO NOT say you're just a game character or that you're here to help on a journey."
        elif attribute_query == "intelligence":
            query_instructions = f"\nIMPORTANT: The player is asking about your intelligence. Your intelligence factor is {cna.intelligence_factor:.1f}. Your response MUST accurately reflect this level of intelligence. DO NOT say you're just a game character or that you're here to help on a journey."
        elif attribute_query == "personality":
            query_instructions = f"\nIMPORTANT: The player is asking about your personality. Describe your personality based on your traits and background. DO NOT say you're just a game character or that you're here to help on a journey."
        elif attribute_query == "general_feeling":
            query_instructions = f"\nIMPORTANT: The player is asking how you're feeling. Consider your mental health ({cna.mental_health}/5), physical health ({cna.physical_health}/5), and current needs in your response. DO NOT say you're just a game character or that you're here to help on a journey."
            
    # Complete the prompt with stronger instructions
    prompt = f"{profile}{query_instructions}\n\nPlayer: {player_message}\n\nIMPORTANT INSTRUCTIONS:\n1. Respond as {name} in a way that accurately reflects your attributes and current state.\n2. Keep your response natural, concise, and in character.\n3. DO NOT prefix your response with your name.\n4. DO NOT say you're just a game character.\n5. DO NOT say you're here to help on a journey or adventure.\n6. DO NOT break the fourth wall or reference that you're in a game.\n7. If asked about your mental health, physical health, or intelligence, your response MUST reflect your actual attribute values."
    
    return prompt

def extract_npc_response(response_text, agent):
    """Extract and clean up the NPC's response from the model output"""
    if not response_text:
        return "I'm not sure what to say."
    
    # Remove any name prefix (e.g., "Dakota: ")
    if ":" in response_text and hasattr(agent, 'cna_data') and agent.cna_data:
        name = agent.cna_data.first_name
        if response_text.split(":")[0].strip() == name:
            response_text = response_text.split(":", 1)[1].strip()
    
    # Remove any JSON-like formatting that might have been generated
    response_text = response_text.replace('{"speech": "', '').replace('"}', '')
    response_text = response_text.replace('"', '')
    
    # Remove any references to being a game character or helping on a journey
    lower_text = response_text.lower()
    if "game character" in lower_text or "npc" in lower_text or "ai" in lower_text:
        return generate_fallback_response(agent)
    
    if "journey" in lower_text or "adventure" in lower_text or "quest" in lower_text:
        if "help you" in lower_text or "assist you" in lower_text:
            return generate_fallback_response(agent)
    
    return response_text

def generate_fallback_response(agent):
    """Generate a fallback response based on agent attributes"""
    if not hasattr(agent, 'cna_data') or not agent.cna_data:
        return "I'm not sure what to say about that."
    
    cna = agent.cna_data
    
    # Check if agent is thirsty
    if hasattr(agent, 'thirst') and agent.thirst <= 2:
        return "I'm too thirsty to think clearly right now. I need to find water."
    
    # Generate responses based on mental health
    if hasattr(cna, 'mental_health'):
        if cna.mental_health <= 1:
            return "Sorry, I'm not in a good place mentally right now. It's hard to focus."
        elif cna.mental_health <= 3:
            return "I'm doing alright, I suppose. What were we talking about?"
        else:
            return "I'm feeling quite good today! What's on your mind?"
    
    # Default fallback
    return f"That's an interesting question. I'm from {cna.culture.name} culture, we have different perspectives on things."