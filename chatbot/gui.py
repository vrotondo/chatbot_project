import tkinter as tk
from tkinter import scrolledtext, Entry, Button, END, Frame
import threading
import queue
from .chatbot import ImprovedChat, pairs, reflections, bot_name, save_name_and_update

class ChatbotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Chat with {bot_name}")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Set up the chat display
        self.chat_frame = Frame(root)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.chat_log = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, 
                                               height=20, bg="#f9f9f9", font=("Arial", 11))
        self.chat_log.pack(fill=tk.BOTH, expand=True)
        self.chat_log.config(state=tk.DISABLED)
        
        # Set up the input area
        self.input_frame = Frame(root)
        self.input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.user_input = Entry(self.input_frame, font=("Arial", 11))
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.user_input.bind("<Return>", lambda event: self.send_message())
        
        self.send_button = Button(self.input_frame, text="Send", command=self.send_message, 
                               bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        self.send_button.pack(side=tk.RIGHT, padx=5)
        
        # Initialize chatbot
        self.chatbot = ImprovedChat(pairs, reflections, bot_name)
        
        # Message queue for thread-safe operations
        self.msg_queue = queue.Queue()
        
        # Welcome message
        self.display_bot_message(f"Hi! I'm {bot_name}. How can I help you today?\n\nTry asking me about the weather in a city!")
        
        # Start checking the message queue
        self.check_messages()
        
        # Focus on the input field
        self.user_input.focus()
    
    def send_message(self):
        """Get user input and process it"""
        user_message = self.user_input.get().strip()
        if not user_message:
            return
        
        # Clear input field
        self.user_input.delete(0, END)
        
        # Display user message
        self.display_user_message(user_message)
        
        # Process in a separate thread to keep GUI responsive
        threading.Thread(target=self.process_message, args=(user_message,), daemon=True).start()
    
    def process_message(self, message):
        """Process the user message and get bot response"""
        # Check for exit command
        if message.lower() in ["quit", "exit", "bye", "goodbye"]:
            response = "Goodbye! Close the window when you're done."
        else:
            # Get response from chatbot
            response = self.chatbot.respond(message)
            
            # Update bot name for display
            self.update_bot_name()
        
        # Queue bot response for display
        self.msg_queue.put(response)
    
    def update_bot_name(self):
        """Update the GUI with the current bot name"""
        global bot_name
        # Update window title with new name
        self.root.after(0, lambda: self.root.title(f"Chat with {self.chatbot.bot_name}"))
    
    def display_user_message(self, message):
        """Display user message in the chat log"""
        self.chat_log.config(state=tk.NORMAL)
        if self.chat_log.index('end-1c') != '1.0':
            self.chat_log.insert(tk.END, "\n")
        self.chat_log.insert(tk.END, "You: ", "user_tag")
        self.chat_log.insert(tk.END, message)
        self.chat_log.config(state=tk.DISABLED)
        
        # Configure tag
        self.chat_log.tag_config("user_tag", foreground="#0066CC", font=("Arial", 11, "bold"))
        
        # Auto-scroll to bottom
        self.chat_log.see(tk.END)
    
    def display_bot_message(self, message):
        """Display bot message in the chat log"""
        self.chat_log.config(state=tk.NORMAL)
        if self.chat_log.index('end-1c') != '1.0':
            self.chat_log.insert(tk.END, "\n")
        self.chat_log.insert(tk.END, f"{self.chatbot.bot_name}: ", "bot_tag")
        self.chat_log.insert(tk.END, message)
        self.chat_log.config(state=tk.DISABLED)
        
        # Configure tag
        self.chat_log.tag_config("bot_tag", foreground="#CC0000", font=("Arial", 11, "bold"))
        
        # Auto-scroll to bottom
        self.chat_log.see(tk.END)
    
    def check_messages(self):
        """Check for messages in the queue and display them"""
        try:
            while True:
                message = self.msg_queue.get_nowait()
                self.display_bot_message(message)
                self.msg_queue.task_done()
        except queue.Empty:
            # Schedule next check
            self.root.after(100, self.check_messages)

def run_gui():
    """Run the chatbot GUI"""
    root = tk.Tk()
    app = ChatbotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()