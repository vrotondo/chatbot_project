# voice_demo.py
# A demonstration script showing how to use speech recognition and speech synthesis
# with the chatbot (for reference and testing purposes)

import speech_recognition as sr
import pyttsx3
from chatbot.chatbot import ImprovedChat, pairs, reflections, bot_name

def main():
    """
    Run a voice-enabled version of the chatbot in console mode
    """
    print(f"Starting voice-enabled chatbot - {bot_name}")
    print("Say 'quit' or 'exit' to end the conversation")

    # Initialize chatbot
    chatbot = ImprovedChat(pairs, reflections, bot_name)
    chatbot.set_user_id("voice_user")

    # Initialize speech recognition
    recognizer = sr.Recognizer()
    
    # Initialize text-to-speech engine
    engine = pyttsx3.init()
    # Adjust speech rate (default is 200)
    engine.setProperty('rate', 175)
    
    # Say welcome message
    welcome_msg = f"Hello! I'm {bot_name}. How can I help you today?"
    print(f"{bot_name}: {welcome_msg}")
    engine.say(welcome_msg)
    engine.runAndWait()
    
    # Main conversation loop
    while True:
        # Get user input via microphone
        try:
            with sr.Microphone() as source:
                print("\nListening...")
                
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen for user input
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                
                print("Processing speech...")
                try:
                    # Recognize speech using Google Speech Recognition
                    user_input = recognizer.recognize_google(audio)
                    print(f"You: {user_input}")
                    
                    # Check for exit command
                    if user_input.lower() in ["quit", "exit", "bye", "goodbye"]:
                        farewell = "Goodbye! Have a great day!"
                        print(f"{bot_name}: {farewell}")
                        engine.say(farewell)
                        engine.runAndWait()
                        break
                    
                    # Get chatbot response
                    response = chatbot.respond(user_input)
                    print(f"{bot_name}: {response}")
                    
                    # Read response aloud
                    engine.say(response)
                    engine.runAndWait()
                    
                except sr.UnknownValueError:
                    error_msg = "Sorry, I couldn't understand what you said. Could you try again?"
                    print(f"{bot_name}: {error_msg}")
                    engine.say(error_msg)
                    engine.runAndWait()
                    
                except sr.RequestError as e:
                    error_msg = f"Sorry, there was an error with the speech service: {e}"
                    print(f"{bot_name}: {error_msg}")
                    engine.say("Sorry, there was an error with the speech service.")
                    engine.runAndWait()
                    
        except KeyboardInterrupt:
            print("\nDetected keyboard interrupt. Exiting...")
            farewell = "Goodbye! Have a great day!"
            print(f"{bot_name}: {farewell}")
            engine.say(farewell)
            engine.runAndWait()
            break
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            continue

if __name__ == "__main__":
    main()