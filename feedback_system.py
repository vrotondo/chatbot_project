# feedback_system.py
# A system for collecting and processing user feedback to improve the chatbot

import os
import json
import logging
import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chatbot.feedback")

# Define constants
FEEDBACK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "feedback")
APPROVED_FILE = os.path.join(FEEDBACK_DIR, "approved_examples.json")
REJECTED_FILE = os.path.join(FEEDBACK_DIR, "rejected_examples.json")
TRAINING_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "intent_training_data.json")

# Ensure directories exist
os.makedirs(FEEDBACK_DIR, exist_ok=True)

def store_feedback(user_input, response, quality, intent=None, user_id=None):
    """
    Store user feedback about a chatbot response
    
    Args:
        user_input (str): The user's message
        response (str): The chatbot's response
        quality (str): Feedback quality ('good', 'bad', or 'neutral')
        intent (str, optional): The detected intent, if available
        user_id (str, optional): User identifier
        
    Returns:
        bool: Success status
    """
    if quality not in ['good', 'bad', 'neutral']:
        logger.error(f"Invalid quality value: {quality}. Use 'good', 'bad', or 'neutral'.")
        return False
    
    # Create feedback entry
    feedback_entry = {
        "user_input": user_input,
        "response": response,
        "quality": quality,
        "intent": intent,
        "user_id": user_id,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    # Determine target file based on quality
    if quality == 'good':
        target_file = APPROVED_FILE
    elif quality == 'bad':
        target_file = REJECTED_FILE
    else:
        # For neutral feedback, we don't store it for now
        return True
    
    try:
        # Load existing entries if file exists
        entries = []
        if os.path.exists(target_file):
            with open(target_file, 'r', encoding='utf-8') as f:
                entries = json.load(f)
        
        # Add new entry
        entries.append(feedback_entry)
        
        # Save updated entries
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Stored {quality} feedback for: '{user_input}'")
        return True
    
    except Exception as e:
        logger.error(f"Error storing feedback: {e}")
        return False

def analyze_and_incorporate_feedback(min_approval_count=3):
    """
    Analyze feedback and incorporate good examples into training data
    
    Args:
        min_approval_count (int): Minimum times an example must be marked 'good'
                                to be added to training data
                                
    Returns:
        dict: Statistics about the incorporation process
    """
    stats = {
        "approved_examples": 0,
        "rejected_examples": 0,
        "new_added": 0,
        "existing_count": 0
    }
    
    try:
        # Load existing training data
        training_data = []
        if os.path.exists(TRAINING_DATA_FILE):
            with open(TRAINING_DATA_FILE, 'r', encoding='utf-8') as f:
                training_data = json.load(f)
                stats["existing_count"] = len(training_data)
        
        # Load approved feedback
        approved_examples = []
        if os.path.exists(APPROVED_FILE):
            with open(APPROVED_FILE, 'r', encoding='utf-8') as f:
                approved_examples = json.load(f)
                stats["approved_examples"] = len(approved_examples)
        
        # Load rejected feedback for analysis (not used in this version)
        rejected_examples = []
        if os.path.exists(REJECTED_FILE):
            with open(REJECTED_FILE, 'r', encoding='utf-8') as f:
                rejected_examples = json.load(f)
                stats["rejected_examples"] = len(rejected_examples)
        
        # Group approved examples by user_input
        grouped_examples = {}
        for example in approved_examples:
            user_input = example["user_input"].lower().strip()
            intent = example.get("intent")
            
            if not intent:
                # Skip examples without intent information
                continue
                
            if user_input not in grouped_examples:
                grouped_examples[user_input] = {"count": 0, "intent": intent}
            
            grouped_examples[user_input]["count"] += 1
            
        # Find examples with sufficient approval count
        for user_input, data in grouped_examples.items():
            if data["count"] >= min_approval_count:
                # Check if this example already exists in training data
                exists = False
                for entry in training_data:
                    if entry.get("text", "").lower().strip() == user_input:
                        exists = True
                        break
                
                # If it doesn't exist, add it
                if not exists:
                    training_data.append({
                        "text": user_input,
                        "intent": data["intent"]
                    })
                    stats["new_added"] += 1
        
        # Save updated training data if changes were made
        if stats["new_added"] > 0:
            # Create backup of existing training data
            if os.path.exists(TRAINING_DATA_FILE):
                backup_file = f"{TRAINING_DATA_FILE}.bak.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                with open(TRAINING_DATA_FILE, 'r', encoding='utf-8') as src, open(backup_file, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
                    logger.info(f"Created backup of training data: {backup_file}")
            
            # Save updated training data
            with open(TRAINING_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Added {stats['new_added']} new examples to training data")
        else:
            logger.info("No new examples added to training data")
        
        return stats
    
    except Exception as e:
        logger.error(f"Error analyzing and incorporating feedback: {e}")
        return {"error": str(e)}

def clean_up_feedback_files(max_age_days=30):
    """
    Clean up old feedback files to prevent them from growing too large
    
    Args:
        max_age_days (int): Maximum age of feedback entries in days
        
    Returns:
        dict: Statistics about the cleanup process
    """
    stats = {
        "approved_cleaned": 0,
        "rejected_cleaned": 0
    }
    
    try:
        now = datetime.datetime.now()
        cutoff_date = now - datetime.timedelta(days=max_age_days)
        
        # Process approved examples
        if os.path.exists(APPROVED_FILE):
            approved_examples = []
            with open(APPROVED_FILE, 'r', encoding='utf-8') as f:
                approved_examples = json.load(f)
            
            # Filter out old entries
            new_approved = []
            for entry in approved_examples:
                try:
                    entry_date = datetime.datetime.fromisoformat(entry["timestamp"])
                    if entry_date >= cutoff_date:
                        new_approved.append(entry)
                    else:
                        stats["approved_cleaned"] += 1
                except (ValueError, KeyError):
                    # Keep entries with invalid timestamps for now
                    new_approved.append(entry)
            
            # Save updated list
            if stats["approved_cleaned"] > 0:
                with open(APPROVED_FILE, 'w', encoding='utf-8') as f:
                    json.dump(new_approved, f, indent=2, ensure_ascii=False)
                logger.info(f"Removed {stats['approved_cleaned']} old approved examples")
        
        # Process rejected examples
        if os.path.exists(REJECTED_FILE):
            rejected_examples = []
            with open(REJECTED_FILE, 'r', encoding='utf-8') as f:
                rejected_examples = json.load(f)
            
            # Filter out old entries
            new_rejected = []
            for entry in rejected_examples:
                try:
                    entry_date = datetime.datetime.fromisoformat(entry["timestamp"])
                    if entry_date >= cutoff_date:
                        new_rejected.append(entry)
                    else:
                        stats["rejected_cleaned"] += 1
                except (ValueError, KeyError):
                    # Keep entries with invalid timestamps for now
                    new_rejected.append(entry)
            
            # Save updated list
            if stats["rejected_cleaned"] > 0:
                with open(REJECTED_FILE, 'w', encoding='utf-8') as f:
                    json.dump(new_rejected, f, indent=2, ensure_ascii=False)
                logger.info(f"Removed {stats['rejected_cleaned']} old rejected examples")
        
        return stats
    
    except Exception as e:
        logger.error(f"Error cleaning up feedback files: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # Example usage
    print("Feedback System Command Line Interface")
    print("1. Analyze and incorporate feedback")
    print("2. Clean up old feedback")
    print("3. Exit")
    
    choice = input("Enter your choice (1-3): ")
    
    if choice == "1":
        min_count = int(input("Minimum approval count (default 3): ") or "3")
        stats = analyze_and_incorporate_feedback(min_approval_count=min_count)
        print(f"Results: {json.dumps(stats, indent=2)}")
    
    elif choice == "2":
        max_days = int(input("Maximum age in days (default 30): ") or "30")
        stats = clean_up_feedback_files(max_age_days=max_days)
        print(f"Results: {json.dumps(stats, indent=2)}")
    
    else:
        print("Exiting")