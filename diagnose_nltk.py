# diagnose_nltk.py
# Diagnostic script to identify NLTK issues

import os
import sys
import nltk
import importlib

def print_header(text):
    """Print a header with decorative elements"""
    print("\n" + "=" * 60)
    print(f" {text} ".center(60, "="))
    print("=" * 60)

def print_success(text):
    """Print a success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print an error message"""
    print(f"❌ {text}")

def print_warning(text):
    """Print a warning message"""
    print(f"⚠️ {text}")

def diagnose_nltk():
    """Run comprehensive diagnostics on NLTK setup"""
    
    print_header("NLTK DIAGNOSTIC TOOL")
    print(f"Python version: {sys.version}")
    print(f"NLTK version: {nltk.__version__}")
    
    # 1. Check NLTK data path
    print_header("NLTK DATA PATHS")
    for i, path in enumerate(nltk.data.path):
        if os.path.exists(path):
            print_success(f"Path {i+1}: {path} (EXISTS)")
        else:
            print_error(f"Path {i+1}: {path} (NOT FOUND)")
    
    # 2. Add local path if available
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_nltk_data = os.path.join(script_dir, "nltk_data")
    
    if os.path.exists(local_nltk_data):
        if local_nltk_data not in nltk.data.path:
            print_warning(f"Adding local NLTK data path: {local_nltk_data}")
            nltk.data.path.insert(0, local_nltk_data)
        else:
            print_success(f"Local NLTK data path already configured: {local_nltk_data}")
    else:
        print_error(f"Local NLTK data directory not found: {local_nltk_data}")
    
    # 3. Check for installed packages
    print_header("NLTK PACKAGE VERIFICATION")
    
    packages_to_check = [
        ('punkt', 'tokenizers/punkt'),
        ('wordnet', 'corpora/wordnet'),
        ('wordnet', 'corpora/wordnet.zip'),
        ('wordnet', 'corpora/omw-1.4'),
        ('stopwords', 'corpora/stopwords'),
        ('averaged_perceptron_tagger', 'taggers/averaged_perceptron_tagger'),
        ('maxent_ne_chunker', 'chunkers/maxent_ne_chunker'),
        ('words', 'corpora/words')
    ]
    
    for package_name, resource_path in packages_to_check:
        try:
            nltk.data.find(resource_path)
            print_success(f"Found {package_name} ({resource_path})")
        except LookupError:
            print_error(f"Could not find {package_name} ({resource_path})")
    
    # 4. Test individual components
    print_header("COMPONENT TESTING")
    
    # Test tokenizer
    try:
        from nltk.tokenize import word_tokenize
        result = word_tokenize("Testing tokenization functionality.")
        print_success(f"Tokenizer working: {result}")
    except Exception as e:
        print_error(f"Tokenizer error: {e}")
    
    # Test stopwords
    try:
        from nltk.corpus import stopwords
        stop_words = stopwords.words('english')
        print_success(f"Stopwords working: {len(stop_words)} English stopwords available")
    except Exception as e:
        print_error(f"Stopwords error: {e}")
    
    # Test lemmatizer (this often fails with wordnet issues)
    try:
        from nltk.stem import WordNetLemmatizer
        lemmatizer = WordNetLemmatizer()
        result = lemmatizer.lemmatize("running")
        print_success(f"Lemmatizer working: 'running' → '{result}'")
    except Exception as e:
        print_error(f"Lemmatizer error: {e}")
        
        # Try to diagnose wordnet issues in more detail
        try:
            # Check if wordnet corpus is accessible directly
            from nltk.corpus import wordnet
            synsets = wordnet.synsets("test")
            if synsets:
                print_success(f"WordNet corpus accessible directly: {len(synsets)} synsets for 'test'")
            else:
                print_warning("WordNet corpus accessible but returned no synsets for 'test'")
        except Exception as wordnet_error:
            print_error(f"WordNet corpus error: {wordnet_error}")
    
    # 5. Check file structure
    print_header("FILE STRUCTURE CHECK")
    
    # Define expected directory structure for key packages
    key_directories = [
        os.path.join(local_nltk_data, "tokenizers", "punkt"),
        os.path.join(local_nltk_data, "corpora", "stopwords"),
        os.path.join(local_nltk_data, "taggers", "averaged_perceptron_tagger"),
        os.path.join(local_nltk_data, "chunkers", "maxent_ne_chunker"),
        os.path.join(local_nltk_data, "corpora", "words")
    ]
    
    # Wordnet directories - check various possibilities
    wordnet_directories = [
        os.path.join(local_nltk_data, "corpora", "wordnet"),
        os.path.join(local_nltk_data, "corpora", "wordnet.zip"),
        os.path.join(local_nltk_data, "corpora", "omw-1.4")
    ]
    
    found_wordnet = False
    for wordnet_dir in wordnet_directories:
        if os.path.exists(wordnet_dir):
            print_success(f"Found WordNet at: {wordnet_dir}")
            found_wordnet = True
    
    if not found_wordnet:
        print_error("Could not find WordNet in any expected location")
        
        # List all files in corpora directory to help debug
        corpora_dir = os.path.join(local_nltk_data, "corpora")
        if os.path.exists(corpora_dir):
            print("\nListing all files in corpora directory:")
            for item in os.listdir(corpora_dir):
                item_path = os.path.join(corpora_dir, item)
                if os.path.isdir(item_path):
                    print(f"  - {item}/")
                else:
                    print(f"  - {item}")
    
    for directory in key_directories:
        if os.path.exists(directory):
            print_success(f"Found required directory: {directory}")
        else:
            print_error(f"Missing required directory: {directory}")
    
    # 6. Recommendations
    print_header("RECOMMENDATIONS")
    
    if not os.path.exists(local_nltk_data):
        print("1. Run the download script: python download_nltk_data.py")
    elif not found_wordnet:
        print("1. WordNet is missing or not in the expected location.")
        print("   Run: python -c \"import nltk; nltk.download('wordnet')\"")
        print("   Run: python -c \"import nltk; nltk.download('omw-1.4')\"")
    else:
        print("Your NLTK setup looks good! If you're still having issues:")
        print("1. Try running the download script again: python download_nltk_data.py")
        print("2. Try importing components in this order in your code:")
        print("   - First import and configure nltk.data.path")
        print("   - Then import specific components (tokenizers, wordnet, etc.)")
    
    print("\nNote: Some NLTK errors, especially with WordNet, are common but")
    print("don't always affect functionality. If the lemmatizer test passed,")
    print("you should be good to go despite other warnings.\n")

if __name__ == "__main__":
    diagnose_nltk()