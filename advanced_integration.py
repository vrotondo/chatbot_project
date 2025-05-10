# advanced_integration.py
# Example of how to integrate all advanced ML features

import logging
import datetime
import json
from typing import Dict, List, Tuple, Optional, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chatbot.advanced")

class AdvancedChatbot:
    """
    Advanced chatbot implementation with all ML features integrated
    """
    
    def __init__(self, user_id="default_user"):
        """Initialize the advanced chatbot with all components"""
        self.user_id = user_id
        self.conversation_history = []
        self.components_status = self._initialize_components()
        logger.info(f"Advanced chatbot initialized for user {user_id}")
    
    def _initialize_components(self) -> Dict[str, bool]:
        """Initialize all advanced components and track availability"""
        status = {
            "ml_engine": False,
            "transformer": False,
            "entity_extraction": False,
            "feedback_system": False
        }
        
        # Initialize core ML engine
        try:
            from chatbot.ml_engine import intent_classifier
            status["ml_engine"] = True
            logger.info("ML engine initialized successfully")
        except ImportError:
            logger.warning("ML engine not available - core functionality will be limited")
        
        # Initialize transformer engine
        try:
            from chatbot.transformers_engine import is_available
            status["transformer"] = is_available()
            if status["transformer"]:
                logger.info("Transformer engine initialized successfully")
            else:
                logger.warning("Transformer model not available - semantic understanding will be limited")
        except ImportError:
            logger.warning("Transformer engine not available - advanced understanding disabled")
        
        # Initialize entity extraction
        try:
            from chatbot.entity_extraction import extract_entities
            # Test with a simple example
            test_entities = extract_entities("Test message")
            status["entity_extraction"] = True
            logger.info("Entity extraction initialized successfully")
        except ImportError:
            logger.warning("Entity extraction not available - understanding context will be limited")
        
        # Initialize feedback system
        try:
            from chatbot.feedback_system import store_feedback
            status["feedback_system"] = True
            logger.info("Feedback system initialized successfully")
        except ImportError:
            logger.warning("Feedback system not available - learning from interactions disabled")
        
        return status
        
    def process_message(self, user_message: str) -> Dict[str, Any]:
        """
        Process a user message using all available advanced features
        
        Args:
            user_message (str): The user's message
            
        Returns:
            dict: Response data with text and metadata
        """
        # Record start time for performance monitoring
        start_time = datetime.datetime.now()
        
        # Initialize response data
        response_data = {
            "text": None,
            "intent": None,
            "confidence": 0,
            "entities": {},
            "sources": [],
            "processing_time": None
        }
        
        # Store user message in conversation history
        self.conversation_history.append({
            "user": user_message,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        try:
            # 1. Extract entities if available
            if self.components_status["entity_extraction"]:
                try:
                    from chatbot.entity_extraction import extract_entities
                    entities = extract_entities(user_message)
                    response_data["entities"] = entities
                    logger.debug(f"Extracted entities: {entities}")
                except Exception as e:
                    logger.error(f"Error extracting entities: {e}")
            
            # 2. Determine intent using available methods
            intent_confidence_threshold = 0.5
            transformer_threshold = 0.7
            intent = None
            confidence = 0
            
            # Try transformer-based understanding first if available
            if self.components_status["transformer"]:
                try:
                    from chatbot.transformers_engine import find_similar_intent
                    transformer_intent, transformer_score = find_similar_intent(user_message, threshold=transformer_threshold)
                    
                    if transformer_intent and transformer_score >= transformer_threshold:
                        intent = transformer_intent
                        confidence = transformer_score
                        response_data["sources"].append("transformer")
                        logger.debug(f"Transformer determined intent: {intent} (confidence: {confidence:.2f})")
                except Exception as e:
                    logger.error(f"Error using transformer understanding: {e}")
            
            # Fall back to traditional ML classification if needed
            if not intent and self.components_status["ml_engine"]:
                try:
                    from chatbot.ml_engine import classify_intent
                    ml_result = classify_intent(user_message)
                    
                    ml_intent = ml_result.get("intent")
                    ml_confidence = ml_result.get("confidence", 0)
                    
                    if ml_intent and ml_confidence >= intent_confidence_threshold:
                        intent = ml_intent
                        confidence = ml_confidence
                        response_data["sources"].append("ml_engine")
                        logger.debug(f"ML engine determined intent: {intent} (confidence: {confidence:.2f})")
                except Exception as e:
                    logger.error(f"Error using ML classification: {e}")
            
            # Store intent and confidence in response data
            response_data["intent"] = intent
            response_data["confidence"] = confidence
            
            # 3. Generate response based on intent and entities
            response_text = None
            
            if intent:
                # Use intent-specific logic to generate response
                response_text = self._generate_response_for_intent(
                    intent, 
                    user_message, 
                    response_data["entities"]
                )
            
            # 4. If no intent or response yet, fall back to pattern matching
            if not response_text:
                response_text = self._fallback_response(user_message)
                response_data["sources"].append("pattern_matching")
            
            # 5. Enhance with conversation context
            if len(self.conversation_history) > 1:
                response_text = self._enhance_with_context(response_text, user_message)
            
            # Store the final response text
            response_data["text"] = response_text
            
            # Add bot response to conversation history
            self.conversation_history.append({
                "bot": response_text,
                "timestamp": datetime.datetime.now().isoformat(),
                "intent": intent,
                "confidence": confidence
            })
            
            # Limit conversation history length
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            # Calculate processing time
            end_time = datetime.datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            response_data["processing_time"] = processing_time
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
            # Provide fallback response on error
            error_response = "I'm having some trouble processing that right now. Could you try rephrasing?"
            
            # Add error response to conversation history
            self.conversation_history.append({
                "bot": error_response,
                "timestamp": datetime.datetime.now().isoformat(),
                "error": str(e)
            })
            
            # Calculate processing time even for errors
            end_time = datetime.datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            return {
                "text": error_response,
                "error": str(e),
                "processing_time": processing_time
            }
    
    def _generate_response_for_intent(self, intent: str, message: str, entities: Dict[str, Any]) -> Optional[str]:
        """
        Generate a response for a specific intent
        
        Args:
            intent (str): The detected intent
            message (str): Original user message
            entities (dict): Extracted entities
            
        Returns:
            str: Response text or None if no appropriate response
        """
        # Intent-specific response logic
        if intent == "greeting":
            return self._handle_greeting_intent(entities)
        
        elif intent == "weather":
            return self._handle_weather_intent(entities)
        
        elif intent == "set_name":
            return self._handle_set_name_intent(entities)
        
        elif intent == "get_favorite":
            return self._handle_get_favorite_intent(entities)
        
        elif intent == "set_favorite":
            return self._handle_set_favorite_intent(entities)
        
        elif intent == "help":
            return self._handle_help_intent()
        
        elif intent == "thanks":
            return self._handle_thanks_intent()
        
        elif intent == "farewell":
            return self._handle_farewell_intent()
        
        # Add more intent handlers as needed
        
        # No specific handler for this intent
        return None
    
    def _fallback_response(self, message: str) -> str:
        """Generate a fallback response when no intent is detected"""
        # Use traditional pattern matching from the original chatbot
        try:
            from chatbot.chatbot import ImprovedChat, pairs, reflections, bot_name
            chatbot = ImprovedChat(pairs, reflections, bot_name)
            chatbot.set_user_id(self.user_id)
            
            response = chatbot.respond(message)
            return response
        except Exception as e:
            logger.error(f"Error using pattern matching fallback: {e}")
            return "I'm not sure I understand. Could you rephrase that?"
    
    def _enhance_with_context(self, response: str, message: str) -> str:
        """Enhance response with conversation context"""
        # Get recent conversation for context
        last_exchanges = self.conversation_history[-4:]  # Last 2 turns
        
        # Check if this is a follow-up question
        is_followup = self._detect_followup(message, last_exchanges)
        
        if is_followup:
            # Find the topic being discussed
            topic = self._extract_topic(last_exchanges)
            
            if topic and "I'm not sure" in response:
                # Reference the topic in the response
                context_prefix = f"Regarding {topic}, "
                return context_prefix + response
        
        return response
    
    def _detect_followup(self, message: str, recent_exchanges: List[Dict[str, Any]]) -> bool:
        """Detect if the current message is a follow-up to previous conversation"""
        # Simple heuristic: short questions are often follow-ups
        if len(message.split()) <= 3 and "?" in message:
            return True
        
        # Check for follow-up indicators
        followup_phrases = ["what about", "how about", "and", "also", "then", "what else"]
        for phrase in followup_phrases:
            if phrase in message.lower():
                return True
        
        # Use transformer similarity if available
        if self.components_status["transformer"] and len(recent_exchanges) >= 2:
            try:
                from chatbot.transformers_engine import calculate_similarity
                
                # Extract the previous user message
                previous_user_msg = None
                for exchange in reversed(recent_exchanges):
                    if "user" in exchange:
                        previous_user_msg = exchange["user"]
                        break
                
                if previous_user_msg:
                    # Compare current message to previous message
                    similarity = calculate_similarity(message, previous_user_msg)
                    if similarity > 0.7:  # High similarity threshold
                        return True
            except Exception as e:
                logger.error(f"Error detecting follow-up with transformers: {e}")
        
        return False
    
    def _extract_topic(self, recent_exchanges: List[Dict[str, Any]]) -> Optional[str]:
        """Extract the main topic being discussed in recent exchanges"""
        # Combine recent messages
        combined_text = ""
        for exchange in recent_exchanges:
            if "user" in exchange:
                combined_text += exchange["user"] + " "
            if "bot" in exchange:
                combined_text += exchange["bot"] + " "
        
        # Use entity extraction if available
        if self.components_status["entity_extraction"]:
            try:
                from chatbot.entity_extraction import extract_entities
                entities = extract_entities(combined_text)
                
                # Location is often a topic
                if "location" in entities:
                    return entities["location"]
                
                # Use other entity types as topics
                for entity_type in ["person", "organization", "date", "time"]:
                    if entity_type in entities:
                        return entities[entity_type]
            except Exception as e:
                logger.error(f"Error extracting topic from entities: {e}")
        
        # Simple fallback: find the most common noun
        words = combined_text.lower().split()
        # This is a very simplified approach; in a real system, use POS tagging
        return max(set(words), key=words.count) if words else None
    
    def record_feedback(self, message: str, response: str, quality: str) -> bool:
        """
        Record user feedback about a response
        
        Args:
            message (str): The user's original message
            response (str): The bot's response
            quality (str): Feedback quality ('good', 'bad', or 'neutral')
            
        Returns:
            bool: Success status
        """
        if not self.components_status["feedback_system"]:
            logger.warning("Feedback system not available")
            return False
        
        try:
            from chatbot.feedback_system import store_feedback
            
            # Get the intent if available
            intent = None
            for exchange in reversed(self.conversation_history):
                if "bot" in exchange and exchange.get("bot") == response:
                    intent = exchange.get("intent")
                    break
            
            # Store the feedback
            success = store_feedback(
                user_input=message,
                response=response,
                quality=quality,
                intent=intent,
                user_id=self.user_id
            )
            
            return success
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            return False
    
    # Intent-specific handlers
    
    def _handle_greeting_intent(self, entities: Dict[str, Any]) -> str:
        """Handle greeting intent"""
        from chatbot.chatbot import bot_name
        
        # Check for time of day
        current_hour = datetime.datetime.now().hour
        time_greeting = ""
        
        if 5 <= current_hour < 12:
            time_greeting = "Good morning! "
        elif 12 <= current_hour < 18:
            time_greeting = "Good afternoon! "
        elif 18 <= current_hour < 22:
            time_greeting = "Good evening! "
        
        # Check if we know the user's name
        from chatbot.chatbot import get_user_info
        user_name = get_user_info(self.user_id, "name")
        
        if user_name:
            return f"{time_greeting}Hello, {user_name}! How can I help you today?"
        else:
            return f"{time_greeting}Hello there! I'm {bot_name}. How can I help you today?"
    
    def _handle_weather_intent(self, entities: Dict[str, Any]) -> str:
        """Handle weather intent"""
        # Extract location from entities
        location = entities.get("location") or entities.get("city")
        
        if not location:
            return "I'd be happy to check the weather for you. Which city are you interested in?"
        
        # Use the weather function from the original chatbot
        from chatbot.chatbot import get_weather
        return get_weather(location)
    
    def _handle_set_name_intent(self, entities: Dict[str, Any]) -> str:
        """Handle intent to set user's name"""
        # Extract name from entities
        name = entities.get("person_name")
        
        if not name:
            return "I'd like to call you by name. What should I call you?"
        
        # Store the name
        from chatbot.chatbot import store_user_info
        success = store_user_info(self.user_id, "name", name)
        
        if success:
            return f"Nice to meet you, {name}! I'll remember your name."
        else:
            return f"Hello {name}! I'm having trouble remembering names right now, but it's nice to meet you."
    
    def _handle_get_favorite_intent(self, entities: Dict[str, Any]) -> str:
        """Handle intent to get user's favorite thing"""
        # Look for category in entities (food, color, etc.)
        category = None
        
        for key, value in entities.items():
            if key.startswith("favorite_"):
                category = key.replace("favorite_", "")
                break
        
        if not category:
            return "I'm not sure which favorite thing you're asking about. Could you specify?"
        
        # Retrieve the favorite thing
        from chatbot.chatbot import get_user_info
        favorite = get_user_info(self.user_id, f"favorite_{category}")
        
        if favorite:
            return f"Your favorite {category} is {favorite}!"
        else:
            return f"I don't know your favorite {category} yet. What is it?"
    
    def _handle_set_favorite_intent(self, entities: Dict[str, Any]) -> str:
        """Handle intent to set user's favorite thing"""
        # Extract favorite category and value from entities
        category = None
        value = None
        
        for key, val in entities.items():
            if key.startswith("favorite_"):
                category = key.replace("favorite_", "")
                value = val
                break
        
        if not category or not value:
            return "I'm not sure what favorite thing you're telling me about. Could you be more specific?"
        
        # Store the favorite thing
        from chatbot.chatbot import store_user_info
        success = store_user_info(self.user_id, f"favorite_{category}", value)
        
        if success:
            return f"I'll remember that your favorite {category} is {value}!"
        else:
            return f"I'm having trouble remembering preferences right now, but it's nice to know your favorite {category} is {value}."
    
    def _handle_help_intent(self) -> str:
        """Handle help intent"""
        from chatbot.chatbot import bot_name
        
        # Create custom help text based on available components
        help_text = f"I'm {bot_name}, your chatbot assistant. Here's what I can do for you:\n\n"
        
        help_text += "- Chat with you about various topics\n"
        help_text += "- Remember your name and preferences\n"
        
        if self.components_status["entity_extraction"]:
            help_text += "- Understand specific details like locations, dates, and names\n"
        
        if self.components_status["ml_engine"]:
            help_text += "- Learn from our conversations to improve over time\n"
        
        help_text += "- Check the weather for different locations\n"
        help_text += "- Answer questions about myself\n\n"
        
        help_text += "What would you like to talk about?"
        
        return help_text
    
    def _handle_thanks_intent(self) -> str:
        """Handle thanks intent"""
        responses = [
            "You're welcome! Is there anything else I can help with?",
            "My pleasure! Let me know if you need anything else.",
            "Glad I could help! What else would you like to know?",
            "No problem at all! Anything else on your mind?",
            "Happy to be of assistance! What can I help with next?"
        ]
        import random
        return random.choice(responses)
    
    def _handle_farewell_intent(self) -> str:
        """Handle farewell intent"""
        from chatbot.chatbot import bot_name
        
        responses = [
            f"Goodbye! Feel free to chat with {bot_name} anytime!",
            "See you later! Have a great day!",
            "Take care! Come back soon!",
            "Bye for now! It was nice chatting with you!",
            "Until next time! Have a wonderful day!"
        ]
        import random
        return random.choice(responses)

# Example usage
if __name__ == "__main__":
    import json
    
    print("Initializing Advanced Chatbot...")
    chatbot = AdvancedChatbot()
    
    print("\nComponent Status:")
    for component, status in chatbot.components_status.items():
        status_text = "✓ Available" if status else "✗ Not available"
        print(f"  - {component}: {status_text}")
    
    print("\nSimple conversation test:")
    
    test_messages = [
        "Hello there",
        "My name is John",
        "What's the weather like in New York?",
        "Tell me about yourself",
        "My favorite color is blue",
        "What's my favorite color?",
        "Thank you for your help",
        "Goodbye"
    ]
    
    for message in test_messages:
        print(f"\nUser: {message}")
        response = chatbot.process_message(message)
        print(f"Bot: {response['text']}")
        print(f"Intent: {response['intent']} (confidence: {response['confidence']:.2f})")
        if response['entities']:
            print(f"Entities: {json.dumps(response['entities'], indent=2)}")
        print(f"Processing time: {response['processing_time']:.3f} seconds")