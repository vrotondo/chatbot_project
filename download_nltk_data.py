# download_nltk_data.py
import nltk
import sys
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("nltk_downloader")

def download_nltk_data():
    """Download all required NLTK data packages"""
    required_packages = [
        'punkt',
        'wordnet',
        'stopwords',
        'averaged_perceptron_tagger',
        'maxent_ne_chunker',
        'words'
    ]
    
    # Create a custom download directory in the project folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    nltk_data_dir = os.path.join(script_dir, "nltk_data")
    os.makedirs(nltk_data_dir, exist_ok=True)
    
    logger.info(f"Downloading NLTK data to: {nltk_data_dir}")
    
    # Set the download directory
    nltk.data.path.append(nltk_data_dir)
    
    success = True
    for package in required_packages:
        logger.info(f"Downloading {package}...")
        try:
            nltk.download(package, download_dir=nltk_data_dir, quiet=False)
            logger.info(f"Successfully downloaded {package}")
        except Exception as e:
            logger.error(f"Failed to download {package}: {e}")
            success = False
    
    if success:
        logger.info("All NLTK data packages downloaded successfully!")
        
        # Add a verification step
        logger.info("Verifying installations...")
        for package in required_packages:
            try:
                nltk.data.find(f"{package}")
                logger.info(f"✅ {package} is available")
            except LookupError:
                logger.error(f"❌ {package} could not be verified")
                success = False
        
        if success:
            logger.info("All packages verified! NLTK setup complete.")
        else:
            logger.error("Some packages could not be verified. See errors above.")
    else:
        logger.error("Some packages failed to download. See errors above.")
    
    return success

if __name__ == "__main__":
    print("Downloading required NLTK data packages...")
    
    if download_nltk_data():
        print("\nNLTK data download complete! You can now train the ML model.")
        sys.exit(0)
    else:
        print("\nSome NLTK data packages failed to download. Please check the logs.")
        print("You can try running this script again with administrator privileges.")
        sys.exit(1)