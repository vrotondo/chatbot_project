# app.py
from flask import Flask, request, jsonify, render_template, send_file
from chatbot.chatbot import ImprovedChat, pairs, reflections, bot_name, get_user_info, store_user_info
import os
import tempfile
import logging

# Set up optional imports for voice recognition
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_ENABLED = True
except ImportError:
    VOICE_ENABLED = False
    logging.warning("Speech recognition libraries not installed. Voice features will be disabled.")

app = Flask(__name__)

# Initialize the chatbot
chatbot = ImprovedChat(pairs, reflections, bot_name)
chatbot.set_user_id("web_user")  # Set a user ID for the web interface

# Initialize speech recognition if available
if VOICE_ENABLED:
    recognizer = sr.Recognizer()
    
    # Initialize text-to-speech engine
    tts_engine = pyttsx3.init()
    tts_engine.setProperty('rate', 175)  # Adjust speech rate

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

if __name__ == '__main__':
    app.run(debug=True)