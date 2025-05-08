import json
import nltk
from nltk.chat.util import Chat, reflections
import re

class FixedChat(Chat):
    def respond(self, str):
        # Override to prevent automatic % wildcard processing
        response = super().respond(str)
        if response and '%' in response:
            # Only process wildcards if the pattern actually has groups
            for pattern, responses in self._pairs:
                match = re.match(pattern, str, re.IGNORECASE)
                if match:
                    return super()._wildcards(response, match)
        return response

    def converse(self, quit="quit"):
        while True:
            user_input = input("> ")
            if user_input.lower() == quit:
                print("Goodbye!")
                break
            response = None
            for pattern, responses in self._pairs:
                if isinstance(responses, tuple):  # Handle custom callbacks
                    responses, callback = responses
                    match = pattern.match(user_input)
                    if match:
                        response = self._wildcards(responses[0], match)
                        callback(match.groups())
                        break
                else:
                    match = pattern.match(user_input)
                    if match:
                        response = self._wildcards(responses[0], match)
                        break
            if response:
                print(response)
            else:
                print("I didn't understand that.")


def load_name():
    try:
        with open("config.json", "r") as f:
            return json.load(f).get("bot_name", "Wicked")
    except (FileNotFoundError, json.JSONDecodeError):
        return "Wicked"

def save_name_and_update(new_name):
    global bot_name
    bot_name = new_name
    save_name(new_name)

bot_name = load_name()

# Define chatbot responses - FINAL WORKING VERSION
pairs = [
    [
        r"my name is (.*)",
        ["Hello %1! How can I help you today?"]
    ],
    [
        r"what is your name\??",
        [f"I'm {bot_name}, your swell-as-hell AI companion! 🌟",
         f"Call me {bot_name}—your guide to the darkness of socializing!"]
    ],
    [
        r"who are you\??",
        [f"I'm {bot_name}, a chatbot with a passion for defying gravity!"]
    ],
    [
        r"how are you ?",
        ["I'm doing well!", "Functioning properly!"]
    ],
    [
        r"call you (.*)",
        (["Sure, I'll answer to %1 from now on!",
          "I love the name %1! Let's chat."],
         lambda matches: save_name_and_update(matches[0]))  # Callback
    ],
    [
        r"how did you get your name\??",
        [f"My creator named me {bot_name} because I have an edge! ✨"]
    ],
    [
        fr"(?i){re.escape(bot_name)}, (.*)",
        ["Ah, you summoned me! About '%1'..."]
    ],
    [
        r"quit",
        ["Goodbye!", "See you later!"]
    ],
    [
        r"(.*)",
        ["I'm not sure I understand.", "Interesting! Tell me more."]
    ]
]

def load_name():
    try:
        with open("config.json", "r") as f:
            return json.load(f).get("bot_name", "Wicked")
    except FileNotFoundError:
        print("Warning: config.json not found. Using default bot name.")
        return "Wicked"
    except json.JSONDecodeError:
        print("Warning: config.json is corrupted. Using default bot name.")
        return "Wicked"

def simple_chatbot():
    print(f"Hi! I'm {bot_name}, your chatbot. Type 'quit' to exit.")
    chat = FixedChat(pairs, reflections)
    chat.converse()

if __name__ == "__main__":
    simple_chatbot()