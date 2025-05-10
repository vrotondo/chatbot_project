# transformers_engine.py
# Advanced language understanding using transformer models

import os
import json
import logging
import numpy as np
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chatbot.transformers")

# Check if transformers is available
try:
    import torch
    import transformers
    from transformers import AutoTokenizer, AutoModel
    transformers_available = True
    logger.info(f"Transformers library version: {transformers.__version__}")
    
    # Check CUDA availability
    if torch.cuda.is_available():
        logger.info(f"CUDA is available: {torch.cuda.get_device_name(0)}")
        device = "cuda"
    else:
        logger.info("CUDA not available, using CPU")
        device = "cpu"
        
except ImportError:
    transformers_available = False
    logger.warning("Transformers library not installed, advanced features will be disabled")
    logger.warning("Install with: pip install transformers torch")

# Define model name and paths
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # Small but effective model
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
EMBEDDINGS_FILE = os.path.join(DATA_DIR, "intent_embeddings.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

class TransformerEmbeddings:
    """
    Generate and use transformer-based text embeddings for semantic understanding
    """
    
    def __init__(self, model_name=MODEL_NAME):
        """Initialize the transformer embeddings model"""
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.embeddings = {}
        self.available = False
        
        # Try to initialize the model
        if transformers_available:
            try:
                logger.info(f"Loading transformer model: {model_name}")
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModel.from_pretrained(model_name)
                
                # Move model to appropriate device
                self.model.to(device)
                
                self.available = True
                logger.info("Transformer model loaded successfully")
                
                # Load cached embeddings if available
                self.load_embeddings()
                
            except Exception as e:
                logger.error(f"Error loading transformer model: {e}")
                logger.warning("Advanced semantic features will be disabled")
        else:
            logger.warning("Transformers library not available, semantic features disabled")
    
    def generate_embedding(self, text):
        """
        Generate an embedding vector for the given text
        
        Args:
            text (str): Input text
            
        Returns:
            np.ndarray: Embedding vector or None if not available
        """
        if not self.available:
            return None
        
        try:
            # Tokenize and prepare input
            inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            inputs = {key: val.to(device) for key, val in inputs.items()}
            
            # Get model output with no gradient calculation
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Use mean of last hidden state as the sentence embedding
            embeddings = outputs.last_hidden_state.mean(dim=1)
            
            # Convert to numpy and move to CPU if needed
            embedding_np = embeddings.cpu().numpy()
            
            # Return the first (and only) embedding
            return embedding_np[0]
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def compute_embedding_for_intent(self, intent, examples):
        """
        Compute an embedding for an intent based on multiple examples
        
        Args:
            intent (str): The intent name
            examples (list): List of example texts for the intent
            
        Returns:
            np.ndarray: Average embedding vector for the intent
        """
        if not self.available or not examples:
            return None
        
        # Generate embeddings for each example
        embeddings = []
        for text in examples:
            embedding = self.generate_embedding(text)
            if embedding is not None:
                embeddings.append(embedding)
        
        # Compute average embedding if we have at least one valid embedding
        if embeddings:
            return np.mean(embeddings, axis=0)
        else:
            return None
    
    def compute_all_intent_embeddings(self, training_data):
        """
        Compute embeddings for all intents in the training data
        
        Args:
            training_data (list): List of training examples with intent labels
            
        Returns:
            dict: Intent embeddings dictionary
        """
        if not self.available or not training_data:
            return {}
        
        # Group examples by intent
        intent_examples = {}
        for item in training_data:
            intent = item.get("intent")
            text = item.get("text")
            
            if not intent or not text:
                continue
            
            if intent not in intent_examples:
                intent_examples[intent] = []
            
            intent_examples[intent].append(text)
        
        # Compute embeddings for each intent
        intent_embeddings = {}
        for intent, examples in intent_examples.items():
            embedding = self.compute_embedding_for_intent(intent, examples)
            if embedding is not None:
                intent_embeddings[intent] = embedding.tolist()  # Convert to list for JSON serialization
        
        # Update internal embeddings
        self.embeddings = intent_embeddings
        
        # Save embeddings to file
        self.save_embeddings()
        
        return intent_embeddings
    
    def find_most_similar_intent(self, text, threshold=0.7):
        """
        Find the most similar intent for a given text
        
        Args:
            text (str): Input text
            threshold (float): Similarity threshold (0-1)
            
        Returns:
            tuple: (intent, similarity score) or (None, 0) if no match
        """
        if not self.available or not self.embeddings:
            return None, 0
        
        # Generate embedding for the input text
        text_embedding = self.generate_embedding(text)
        if text_embedding is None:
            return None, 0
        
        # Compute cosine similarity with each intent embedding
        best_intent = None
        best_score = -1
        
        for intent, embedding in self.embeddings.items():
            # Convert stored embedding from list back to numpy array
            intent_embedding = np.array(embedding)
            
            # Compute cosine similarity
            similarity = self.cosine_similarity(text_embedding, intent_embedding)
            
            if similarity > best_score:
                best_score = similarity
                best_intent = intent
        
        # Return the best match if above threshold
        if best_score >= threshold:
            return best_intent, best_score
        else:
            return None, best_score
    
    def cosine_similarity(self, a, b):
        """
        Compute cosine similarity between two vectors
        
        Args:
            a (np.ndarray): First vector
            b (np.ndarray): Second vector
            
        Returns:
            float: Cosine similarity (0-1)
        """
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0
        
        return np.dot(a, b) / (norm_a * norm_b)
    
    def load_embeddings(self):
        """
        Load intent embeddings from file
        
        Returns:
            bool: Success status
        """
        if not os.path.exists(EMBEDDINGS_FILE):
            logger.info("No cached embeddings found")
            return False
        
        try:
            with open(EMBEDDINGS_FILE, 'r', encoding='utf-8') as f:
                self.embeddings = json.load(f)
                
            logger.info(f"Loaded {len(self.embeddings)} intent embeddings from file")
            return True
            
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            return False
    
    def save_embeddings(self):
        """
        Save intent embeddings to file
        
        Returns:
            bool: Success status
        """
        if not self.embeddings:
            logger.warning("No embeddings to save")
            return False
        
        try:
            with open(EMBEDDINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.embeddings, f)
                
            logger.info(f"Saved {len(self.embeddings)} intent embeddings to file")
            return True
            
        except Exception as e:
            logger.error(f"Error saving embeddings: {e}")
            return False
    
    def get_similar_texts(self, text1, text2):
        """
        Compute similarity between two texts
        
        Args:
            text1 (str): First text
            text2 (str): Second text
            
        Returns:
            float: Similarity score (0-1)
        """
        if not self.available:
            return 0
        
        emb1 = self.generate_embedding(text1)
        emb2 = self.generate_embedding(text2)
        
        if emb1 is None or emb2 is None:
            return 0
        
        return self.cosine_similarity(emb1, emb2)
    
    def is_similar_to_previous(self, current_text, previous_texts, threshold=0.85):
        """
        Check if current text is semantically similar to any previous text
        
        Args:
            current_text (str): Current text to check
            previous_texts (list): List of previous texts
            threshold (float): Similarity threshold (0-1)
            
        Returns:
            bool: True if similar to any previous text
        """
        if not self.available or not previous_texts:
            return False
        
        for prev_text in previous_texts:
            similarity = self.get_similar_texts(current_text, prev_text)
            if similarity >= threshold:
                return True
        
        return False

# Create a singleton instance
transformer_embeddings = TransformerEmbeddings()

def is_available():
    """Check if transformer functionality is available"""
    return transformer_embeddings.available

def generate_embedding(text):
    """Generate embedding for a text"""
    return transformer_embeddings.generate_embedding(text)

def find_similar_intent(text, threshold=0.7):
    """Find the most similar intent for a text"""
    return transformer_embeddings.find_most_similar_intent(text, threshold)

def update_embeddings(training_data):
    """Update embeddings with new training data"""
    return transformer_embeddings.compute_all_intent_embeddings(training_data)

def calculate_similarity(text1, text2):
    """Calculate similarity between two texts"""
    return transformer_embeddings.get_similar_texts(text1, text2)

if __name__ == "__main__":
    # Test the transformer embeddings
    if transformers_available:
        print("\nTesting transformer embeddings")
        
        # Sample texts
        texts = [
            "What's the weather like today?",
            "How's the weather looking?",
            "Tell me the current weather forecast.",
            "What's the temperature outside?",
            "Can you help me with my homework?",
            "What time is it?",
            "I need assistance with a programming problem."
        ]
        
        # Generate embeddings and compute similarities
        print("\nComputing similarity matrix:")
        similarity_matrix = np.zeros((len(texts), len(texts)))
        
        for i, text1 in enumerate(texts):
            for j, text2 in enumerate(texts):
                similarity = transformer_embeddings.get_similar_texts(text1, text2)
                similarity_matrix[i][j] = similarity
                
                if i < j:  # Only print upper triangle
                    print(f"Similarity between \"{text1}\" and \"{text2}\": {similarity:.4f}")
        
        # Mock training data for intent embeddings
        training_data = [
            {"text": "What's the weather like today?", "intent": "weather"},
            {"text": "How's the weather looking?", "intent": "weather"},
            {"text": "Tell me the current weather forecast.", "intent": "weather"},
            {"text": "What's the temperature outside?", "intent": "weather"},
            {"text": "Can you help me with my homework?", "intent": "help"},
            {"text": "I need assistance with a programming problem.", "intent": "help"},
            {"text": "What time is it?", "intent": "time"},
            {"text": "Can you tell me the current time?", "intent": "time"}
        ]
        
        # Compute intent embeddings
        print("\nComputing intent embeddings...")
        intent_embeddings = transformer_embeddings.compute_all_intent_embeddings(training_data)
        print(f"Generated embeddings for {len(intent_embeddings)} intents")
        
        # Test intent prediction
        test_texts = [
            "Is it going to rain today?",
            "I need help with my math homework",
            "What's the current time?"
        ]
        
        print("\nTesting intent prediction:")
        for text in test_texts:
            intent, score = transformer_embeddings.find_most_similar_intent(text)
            print(f"Text: \"{text}\"")
            print(f"Predicted intent: {intent} (score: {score:.4f})")
        
    else:
        print("\nTransformers library is not available.")
        print("Install it with: pip install transformers torch")