import json
import re
import os
import random
import requests  # For API requests
from nltk.chat.util import Chat as NLTKChat, reflections

# Path to config file - made relative to the script location
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "memory.json")
DEFAULT_BOT_NAME = "Wicked"

# Weather API configuration
WEATHER_API_KEY = "11ca5bc346a77d53d4dc1277552ae50f"  # Your API key

# User memory storage
user_memory = {}

# Response history to avoid repetition
response_history = {}

def load_memory():
    """Load user memory from file"""
    global user_memory
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r") as f:
                user_memory = json.load(f)
        else:
            user_memory = {}
    except Exception as e:
        print(f"Error loading memory: {e}")
        user_memory = {}

def save_memory():
    """Save user memory to file"""
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(user_memory, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving memory: {e}")
        return False

def store_user_info(user_id, key, value):
    """Store user information in memory"""
    if user_id not in user_memory:
        user_memory[user_id] = {}
    user_memory[user_id][key] = value
    save_memory()
    return True

def get_user_info(user_id, key):
    """Retrieve user information from memory"""
    return user_memory.get(user_id, {}).get(key)

def get_weather(city):
    """
    Fetch weather information for a given city
    
    Args:
        city (str): Name of the city
        
    Returns:
        str: Weather information or error message
    """
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            weather_description = data["weather"][0]["description"]
            temperature = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            
            weather_info = (
                f"Weather in {city}:\n"
                f"• Condition: {weather_description.capitalize()}\n"
                f"• Temperature: {temperature:.1f}°C (feels like {feels_like:.1f}°C)\n"
                f"• Humidity: {humidity}%"
            )
            return weather_info
        else:
            return f"Sorry, I couldn't find weather information for '{city}'. Please check the city name and try again."
    
    except Exception as e:
        print(f"Weather API error: {e}")
        return f"Sorry, there was an error fetching weather data for '{city}'."

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

def smart_response_selector(pattern, responses, user_id="default"):
    """
    Selects a response intelligently to avoid repetition
    
    Args:
        pattern (str): The pattern being matched
        responses (list): List of possible responses
        user_id (str): User identifier for tracking history
        
    Returns:
        str: Selected response
    """
    # Initialize pattern history if not exists
    if user_id not in response_history:
        response_history[user_id] = {}
    
    if pattern not in response_history[user_id]:
        response_history[user_id][pattern] = {
            "last_used": None,
            "history": []
        }
    
    pattern_history = response_history[user_id][pattern]
    
    # If we've used all responses, reset history
    if len(pattern_history["history"]) >= len(responses):
        pattern_history["history"] = []
    
    # Get responses we haven't used yet
    unused_responses = [r for i, r in enumerate(responses) if i not in pattern_history["history"]]
    
    if not unused_responses:
        # Should not happen but just in case
        selected = random.choice(responses)
    else:
        # Select a random unused response
        selected = random.choice(unused_responses)
    
    # Store the index of the selected response
    selected_index = responses.index(selected)
    pattern_history["history"].append(selected_index)
    pattern_history["last_used"] = selected_index
    
    return selected

class ImprovedChat(NLTKChat):
    """
    An improved chat class that handles custom callbacks and better wildcard processing
    """
    def __init__(self, pairs, reflections, bot_name):
        """Initialize with pairs, reflections, and bot name"""
        # Store the bot name
        self.bot_name = bot_name
        
        # Store the current user ID (default for now)
        self.current_user_id = "default_user"
        
        # Format pairs with the current bot name before passing to parent
        formatted_pairs = []
        for pattern, response in pairs:
            # Handle the special case for the bot name in regex pattern
            if "{bot_name}" in pattern:
                pattern = pattern.format(bot_name=re.escape(bot_name))
            
            # Add to formatted pairs
            formatted_pairs.append((pattern, response))
        
        # Call parent init with formatted pairs and custom response selector
        super().__init__(formatted_pairs, reflections)
    
    def respond(self, user_input):
        """Generate a response to the user input."""
        # Format responses that contain the bot name
        for i, (pattern, responses) in enumerate(self._pairs):
            if isinstance(responses, list):
                for j, response in enumerate(responses):
                    if isinstance(response, str) and "{bot_name}" in response:
                        self._pairs[i][1][j] = response.format(bot_name=self.bot_name)
                    # Replace memory placeholders
                    elif isinstance(response, str) and "{memory:" in response:
                        # Extract memory key from pattern like {memory:favorite_color}
                        memory_keys = re.findall(r'\{memory:([^}]+)\}', response)
                        for key in memory_keys:
                            value = get_user_info(self.current_user_id, key) or "unknown"
                            self._pairs[i][1][j] = response.replace(f"{{memory:{key}}}", value)
        
        # Check for custom callback pairs
        for pattern, response in self._pairs:
            match = pattern.search(user_input)
            if match:
                # Handle callbacks with custom response selection
                if isinstance(response, tuple):
                    response_list, callback = response
                    # Use smart response selector to avoid repetition
                    chosen_response = smart_response_selector(
                        str(pattern.pattern), response_list, self.current_user_id
                    )
                    
                    # Execute the callback with matched groups
                    callback_result = callback(match.groups())
                    
                    # If callback returns a value, use it instead of the response template
                    if callback_result:
                        return callback_result
                    
                    # Otherwise, process the template response
                    processed = self._wildcards(chosen_response, match)
                    return processed
                # Regular responses (no callback)
                else:
                    # Use smart response selector to avoid repetition
                    chosen_response = smart_response_selector(
                        str(pattern.pattern), response, self.current_user_id
                    )
                    return self._wildcards(chosen_response, match)
        
        # No match found
        return "I'm not sure I understand. Could you rephrase that?"
    
    def set_user_id(self, user_id):
        """Set the current user ID for memory storage"""
        self.current_user_id = user_id
    
    def converse(self, quit="quit"):
        """Interact with the user in a console."""
        print(f"Hi! I'm {self.bot_name}, your chatbot. Type '{quit}' to exit.")
        
        user_name = get_user_info(self.current_user_id, "name")
        if user_name:
            print(f"Welcome back, {user_name}! It's good to see you again.")
        
        while True:
            try:
                user_input = input("> ")
                if user_input.lower() == quit:
                    print("Goodbye!")
                    break
                
                response = self.respond(user_input)
                if response:
                    print(response)
                else:
                    print("I'm not sure I understand. Can you rephrase that?")
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

# Weather callback for pattern matching
def weather_callback(groups):
    """Process weather request and return weather information"""
    if groups and groups[0]:
        city = groups[0].strip()
        return get_weather(city)
    return None

# Memory callbacks
def store_name_callback(groups):
    """Store user's name in memory"""
    if groups and groups[0]:
        name = groups[0].strip()
        store_user_info("default_user", "name", name)
        return None  # Let the template handle the response
    return None

def store_favorite_callback(groups):
    """Store user's favorite thing in memory"""
    if groups and len(groups) >= 2:
        category = groups[0].strip()
        item = groups[1].strip()
        store_user_info("default_user", f"favorite_{category}", item)
        return None  # Let the template handle the response
    return None

def get_favorite_callback(groups):
    """Retrieve user's favorite thing from memory"""
    if groups and groups[0]:
        category = groups[0].strip()
        favorite = get_user_info("default_user", f"favorite_{category}")
        if favorite:
            return f"Your favorite {category} is {favorite}!"
        else:
            return f"I don't know your favorite {category} yet. What is it?"
    return None

# Initialize memory when module is loaded
load_memory()

# Initialize bot name
bot_name = load_name()

# Define chatbot response patterns with improved formatting and more variety
pairs = [
    # Basic greeting and name exchange
    [
        r"my name is (.*)",
        (["Hello %1! I'll remember your name.", 
          "Nice to meet you, %1! I'll remember that.",
          "Great to meet you, %1! I've saved your name.",
          "Hi %1! I'll keep that in mind for our future chats."],
         store_name_callback)
    ],
    [
        r"(?:what(?:'s| is) your name|who are you)\??",
        [
            "I'm {bot_name}, your friendly AI assistant! 🌟",
            "My name is {bot_name}. How can I assist you today?",
            "I go by {bot_name}. What can I help you with?",
            "They call me {bot_name}! How can I be of service?",
            "{bot_name} is my name, chatting is my game!",
            "I'm your virtual assistant, {bot_name}. What's on your mind today?"
        ]
    ],
    [
        r"how are you\??",
        ["I'm doing well, thanks for asking!", 
         "All systems operational! How about you?", 
         "I'm great! How can I help you today?",
         "I'm functioning perfectly! How are you doing?",
         "Feeling fantastic! Ready to chat!",
         "Never been better! What about you?",
         "I'm having a great day in the digital world!"]
    ],
    
    # Memory-based responses
    [
        r"what(?:'s| is) my name\??",
        ["Your name is {memory:name}.", 
         "I remember you as {memory:name}!",
         "You told me your name is {memory:name}.",
         "According to my memory, you're {memory:name}."]
    ],
    [
        r"my favorite (color|food|movie|book|song|animal) is (.*)",
        (["I'll remember your favorite %1 is %2!",
          "Got it! Your favorite %1 is %2.",
          "I've noted that you like %2 as your favorite %1.",
          "I'll keep in mind that %2 is your favorite %1."],
         store_favorite_callback)
    ],
    [
        r"what(?:'s| is) my favorite (color|food|movie|book|song|animal)\??",
        (["I'll tell you what I know about your favorite %1..."],
         get_favorite_callback)
    ],
    [
        r"do you remember me\??",
        ["Yes, you're {memory:name}! It's good to chat with you again.",
         "Of course! You're {memory:name}.",
         "I never forget a friend, {memory:name}!",
         "How could I forget you, {memory:name}?"]
    ],
    
    # Name changing functionality
    [
        r"(?:call|name) you (.*)",
        (["I'll respond to %1 from now on!", 
          "I like the name %1! Let's continue our chat.",
          "From now on, I'll go by %1!",
          "%1 it is! I'm enjoying my new identity already."],
         lambda matches: save_name_and_update(matches[0]))
    ],
    [
        r"how did you get your name\??",
        ["My creator named me {bot_name}! I think it's a great name, don't you?",
         "I was born with the name {bot_name}. Do you like it?",
         "The name {bot_name} was chosen for me. It has a nice ring to it!",
         "I've always been {bot_name}! Well, unless you rename me, of course."]
    ],
    
    # Direct address using bot name
    [
        r"(?i){bot_name},? (.*)",
        ["Yes, I'm listening! About '%1'...", 
         "I'm here! Regarding '%1'...",
         "You called? You were saying something about '%1'...",
         "At your service! Let's discuss '%1'..."]
    ],
    
    # WEATHER FUNCTIONALITY
    [
        r"(?:what(?:'s| is) the )?weather(?: like)? in ([\w\s]+)(?:\?)?",
        (["Let me check the weather for you...",
          "Checking the forecast for %1...",
          "Let me look up the current weather in %1...",
          "Fetching weather information for %1..."], 
         weather_callback)
    ],
    [
        r"(?:what(?:'s| is) the )?temperature(?: like)? in ([\w\s]+)(?:\?)?",
        (["Checking temperature information in %1...",
          "Let me find out how warm or cold it is in %1...",
          "Looking up the current temperature in %1...",
          "Getting the latest temperature readings for %1..."], 
         weather_callback)
    ],
    [
        r"(?:how(?:'s| is) the )?weather(?: like)? (?:in|at) ([\w\s]+)(?:\?)?",
        (["Fetching weather data for %1...",
          "Let me check on the conditions in %1...",
          "I'll find out what it's like in %1 right now...",
          "Getting the latest weather update for %1..."], 
         weather_callback)
    ],
    
    # Help and capabilities
    [
        r"(?:help|what can you do|your abilities)\??",
        ["I can chat with you about various topics, remember your name and preferences, check weather, and even change my name if you'd like!",
         "I'm a chatbot that can have conversations, remember your details, check weather forecasts, and respond to basic queries.",
         "I can remember your name and preferences, tell you the weather, and chat with you about various topics!",
         "My capabilities include remembering information about you, checking weather forecasts, and having friendly conversations.",
         "I'm designed to chat, remember details about you, check the weather, and respond to various questions!"]
    ],
    
    # Exit commands
    [
        r"(?:quit|exit|bye|goodbye)",
        ["Goodbye! Have a great day!", 
         "See you later!", 
         "Until next time!",
         "Farewell! Come back soon!",
         "Take care! Hope to chat again soon!",
         "Goodbye! It was nice talking with you."]
    ],
    
    # Fallback response
    [
        r"(.*)",
        ["I'm not sure I understand. Could you rephrase that?", 
         "Interesting. Tell me more about that.", 
         "I'm still learning. Can you elaborate?",
         "I didn't quite catch that. Mind saying it differently?",
         "That's a new one for me. Could you say it another way?",
         "I'm not following. Could you explain in different words?"]
    ]
]

def simple_chatbot():
    """Run the chatbot in console mode"""
    chat = ImprovedChat(pairs, reflections, bot_name)
    chat.converse()

if __name__ == "__main__":
    simple_chatbot()