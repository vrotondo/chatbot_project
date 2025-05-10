# deploy.py
# Script to deploy the advanced chatbot

import os
import sys
import shutil
import argparse
import subprocess
import logging
import zipfile
import json
import platform
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("deployment.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("deployment")

# Define constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(SCRIPT_DIR, "build")
DIST_DIR = os.path.join(SCRIPT_DIR, "dist")
CONFIG_FILE = os.path.join(SCRIPT_DIR, "deployment_config.json")

# Default configuration
DEFAULT_CONFIG = {
    "app_name": "wicked_chatbot",
    "version": "1.0.0",
    "python_version": "3.9",
    "include_web": True,
    "include_ml": True,
    "include_transformers": True,
    "include_voice": False,
    "deployment_target": "local",  # local, heroku, render, pythonanywhere
    "web_port": 5000,
    "requirements_file": "requirements.txt"
}

def load_config():
    """
    Load deployment configuration
    
    Returns:
        dict: The deployment configuration
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info("Loaded deployment configuration")
                return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    # Create default config if not exists
    logger.info("Creating default deployment configuration")
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """
    Save deployment configuration
    
    Args:
        config (dict): The configuration to save
    """
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    logger.info("Saved deployment configuration")

def clean_build():
    """
    Clean build and dist directories
    """
    for directory in [BUILD_DIR, DIST_DIR]:
        if os.path.exists(directory):
            shutil.rmtree(directory)
            logger.info(f"Removed directory: {directory}")
        
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

def create_requirements(config):
    """
    Create customized requirements file based on configuration
    
    Args:
        config (dict): Deployment configuration
        
    Returns:
        str: Path to the generated requirements file
    """
    # Start with basic requirements
    requirements = [
        "flask==2.0.1",
        "werkzeug==2.0.1",
        "jinja2==3.0.1",
        "gunicorn==20.1.0",
        "requests==2.32.3",
        "nltk==3.9.1"
    ]
    
    # Add ML requirements if included
    if config.get("include_ml", True):
        requirements.extend([
            "scikit-learn==1.3.0",
            "numpy==1.24.3",
            "scipy==1.10.1"
        ])
    
    # Add transformers if included
    if config.get("include_transformers", False):
        requirements.extend([
            "transformers==4.30.2",
            "torch==2.0.1",
            "sentence-transformers==2.2.2"
        ])
    
    # Add voice recognition if included
    if config.get("include_voice", False):
        requirements.extend([
            "SpeechRecognition==3.10.0",
            "pyttsx3==2.90",
            "PyAudio==0.2.13"
        ])
    
    # Add spaCy if included
    if config.get("include_spacy", False):
        requirements.extend([
            "spacy==3.6.1"
        ])
    
    # Add deployment-specific requirements
    target = config.get("deployment_target", "local")
    if target == "heroku":
        requirements.append("psycopg2-binary==2.9.6")  # For PostgreSQL
    elif target == "pythonanywhere":
        requirements.append("mysql-connector-python==8.0.33")  # For MySQL
    
    # Write to file
    requirements_path = os.path.join(BUILD_DIR, "requirements.txt")
    with open(requirements_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(requirements))
    
    logger.info(f"Created requirements file: {requirements_path}")
    return requirements_path

def copy_project_files(config):
    """
    Copy project files to build directory
    
    Args:
        config (dict): Deployment configuration
    """
    # Core files to always include
    core_files = [
        "config.json",
        "memory.json",
        "app.py"
    ]
    
    # Directories to copy
    directories = [
        "chatbot",
        "templates",
        "data"
    ]
    
    # Copy core files
    for file in core_files:
        src = os.path.join(SCRIPT_DIR, file)
        if os.path.exists(src):
            dst = os.path.join(BUILD_DIR, file)
            shutil.copy2(src, dst)
            logger.info(f"Copied file: {file}")
    
    # Copy directories
    for directory in directories:
        src = os.path.join(SCRIPT_DIR, directory)
        if os.path.exists(src):
            dst = os.path.join(BUILD_DIR, directory)
            shutil.copytree(src, dst, dirs_exist_ok=True)
            logger.info(f"Copied directory: {directory}")
    
    # Create additional files as needed
    create_procfile(config)
    create_wsgi_file(config)
    create_runtime_file(config)
    create_gitignore()
    
    logger.info("Finished copying project files")

def create_procfile(config):
    """
    Create Procfile for Heroku deployment
    
    Args:
        config (dict): Deployment configuration
    """
    if config.get("deployment_target") == "heroku":
        procfile_path = os.path.join(BUILD_DIR, "Procfile")
        with open(procfile_path, 'w', encoding='utf-8') as f:
            f.write("web: gunicorn app:app")
        logger.info("Created Procfile for Heroku")

def create_wsgi_file(config):
    """
    Create WSGI file for PythonAnywhere deployment
    
    Args:
        config (dict): Deployment configuration
    """
    if config.get("deployment_target") == "pythonanywhere":
        wsgi_path = os.path.join(BUILD_DIR, "flask_app.py")
        app_name = config.get("app_name", "wicked_chatbot")
        
        wsgi_content = f"""
# flask_app.py - PythonAnywhere WSGI configuration

import sys
import os

# Add the application directory to the Python path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Import the Flask application
from app import app as application
"""
        with open(wsgi_path, 'w', encoding='utf-8') as f:
            f.write(wsgi_content.strip())
        logger.info("Created WSGI file for PythonAnywhere")

def create_runtime_file(config):
    """
    Create runtime.txt for Heroku deployment
    
    Args:
        config (dict): Deployment configuration
    """
    if config.get("deployment_target") == "heroku":
        runtime_path = os.path.join(BUILD_DIR, "runtime.txt")
        python_version = config.get("python_version", "3.9")
        
        with open(runtime_path, 'w', encoding='utf-8') as f:
            f.write(f"python-{python_version}")
        logger.info(f"Created runtime.txt with Python {python_version}")

def create_gitignore():
    """
    Create .gitignore file for deployment
    """
    gitignore_path = os.path.join(BUILD_DIR, ".gitignore")
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS specific
.DS_Store
Thumbs.db

# Application specific
*.log
nltk_data/
**/__pycache__/
*.pkl
"""
    with open(gitignore_path, 'w', encoding='utf-8') as f:
        f.write(gitignore_content.strip())
    logger.info("Created .gitignore file")

def create_archive():
    """
    Create a deployment archive
    
    Returns:
        str: Path to the created archive
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create a zip file
    zip_path = os.path.join(DIST_DIR, f"chatbot_deployment_{timestamp}.zip")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BUILD_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, BUILD_DIR)
                zipf.write(file_path, arcname)
    
    logger.info(f"Created deployment archive: {zip_path}")
    return zip_path

def deploy_local(config):
    """
    Deploy locally for testing
    
    Args:
        config (dict): Deployment configuration
    """
    logger.info("Starting local deployment test")
    
    # Create a virtual environment
    venv_dir = os.path.join(BUILD_DIR, "venv")
    
    if platform.system() == "Windows":
        python_exe = sys.executable
        subprocess.run([python_exe, "-m", "venv", venv_dir], check=True)
        pip_exe = os.path.join(venv_dir, "Scripts", "pip.exe")
        python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        python_exe = sys.executable
        subprocess.run([python_exe, "-m", "venv", venv_dir], check=True)
        pip_exe = os.path.join(venv_dir, "bin", "pip")
        python_exe = os.path.join(venv_dir, "bin", "python")
    
    # Install requirements
    requirements_path = os.path.join(BUILD_DIR, "requirements.txt")
    subprocess.run([pip_exe, "install", "-r", requirements_path], check=True)
    
    # Set up NLTK data
    subprocess.run([python_exe, "download_nltk_data.py"], cwd=BUILD_DIR, check=True)
    
    # Test the application
    port = config.get("web_port", 5000)
    
    print(f"\n\n{'='*60}")
    print(f"Local deployment test complete! To run the server:")
    print(f"{'='*60}")
    print(f"1. cd {BUILD_DIR}")
    print(f"2. {os.path.join('venv', 'Scripts' if platform.system() == 'Windows' else 'bin', 'python')} app.py")
    print(f"3. Visit http://localhost:{port} in your browser")
    print(f"{'='*60}\n")

def deploy_heroku(config):
    """
    Deploy to Heroku
    
    Args:
        config (dict): Deployment configuration
    """
    logger.info("Starting Heroku deployment")
    
    app_name = config.get("app_name", "wicked-chatbot")
    
    # Check if Heroku CLI is installed
    try:
        subprocess.run(["heroku", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Heroku CLI not found. Please install it first.")
        print("\nHeroku CLI not found. Please install it from: https://devcenter.heroku.com/articles/heroku-cli")
        return
    
    # Initialize Git repository
    os.chdir(BUILD_DIR)
    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Initial deployment"], check=True)
    
    # Create Heroku app
    try:
        subprocess.run(["heroku", "create", app_name], check=True)
    except subprocess.CalledProcessError:
        # App might already exist
        logger.warning(f"Heroku app '{app_name}' might already exist, trying to deploy anyway")
    
    # Push to Heroku
    subprocess.run(["git", "push", "heroku", "master", "--force"], check=True)
    
    # Open the app
    subprocess.run(["heroku", "open"], check=True)
    
    logger.info(f"Deployed to Heroku: https://{app_name}.herokuapp.com")

def deploy_pythonanywhere(config):
    """
    Deploy to PythonAnywhere
    
    Args:
        config (dict): Deployment configuration
    """
    logger.info("Starting PythonAnywhere deployment preparation")
    
    # Create the deployment archive
    archive_path = create_archive()
    
    print(f"\n\n{'='*60}")
    print(f"PythonAnywhere Deployment Instructions")
    print(f"{'='*60}")
    print(f"1. Log in to your PythonAnywhere account")
    print(f"2. Go to the 'Files' tab")
    print(f"3. Upload the deployment archive: {archive_path}")
    print(f"4. In the 'Consoles' tab, start a Bash console")
    print(f"5. Run: unzip {os.path.basename(archive_path)}")
    print(f"6. In the 'Web' tab, set up a new web app with Flask")
    print(f"7. Set the source code directory to where you unzipped the files")
    print(f"8. Set the WSGI configuration file to point to 'flask_app.py'")
    print(f"9. Click the 'Reload' button to apply changes")
    print(f"{'='*60}\n")

def deploy_render(config):
    """
    Deploy to Render
    
    Args:
        config (dict): Deployment configuration
    """
    logger.info("Starting Render deployment preparation")
    
    # Create render.yaml configuration file
    render_config = {
        "services": [
            {
                "type": "web",
                "name": config.get("app_name", "wicked-chatbot"),
                "env": "python",
                "buildCommand": "pip install -r requirements.txt && python download_nltk_data.py",
                "startCommand": "gunicorn app:app",
                "plan": "free",
                "autoDeploy": True,
                "envVars": [
                    {
                        "key": "PYTHON_VERSION",
                        "value": config.get("python_version", "3.9")
                    }
                ]
            }
        ]
    }
    
    render_config_path = os.path.join(BUILD_DIR, "render.yaml")
    with open(render_config_path, 'w', encoding='utf-8') as f:
        json.dump(render_config, f, indent=2)
    
    logger.info("Created render.yaml configuration file")
    
    # Create the deployment archive
    archive_path = create_archive()
    
    print(f"\n\n{'='*60}")
    print(f"Render Deployment Instructions")
    print(f"{'='*60}")
    print(f"1. Go to Render.com and create an account if you don't have one")
    print(f"2. Click 'New' and select 'Web Service'")
    print(f"3. Connect your GitHub or GitLab repository")
    print(f"4. Select the repository where you've pushed the deployment files")
    print(f"5. Render will automatically detect the configuration and deploy")
    print(f"6. Alternatively, create a GitHub repository with the contents of:")
    print(f"   {BUILD_DIR}")
    print(f"7. Then connect that repository to Render")
    print(f"{'='*60}\n")

def main():
    """Process command line arguments and run deployment"""
    parser = argparse.ArgumentParser(description="Deploy the advanced chatbot")
    
    parser.add_argument(
        "--target", 
        choices=["local", "heroku", "pythonanywhere", "render"],
        default=None,
        help="Deployment target"
    )
    
    parser.add_argument(
        "--name",
        type=str,
        help="Application name"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        help="Web server port (for local deployment)"
    )
    
    parser.add_argument(
        "--python-version",
        type=str,
        help="Python version to use"
    )
    
    parser.add_argument(
        "--no-ml",
        action="store_true",
        help="Exclude machine learning components"
    )
    
    parser.add_argument(
        "--no-transformers",
        action="store_true",
        help="Exclude transformer components"
    )
    
    parser.add_argument(
        "--include-voice",
        action="store_true",
        help="Include voice recognition components"
    )
    
    parser.add_argument(
        "--include-spacy",
        action="store_true",
        help="Include spaCy for advanced entity extraction"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Update configuration with command line arguments
    if args.target:
        config["deployment_target"] = args.target
    
    if args.name:
        config["app_name"] = args.name
    
    if args.port:
        config["web_port"] = args.port
    
    if args.python_version:
        config["python_version"] = args.python_version
    
    if args.no_ml:
        config["include_ml"] = False
    
    if args.no_transformers:
        config["include_transformers"] = False
    
    if args.include_voice:
        config["include_voice"] = True
    
    if args.include_spacy:
        config["include_spacy"] = True
    
    # Save updated configuration
    save_config(config)
    
    # Prepare the deployment
    logger.info(f"Preparing deployment for target: {config['deployment_target']}")
    clean_build()
    create_requirements(config)
    copy_project_files(config)
    
    # Deploy to the target
    if config["deployment_target"] == "local":
        deploy_local(config)
    elif config["deployment_target"] == "heroku":
        deploy_heroku(config)
    elif config["deployment_target"] == "pythonanywhere":
        deploy_pythonanywhere(config)
    elif config["deployment_target"] == "render":
        deploy_render(config)
    else:
        logger.error(f"Unknown deployment target: {config['deployment_target']}")
        sys.exit(1)
    
    logger.info("Deployment complete")

if __name__ == "__main__":
    main()