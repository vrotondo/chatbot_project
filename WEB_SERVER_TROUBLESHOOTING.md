# Web Server Troubleshooting Guide

If you're encountering connection issues with your chatbot web interface, follow this guide to diagnose and resolve them.

## "This site can't be reached" or "Connection Refused"

### 1. Check if the Server is Running

The first thing to check is whether the Flask server is running:

```bash
# Run the server
python app.py
```

You should see output like:
```
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 123-456-789
```

If you don't see this, the server failed to start.

### 2. Check for Port Conflicts

Flask uses port 5000 by default. If another application is using this port, you'll get a connection error.

Run our diagnostic script:
```bash
python check_server.py
```

This will check common ports and help start the server if needed.

### 3. Verify Your URL

Make sure you're using the correct URL:
- Default: `http://127.0.0.1:5000/` or `http://localhost:5000/`
- If using a custom port: `http://127.0.0.1:YOUR_PORT/`

### 4. Check for Firewall Issues

Your firewall might be blocking Flask:

- **Windows**: Check Windows Defender Firewall
- **macOS**: Check System Preferences > Security & Privacy > Firewall
- **Linux**: Check your distro's firewall settings (e.g., `ufw status`)

### 5. Restart with Administrator Privileges

Try running the server as administrator:

- **Windows**: Right-click on Command Prompt and select "Run as administrator"
- **macOS/Linux**: Use `sudo python app.py` (not recommended unless necessary)

### 6. Check Flask Installation

Ensure Flask is properly installed:

```bash
pip install flask
pip list | grep Flask
```

### 7. Check Network Settings

If trying to access from another device:
- Make sure app is running with `host='0.0.0.0'` (check app.py)
- Use your computer's IP address instead of localhost

## Common Error Messages

### "ImportError: No module named flask"

```bash
pip install flask
```

### "Address already in use"

```bash
# Find the process using the port (Linux/macOS)
lsof -i :5000

# Find the process using the port (Windows)
netstat -ano | findstr :5000

# Kill the process
# Linux/macOS: kill [PID]
# Windows: taskkill /PID [PID] /F
```

### "Permission denied" on Linux/macOS

```bash
# Use a port higher than 1024
python app.py --port 8080
```

## Using the Modified app.py

We've updated your app.py to try multiple ports automatically. If port 5000 is unavailable, it will try 5001, 8080, and 8000.

You'll see the actual port in the terminal output when you start the server:
```
Starting Flask server on port 5001...
 * Running on http://127.0.0.1:5001/ (Press CTRL+C to quit)
```

## Complete Server Reset

If all else fails, try a complete reset:

1. Close all terminal windows/command prompts
2. Restart your computer
3. Start the Flask server with the updated app.py
4. Try accessing the web interface again

## Still Having Issues?

1. Check the error logs for more details
2. Try running a minimal Flask application to isolate the problem:

```python
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello World!"

if __name__ == '__main__':
    app.run(debug=True)
```