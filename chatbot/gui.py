from tkinter import Tk, Label, Button, Entry, Text, END
from .chatbot import pairs, reflections
from nltk.chat.util import Chat

def run_gui():
    chat = Chat(pairs, reflections)
    
    root = Tk()
    root.title("ChatBot GUI")
    
    # Chat display
    chat_log = Text(root, height=20, width=50)
    chat_log.pack()
    
    # User input
    user_input = Entry(root, width=50)
    user_input.pack()
    
    def send_message():
        message = user_input.get()
        chat_log.insert(END, f"You: {message}\n")
        user_input.delete(0, END)
        response = chat.respond(message)
        chat_log.insert(END, f"Bot: {response}\n")
    
    Button(root, text="Send", command=send_message).pack()
    root.mainloop()

if __name__ == "__main__":
    run_gui()