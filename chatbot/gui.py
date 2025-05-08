import tkinter as tk
from tkinter import scrolledtext, Entry, Button, END, Frame
import threading
import queue
import logging
from .chatbot import ImprovedChat, pairs, reflections, bot_name, get_user_info

# Set up logging
logger = logging.getLogger("chatbot.gui")

class ChatbotGUI:
    def __init__(self, root):
        try:
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
            self.chatbot.set_user_id("gui_user")  # Set a specific user ID for the GUI
            
            # Message queue for thread-safe operations
            self.msg_queue = queue.Queue()
            
            # Welcome message
            user_name = get_user_info("gui_user", "name")
            if user_name:
                welcome_msg = f"Welcome back, {user_name}! How can I help you today?"
            else:
                welcome_msg = f"Hi! I'm {bot_name}. I can remember things about you and check the weather.\nTry telling me your name or asking about the weather!"
            
            self.display_bot_message(welcome_msg)
            
            # Start checking the message queue
            self.check_messages()
            
            # Focus on the input field
            self.user_input.focus()
            
            # Set up error handling for GUI window
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            logger.info("GUI initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing GUI: {e}")
            try:
                # Display error message in GUI if possible
                self.display_bot_message(f"Error initializing chat interface. Please restart the application.")
            except:
                # Fall back to console if GUI not available
                print("Error initializing chat interface. Please restart the application.")
    
    def send_message(self):
        """Get user input and process it"""
        try:
            user_message = self.user_input.get().strip()
            if not user_message:
                return
            
            # Clear input field
            self.user_input.delete(0, END)
            
            # Display user message
            self.display_user_message(user_message)
            
            # Process in a separate thread to keep GUI responsive
            threading.Thread(target=self.process_message, args=(user_message,), daemon=True).start()
            
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            self.display_bot_message("I had trouble processing your message. Please try again.")
    
    def process_message(self, message):
        """Process the user message and get bot response"""
        try:
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
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.msg_queue.put("I encountered an error while processing your message. Please try again.")
    
    def update_bot_name(self):
        """Update the GUI with the current bot name"""
        try:
            # Update window title with new name
            self.root.after(0, lambda: self.root.title(f"Chat with {self.chatbot.bot_name}"))
        except Exception as e:
            logger.error(f"Error updating bot name in GUI: {e}")
    
    def display_user_message(self, message):
        """Display user message in the chat log"""
        try:
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
        except Exception as e:
            logger.error(f"Error displaying user message: {e}")
            # Try to recover by showing an error message
            try:
                self.chat_log.config(state=tk.NORMAL)
                self.chat_log.insert(tk.END, "\n[Error displaying message]")
                self.chat_log.config(state=tk.DISABLED)
                self.chat_log.see(tk.END)
            except:
                pass  # Last resort - silently fail if even error message can't be shown
    
    def display_bot_message(self, message):
        """Display bot message in the chat log"""
        try:
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
        except Exception as e:
            logger.error(f"Error displaying bot message: {e}")
            # Try to recover
            try:
                self.chat_log.config(state=tk.NORMAL)
                self.chat_log.insert(tk.END, "\n[Error displaying response]")
                self.chat_log.config(state=tk.DISABLED)
                self.chat_log.see(tk.END)
            except:
                pass  # Last resort - silently fail if even error message can't be shown
    
    def check_messages(self):
        """Check for messages in the queue and display them"""
        try:
            # Process all messages in the queue
            while not self.msg_queue.empty():
                try:
                    message = self.msg_queue.get_nowait()
                    self.display_bot_message(message)
                    self.msg_queue.task_done()
                except queue.Empty:
                    break
                except Exception as e:
                    logger.error(f"Error processing message from queue: {e}")
        except Exception as e:
            logger.error(f"Error in check_messages: {e}")
        finally:
            # Always schedule the next check, even if there was an error
            try:
                self.root.after(100, self.check_messages)
            except Exception as e:
                logger.error(f"Could not schedule next message check: {e}")
    
    def on_closing(self):
        """Handle window close event"""
        try:
            # Any cleanup needed before closing
            logger.info("Chat GUI closing")
            self.root.destroy()
        except Exception as e:
            logger.error(f"Error during GUI shutdown: {e}")
            # Force exit if normal shutdown fails
            try:
                self.root.destroy()
            except:
                pass

def run_gui():
    """Run the chatbot GUI with error handling"""
    try:
        logger.info("Starting chatbot GUI")
        root = tk.Tk()
        app = ChatbotGUI(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Critical error in GUI: {e}")
        print(f"Error starting GUI: {e}")
        # Try to show a simple error dialog if Tk is initialized
        try:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Chatbot Error", f"Error starting chatbot: {e}")
        except:
            pass  # Fall back to the console error already printed

if __name__ == "__main__":
    run_gui()