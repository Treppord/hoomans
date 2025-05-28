import json
import re
import logging
import traceback

logger = logging.getLogger("AIUniverseController")

class LocalModelInterface:
    """Interface for local LLM inference using llama-cpp-python"""
    
    def __init__(self, model_path="models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"):
        try:
            from llama_cpp import Llama
            
            # Load the model
            self.llm = Llama(
                model_path=model_path,
                n_ctx=9256,  # Smaller context window to save memory
                n_batch=64,  # Smaller batch size
                n_threads=8,  # Adjust based on your CPU
                verbose=False
            )
            
            logger.info(f"Successfully loaded local model from {model_path}")
            self.model_loaded = True
            
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            logger.error(traceback.format_exc())
            self.model_loaded = False
    
    def generate_response(self, prompt, system_prompt="", max_tokens=64):
        """Generate a response using the local model"""
        if not self.model_loaded:
            return {"action": "idle", "speech": ""}
        
        try:
            # Format the prompt for chat completion
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Generate completion
            output = self.llm.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=0.9,
                stop=["</s>", "user:", "User:", "system:", "System:"],
            )
            
            # Extract the response text
            response_text = output["choices"][0]["message"]["content"].strip()
            
            # Try to parse as JSON
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                # If not valid JSON, try to extract action and speech
                action_match = re.search(r'"action"\s*:\s*"([^"]+)"', response_text)
                speech_match = re.search(r'"speech"\s*:\s*"([^"]*)"', response_text)
                
                action = action_match.group(1) if action_match else "idle"
                speech = speech_match.group(1) if speech_match else ""
                
                return {"action": action, "speech": speech}
                
        except Exception as e:
            logger.error(f"Error generating response with local model: {e}")
            logger.error(traceback.format_exc())
            return {"action": "idle", "speech": ""}
