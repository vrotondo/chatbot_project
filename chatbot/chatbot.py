import json
import re
import os
import random
from nltk.chat.util import Chat as NLTKChat, reflections

# Path to config file - made relative to the script location
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
DEFAULT_BOT_NAME = "Wicked"

def load_name():
    """Load the bot name from config file or use default"""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            name = config.get("bot_name", DEFAULT_BOT_NAME)
            # Ensure we don't load a placeholder
            return name if name != "%1" else DEFAULT_BOT_NAME
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Warning: Config file issue. Using default bot name '{DEFAULT_BOT_NAME}'.")
        return DEFAULT_BOT_NAME

def save_name(new_name):
    """Save the bot name to config file"""
    try:
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        # Load existing config or create new one
        config = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
            except json.JSONDecodeError:
                pass
        
        # Update name and save
        config["bot_name"] = new_name
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

class ImprovedChat(NLTKChat):
    """
    An improved chat class that handles custom callbacks and better wildcard processing
    """
    def __init__(self, pairs, reflections, bot_name):
        """Initialize with pairs, reflections, and bot name"""
        # Compile regex patterns
        compiled_pairs = []
        for pattern, response in pairs:
            compiled_pattern = re.compile(pattern, re.IGNORECASE)
            compiled_pairs.append((compiled_pattern, response))
        
        super().__init__(compiled_pairs, reflections)
        self.bot_name = bot_name
    
    def respond(self, user_input):
        """Generate a response to the user input."""
        # Update pairs that use the bot name
        self._update_bot_name_in_pairs()
        
        # Process the input against our patterns
        for pattern, responses in self._pairs:
            match = pattern.search(user_input)
            if match:
                # Handle response options with callbacks
                if isinstance(responses, tuple):
                    response_list, callback = responses
                    response = random.choice(response_list)
                    processed = self._wildcards(response, match)
                    callback(match.groups())
                    return processed
                else:
                    response = random.choice(responses)
                    return self._wildcards(response, match)
        
        # No match found
        return "I'm not sure I understand. Can you rephrase that?"
    
    def _update_bot_name_in_pairs(self):
        """Update dynamic responses with current bot name"""
        for i, (pattern, responses) in enumerate(self._pairs):
            # Update responses that mention the bot name
            if isinstance(responses, list):
                for j, response in enumerate(responses):
                    if isinstance(response, str) and "{bot_name}" in response:
                        self._pairs[i][1][j] = response.format(bot_name=self.bot_name)
    
    def converse(self, quit="quit"):
        """Interact with the user in a console."""
        print(f"Hi! I'm {self.bot_name}, your chatbot. Type '{quit}' to exit.")
        
        while True:
            try:
                user_input = input("> ")
                if user_input.lower() == quit:
                    print("Goodbye!")
                    break
                
                response = self.respond(user_input)
                if response:
                    print(response)
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break

def save_name_and_update(new_name):
    """Callback to save the new bot name and update the global variable"""
    global bot_name
    if new_name:
        bot_name = new_name
        save_name(new_name)
        return True
    return False

# Initialize bot name
bot_name = load_name()

# Define chatbot response patterns with improved formatting
pairs = [
    # Basic greeting and name exchange
    [
        r"my name is (.*)",
        ["Hello %1! How can I help you today?", "Nice to meet you, %1! What can I do for you?"]
    ],
    [
        r"(?:what(?:'s| is) your name|who are you)\??",
        [
            "I'm {bot_name}, your friendly AI assistant! 🌟",
            "My name is {bot_name}. How can I assist you today?",
            "I go by {bot_name}. What can I help you with?"
        ]
    ],
    [
        r"how are you\??",
        ["I'm doing well, thanks for asking!", "All systems operational! How about you?", 
         "I'm great! How can I help you today?"]
    ],
    
    # Name changing functionality
    [
        r"(?:call|name) you (.*)",
        (["I'll respond to %1 from now on!", "I like the name %1! Let's continue our chat."],
         lambda matches: save_name_and_update(matches[0]))
    ],
    [
        r"how did you get your name\??",
        ["My creator named me {bot_name}! I think it's a great name, don't you?",
         "I was born with the name {bot_name}. Do you like it?"]
    ],
    
    # Direct address using bot name
    [
        r"(?i){bot_name},? (.*)",
        ["Yes, I'm listening! About '%1'...", "I'm here! Regarding '%1'..."]
    ],
    
    # Help and capabilities
    [
        r"(?:help|what can you do|your abilities)\??",
        ["I can chat with you about various topics, remember your name, and even change my name if you'd like!",
         "I'm a simple chatbot that can have conversations, remember names, and respond to basic queries."]
    ],
    
    # Exit commands
    [
        r"(?:quit|exit|bye|goodbye)",
        ["Goodbye! Have a great day!", "See you later!", "Until next time!"]
    ],
    
    # Fallback response
    [
        r"(.*)",
        ["I'm not sure I understand. Could you rephrase that?", 
         "Interesting. Tell me more about that.", 
         "I'm still learning. Can you elaborate?"]
    ]
]

def simple_chatbot():
    """Run the chatbot in console mode"""
    chat = ImprovedChat(pairs, reflections, bot_name)
    chat.converse()

if __name__ == "__main__":
    simple_chatbot()