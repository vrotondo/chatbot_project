import random
import nltk
from nltk.chat.util import Chat, reflections

# Define chatbot responses
pairs = [
    [
        r"my name is (.*)",
        ["Hello %1! How can I help you today?",]
    ],
    [
        r"what is your name?",
        ["I'm a simple chatbot. You can call me Chatty!",]
    ],
    [
        r"how are you ?",
        ["I'm doing well, thanks for asking!", "I'm just a program, but I'm functioning properly!",]
    ],
    [
        r"(.*) (help|support)(.*)",
        ["I can try to help. What do you need assistance with?",]
    ],
    [
        r"(.*) (weather|temperature)(.*)",
        ["I'm sorry, I don't have real-time weather data.",]
    ],
    [
        r"quit",
        ["Goodbye! It was nice chatting with you.", "See you later!"]
    ],
    [
        r"(.*)",
        ["I'm not sure I understand. Could you rephrase that?", 
        "Interesting! Tell me more."]
    ]
]

def simple_chatbot():
    print("Hi! I'm a simple chatbot. Type 'quit' to end our conversation.")
    chat = Chat(pairs, reflections)
    chat.converse()

if __name__ == "__main__":
    simple_chatbot()