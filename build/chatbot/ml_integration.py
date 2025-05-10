# ml_integration.py
# Integration module to connect machine learning capabilities with the existing chatbot

import logging
import re
from .ml_engine import intent_classifier, classify_intent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chatbot.ml_integration")

# Define confidence thresholds
HIGH_CONFIDENCE = 0.8
MEDIUM_CONFIDENCE = 0.5

def extract_entities(text):
    """
    Extract important entities from user text
    
    Args:
        text (str): User message
        
    Returns:
        dict: Extracted entities
    """
    entities = {}
    
    # Extract city for weather queries
    weather_city_match = re.search(r'weather (?:in|at|for) ([\w\s]+)(?:\?)?', text, re.IGNORECASE)
    if weather_city_match:
        entities['city'] = weather_city_match.group(1).strip()
    
    # Extract name for set_name intent
    name_match = re.search(r'(?:my name is|I am|I\'m|call me) ([\w\s]+)', text, re.IGNORECASE)
    if name_match:
        entities['person_name'] = name_match.group(1).strip()
    
    # Extract favorite things
    favorite_match = re.search(r'(?:favorite|favourites) (color|colour|food|movie|film|book|animal|music|song) (?:is|are) ([\w\s]+)', text, re.IGNORECASE)
    if favorite_match:
        category = favorite_match.group(1).lower()
        if category == 'colour':  # Normalize spelling
            category = 'color'
        if category == 'film':
            category = 'movie'
        
        entities['favorite_category'] = category
        entities['favorite_item'] = favorite_match.group(2).strip()
    
    # Extract bot name for rename_bot intent
    rename_match = re.search(r'(?:call you|name you|your name) ([\w\s]+)', text, re.IGNORECASE)
    if rename_match:
        entities['bot_name'] = rename_match.group(1).strip()
    
    return entities

def get_ml_response(user_input, chatbot_instance=None):
    """
    Get a response based on machine learning intent classification
    
    Args:
        user_input (str): User message
        chatbot_instance: Instance of the ImprovedChat class or None
        
    Returns:
        dict: Response data with text and metadata
    """
    # Default response if classification fails
    default_response = {
        "text": None,  # None indicates fallback to pattern matching
        "confidence": 0,
        "intent": None,
        "entities": {}
    }
    
    if not user_input:
        return default_response
    
    # Try to classify intent
    prediction = classify_intent(user_input)
    
    # If error or low confidence, fallback to pattern matching
    if "error" in prediction or not prediction["intent"]:
        logger.debug(f"ML engine prediction failed or low confidence: {prediction}")
        return default_response
        
    # Extract entities from user input
    entities = extract_entities(user_input)
    
    # Record the intent and confidence
    intent = prediction["intent"]
    confidence = prediction["confidence"]
    
    logger.info(f"ML intent: {intent} (confidence: {confidence:.2f})")
    
    # Generate response based on intent
    response_text = None
    
    # Only handle intents with at least medium confidence
    if confidence >= MEDIUM_CONFIDENCE:
        if intent == "greeting":
            if confidence > HIGH_CONFIDENCE:
                response_text = "Hello there! How can I help you today?"
            else:
                response_text = "Hi! What can I do for you?"
                
        elif intent == "farewell":
            if confidence > HIGH_CONFIDENCE:
                response_text = "Goodbye! Have a wonderful day!"
            else:
                response_text = "See you later!"
                
        elif intent == "weather" and chatbot_instance:
            # For weather, use the entities to extract city if available
            city = entities.get('city', None)
            if city:
                # Let the existing weather system handle the request
                return {
                    "text": None,  # Let pattern matching handle it
                    "confidence": confidence,
                    "intent": intent,
                    "entities": entities,
                    "special_handling": "weather",
                    "params": {"city": city}
                }
            else:
                response_text = "I can check the weather for you. Which city are you interested in?"
                
        elif intent == "name":
            if chatbot_instance:
                response_text = f"My name is {chatbot_instance.bot_name}. How can I help you?"
            else:
                response_text = "I'm your friendly chatbot assistant!"
                
        elif intent == "set_name" and chatbot_instance:
            name = entities.get('person_name', None)
            if name:
                # Let the pattern matcher handle name storage
                return {
                    "text": None,
                    "confidence": confidence,
                    "intent": intent,
                    "entities": entities
                }
            else:
                response_text = "I'd be happy to call you by name. What is your name?"
                
        elif intent == "help":
            response_text = ("I can help you with several things:\n"
                           "- Chat with you about various topics\n"
                           "- Check the weather for different cities\n"
                           "- Remember your preferences and favorite things\n"
                           "- Change my name if you'd like to call me something else\n"
                           "What would you like to do?")
                           
        elif intent == "thanks":
            if confidence > HIGH_CONFIDENCE:
                response_text = "You're very welcome! Is there anything else I can help with?"
            else:
                response_text = "No problem! Let me know if you need anything else."
                
        elif intent == "get_favorite" and chatbot_instance:
            # For favorites, let pattern matching handle it
            return {
                "text": None,
                "confidence": confidence,
                "intent": intent,
                "entities": entities
            }
            
        elif intent == "set_favorite" and chatbot_instance:
            # For setting favorites, let pattern matching handle it
            return {
                "text": None,
                "confidence": confidence,
                "intent": intent,
                "entities": entities
            }
            
        elif intent == "rename_bot" and chatbot_instance:
            bot_name = entities.get('bot_name', None)
            if bot_name:
                # Let pattern matching handle the renaming
                return {
                    "text": None,
                    "confidence": confidence,
                    "intent": intent,
                    "entities": entities
                }
            else:
                response_text = "I'd be happy to change my name. What would you like to call me?"
    
    return {
        "text": response_text,
        "confidence": confidence,
        "intent": intent,
        "entities": entities
    }

def enhance_chatbot_response(user_input, original_response, chatbot_instance=None):
    """
    Enhance the chatbot's response using ML when appropriate
    
    Args:
        user_input (str): User message
        original_response (str): Response from pattern matching
        chatbot_instance: Instance of the ImprovedChat class or None
        
    Returns:
        str: Enhanced response
    """
    # Get ML-based response
    ml_response = get_ml_response(user_input, chatbot_instance)
    
    # If ML provides a definitive response, use it
    if ml_response["text"]:
        logger.info(f"Using ML response for intent: {ml_response['intent']}")
        return ml_response["text"]
    
    # Otherwise, use the original pattern-based response
    logger.debug("Using original pattern-based response")
    return original_response

# Function to train the model if needed
def ensure_model_trained():
    """
    Ensure the model is trained by checking if it can make predictions
    
    Returns:
        bool: Whether the model is ready
    """
    # Try making a test prediction
    test_prediction = classify_intent("hello")
    
    # If prediction works and returns an intent, model is ready
    if test_prediction.get("intent") is not None:
        logger.info("ML model is ready")
        return True
    
    # Otherwise, need to train the model
    from .ml_engine import create_sample_training_data, intent_classifier
    
    logger.info("ML model not ready, creating sample data and training...")
    create_sample_training_data()
    result = intent_classifier.train()
    
    if "error" in result:
        logger.error(f"Error training model: {result['error']}")
        return False
    
    logger.info(f"Model trained successfully. Accuracy: {result['accuracy']:.2f}")
    return True