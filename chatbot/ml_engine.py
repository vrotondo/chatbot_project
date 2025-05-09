# ml_engine.py
# Machine learning module for enhancing chatbot response capabilities

import os
import json
import pickle
import numpy as np
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chatbot.ml")

# Define constants
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
MODEL_PATH = os.path.join(DATA_DIR, "intent_model.pkl")
TRAINING_DATA_PATH = os.path.join(DATA_DIR, "intent_training_data.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

class IntentClassifier:
    """
    A machine learning classifier for determining user intent from messages
    """
    
    def __init__(self):
        """Initialize the intent classifier"""
        self.pipeline = None
        self.classes = []
        self.confidence_threshold = 0.5
        
        # Initialize NLTK resources
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/wordnet')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            logger.info("Downloading required NLTK resources...")
            nltk.download('punkt', quiet=True)
            nltk.download('wordnet', quiet=True)
            nltk.download('stopwords', quiet=True)
            logger.info("NLTK resources downloaded")
        
        # Load existing model if available
        if os.path.exists(MODEL_PATH):
            self.load_model()
        else:
            logger.info("No pre-trained model found. Use train() to create one.")
            
            # Initialize a basic pipeline even without training
            self.pipeline = Pipeline([
                ('vectorizer', TfidfVectorizer(tokenizer=self._tokenize)),
                ('classifier', SVC(probability=True))
            ])
    
    def _tokenize(self, text):
        """
        Process text by tokenizing, removing stopwords, and lemmatizing
        
        Args:
            text (str): Input text to tokenize
            
        Returns:
            list: Processed tokens
        """
        # Convert to lowercase and tokenize
        tokens = word_tokenize(text.lower())
        
        # Get stopwords
        stop_words = set(stopwords.words('english'))
        
        # Initialize lemmatizer
        lemmatizer = WordNetLemmatizer()
        
        # Filter out stopwords and lemmatize remaining tokens
        return [lemmatizer.lemmatize(token) for token in tokens 
                if token.isalpha() and token not in stop_words]
    
    def train(self, X=None, y=None, data_path=None, test_size=0.2):
        """
        Train the intent classifier model
        
        Args:
            X (list, optional): List of training texts
            y (list, optional): List of intent labels
            data_path (str, optional): Path to JSON training data
            test_size (float): Portion of data to use for testing (0.0-1.0)
            
        Returns:
            dict: Training report with metrics
        """
        # Load data from file if not provided directly
        if X is None or y is None:
            if data_path is None:
                data_path = TRAINING_DATA_PATH
                
            if not os.path.exists(data_path):
                logger.error(f"Training data not found at {data_path}")
                return {"error": "Training data not found"}
                
            try:
                with open(data_path, 'r', encoding='utf-8') as f:
                    training_data = json.load(f)
                
                if not isinstance(training_data, list) or not training_data:
                    logger.error("Invalid training data format")
                    return {"error": "Invalid training data format"}
                    
                X = [item.get("text", "") for item in training_data]
                y = [item.get("intent", "") for item in training_data]
                
                logger.info(f"Loaded {len(X)} training examples from {data_path}")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading training data: {e}")
                return {"error": f"Error loading training data: {e}"}
        
        # Ensure we have data
        if not X or not y or len(X) != len(y):
            logger.error("Invalid or mismatched training data")
            return {"error": "Invalid or mismatched training data"}
        
        # Save classes for prediction
        self.classes = sorted(list(set(y)))
        
        if len(self.classes) < 2:
            logger.error("Need at least 2 intent classes for training")
            return {"error": "Need at least 2 intent classes for training"}
            
        logger.info(f"Training model with {len(self.classes)} intent classes")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y)
            
        # Create and configure the pipeline
        self.pipeline = Pipeline([
            ('vectorizer', TfidfVectorizer(
                tokenizer=self._tokenize,
                max_features=5000,
                min_df=2,
                max_df=0.85
            )),
            ('classifier', SVC(
                probability=True,
                kernel='linear',
                C=1,
                class_weight='balanced'
            ))
        ])
        
        # Define parameters for grid search
        param_grid = {
            'vectorizer__max_features': [3000, 5000],
            'classifier__C': [0.1, 1, 10]
        }
        
        # Perform grid search for hyperparameter tuning
        grid_search = GridSearchCV(
            self.pipeline,
            param_grid,
            cv=5,
            scoring='f1_weighted',
            n_jobs=-1,
            verbose=1
        )
        
        # Fit the model
        logger.info("Training intent classifier...")
        grid_search.fit(X_train, y_train)
        self.pipeline = grid_search.best_estimator_
        
        # Evaluate the model
        y_pred = self.pipeline.predict(X_test)
        
        # Generate classification report
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # Log results
        logger.info(f"Best parameters: {grid_search.best_params_}")
        logger.info(f"Model accuracy: {report['accuracy']:.2f}")
        for intent in self.classes:
            if intent in report:
                logger.info(f"Intent '{intent}' F1-score: {report[intent]['f1-score']:.2f}")
        
        # Save the model
        self.save_model()
        
        return {
            "best_params": grid_search.best_params_,
            "accuracy": report["accuracy"],
            "report": report,
            "classes": self.classes
        }
    
    def predict(self, text):
        """
        Predict the intent of a user message
        
        Args:
            text (str): User message text
            
        Returns:
            dict: Prediction results with intent and confidence
        """
        if self.pipeline is None or not self.classes:
            logger.warning("Model not trained yet")
            return {"intent": None, "confidence": 0.0, "error": "Model not trained"}
        
        try:
            # Get intent probabilities
            intent_probs = self.pipeline.predict_proba([text])[0]
            
            # Get highest probability and corresponding intent
            max_idx = np.argmax(intent_probs)
            confidence = intent_probs[max_idx]
            
            # Only return the intent if confidence is above threshold
            if confidence >= self.confidence_threshold:
                intent = self.classes[max_idx]
            else:
                intent = None
            
            # Get top 3 intents for debugging
            top_indices = intent_probs.argsort()[-3:][::-1]
            top_intents = [(self.classes[i], float(intent_probs[i])) for i in top_indices]
            
            return {
                "intent": intent,
                "confidence": float(confidence),
                "top_intents": top_intents
            }
            
        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            return {"intent": None, "confidence": 0.0, "error": str(e)}
    
    def save_model(self, path=None):
        """
        Save the trained model to disk
        
        Args:
            path (str, optional): Path to save the model
            
        Returns:
            bool: Success status
        """
        if self.pipeline is None:
            logger.warning("No model to save")
            return False
            
        if path is None:
            path = MODEL_PATH
        
        try:
            model_data = {
                "pipeline": self.pipeline,
                "classes": self.classes,
                "threshold": self.confidence_threshold
            }
            
            with open(path, 'wb') as f:
                pickle.dump(model_data, f)
                
            logger.info(f"Model saved to {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
    
    def load_model(self, path=None):
        """
        Load a trained model from disk
        
        Args:
            path (str, optional): Path to load the model from
            
        Returns:
            bool: Success status
        """
        if path is None:
            path = MODEL_PATH
            
        if not os.path.exists(path):
            logger.warning(f"Model file not found: {path}")
            return False
            
        try:
            with open(path, 'rb') as f:
                model_data = pickle.load(f)
                
            self.pipeline = model_data.get("pipeline")
            self.classes = model_data.get("classes", [])
            self.confidence_threshold = model_data.get("threshold", 0.5)
            
            logger.info(f"Model loaded from {path} with {len(self.classes)} intent classes")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def set_confidence_threshold(self, threshold):
        """
        Set the confidence threshold for intent prediction
        
        Args:
            threshold (float): Value between 0.0 and 1.0
            
        Returns:
            bool: Success status
        """
        if not 0.0 <= threshold <= 1.0:
            logger.warning(f"Invalid threshold value: {threshold}")
            return False
            
        self.confidence_threshold = threshold
        logger.info(f"Confidence threshold set to {threshold}")
        return True

# Singleton instance for global use
intent_classifier = IntentClassifier()

def create_sample_training_data():
    """
    Create sample training data for the intent classifier
    
    Returns:
        bool: Success status
    """
    sample_data = [
        # Greetings
        {"text": "hello", "intent": "greeting"},
        {"text": "hi there", "intent": "greeting"},
        {"text": "hey", "intent": "greeting"},
        {"text": "good morning", "intent": "greeting"},
        {"text": "good afternoon", "intent": "greeting"},
        {"text": "good evening", "intent": "greeting"},
        {"text": "what's up", "intent": "greeting"},
        {"text": "hello there", "intent": "greeting"},
        {"text": "hi, how are you", "intent": "greeting"},
        {"text": "hey, how's it going", "intent": "greeting"},
        {"text": "howdy", "intent": "greeting"},
        {"text": "nice to meet you", "intent": "greeting"},
        
        # Farewells
        {"text": "goodbye", "intent": "farewell"},
        {"text": "bye", "intent": "farewell"},
        {"text": "see you later", "intent": "farewell"},
        {"text": "see you soon", "intent": "farewell"},
        {"text": "have a good day", "intent": "farewell"},
        {"text": "talk to you later", "intent": "farewell"},
        {"text": "i have to go", "intent": "farewell"},
        {"text": "i'm leaving", "intent": "farewell"},
        {"text": "catch you later", "intent": "farewell"},
        {"text": "until next time", "intent": "farewell"},
        {"text": "good night", "intent": "farewell"},
        
        # Weather queries
        {"text": "what's the weather like", "intent": "weather"},
        {"text": "how's the weather today", "intent": "weather"},
        {"text": "weather forecast", "intent": "weather"},
        {"text": "is it going to rain today", "intent": "weather"},
        {"text": "what's the temperature outside", "intent": "weather"},
        {"text": "how hot is it", "intent": "weather"},
        {"text": "how cold is it", "intent": "weather"},
        {"text": "will it be sunny tomorrow", "intent": "weather"},
        {"text": "check the weather for me", "intent": "weather"},
        {"text": "what's the weather like in new york", "intent": "weather"},
        {"text": "tell me about the weather in chicago", "intent": "weather"},
        {"text": "is it snowing", "intent": "weather"},
        
        # Name queries
        {"text": "what's your name", "intent": "name"},
        {"text": "who are you", "intent": "name"},
        {"text": "what should i call you", "intent": "name"},
        {"text": "tell me your name", "intent": "name"},
        {"text": "do you have a name", "intent": "name"},
        {"text": "what are you called", "intent": "name"},
        
        # Set name
        {"text": "my name is john", "intent": "set_name"},
        {"text": "i'm sarah", "intent": "set_name"},
        {"text": "you can call me mike", "intent": "set_name"},
        {"text": "i am david", "intent": "set_name"},
        {"text": "call me alex", "intent": "set_name"},
        {"text": "name's james", "intent": "set_name"},
        
        # Help
        {"text": "help", "intent": "help"},
        {"text": "what can you do", "intent": "help"},
        {"text": "show me what you can do", "intent": "help"},
        {"text": "how do you work", "intent": "help"},
        {"text": "i need help", "intent": "help"},
        {"text": "what are your capabilities", "intent": "help"},
        {"text": "tell me about your features", "intent": "help"},
        {"text": "what commands do you understand", "intent": "help"},
        
        # Thanks
        {"text": "thank you", "intent": "thanks"},
        {"text": "thanks", "intent": "thanks"},
        {"text": "appreciate it", "intent": "thanks"},
        {"text": "thanks a lot", "intent": "thanks"},
        {"text": "thank you very much", "intent": "thanks"},
        {"text": "thanks for your help", "intent": "thanks"},
        {"text": "great, thanks", "intent": "thanks"},
        
        # Favorites
        {"text": "what's my favorite color", "intent": "get_favorite"},
        {"text": "tell me my favorite food", "intent": "get_favorite"},
        {"text": "what food do i like", "intent": "get_favorite"},
        {"text": "what's my favorite movie", "intent": "get_favorite"},
        {"text": "my favorite animal", "intent": "get_favorite"},
        
        # Set favorites
        {"text": "my favorite color is blue", "intent": "set_favorite"},
        {"text": "i like the color red", "intent": "set_favorite"},
        {"text": "my favorite food is pizza", "intent": "set_favorite"},
        {"text": "i love sushi", "intent": "set_favorite"},
        {"text": "my favorite movie is inception", "intent": "set_favorite"},
        {"text": "i like star wars", "intent": "set_favorite"},
        {"text": "my favorite animal is dog", "intent": "set_favorite"},
        
        # Rename bot
        {"text": "change your name", "intent": "rename_bot"},
        {"text": "i want to call you alfred", "intent": "rename_bot"},
        {"text": "your name should be siri", "intent": "rename_bot"},
        {"text": "can i rename you", "intent": "rename_bot"},
        {"text": "call you jarvis", "intent": "rename_bot"},
    ]
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    try:
        with open(TRAINING_DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2)
            
        logger.info(f"Sample training data created at {TRAINING_DATA_PATH}")
        return True
    except Exception as e:
        logger.error(f"Error creating sample training data: {e}")
        return False

def classify_intent(text):
    """
    Classify the intent of a user message
    
    Args:
        text (str): User message text
        
    Returns:
        dict: Prediction with intent and confidence
    """
    return intent_classifier.predict(text)

if __name__ == "__main__":
    # If run as a script, create sample data and train the model
    print("Creating sample training data...")
    create_sample_training_data()
    
    print("Training intent classifier...")
    results = intent_classifier.train()
    
    if "error" in results:
        print(f"Error: {results['error']}")
    else:
        print(f"Model trained successfully!")
        print(f"Accuracy: {results['accuracy']:.2f}")
        
        # Test the model with some examples
        test_messages = [
            "hello there",
            "what's the weather like today",
            "my name is Alice",
            "what can you do",
            "thanks for your help",
            "goodbye now"
        ]
        
        print("\nTesting with example messages:")
        for message in test_messages:
            prediction = intent_classifier.predict(message)
            print(f"Message: '{message}'")
            print(f"Predicted intent: {prediction['intent']} (confidence: {prediction['confidence']:.2f})")
            print("---")