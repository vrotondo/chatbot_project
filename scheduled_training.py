# scheduled_training.py
# Script to automate regular retraining and evaluation of the chatbot model

import os
import sys
import json
import time
import logging
import datetime
import subprocess
import argparse
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduled_training.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("scheduled_training")

# Path constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
MODEL_DIR = os.path.join(DATA_DIR, "models")
CONFIG_FILE = os.path.join(DATA_DIR, "scheduled_training_config.json")
STATUS_FILE = os.path.join(DATA_DIR, "scheduled_training_status.json")

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# Default configuration
DEFAULT_CONFIG = {
    "frequency": "weekly",  # Can be 'daily', 'weekly', 'monthly', or a number of hours
    "test_size": 0.2,
    "analyze_trends": True,
    "analyze_errors": True,
    "incorporate_feedback": True,
    "cleanup_old_models": True,
    "keep_models": 5,
    "notification_email": None,
    "enabled": True,
    "next_training_time": None
}

def load_config():
    """
    Load the configuration for scheduled training
    
    Returns:
        dict: The loaded configuration
    """
    # Start with default config
    config = DEFAULT_CONFIG.copy()
    
    # Override with values from config file if it exists
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                
            # Update config with file values
            config.update(file_config)
            
            logger.info("Loaded configuration from file")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    else:
        # Save default config
        save_config(config)
        logger.info("Created default configuration file")
    
    return config

def save_config(config):
    """
    Save the configuration to file
    
    Args:
        config (dict): The configuration to save
        
    Returns:
        bool: Success status
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            
        logger.info("Saved configuration to file")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return False

def update_status(status):
    """
    Update the status file with latest training information
    
    Args:
        status (dict): The status information to save
        
    Returns:
        bool: Success status
    """
    try:
        # Load existing status if file exists
        existing_status = {}
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                existing_status = json.load(f)
        
        # Update with new status
        existing_status.update(status)
        
        # Add timestamp
        existing_status["last_updated"] = datetime.datetime.now().isoformat()
        
        # Save updated status
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing_status, f, indent=2, ensure_ascii=False)
            
        logger.info("Updated status file")
        return True
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        return False

def get_next_training_time(config):
    """
    Calculate the next scheduled training time
    
    Args:
        config (dict): The training configuration
        
    Returns:
        datetime: The next training time
    """
    now = datetime.datetime.now()
    
    # If next_training_time is specified in config and it's in the future, use it
    if config.get("next_training_time"):
        try:
            next_time = datetime.datetime.fromisoformat(config["next_training_time"])
            if next_time > now:
                return next_time
        except:
            pass  # Invalid format, recalculate
    
    # Otherwise, calculate based on frequency
    frequency = config.get("frequency", "weekly")
    
    if frequency == "daily":
        # Next day, same time
        return now + datetime.timedelta(days=1)
    
    elif frequency == "weekly":
        # Next week, same day and time
        return now + datetime.timedelta(days=7)
    
    elif frequency == "monthly":
        # Next month, same day and time (approximately)
        if now.month == 12:
            next_month = 1
            next_year = now.year + 1
        else:
            next_month = now.month + 1
            next_year = now.year
            
        # Handle month length differences
        try:
            next_date = datetime.datetime(
                year=next_year, 
                month=next_month, 
                day=now.day,
                hour=now.hour, 
                minute=now.minute
            )
        except ValueError:
            # Handle cases like February 30 by using last day of month
            if next_month == 2:
                if next_year % 4 == 0 and (next_year % 100 != 0 or next_year % 400 == 0):
                    # Leap year
                    day = min(now.day, 29)
                else:
                    day = min(now.day, 28)
            else:
                # Other months with fewer than 31 days
                month_days = {
                    1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
                    7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
                }
                day = min(now.day, month_days[next_month])
                
            next_date = datetime.datetime(
                year=next_year, 
                month=next_month, 
                day=day,
                hour=now.hour, 
                minute=now.minute
            )
            
        return next_date
    
    else:
        # Try to interpret as number of hours
        try:
            hours = int(frequency)
            return now + datetime.timedelta(hours=hours)
        except:
            # Default to daily if frequency is invalid
            logger.warning(f"Invalid frequency format: {frequency}. Using daily instead.")
            return now + datetime.timedelta(days=1)

def should_train_now(config):
    """
    Check if it's time to train based on the configuration
    
    Args:
        config (dict): The training configuration
        
    Returns:
        bool: True if it's time to train, False otherwise
    """
    if not config.get("enabled", True):
        return False
    
    # Check if next_training_time is set and we've reached or passed it
    if config.get("next_training_time"):
        try:
            next_time = datetime.datetime.fromisoformat(config["next_training_time"])
            return datetime.datetime.now() >= next_time
        except:
            # Invalid format, fall back to calculating based on last training
            pass
    
    # If no specific next time or invalid format, check based on last training
    status = {}
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                status = json.load(f)
        except:
            pass
    
    last_training = status.get("last_training_time")
    if not last_training:
        # If no previous training, we should train now
        return True
    
    try:
        last_time = datetime.datetime.fromisoformat(last_training)
        frequency = config.get("frequency", "weekly")
        
        # Calculate time elapsed since last training
        elapsed = datetime.datetime.now() - last_time
        
        if frequency == "daily":
            return elapsed.total_seconds() >= 24 * 60 * 60  # 24 hours
        
        elif frequency == "weekly":
            return elapsed.total_seconds() >= 7 * 24 * 60 * 60  # 7 days
        
        elif frequency == "monthly":
            return elapsed.total_seconds() >= 30 * 24 * 60 * 60  # ~30 days
        
        else:
            # Try to interpret as number of hours
            try:
                hours = int(frequency)
                return elapsed.total_seconds() >= hours * 60 * 60
            except:
                # Default to daily if frequency is invalid
                return elapsed.total_seconds() >= 24 * 60 * 60  # 24 hours
    
    except:
        # If we can't parse last training time, assume we should train
        return True

def run_training():
    """
    Run the training process
    
    Returns:
        dict: Results of the training process
    """
    try:
        # Import model training module
        sys.path.append(SCRIPT_DIR)
        from model_training import (
            train_and_evaluate_model, 
            analyze_training_trends, 
            analyze_model_errors
        )
        
        # Load config
        config = load_config()
        
        # Update status
        update_status({
            "last_training_time": datetime.datetime.now().isoformat(),
            "training_status": "in_progress"
        })
        
        # First, incorporate feedback if enabled
        if config.get("incorporate_feedback", True):
            try:
                from chatbot.feedback_system import analyze_and_incorporate_feedback
                feedback_results = analyze_and_incorporate_feedback()
                logger.info(f"Incorporated feedback: {feedback_results.get('new_added', 0)} new examples added")
            except ImportError:
                logger.warning("Feedback system not available, skipping feedback incorporation")
            except Exception as e:
                logger.error(f"Error incorporating feedback: {e}")
        
        # Train and evaluate the model
        version = datetime.datetime.now().strftime("%Y%m%d")
        training_results = train_and_evaluate_model(
            test_size=config.get("test_size", 0.2),
            save_model=True,
            version_suffix=version
        )
        
        # Update status with training results
        training_status = "completed" if "success" in training_results else "failed"
        training_metrics = training_results.get("metrics", {})
        
        status_update = {
            "training_status": training_status,
            "training_metrics": training_metrics
        }
        
        # Run trend analysis if enabled
        if config.get("analyze_trends", True):
            try:
                trends = analyze_training_trends()
                status_update["training_trends"] = trends
                logger.info(f"Trend analysis completed")
            except Exception as e:
                logger.error(f"Error analyzing trends: {e}")
        
        # Run error analysis if enabled
        if config.get("analyze_errors", True):
            try:
                error_analysis = analyze_model_errors(best_model=False)  # Use the model we just trained
                status_update["error_analysis"] = error_analysis
                logger.info(f"Error analysis completed")
            except Exception as e:
                logger.error(f"Error analyzing errors: {e}")
        
        # Clean up old models if enabled
        if config.get("cleanup_old_models", True):
            try:
                keep_models = config.get("keep_models", 5)
                cleanup_old_models(keep_models)
            except Exception as e:
                logger.error(f"Error cleaning up old models: {e}")
        
        # Calculate next training time
        next_training_time = get_next_training_time(config)
        config["next_training_time"] = next_training_time.isoformat()
        save_config(config)
        
        status_update["next_training_time"] = config["next_training_time"]
        update_status(status_update)
        
        # Send notification if configured
        if config.get("notification_email"):
            try:
                send_notification(config["notification_email"], training_results, status_update)
            except Exception as e:
                logger.error(f"Error sending notification: {e}")
        
        return {
            "success": "success" in training_results,
            "status": status_update
        }
        
    except Exception as e:
        logger.error(f"Error running training: {e}")
        update_status({
            "training_status": "failed",
            "error": str(e)
        })
        return {"error": str(e)}

def cleanup_old_models(keep=5):
    """
    Remove old model files, keeping only the most recent ones
    
    Args:
        keep (int): Number of models to keep
        
    Returns:
        int: Number of models removed
    """
    try:
        # Get all model files
        model_files = []
        for file in os.listdir(MODEL_DIR):
            if file.startswith("intent_model_") and file.endswith(".pkl"):
                path = os.path.join(MODEL_DIR, file)
                stat = os.stat(path)
                model_files.append((path, stat.st_mtime))
        
        # Sort by modification time (newest first)
        model_files.sort(key=lambda x: x[1], reverse=True)
        
        # Keep the specified number of models
        models_to_remove = model_files[keep:]
        
        # Remove old models
        for path, _ in models_to_remove:
            os.remove(path)
            logger.info(f"Removed old model: {path}")
        
        return len(models_to_remove)
        
    except Exception as e:
        logger.error(f"Error cleaning up old models: {e}")
        return 0

def send_notification(email, training_results, status_update):
    """
    Send a notification email about training results
    
    Args:
        email (str): Email address to notify
        training_results (dict): Results from the training process
        status_update (dict): Status update information
        
    Returns:
        bool: Success status
    """
    # This is a placeholder. In a real implementation, you would:
    # 1. Use an email library like smtplib
    # 2. Or integrate with a notification service like SendGrid, Mailgun, etc.
    # 3. Or use a cloud service's notification mechanism
    
    logger.info(f"Would send notification to {email} if implemented")
    return True

def main():
    """Process command line arguments and run requested actions"""
    parser = argparse.ArgumentParser(description="Scheduled training for chatbot ML model")
    
    parser.add_argument(
        "--action", 
        choices=["check", "train", "config", "status"],
        default="check",
        help="Action to perform"
    )
    
    parser.add_argument(
        "--frequency", 
        choices=["daily", "weekly", "monthly"],
        help="Set training frequency"
    )
    
    parser.add_argument(
        "--enable", 
        action="store_true",
        help="Enable scheduled training"
    )
    
    parser.add_argument(
        "--disable", 
        action="store_true",
        help="Disable scheduled training"
    )
    
    parser.add_argument(
        "--force", 
        action="store_true",
        help="Force training to run now"
    )
    
    parser.add_argument(
        "--email", 
        type=str,
        help="Set notification email address"
    )
    
    args = parser.parse_args()
    
    # Load existing configuration
    config = load_config()
    
    # Update configuration if specified
    config_changed = False
    
    if args.frequency:
        config["frequency"] = args.frequency
        config_changed = True
    
    if args.enable:
        config["enabled"] = True
        config_changed = True
    
    if args.disable:
        config["enabled"] = False
        config_changed = True
    
    if args.email:
        config["notification_email"] = args.email
        config_changed = True
    
    # Save updated configuration
    if config_changed:
        save_config(config)
        logger.info("Configuration updated")
    
    # Perform the requested action
    if args.action == "config":
        # Display current configuration
        print("\nCurrent Configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")
    
    elif args.action == "status":
        # Display current status
        status = {}
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                    status = json.load(f)
            except:
                pass
        
        print("\nTraining Status:")
        if not status:
            print("  No status information available")
        else:
            for key, value in status.items():
                if key == "training_metrics" or key == "training_trends" or key == "error_analysis":
                    print(f"  {key}: [detailed information available]")
                else:
                    print(f"  {key}: {value}")
    
    elif args.action == "train" or args.force:
        # Run training immediately
        logger.info("Starting training...")
        results = run_training()
        
        if "error" in results:
            logger.error(f"Training failed: {results['error']}")
        else:
            logger.info("Training completed successfully")
    
    elif args.action == "check":
        # Check if training should run
        if should_train_now(config) or args.force:
            logger.info("It's time to train the model")
            results = run_training()
            
            if "error" in results:
                logger.error(f"Training failed: {results['error']}")
            else:
                logger.info("Training completed successfully")
        else:
            logger.info("It's not time to train yet")
            
            # Calculate time until next training
            next_time = None
            if config.get("next_training_time"):
                try:
                    next_time = datetime.datetime.fromisoformat(config["next_training_time"])
                except:
                    next_time = get_next_training_time(config)
            else:
                next_time = get_next_training_time(config)
            
            if next_time:
                time_until = next_time - datetime.datetime.now()
                logger.info(f"Next training scheduled for: {next_time.isoformat()}")
                logger.info(f"Time until next training: {time_until}")
    
    logger.info("Script execution complete")

if __name__ == "__main__":
    main()