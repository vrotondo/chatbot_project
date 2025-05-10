# app.py
from flask import Flask, request, jsonify, render_template, send_file
from chatbot.chatbot import ImprovedChat, pairs, reflections, bot_name, get_user_info, store_user_info
import os
import tempfile
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Conditionally import voice libraries
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_ENABLED = True
    logger.info("Voice libraries successfully imported. Server-side voice features enabled.")
except ImportError:
    VOICE_ENABLED = False
    logger.warning("Voice libraries (speech_recognition, pyttsx3) not available. "
                  "Server-side voice features will be disabled, but browser-based "
                  "voice interaction will still work.")

app = Flask(__name__)

# Initialize the chatbot
chatbot = ImprovedChat(pairs, reflections, bot_name)
chatbot.set_user_id("web_user")  # Set a user ID for the web interface

# Initialize speech recognition if available
if VOICE_ENABLED:
    try:
        recognizer = sr.Recognizer()
        
        # Initialize text-to-speech engine
        tts_engine = pyttsx3.init()
        tts_engine.setProperty('rate', 175)  # Adjust speech rate
        logger.info("Voice engines initialized successfully")
    except Exception as e:
        VOICE_ENABLED = False
        logger.error(f"Failed to initialize voice engines: {e}")
        logger.warning("Voice features will be disabled")

@app.route('/')
def home():
    """Render the chat interface"""
    return render_template('index.html', bot_name=bot_name)

@app.route('/chat', methods=['POST'])
def chat():
    """Process chat messages and return responses"""
    if not request.json or 'message' not in request.json:
        return jsonify({'error': 'No message provided'}), 400
    
    user_message = request.json['message']
    
    # Extract user ID if provided
    user_id = request.json.get('user_id', 'web_user')
    chatbot.set_user_id(user_id)
    
    # Process the message and get response
    response = chatbot.respond(user_message)
    
    # Return JSON response
    return jsonify({
        'response': response,
        'bot_name': chatbot.bot_name
    })

@app.route('/remember', methods=['POST'])
def remember():
    """Store user information"""
    if not request.json or 'key' not in request.json or 'value' not in request.json:
        return jsonify({'error': 'Missing key or value'}), 400
    
    user_id = request.json.get('user_id', 'web_user')
    key = request.json['key']
    value = request.json['value']
    
    success = store_user_info(user_id, key, value)
    
    return jsonify({'success': success})

@app.route('/recall', methods=['GET'])
def recall():
    """Retrieve user information"""
    if 'key' not in request.args:
        return jsonify({'error': 'No key provided'}), 400
    
    user_id = request.args.get('user_id', 'web_user')
    key = request.args.get('key')
    
    value = get_user_info(user_id, key)
    
    return jsonify({'value': value})

@app.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    """
    Convert speech audio to text using server-side recognition
    Note: This is an alternative to client-side Web Speech API
    """
    if not VOICE_ENABLED:
        return jsonify({'error': 'Speech recognition not available on server'}), 503
    
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    
    try:
        # Save the uploaded audio to a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        audio_file.save(temp_file.name)
        temp_file.close()
        
        # Process the audio file
        with sr.AudioFile(temp_file.name) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            
            # Clean up the temporary file
            os.unlink(temp_file.name)
            
            return jsonify({'text': text})
    
    except sr.UnknownValueError:
        return jsonify({'error': 'Could not understand audio'}), 400
    
    except sr.RequestError as e:
        return jsonify({'error': f'Speech service error: {str(e)}'}), 500
    
    except Exception as e:
        return jsonify({'error': f'Error processing audio: {str(e)}'}), 500
    
    finally:
        # Ensure the temp file is deleted
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    """
    Convert text to speech and return audio file
    Note: This is an alternative to client-side Web Speech API
    """
    if not VOICE_ENABLED:
        return jsonify({'error': 'Text-to-speech not available on server'}), 503
    
    if not request.json or 'text' not in request.json:
        return jsonify({'error': 'No text provided'}), 400
    
    text = request.json['text']
    
    try:
        # Create a temporary file for the audio
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_file.close()
        
        # Generate speech audio
        tts_engine.save_to_file(text, temp_file.name)
        tts_engine.runAndWait()
        
        # Send the file
        return send_file(
            temp_file.name,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name='response.mp3'
        )
    
    except Exception as e:
        return jsonify({'error': f'Error generating speech: {str(e)}'}), 500
    
    finally:
        # Schedule cleanup for after the file is sent
        @app.after_request
        def cleanup(response):
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            return response
        
@app.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    Endpoint for collecting user feedback on chatbot responses
    
    Request JSON format:
    {
        "message": "user's original message",
        "response": "chatbot's response",
        "quality": "good", "bad", or "neutral",
        "user_id": "optional user ID"
    }
    """
    if not request.json:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    # Extract required fields
    message = request.json.get('message')
    response = request.json.get('response')
    quality = request.json.get('quality')
    user_id = request.json.get('user_id', 'web_user')
    
    # Validate fields
    if not message or not response or not quality:
        return jsonify({'error': 'Missing required fields'}), 400
        
    if quality not in ['good', 'bad', 'neutral']:
        return jsonify({'error': 'Quality must be "good", "bad", or "neutral"'}), 400
    
    # Try to get intent from ML system
    intent = None
    try:
        from chatbot.ml_integration import classify_intent
        prediction = classify_intent(message)
        if prediction and 'intent' in prediction:
            intent = prediction['intent']
    except:
        # If ML integration fails, continue without intent
        pass
    
    # Store the feedback
    try:
        from chatbot.feedback_system import store_feedback
        success = store_feedback(
            user_input=message,
            response=response,
            quality=quality,
            intent=intent,
            user_id=user_id
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Feedback stored'})
        else:
            return jsonify({'error': 'Failed to store feedback'}), 500
            
    except ImportError:
        return jsonify({'error': 'Feedback system not available'}), 501
        
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

if __name__ == '__main__':
    # Try different ports if the default port is unavailable
    ports = [5000, 5001, 8080, 8000]
    
    for port in ports:
        try:
            print(f"Starting Flask server on port {port}...")
            # Set host to '0.0.0.0' to make it accessible from other devices on your network
            # Or use '127.0.0.1' for local-only access
            app.run(host='127.0.0.1', port=port, debug=True)
            # If we get here, the app started successfully
            break
        except OSError as e:
            print(f"Port {port} is in use, trying another port...")
    else:
        print("Could not find an available port. Please check your system and try again.")