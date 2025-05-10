# Conversation Memory Implementation Guide

This guide explains how to enhance Wicked with conversation memory to make responses more natural and context-aware.

## Understanding the Implementation

The conversation memory system consists of three main components:

1. **Conversation History Storage**: Records all user inputs and bot responses
2. **Context Utilities**: Functions to analyze and use conversation history
3. **Response Enhancement**: Methods to make responses more contextually relevant

## How to Implement

### Step 1: Add Conversation History to the Chatbot Class

Add the following initialization in the `__init__` method of `ImprovedChat`:

```python
def __init__(self, pairs, reflections, bot_name):
    # Existing initialization code...
    
    # Initialize conversation history
    self.conversation_history = []
```

### Step 2: Update the `respond` Method

Replace your current `respond` method with the implementation provided in the `Conversation Memory Implementation` code. This adds history tracking to every response path.

### Step 3: Add Utility Methods

Add the utility methods from the `Conversation Context Utilities` code to your `ImprovedChat` class.

### Step 4: Use Context in Response Generation

To make responses context-aware, add this code to enhance the final response before returning it:

```python
def respond(self, user_input):
    # Existing code...
    
    # Get the response through normal processing
    response = super().respond(user_input)
    
    # Enhance the response with conversation context
    enhanced_response = self.enhance_with_context(response, user_input)
    
    # Store in history and return the enhanced response
    self.conversation_history.append({"bot": enhanced_response, "timestamp": datetime.now()})
    return enhanced_response
```

## How to Use Conversation Memory in the ML System

To make the ML system context-aware, update the `ml_integration.py` file to pass conversation context:

```python
def enhance_chatbot_response(user_input, original_response, chatbot_instance=None):
    """
    Enhance the chatbot's response using ML when appropriate
    """
    # Get conversation context if available
    context = ""
    if chatbot_instance and hasattr(chatbot_instance, 'get_conversation_context'):
        context = chatbot_instance.get_conversation_context(max_turns=2)
    
    # Get ML-based response with context
    ml_response = get_ml_response(user_input, chatbot_instance, context=context)
    
    # Rest of the function...
```

And update the `get_ml_response` function to accept and use the context:

```python
def get_ml_response(user_input, chatbot_instance=None, context=""):
    """
    Get a response based on machine learning intent classification
    
    Args:
        user_input (str): User message
        chatbot_instance: Instance of the ImprovedChat class or None
        context (str): Conversation context from recent history
        
    Returns:
        dict: Response data with text and metadata
    """
    # Use context in your response generation...
    # For example, you could log it or use it to determine the best response
    if context:
        logger.debug(f"Using conversation context: {context}")
    
    # Rest of the function...
```

## Testing and Tuning

To test the conversation memory:

1. Run the chatbot in CLI mode:
   ```bash
   python -m chatbot.chatbot
   ```

2. Ask a question, then ask a follow-up using a pronoun:
   ```
   > What do you know about weather?
   > Is it important?
   ```

3. The chatbot should recognize "it" refers to weather from the previous exchange.

## Advanced Usage

### Adding Conversation Context to ML Training Data

To make the ML model context-aware:

1. Update your training data to include examples with context:
   ```json
   {"text": "previous message: What's the weather? current message: Is it important?", "intent": "weather_importance"}
   ```

2. Modify the ML engine to process such context-aware examples.

### Serializing Conversation History

To persist conversations between sessions:

```python
def save_conversation_history(self):
    """Save conversation history to user memory"""
    if hasattr(self, 'conversation_history') and self.conversation_history:
        # Convert datetime objects to strings for serialization
        serializable_history = []
        for entry in self.conversation_history:
            serialized_entry = {}
            for key, value in entry.items():
                if key == 'timestamp':
                    serialized_entry[key] = value.isoformat()
                else:
                    serialized_entry[key] = value
            serializable_history.append(serialized_entry)
        
        store_user_info(self.current_user_id, "conversation_history", serializable_history)
        return True
    return False

def load_conversation_history(self):
    """Load conversation history from user memory"""
    saved_history = get_user_info(self.current_user_id, "conversation_history")
    if saved_history:
        # Convert timestamp strings back to datetime objects
        for entry in saved_history:
            if 'timestamp' in entry:
                try:
                    entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                except:
                    entry['timestamp'] = datetime.now()
        
        self.conversation_history = saved_history
        return True
    return False
```

Call these methods when initializing the chatbot and when ending a session.