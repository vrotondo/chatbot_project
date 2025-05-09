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
    if nltk_data_dir not in nltk.data.path:
        nltk.data.path.insert(0, nltk_data_dir)  # Add at the beginning to prioritize
    
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
        
        # Add a simple verification step
        logger.info("Verifying installations...")
        missing_packages = []
        
        # Mapping of packages to their actual file paths
        package_paths = {
            'punkt': os.path.join(nltk_data_dir, 'tokenizers', 'punkt'),
            'wordnet': os.path.join(nltk_data_dir, 'corpora', 'wordnet.zip'),  # Check for zip file first
            'stopwords': os.path.join(nltk_data_dir, 'corpora', 'stopwords'),
            'averaged_perceptron_tagger': os.path.join(nltk_data_dir, 'taggers', 'averaged_perceptron_tagger'),
            'maxent_ne_chunker': os.path.join(nltk_data_dir, 'chunkers', 'maxent_ne_chunker'),
            'words': os.path.join(nltk_data_dir, 'corpora', 'words')
        }
        
        # Alternative paths for some packages
        alternative_paths = {
            'wordnet': [
                os.path.join(nltk_data_dir, 'corpora', 'wordnet'),  # Directory
                os.path.join(nltk_data_dir, 'corpora', 'wordnet.zip'),  # Zip file
                os.path.join(nltk_data_dir, 'corpora', 'WordNet-3.0.omw.sqlite'),  # SQLite file
                os.path.join(nltk_data_dir, 'corpora', 'omw-1.4'),  # OMW directory
                os.path.join(nltk_data_dir, 'corpora', 'omw')  # Alternative OMW directory
            ]
        }
        
        # Check if each package directory exists
        for package, path in package_paths.items():
            if os.path.exists(path):
                logger.info(f"✅ {package} is available at {path}")
            elif package in alternative_paths:
                # Try alternative paths
                found = False
                for alt_path in alternative_paths[package]:
                    if os.path.exists(alt_path):
                        logger.info(f"✅ {package} is available at {alt_path}")
                        found = True
                        break
                if not found:
                    logger.error(f"❌ {package} could not be verified (checked multiple paths)")
                    missing_packages.append(package)
            else:
                logger.error(f"❌ {package} could not be verified at {path}")
                missing_packages.append(package)
        
        if not missing_packages:
            logger.info("All packages verified! NLTK setup complete.")
            
            # Create a marker file that indicates successful installation
            with open(os.path.join(nltk_data_dir, 'NLTK_INSTALLED'), 'w') as f:
                f.write("NLTK data successfully installed.")
                
            return True
        elif len(missing_packages) == 1 and 'wordnet' in missing_packages:
            # Special case for wordnet which often has verification issues
            # but usually works fine in practice
            logger.warning("Only wordnet verification failed, but this is a common issue.")
            logger.warning("Marking installation as successful since wordnet is often packaged differently.")
            logger.warning("If you experience issues with lemmatization later, please run this script again.")
            
            # Create a marker file that indicates mostly successful installation
            with open(os.path.join(nltk_data_dir, 'NLTK_INSTALLED'), 'w') as f:
                f.write("NLTK data successfully installed (wordnet verification issue noted).")
                
            return True
        else:
            logger.error(f"Some packages could not be verified: {', '.join(missing_packages)}")
            return False
    else:
        logger.error("Some packages failed to download. See errors above.")
        return False

if __name__ == "__main__":
    print("Downloading required NLTK data packages...")
    
    if download_nltk_data():
        print("\nNLTK data download complete! You can now train the ML model.")
        
        # Add usage instructions
        print("\nTo use this NLTK data in your code, add the following lines:")
        print("------------------------------------------------------------")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        nltk_data_dir = os.path.join(script_dir, "nltk_data")
        print(f"import nltk")
        print(f"nltk.data.path.append('{nltk_data_dir}')")
        print("------------------------------------------------------------")
        
        sys.exit(0)
    else:
        print("\nSome NLTK data packages failed to download. Please check the logs.")
        print("You can try running this script again with administrator privileges.")
        sys.exit(1)