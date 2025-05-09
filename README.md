# chatbot_project
Chatbot coded in Python with multiple interfaces: CLI, GUI, and Web.

## Project Structure:
```
chatbot_project/
├── chatbot/
│   ├── __init__.py
│   ├── chatbot.py  (original CLI version)
│   └── gui.py      (GUI version)
├── templates/
│   └── index.html  (web interface template)
├── app.py          (Flask web server)
├── download_nltk_data.py
├── requirements.txt
├── Procfile
├── venv/
├── config.json
└── memory.json
```

## Setup:

### Local Development:
1. Clone the repository
   ```
   git clone https://github.com/yourusername/chatbot_project.git
   cd chatbot_project
   ```

2. Set up virtual environment
   ```
   python -m venv venv
   ```

3. Activate virtual environment
   - Windows:
     ```
     .\venv\Scripts\Activate.ps1
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install requirements
   ```
   pip install -r requirements.txt
   ```

5. Download NLTK data
   ```
   python download_nltk_data.py
   ```

## Running the Chatbot:

### CLI Version:
```
python -m chatbot.chatbot
```

### GUI Version:
```
python -m chatbot.gui
```

### Web Version:
```
python app.py
```
Then open a browser and go to http://127.0.0.1:5000/

## Web Deployment Options:

### PythonAnywhere:
1. Sign up for a free account at PythonAnywhere
2. Upload your code files through their interface or using GitHub
3. Create a new web app in your dashboard, selecting Flask as the framework
4. Set the path to your app.py file and configure the WSGI file
5. Reload your web app

### Render:
1. Sign up for a free account at Render
2. Push your code to a GitHub repository
3. Create a new Web Service on Render, pointing to your GitHub repository
4. Specify `gunicorn app:app` as the start command
5. Deploy the app

### Railway:
1. Sign up for Railway
2. Connect your GitHub repository
3. Create a new project and select your repository
4. Add necessary environment variables if needed
5. Deploy the app