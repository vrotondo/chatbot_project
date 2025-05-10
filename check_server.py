# check_server.py
# A simple script to test if the server is running and accessible

import socket
import subprocess
import sys
import os
import time
import webbrowser

def check_port(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def main():
    """Check if the Flask server is running and try to start it if not"""
    print("Checking if Flask server is running...")
    
    # Check common ports
    ports_to_check = [5000, 5001, 8080, 8000]
    found_port = None
    
    for port in ports_to_check:
        if check_port(port):
            print(f"✅ Found server running on port {port}")
            found_port = port
            break
    
    if found_port:
        print(f"Opening browser to http://127.0.0.1:{found_port}/")
        webbrowser.open(f"http://127.0.0.1:{found_port}/")
        return 0
    
    print("❌ No Flask server detected on common ports.")
    
    # Try to start the server
    start_server = input("Would you like to start the Flask server? (y/n): ")
    if start_server.lower() != 'y':
        print("Exiting without starting server.")
        return 1
    
    # Check if app.py exists
    if not os.path.exists('app.py'):
        print("❌ Error: app.py not found in the current directory.")
        print("Please run this script from your project's root directory.")
        return 1
    
    print("Starting Flask server...")
    try:
        # Start the Flask app in a new process
        process = subprocess.Popen([sys.executable, 'app.py'], 
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  universal_newlines=True)
        
        # Wait for server to start (up to 10 seconds)
        for _ in range(10):
            print("Waiting for server to start...")
            time.sleep(1)
            
            # Check if any port is now available
            for port in ports_to_check:
                if check_port(port):
                    print(f"✅ Server started successfully on port {port}")
                    found_port = port
                    break
            
            if found_port:
                break
        
        if found_port:
            print(f"Opening browser to http://127.0.0.1:{found_port}/")
            webbrowser.open(f"http://127.0.0.1:{found_port}/")
            
            # Keep showing server output
            print("\nServer output (press Ctrl+C to exit):")
            try:
                while True:
                    output = process.stdout.readline()
                    if output:
                        print(output.strip())
                    if process.poll() is not None:
                        break
            except KeyboardInterrupt:
                print("\nStopping server...")
                process.terminate()
                
            return 0
        else:
            print("❌ Server didn't start properly. Check the output:")
            output, error = process.communicate(timeout=5)
            print("Output:", output)
            print("Error:", error)
            return 1
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())