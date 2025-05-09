# app.py
from flask import Flask, request, jsonify, render_template
from chatbot.chatbot import ImprovedChat, pairs, reflections, bot_name, get_user_info, store_user_info

app = Flask(__name__)

# Initialize the chatbot
chatbot = ImprovedChat(pairs, reflections, bot_name)
chatbot.set_user_id("web_user")  # Set a user ID for the web interface

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

if __name__ == '__main__':
    app.run(debug=True)