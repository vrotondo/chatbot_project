import json
import re
import os
import random
import time
from datetime import datetime
import requests
import time
import logging
from nltk.chat.util import Chat as NLTKChat, reflections

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chatbot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("chatbot")

# Path to config file - made relative to the script location
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "memory.json")
DEFAULT_BOT_NAME = "Wicked"

# Weather API configuration
WEATHER_API_KEY = "11ca5bc346a77d53d4dc1277552ae50f"  # Your API key

# API request constants
REQUEST_TIMEOUT = 10  # seconds
MAX_RETRIES = 2
RETRY_DELAY = 1  # seconds

# User memory storage
user_memory = {}

def load_memory():
    """
    Load user memory from file
    
    Returns:
        bool: True if memory loaded successfully, False otherwise
    """
    global user_memory
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r") as f:
                user_memory = json.load(f)
                logger.info("Successfully loaded memory from file")
            return True
        else:
            logger.info("No memory file found, initializing empty memory")
            user_memory = {}
            return True
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding memory file: {e}")
        logger.info("Initializing empty memory due to file corruption")
        user_memory = {}
        return False
    except Exception as e:
        logger.error(f"Unexpected error loading memory: {e}")
        user_memory = {}
        return False

def save_memory():
    """
    Save user memory to file
    
    Returns:
        bool: True if memory saved successfully, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        
        with open(MEMORY_FILE, "w") as f:
            json.dump(user_memory, f, indent=2)
        logger.info("Successfully saved memory to file")
        return True
    except PermissionError as e:
        logger.error(f"Permission denied when saving memory: {e}")
        return False
    except IOError as e:
        logger.error(f"IO error when saving memory: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error saving memory: {e}")
        return False

def store_user_info(user_id, key, value):
    """
    Store user information in memory
    
    Args:
        user_id (str): User identifier
        key (str): The attribute key to store
        value: The value to store
        
    Returns:
        bool: True if successfully stored, False otherwise
    """
    try:
        if not user_id or not isinstance(user_id, str):
            logger.warning(f"Invalid user_id: {user_id}")
            return False
            
        if not key or not isinstance(key, str):
            logger.warning(f"Invalid key: {key}")
            return False
        
        # Initialize user record if it doesn't exist
        if user_id not in user_memory:
            user_memory[user_id] = {}
        
        # Store the value
        user_memory[user_id][key] = value
        
        # Persist to file
        return save_memory()
    except Exception as e:
        logger.error(f"Error storing user info: {e}")
        return False

def get_user_info(user_id, key, default=None):
    """
    Retrieve user information from memory
    
    Args:
        user_id (str): User identifier
        key (str): The attribute key to retrieve
        default: Default value to return if not found
        
    Returns:
        The stored value or default if not found
    """
    try:
        if not user_id or not isinstance(user_id, str):
            logger.warning(f"Invalid user_id in get_user_info: {user_id}")
            return default
            
        if not key or not isinstance(key, str):
            logger.warning(f"Invalid key in get_user_info: {key}")
            return default
            
        return user_memory.get(user_id, {}).get(key, default)
    except Exception as e:
        logger.error(f"Error retrieving user info: {e}")
        return default

def get_weather(city):
    """
    Fetch weather information for a given city with robust error handling
    
    Args:
        city (str): Name of the city
        
    Returns:
        str: Weather information or error message
    """
    if not city or not isinstance(city, str):
        return "I need a valid city name to check the weather."
    
    # Clean the city name to avoid injection attacks
    city = re.sub(r'[^\w\s-]', '', city).strip()
    if not city:
        return "Please provide a valid city name with letters and spaces only."
    
    # Attempt API request with retries
    for attempt in range(MAX_RETRIES + 1):
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            
            # Check for API errors
            if response.status_code == 401:
                logger.error("Weather API authentication failed - invalid API key")
                return "Sorry, I'm having trouble with my weather service authentication. Please try again later."
                
            elif response.status_code == 404:
                return f"I couldn't find weather data for '{city}'. Please check the spelling or try another city."
                
            elif response.status_code == 429:
                logger.warning("Weather API rate limit exceeded")
                return "I've checked too many weather forecasts recently. Please try again in a minute."
                
            elif response.status_code != 200:
                logger.error(f"Weather API error: Status code {response.status_code}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                    continue
                return f"Sorry, the weather service returned an error (code {response.status_code}). Please try again later."
            
            # Process successful response
            data = response.json()
            
            # Validate expected data structure
            if not data.get("weather") or not data.get("main"):
                logger.error(f"Weather API returned unexpected data format: {data}")
                return "The weather service returned incomplete data. Please try again later."
            
            # Extract weather information
            weather_description = data["weather"][0]["description"]
            temperature = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            
            # Format the response
            weather_info = (
                f"Weather in {city}:\n"
                f"• Condition: {weather_description.capitalize()}\n"
                f"• Temperature: {temperature:.1f}°C (feels like {feels_like:.1f}°C)\n"
                f"• Humidity: {humidity}%"
            )
            return weather_info
            
        except requests.exceptions.ConnectTimeout:
            logger.error(f"Weather API connection timeout (attempt {attempt+1}/{MAX_RETRIES+1})")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return "The weather service is taking too long to respond. Please try again later."
            
        except requests.exceptions.ReadTimeout:
            logger.error(f"Weather API read timeout (attempt {attempt+1}/{MAX_RETRIES+1})")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return "The weather service is taking too long to provide data. Please try again later."
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Weather API connection error (attempt {attempt+1}/{MAX_RETRIES+1})")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return "I can't connect to the weather service right now. Please check your internet connection and try again."
            
        except json.JSONDecodeError:
            logger.error(f"Weather API returned invalid JSON (attempt {attempt+1}/{MAX_RETRIES+1})")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return "The weather service provided an invalid response. Please try again later."
            
        except Exception as e:
            logger.error(f"Unexpected error in weather API: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return f"Sorry, I encountered an unexpected error while checking the weather. Please try again later."
    
    # If we get here, all retries failed
    return "I'm having persistent issues connecting to the weather service. Please try again later."

def load_name():
    """
    Load the bot name from config file or use default
    
    Returns:
        str: The bot name loaded from config or the default
    """
    try:
        if not os.path.exists(CONFIG_FILE):
            logger.info(f"Config file not found, using default bot name: {DEFAULT_BOT_NAME}")
            return DEFAULT_BOT_NAME
            
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            name = config.get("bot_name", DEFAULT_BOT_NAME)
            
            # Validate the name
            if not name or name == "%1" or not isinstance(name, str):
                logger.warning(f"Invalid bot name in config: {name}, using default")
                return DEFAULT_BOT_NAME
                
            logger.info(f"Successfully loaded bot name: {name}")
            return name
            
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding config file: {e}")
        return DEFAULT_BOT_NAME
    except Exception as e:
        logger.error(f"Unexpected error loading bot name: {e}")
        return DEFAULT_BOT_NAME

def save_name(new_name):
    """
    Save the bot name to config file
    
    Args:
        new_name (str): The new bot name to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not new_name or not isinstance(new_name, str):
        logger.warning(f"Attempted to save invalid bot name: {new_name}")
        return False
        
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
                logger.warning("Config file was corrupted, creating new config")
                config = {}
        
        # Update name and save
        config["bot_name"] = new_name
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
            
        logger.info(f"Successfully saved bot name: {new_name}")
        return True
        
    except PermissionError as e:
        logger.error(f"Permission denied when saving config: {e}")
        return False
    except IOError as e:
        logger.error(f"IO error when saving config: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error saving config: {e}")
        return False

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
        
        # Track previous responses to avoid repetition
        self.previous_responses = {}
        
        try:
            # Format pairs with the current bot name before passing to parent
            formatted_pairs = []
            for pattern, response in pairs:
                # Handle the special case for the bot name in regex pattern
                if "{bot_name}" in pattern:
                    pattern = pattern.format(bot_name=re.escape(bot_name))
                
                # Add to formatted pairs
                formatted_pairs.append((pattern, response))
            
            # Call parent init with formatted pairs
            super().__init__(formatted_pairs, reflections)
            
        except Exception as e:
            logger.error(f"Error initializing ImprovedChat: {e}")
            # Fall back to basic initialization if formatting fails
            super().__init__(pairs, reflections)
    
    def respond(self, user_input):
        """Generate a response to the user input with error handling"""
        if not user_input:
            return "You didn't say anything. How can I help you?"
            
        try:
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
                try:
                    match = pattern.search(user_input)
                    if match and isinstance(response, tuple):
                        # This is a special case for callback functions
                        response_list, callback = response
                        
                        # Get pattern string for tracking previous responses
                        pattern_str = pattern.pattern
                        prev_response = self.previous_responses.get(pattern_str)
                        
                        # Use custom selector for response
                        chosen_response = custom_response_selector(
                            response_list, 
                            previous_response=prev_response,
                            user_id=self.current_user_id
                        )
                        
                        # Store this response to avoid repetition next time
                        self.previous_responses[pattern_str] = chosen_response
                        
                        # Execute the callback with matched groups
                        try:
                            callback_result = callback(match.groups())
                            
                            # If callback returns a value, use it instead of the response template
                            if callback_result:
                                return callback_result
                                
                            # Otherwise, process the template response
                            processed = self._wildcards(chosen_response, match)
                            return processed
                        except Exception as e:
                            logger.error(f"Error in callback function: {e}")
                            return "I encountered an error processing your request. Please try again."
                    
                    # For regular pattern matches (not callbacks)
                    elif match and isinstance(response, list):
                        # Get pattern string for tracking previous responses
                        pattern_str = pattern.pattern
                        prev_response = self.previous_responses.get(pattern_str)
                        
                        # Use custom selector for response
                        chosen_response = custom_response_selector(
                            response, 
                            previous_response=prev_response,
                            user_id=self.current_user_id
                        )
                        
                        # Store this response to avoid repetition next time
                        self.previous_responses[pattern_str] = chosen_response
                        
                        return self._wildcards(chosen_response, match)
                        
                except Exception as e:
                    logger.error(f"Error processing pattern match: {e}")
                    continue
            
            # Let parent class handle standard responses
            return super().respond(user_input)
            
        except Exception as e:
            logger.error(f"Unexpected error generating response: {e}")
            return "I'm having trouble understanding right now. Could you try rephrasing that?"
    
    def custom_response_selector(responses, previous_response=None, user_id=None):
        """
        Advanced response selector with nuanced randomization
        
        Args:
            responses: List of possible responses
            previous_response: Last response given (to avoid repetition)
            user_id: ID of the current user (for personalization)
            
        Returns:
            str: A carefully selected response
        """
        if not responses:
            return "I'm not sure what to say."
        
        # If there's only one response, we have no choice
        if len(responses) == 1:
            return responses[0]
        
        # Get current time to customize responses by time of day
        current_hour = datetime.now().hour
        
        # Morning: 5am-11am, Afternoon: 12pm-5pm, Evening: 6pm-9pm, Night: 10pm-4am
        time_of_day = "morning" if 5 <= current_hour < 12 else \
                    "afternoon" if 12 <= current_hour < 18 else \
                    "evening" if 18 <= current_hour < 22 else "night"
        
        # Filter out the previous response to avoid repetition
        available_responses = [r for r in responses if r != previous_response]
        
        # If we filtered all responses, reset to original list
        if not available_responses:
            available_responses = responses
        
        # Assign weights to responses for more natural selection
        weighted_responses = []
        
        for response in available_responses:
            # Base weight is 1.0
            weight = 1.0
            
            # Prioritize responses appropriate for the time of day
            if time_of_day == "morning" and any(word in response.lower() for word in ["morning", "day", "today"]):
                weight += 0.5
            elif time_of_day == "afternoon" and "afternoon" in response.lower():
                weight += 0.5
            elif time_of_day == "evening" and any(word in response.lower() for word in ["evening", "tonight"]):
                weight += 0.5
            elif time_of_day == "night" and any(word in response.lower() for word in ["night", "late"]):
                weight += 0.5
                
            # Prefer shorter responses normally, longer responses for complex questions
            response_length = len(response.split())
            if response_length < 10:  # Short and sweet responses
                weight += 0.3
            
            # Prefer responses with emoji for a friendlier tone (adjust by preference)
            if any(emoji in response for emoji in ["😊", "👍", "🌟", "✨", "👋"]):
                weight += 0.2
                
            # Add random slight variation to prevent predictable patterns
            weight += random.uniform(-0.1, 0.1)
            
            weighted_responses.append((response, weight))
        
        # Select response based on weights
        total_weight = sum(weight for _, weight in weighted_responses)
        random_val = random.uniform(0, total_weight)
        
        current_weight = 0
        for response, weight in weighted_responses:
            current_weight += weight
            if random_val <= current_weight:
                selected_response = response
                break
        else:
            # Fallback if something goes wrong with the weighting
            selected_response = random.choice(available_responses)
        
        # Add slight variations to responses
        selected_response = add_response_variation(selected_response, time_of_day, user_id)
        
        return selected_response

    def add_response_variation(response, time_of_day, user_id=None):
        """
        Add slight variations to responses to make them more natural
        
        Args:
            response: The selected response
            time_of_day: Current time of day
            user_id: ID of the current user
            
        Returns:
            str: The response with variations
        """
        # Get user's name if available
        user_name = get_user_info(user_id, "name") if user_id else None
        
        # Add time-of-day greeting occasionally (20% chance)
        if random.random() < 0.2:
            time_greeting = {
                "morning": "Good morning! ",
                "afternoon": "Good afternoon! ",
                "evening": "Good evening! ",
                "night": "Hi there! "
            }.get(time_of_day, "")
            
            # Add user's name to greeting if available
            if user_name and random.random() < 0.5:
                time_greeting = time_greeting.rstrip() + f", {user_name}! "
                
            # Only prepend greeting if the response doesn't already have one
            greeting_patterns = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
            if not any(response.lower().startswith(greeting) for greeting in greeting_patterns):
                response = time_greeting + response
        
        # Add filler words occasionally (10% chance)
        if random.random() < 0.1:
            fillers = ["Well, ", "Hmm, ", "Let's see, ", "Actually, ", "You know, "]
            if not any(response.startswith(filler) for filler in fillers):
                response = random.choice(fillers) + response[0].lower() + response[1:]
        
        # Add thinking sounds occasionally (5% chance)
        if random.random() < 0.05:
            thinking = ["hmm", "uh", "um", "let me think"]
            response = response.replace(".", f"... {random.choice(thinking)}.")
        
        # Add emphasis to important words (15% chance)
        if random.random() < 0.15:
            # Find words to emphasize (longer words are usually more important)
            words = response.split()
            for i, word in enumerate(words):
                if len(word) > 5 and random.random() < 0.3:
                    # Different emphasis styles
                    emphasis_style = random.choice([
                        lambda w: w.upper(),  # ALL CAPS
                        lambda w: f"*{w}*",    # *asterisks*
                        lambda w: f"_{w}_"     # _underscores_
                    ])
                    words[i] = emphasis_style(word)
            response = " ".join(words)
        
        # Add friendly emoji occasionally (25% chance for certain message types)
        if random.random() < 0.25 and "?" not in response and not response.endswith("!"):
            emojis = ["😊", "👍", "✨", "🌟", "👋"]
            response += f" {random.choice(emojis)}"
        
        return response
    
    def set_user_id(self, user_id):
        """Set the current user ID for memory storage"""
        if user_id and isinstance(user_id, str):
            self.current_user_id = user_id
        else:
            logger.warning(f"Attempted to set invalid user_id: {user_id}")

    # Add this to your memory initialization part
    def set_user_personality_preference(user_id, style):
        """
        Set the user's preferred conversation style
        
        Args:
            user_id (str): User identifier
            style (str): Preferred style (formal, casual, humorous, etc.)
            
        Returns:
            bool: True if successful
        """
        return store_user_info(user_id, "personality_preference", style)

    # Then in custom_response_selector, add:
        # Get user's personality preference if available
        personality = get_user_info(user_id, "personality_preference") if user_id else None
        
        # Adjust weights based on user's personality preference
        if personality:
            for i, (response, weight) in enumerate(weighted_responses):
                if personality == "formal" and re.search(r'\b(hello|greetings|indeed|certainly)\b', response.lower()):
                    weighted_responses[i] = (response, weight + 0.5)
                elif personality == "casual" and re.search(r'\b(hey|hi|sure|cool)\b', response.lower()):
                    weighted_responses[i] = (response, weight + 0.5)
                elif personality == "humorous" and any(w in response.lower() for w in ["!", "joke", "funny", "haha"]):
                    weighted_responses[i] = (response, weight + 0.5)
    
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
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except EOFError:
                print("\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Unexpected error in conversation: {e}")
                print("Sorry, I encountered an unexpected error. Let's continue our conversation.")

# Callbacks for various functions
def save_name_and_update(groups):
    """
    Callback to save the new bot name and update the global variable
    
    Args:
        groups (tuple): Matched regex groups
        
    Returns:
        bool: True if successful, None otherwise
    """
    global bot_name
    try:
        if not groups or not groups[0]:
            return None
            
        new_name = groups[0].strip()
        if not new_name:
            return None
            
        if save_name(new_name):
            bot_name = new_name
            logger.info(f"Bot name changed to: {new_name}")
            return True
            
        return None
    except Exception as e:
        logger.error(f"Error in save_name_and_update: {e}")
        return None

# Weather callback for pattern matching
def weather_callback(groups):
    """
    Process weather request and return weather information
    
    Args:
        groups (tuple): Matched regex groups
        
    Returns:
        str: Weather information or error message
    """
    try:
        if not groups or not groups[0]:
            return "I need a city name to check the weather."
            
        city = groups[0].strip()
        if not city:
            return "Please provide a valid city name."
            
        return get_weather(city)
    except Exception as e:
        logger.error(f"Error in weather_callback: {e}")
        return "I encountered an error while checking the weather. Please try again."

# Memory callbacks
def store_name_callback(groups):
    """
    Store user's name in memory
    
    Args:
        groups (tuple): Matched regex groups
        
    Returns:
        None: Let the template handle the response
    """
    try:
        if not groups or not groups[0]:
            return None
            
        name = groups[0].strip()
        if not name:
            return None
            
        if store_user_info("default_user", "name", name):
            logger.info(f"Stored user name: {name}")
            
        return None  # Let the template handle the response
    except Exception as e:
        logger.error(f"Error in store_name_callback: {e}")
        return None

def store_favorite_callback(groups):
    """
    Store user's favorite thing in memory
    
    Args:
        groups (tuple): Matched regex groups
        
    Returns:
        None: Let the template handle the response
    """
    try:
        if not groups or len(groups) < 2:
            return None
            
        category = groups[0].strip()
        item = groups[1].strip()
        
        if not category or not item:
            return None
            
        if store_user_info("default_user", f"favorite_{category}", item):
            logger.info(f"Stored favorite {category}: {item}")
            
        return None  # Let the template handle the response
    except Exception as e:
        logger.error(f"Error in store_favorite_callback: {e}")
        return None

def get_favorite_callback(groups):
    """
    Retrieve user's favorite thing from memory
    
    Args:
        groups (tuple): Matched regex groups
        
    Returns:
        str: Response with favorite item or message if not found
    """
    try:
        if not groups or not groups[0]:
            return "I need to know what favorite thing you're asking about."
            
        category = groups[0].strip()
        if not category:
            return "Please specify which favorite thing you're asking about."
            
        favorite = get_user_info("default_user", f"favorite_{category}")
        if favorite:
            return f"Your favorite {category} is {favorite}!"
        else:
            return f"I don't know your favorite {category} yet. What is it?"
    except Exception as e:
        logger.error(f"Error in get_favorite_callback: {e}")
        return "I'm having trouble remembering right now. Could you tell me again?"

# Initialize logging when module is loaded
try:
    logger.info("Initializing chatbot module")
except Exception as e:
    print(f"Warning: Failed to initialize logging: {e}")

# Initialize memory when module is loaded
try:
    load_memory()
except Exception as e:
    print(f"Warning: Failed to load memory: {e}")
    user_memory = {}

# Initialize bot name
try:
    bot_name = load_name()
except Exception as e:
    print(f"Warning: Failed to load bot name: {e}")
    bot_name = DEFAULT_BOT_NAME

# Define chatbot response patterns with improved formatting
pairs = [
    pairs = [
    # Basic greeting and name exchange with time-of-day variations
    [
        r"my name is (.*)",
        (["Hello %1! I'll remember your name.", 
          "Nice to meet you, %1! I'll remember that.",
          "Good morning, %1! I'll make a note of your name.",
          "Good afternoon, %1! Nice to meet you.",
          "Good evening, %1! Pleased to make your acquaintance.",
          "Hi there, %1! I'll remember you."],
         store_name_callback)
    ],
    
    # Add time-specific greetings
    [
        r"(?:good )?morning|(?:good )?day",
        ["Good morning to you too! How can I help you today?",
         "Morning! How's your day starting out?",
         "Top of the morning to you! What can I assist with?",
         "Good morning! Got any exciting plans for today?"]
    ],
    [
        r"(?:good )?afternoon",
        ["Good afternoon! How's your day going so far?",
         "Afternoon! Hope you're having a productive day.",
         "Good afternoon to you! What can I help with?",
         "Hi there! Enjoying the afternoon?"]
    ],
    [
        r"(?:good )?evening",
        ["Good evening! Winding down for the day?",
         "Evening! How was your day?",
         "Good evening to you! How can I assist you tonight?",
         "Hi there! Having a pleasant evening?"]
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
    
    # Memory-based responses
    [
        r"what(?:'s| is) my name\??",
        ["Your name is {memory:name}.", 
         "I remember you as {memory:name}!"]
    ],
    [
        r"my favorite (color|food|movie|book|song|animal) is (.*)",
        (["I'll remember your favorite %1 is %2!",
          "Got it! Your favorite %1 is %2."],
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
         "Of course! You're {memory:name}."]
    ],
    
    # Name changing functionality
    [
        r"(?:call|name) you (.*)",
        (["I'll respond to %1 from now on!", "I like the name %1! Let's continue our chat."],
         lambda groups: save_name_and_update(groups))
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
    
    # WEATHER FUNCTIONALITY
    [
        r"(?:what(?:'s| is) the )?weather(?: like)? in ([\w\s]+)(?:\?)?",
        (["Let me check the weather for you..."], weather_callback)
    ],
    [
        r"(?:what(?:'s| is) the )?temperature(?: like)? in ([\w\s]+)(?:\?)?",
        (["Checking temperature information..."], weather_callback)
    ],
    [
        r"(?:how(?:'s| is) the )?weather(?: like)? (?:in|at) ([\w\s]+)(?:\?)?",
        (["Fetching weather data..."], weather_callback)
    ],
    
    # Help and capabilities
    [
        r"(?:help|what can you do|your abilities)\??",
        ["I can chat with you about various topics, remember your name and preferences, check weather, and even change my name if you'd like!",
         "I'm a chatbot that can have conversations, remember your details, check weather forecasts, and respond to basic queries.",
         "I can remember your name and preferences, tell you the weather, and chat with you about various topics!"]
    ],
    
    # Exit commands
    [
        r"(?:quit|exit|bye|goodbye)",
        ["Goodbye! Have a great day!", "See you later!", "Until next time!"]
    ],
    
    # Fallback response
    [
        r"(.*)",
        [
            "I'm not sure I understand. Could you rephrase that?", 
            "Interesting. Tell me more about that.", 
            "I'm still learning. Can you elaborate?",
            "I don't quite follow. Could you explain differently?",
            "That's a new one for me. Can you say more about it?",
            "I'm trying to understand what you mean. Could you provide more details?",
            "That's interesting! Could you tell me more?",
            "I'm not quite sure what you mean by that.",
            "Could you try explaining that in a different way?"
        ]
    ],
    [
        r"(?:set|change|make) (?:your|the) (?:personality|tone|style) (?:to )?(formal|casual|humorous|friendly|professional)",
        (["I'll adjust my conversation style to be more %1. Is this better?",
        "I've changed my style to %1 mode. Let me know if you prefer something else.",
        "I'll try to be more %1 in our conversations now."],
        lambda groups: set_user_personality_preference("default_user", groups[0]) if groups else None)
    ],
    ]
]

def simple_chatbot():
    """Run the chatbot in console mode"""
    try:
        chat = ImprovedChat(pairs, reflections, bot_name)
        chat.converse()
    except Exception as e:
        logger.error(f"Fatal error in simple_chatbot: {e}")
        print("Sorry, the chatbot encountered a critical error and needs to shutdown.")

if __name__ == "__main__":
    simple_chatbot()