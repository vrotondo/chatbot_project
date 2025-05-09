# Voice Interaction Setup Guide

This document provides detailed instructions for setting up the voice interaction features of the chatbot.

## Important Note

The web interface uses the browser's Web Speech API for voice recognition and speech synthesis, so it works without additional setup. The server-side voice functionality (used in `voice_demo.py` and optional server-side endpoints) requires additional libraries.

## 1. Installing Required Libraries

### Basic Installation

Run the following command to install the required Python libraries:

```bash
pip install SpeechRecognition pyttsx3 PyAudio
```

### Platform-Specific Setup for PyAudio

PyAudio can sometimes be challenging to install, depending on your platform:

#### Windows
On Windows, PyAudio should install normally using pip. If you encounter issues:

1. Try installing a pre-compiled wheel:
   ```bash
   pip install pipwin
   pipwin install pyaudio
   ```

2. If that fails, download the appropriate `.whl` file for your Python version from:
   https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

   Then install it with:
   ```bash
   pip install path\to\downloaded\PyAudio‑0.2.11‑cp39‑cp39‑win_amd64.whl
   ```

#### macOS
On macOS, you need to install PortAudio first:

1. Using Homebrew:
   ```bash
   brew install portaudio
   pip install pyaudio
   ```

2. If you encounter issues, try:
   ```bash
   brew install --cask anaconda
   conda install pyaudio
   ```

#### Linux (Ubuntu/Debian)
On Linux, you need to install PortAudio and development libraries:

```bash
sudo apt-get update
sudo apt-get install python3-pyaudio
sudo apt-get install portaudio19-dev python-pyaudio python3-pyaudio
pip install pyaudio
```

## 2. Testing Your Setup

After installation, you can verify that the voice libraries are working correctly:

### Testing PyAudio

Run this Python code to check if PyAudio can access your microphone:

```python
import pyaudio
p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
for i in range(0, numdevices):
    if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))
p.terminate()
```

### Testing Speech Recognition

Run this code to test if speech recognition is working:

```python
import speech_recognition as sr
r = sr.Recognizer()
with sr.Microphone() as source:
    print("Say something!")
    audio = r.listen(source)
try:
    print("You said: " + r.recognize_google(audio))
except sr.UnknownValueError:
    print("Google Speech Recognition could not understand audio")
except sr.RequestError as e:
    print("Could not request results from Google Speech Recognition; {0}".format(e))
```

### Testing Text-to-Speech

Run this code to test if text-to-speech is working:

```python
import pyttsx3
engine = pyttsx3.init()
engine.say("This is a test of the text-to-speech engine")
engine.runAndWait()
```

## 3. Troubleshooting

### Common PyAudio Issues

1. **Error: Microsoft Visual C++ 14.0 or greater is required** (Windows)
   - Download and install the Microsoft C++ Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/

2. **Error: Could not find portaudio.h** (macOS/Linux)
   - Make sure you've installed PortAudio as mentioned in the platform-specific instructions above

3. **Error: No Default Input Device Available** (All platforms)
   - Check your microphone is properly connected
   - Make sure it's set as the default input device in your system settings
   - Check microphone permissions for your application

### Speech Recognition Issues

1. **Network-Related Errors**
   - Google Speech Recognition requires an internet connection
   - Check your firewall isn't blocking Python from accessing the internet

2. **API Unavailable**
   - The free tier of Google Speech Recognition has usage limits
   - Try again later or consider using a different recognition engine

## 4. Alternative: Using Only Browser-Based Voice

If you can't get the server-side voice libraries working, you can still use the web interface with browser-based voice capabilities:

1. Run the Flask app without installing the voice libraries:
   ```bash
   python app.py
   ```

2. Open a web browser (Chrome works best) and go to http://127.0.0.1:5000/
3. Use the microphone and speaker buttons in the interface

The browser's Web Speech API handles all the voice processing, so no server-side voice libraries are needed.

## 5. Browser Compatibility for Web Speech API

- **Chrome**: Full support (best option)
- **Edge**: Good support
- **Safari**: Good support
- **Firefox**: Limited support (may require enabling flags)
- **Opera**: Good support
- **Mobile browsers**: Variable support, best on Chrome for Android

## Need More Help?

If you continue to experience issues with voice recognition, please:
1. Check the application logs for specific error messages
2. Ensure your microphone is working with other applications
3. Try the browser-based interface, which is more widely compatible