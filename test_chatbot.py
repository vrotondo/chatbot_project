# test_chatbot.py
# A simple script to test basic chatbot functionality

import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chatbot_test")

def main():
    """Test basic chatbot functionality"""
    print("\n===== CHATBOT FUNCTIONALITY TEST =====\n")
    
    # Add project root to path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.append(script_dir)
    
    # Import chatbot
    try:
        from chatbot.chatbot import ImprovedChat, pairs, reflections, bot_name
        logger.info(f"Successfully imported chatbot module with bot name: {bot_name}")
    except ImportError as e:
        logger.error(f"Failed to import chatbot module: {e}")
        print("Error: Failed to import chatbot. Make sure you're running this from the project root.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during import: {e}")
        print(f"Unexpected error: {e}")
        return 1
    
    # Create chatbot instance
    chatbot = ImprovedChat(pairs, reflections, bot_name)
    chatbot.set_user_id("test_user")
    
    # Test greeting patterns
    greetings = ["hi", "hello", "hey", "greetings", "howdy", "what's up", "hola", "hi there", "hello!"]
    
    print(f"\nTesting greetings with {bot_name}:\n")
    for greeting in greetings:
        response = chatbot.respond(greeting)
        print(f"User: {greeting}")
        print(f"{bot_name}: {response}")
        print("-" * 40)
    
    # Test a few other common patterns
    other_tests = [
        "what's your name?",
        "my name is John",
        "help",
        "what can you do?",
        "thank you",
        "weather in New York"
    ]
    
    print(f"\nTesting other patterns with {bot_name}:\n")
    for test in other_tests:
        response = chatbot.respond(test)
        print(f"User: {test}")
        print(f"{bot_name}: {response}")
        print("-" * 40)
    
    print("\nTest completed. Check responses above to verify functionality.")
    return 0

if __name__ == "__main__":
    sys.exit(main())