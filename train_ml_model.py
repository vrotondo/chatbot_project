# train_ml_model.py
# Script to train the machine learning model for the chatbot

import os
import sys
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("chatbot_trainer")

def main():
    """Train the chatbot ML model"""
    
    logger.info("Starting chatbot ML model training")
    
    # Ensure chatbot module is in path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.append(script_dir)
    
    # First, set up the NLTK data path
    nltk_data_dir = os.path.join(script_dir, "nltk_data")
    if os.path.exists(nltk_data_dir):
        import nltk
        if nltk_data_dir not in nltk.data.path:
            nltk.data.path.insert(0, nltk_data_dir)
        logger.info(f"Added NLTK data path: {nltk_data_dir}")
        
        # Check for installation marker
        if os.path.exists(os.path.join(nltk_data_dir, 'NLTK_INSTALLED')):
            logger.info("NLTK data installation verified")
        else:
            logger.warning("NLTK data directory exists but may not be complete")
            logger.warning("Consider running download_nltk_data.py again")
    else:
        logger.error(f"NLTK data directory not found at: {nltk_data_dir}")
        logger.error("Please run the download_nltk_data.py script first:")
        logger.error("python download_nltk_data.py")
        return 1
    
    try:
        # Import ML engine
        from chatbot.ml_engine import intent_classifier, create_sample_training_data
        
        # Check if we need to create sample data
        data_dir = os.path.join(script_dir, "data")
        training_data_path = os.path.join(data_dir, "intent_training_data.json")
        
        if not os.path.exists(training_data_path):
            logger.info("Training data not found, creating sample data")
            create_sample_training_data()
        else:
            logger.info(f"Found existing training data at {training_data_path}")
            
            # Check the data format
            try:
                with open(training_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Training data contains {len(data)} examples")
            except Exception as e:
                logger.error(f"Error checking training data: {e}")
                logger.info("Creating new sample data")
                create_sample_training_data()
        
        # Train the model
        logger.info("Training intent classifier model")
        start_time = datetime.now()
        results = intent_classifier.train()
        duration = (datetime.now() - start_time).total_seconds()
        
        if "error" in results:
            logger.error(f"Training failed: {results['error']}")
            return 1
            
        # Log results
        logger.info(f"Model trained successfully in {duration:.2f} seconds")
        logger.info(f"Accuracy: {results['accuracy']:.4f}")
        logger.info(f"Best parameters: {results['best_params']}")
        
        # Test the model
        test_messages = [
            "hi there",
            "what's the weather in New York",
            "bye for now",
            "thanks a lot",
            "what's your name",
            "my name is John",
            "what can you do"
        ]
        
        logger.info("\nTesting model with sample messages:")
        for message in test_messages:
            prediction = intent_classifier.predict(message)
            logger.info(f"Message: '{message}'")
            logger.info(f"Intent: {prediction['intent']} (confidence: {prediction['confidence']:.2f})")
            logger.info("---")
            
        return 0
        
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.error("Make sure you have scikit-learn and nltk installed")
        return 1
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())