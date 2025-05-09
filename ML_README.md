# Machine Learning Features

This document provides information about the machine learning capabilities added to the chatbot.

## Overview

The chatbot now includes machine learning-based intent classification that works alongside the traditional pattern matching system. This hybrid approach provides several benefits:

1. **Better understanding of user intent** - The ML model can recognize user intents even when the phrasing is different from the patterns
2. **Improved response selection** - Responses are selected based on the detected intent and confidence level
3. **Entity extraction** - The system can extract specific entities (like city names for weather queries) from user messages
4. **Graceful fallback** - When the ML model isn't confident, the system falls back to pattern matching

## Setup and Training

### Step 1: Install Required Libraries

First, install the necessary machine learning libraries:

```bash
pip install scikit-learn nltk numpy
```

### Step 2: Download NLTK Data

Before training the model, you need to download the required NLTK data files:

```bash
python download_nltk_data.py
```

This script will download all necessary language processing resources and save them to the project directory.

### Step 3: Train the Model

Once the NLTK data is downloaded, you can train the machine learning model:

```bash
python train_ml_model.py
```

This script will:
- Load or create training data from `data/intent_training_data.json`
- Train the model using grid search to find optimal parameters
- Save the trained model to `data/intent_model.pkl`
- Test the model with sample queries

### Step 4: Use the Chatbot

The chatbot will now automatically use the ML model to enhance its responses:

```bash
python -m chatbot.chatbot  # CLI version
python -m chatbot.gui      # GUI version
python app.py              # Web version
```

## How It Works

1. When a user sends a message, it first goes through the ML intent classifier
2. If the classifier identifies the intent with high confidence, it generates a response based on that intent
3. For certain intents (like weather queries), the ML system extracts relevant entities (like city names)
4. If the ML classifier isn't confident enough, or for certain tasks that need pattern matching, the system falls back to the original pattern-based responses

## Supported Intents

The ML system currently recognizes these intents:

- **greeting** - Hello, hi, etc.
- **farewell** - Goodbye, bye, etc.
- **weather** - Weather queries
- **name** - Asking for the chatbot's name
- **set_name** - Telling the chatbot your name
- **help** - Asking what the chatbot can do
- **thanks** - Expressions of gratitude
- **get_favorite** - Asking about stored preferences
- **set_favorite** - Setting new preferences
- **rename_bot** - Changing the bot's name

## Troubleshooting

### NLTK Data Issues

If you encounter errors like `Resource punkt not found` or other NLTK-related issues:

1. Make sure you've run the dedicated NLTK download script:
   ```bash
   python download_nltk_data.py
   ```

2. If you still have issues, try running the script with administrator privileges

3. You can also manually download NLTK data using Python:
   ```python
   import nltk
   nltk.download('punkt')
   nltk.download('wordnet')
   nltk.download('stopwords')
   ```

### ML Model Not Working

If the ML model doesn't seem to be working:

1. Check that the model file exists at `data/intent_model.pkl`
2. Try retraining the model with `python train_ml_model.py`
3. Check the logs for any errors during prediction

### Poor Classification Results

If the model is not classifying intents correctly:

1. Add more training examples, especially for the problematic intents
2. Make sure your training examples are diverse and representative
3. Consider adjusting the confidence thresholds

## Custom Training Data

You can create your own training data by editing the `data/intent_training_data.json` file. Each entry should have:

```json
{
  "text": "example user message",
  "intent": "intent_name"
}
```

The more examples you provide for each intent, the better the model will perform.

## Advanced Customization

### Adding New Intents

To add a new intent:

1. Add training examples to `data/intent_training_data.json` with your new intent
2. Update the `get_ml_response` function in `chatbot/ml_integration.py` to handle your new intent
3. Retrain the model with `python train_ml_model.py`

### Adjusting Confidence Thresholds

The system uses two confidence thresholds:

- `HIGH_CONFIDENCE` (0.8): For very confident predictions
- `MEDIUM_CONFIDENCE` (0.5): Minimum threshold for using ML responses

You can adjust these values in `chatbot/ml_integration.py` to make the system more or less conservative.

### Entity Extraction

The current entity extraction uses regular expressions. To add extraction for new entity types:

1. Add a new regex pattern in the `extract_entities` function in `chatbot/ml_integration.py`
2. Update the response handling to use your new entity type

## Future Improvements

Future versions could include:

1. **Transformer-based models** - Using models like BERT or GPT-2 for more advanced understanding
2. **Learning from interactions** - Recording user interactions to improve the model over time
3. **Named entity recognition** - Using ML-based entity extraction instead of regex patterns
4. **Multi-language support** - Training the model to understand multiple languages