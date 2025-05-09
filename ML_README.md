# Machine Learning Features

This document provides information about the machine learning capabilities added to the chatbot.

## Overview

The chatbot now includes machine learning-based intent classification that works alongside the traditional pattern matching system. This hybrid approach provides several benefits:

1. **Better understanding of user intent** - The ML model can recognize user intents even when the phrasing is different from the patterns
2. **Improved response selection** - Responses are selected based on the detected intent and confidence level
3. **Entity extraction** - The system can extract specific entities (like city names for weather queries) from user messages
4. **Graceful fallback** - When the ML model isn't confident, the system falls back to pattern matching

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

## Setup and Training

### Prerequisites

Make sure you have the required libraries installed:

```bash
pip install scikit-learn nltk
```

### Training the Model

1. To train or retrain the model, run:

```bash
python train_ml_model.py
```

2. The script will:
   - Create sample training data if none exists
   - Train the model using grid search for optimal parameters
   - Save the trained model to `data/intent_model.pkl`
   - Test the model with some sample queries

### Custom Training Data

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

## Troubleshooting

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

## Future Improvements

Future versions could include:

1. **Transformer-based models** - Using models like BERT or GPT-2 for more advanced understanding
2. **Learning from interactions** - Recording user interactions to improve the model over time
3. **Named entity recognition** - Using ML-based entity extraction instead of regex patterns
4. **Multi-language support** - Training the model to understand multiple languages