# NLTK Setup Guide

This guide will help you set up NLTK (Natural Language Toolkit) properly for use with the chatbot's machine learning features.

## Quick Start

Run the dedicated download script:

```bash
python download_nltk_data.py
```

This will:
1. Download all required NLTK packages
2. Install them to a local `nltk_data` directory in your project
3. Configure the necessary paths automatically

## Troubleshooting Common Issues

### 1. "Resource not found" Errors

If you see errors like:
```
LookupError: Resource punkt not found.
Please use the NLTK Downloader to obtain the resource.
```

Solution:
- Run the download script with administrator privileges
- Make sure you have internet access
- Check that the download directory is writable

### 2. Verification Failures

If the download script reports successful downloads but fails verification:

Solution:
- Check for antivirus or permission issues
- Try running the script again
- Manually verify the contents of the `nltk_data` directory

### 3. Import Errors

If you see errors like:
```python
ImportError: No module named 'nltk.tokenize'
```

Solution:
- Make sure you've installed NLTK with `pip install nltk`
- Check that your environment is activated
- Restart your Python environment

## Manual Setup

If the automatic script doesn't work, you can set up NLTK manually:

1. Run Python and execute:
```python
import nltk
nltk.download()
```

2. This will open a graphical downloader - select and download:
   - punkt
   - wordnet
   - stopwords
   - averaged_perceptron_tagger
   - maxent_ne_chunker
   - words

3. In your code, manually set the path to the downloaded data:
```python
import nltk
import os
nltk.data.path.append('/path/to/nltk_data')
```

## Verify Your Setup

To check if NLTK is properly set up, run:

```python
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

# Test tokenization
print(word_tokenize("Testing NLTK setup"))

# Test stopwords
print(stopwords.words('english')[:5])

# Test lemmatization
lemmatizer = WordNetLemmatizer()
print(lemmatizer.lemmatize("running"))
```

If all three examples work without errors, NLTK is correctly set up.

## For Windows Users

Windows users might encounter specific issues:

1. Consider using a virtual environment to avoid permission issues
2. Run the command prompt as administrator when installing
3. If you've installed NLTK in multiple locations, check the search path:
```python
import nltk
print(nltk.data.path)
```

## Advanced: Custom Installation Location

If you need to use a specific location for NLTK data:

1. Set the environment variable `NLTK_DATA`:
   - Windows: `set NLTK_DATA=C:\path\to\nltk_data`
   - Linux/Mac: `export NLTK_DATA=/path/to/nltk_data`

2. Or set the path in your code:
```python
import nltk
nltk.data.path.insert(0, '/path/to/nltk_data')
```