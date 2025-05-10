# model_training.py
# Advanced script for training, evaluating, and versioning ML models

import os
import sys
import json
import logging
import datetime
import argparse
import numpy as np
from pathlib import Path
from sklearn.metrics import classification_report, confusion_matrix

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("model_training.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("model_training")

# Path constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
MODEL_DIR = os.path.join(DATA_DIR, "models")
TRAINING_DATA_PATH = os.path.join(DATA_DIR, "intent_training_data.json")
METRICS_FILE = os.path.join(DATA_DIR, "training_metrics.json")

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

def train_and_evaluate_model(data_path=None, test_size=0.2, save_model=True, version_suffix=None):
    """
    Train and evaluate an intent classification model
    
    Args:
        data_path (str, optional): Path to training data JSON
        test_size (float): Portion of data to use for testing
        save_model (bool): Whether to save the trained model
        version_suffix (str, optional): Custom suffix for model version
        
    Returns:
        dict: Training results and evaluation metrics
    """
    try:
        # Import ML engine
        sys.path.append(SCRIPT_DIR)
        from chatbot.ml_engine import intent_classifier
        
        # Set default data path if not specified
        if data_path is None:
            data_path = TRAINING_DATA_PATH
            
        if not os.path.exists(data_path):
            logger.error(f"Training data not found at {data_path}")
            return {"error": f"Training data not found at {data_path}"}
        
        # Load training data to get counts
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                training_data = json.load(f)
            
            # Count examples per intent
            intent_counts = {}
            for item in training_data:
                intent = item.get("intent")
                if intent:
                    intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            logger.info(f"Loaded {len(training_data)} training examples")
            logger.info(f"Intent distribution: {intent_counts}")
            
            # Check if we have enough examples
            if len(training_data) < 10:
                logger.warning(f"Very small training dataset ({len(training_data)} examples). Results may be unreliable.")
            
            # Check if any intent has too few examples
            for intent, count in intent_counts.items():
                if count < 5:
                    logger.warning(f"Intent '{intent}' has only {count} examples. Consider adding more.")
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing training data: {e}")
            return {"error": f"Invalid training data format: {e}"}
        except Exception as e:
            logger.error(f"Error loading training data: {e}")
            return {"error": f"Error loading training data: {e}"}
        
        # Train the model
        logger.info("Starting model training...")
        train_start = datetime.datetime.now()
        training_results = intent_classifier.train(data_path=data_path, test_size=test_size)
        train_end = datetime.datetime.now()
        train_duration = (train_end - train_start).total_seconds()
        
        if "error" in training_results:
            logger.error(f"Training failed: {training_results['error']}")
            return {"error": f"Training failed: {training_results['error']}"}
        
        logger.info(f"Training completed in {train_duration:.2f} seconds")
        
        # Extract metrics
        accuracy = training_results.get("accuracy", 0)
        logger.info(f"Model accuracy: {accuracy:.4f}")
        
        # Detailed metrics
        metrics = {
            "timestamp": datetime.datetime.now().isoformat(),
            "accuracy": accuracy,
            "training_examples": len(training_data),
            "intent_distribution": intent_counts,
            "training_duration": train_duration,
            "best_params": training_results.get("best_params", {}),
            "report": training_results.get("report", {})
        }
        
        # Save the model with version info if requested
        if save_model:
            model_version = version_suffix
            if not model_version:
                # Generate version based on timestamp
                model_version = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Append accuracy to version
            model_version = f"{model_version}_acc{accuracy:.4f}"
            
            # Save to versioned file
            model_path = os.path.join(MODEL_DIR, f"intent_model_{model_version}.pkl")
            
            if intent_classifier.save_model(model_path):
                logger.info(f"Model saved to {model_path}")
                metrics["model_path"] = model_path
            else:
                logger.error("Failed to save model")
                metrics["error_saving_model"] = True
        
        # Update training metrics history
        update_metrics_history(metrics)
        
        return {
            "success": True,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in training: {e}")
        return {"error": f"Unexpected error: {e}"}

def update_metrics_history(new_metrics):
    """
    Update the metrics history file with new training results
    
    Args:
        new_metrics (dict): The metrics to add
        
    Returns:
        bool: Success status
    """
    try:
        # Load existing metrics if file exists
        metrics_history = []
        if os.path.exists(METRICS_FILE):
            with open(METRICS_FILE, 'r', encoding='utf-8') as f:
                metrics_history = json.load(f)
        
        # Add new metrics
        metrics_history.append(new_metrics)
        
        # Sort by timestamp
        metrics_history.sort(key=lambda x: x.get("timestamp", ""))
        
        # Save updated metrics
        with open(METRICS_FILE, 'w', encoding='utf-8') as f:
            json.dump(metrics_history, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Updated metrics history ({len(metrics_history)} entries)")
        return True
        
    except Exception as e:
        logger.error(f"Error updating metrics history: {e}")
        return False

def analyze_training_trends():
    """
    Analyze training metrics history for trends
    
    Returns:
        dict: Analysis results
    """
    try:
        if not os.path.exists(METRICS_FILE):
            logger.warning("No metrics history found")
            return {"error": "No metrics history found"}
        
        # Load metrics history
        with open(METRICS_FILE, 'r', encoding='utf-8') as f:
            metrics_history = json.load(f)
        
        if not metrics_history:
            return {"error": "Metrics history is empty"}
        
        # Sort by timestamp
        metrics_history.sort(key=lambda x: x.get("timestamp", ""))
        
        # Extract key metrics
        timestamps = []
        accuracies = []
        train_durations = []
        example_counts = []
        intent_counts = []
        
        for metrics in metrics_history:
            try:
                # Parse timestamp
                ts = datetime.datetime.fromisoformat(metrics.get("timestamp", ""))
                timestamps.append(ts)
                
                # Get other metrics
                accuracies.append(metrics.get("accuracy", 0))
                train_durations.append(metrics.get("training_duration", 0))
                example_counts.append(metrics.get("training_examples", 0))
                
                # Count intents
                intent_distribution = metrics.get("intent_distribution", {})
                intent_counts.append(len(intent_distribution))
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid metrics entry: {e}")
                continue
        
        # Calculate trends
        accuracy_trend = None
        example_trend = None
        
        if len(accuracies) >= 2:
            accuracy_trend = "improving" if accuracies[-1] > accuracies[0] else "declining"
            example_trend = "growing" if example_counts[-1] > example_counts[0] else "shrinking"
        
        # Find best and worst models
        best_idx = accuracies.index(max(accuracies)) if accuracies else None
        worst_idx = accuracies.index(min(accuracies)) if accuracies else None
        
        best_model = metrics_history[best_idx] if best_idx is not None else None
        worst_model = metrics_history[worst_idx] if worst_idx is not None else None
        
        # Most common intents across all models
        all_intents = set()
        for metrics in metrics_history:
            intent_distribution = metrics.get("intent_distribution", {})
            all_intents.update(intent_distribution.keys())
        
        # Prepare analysis
        analysis = {
            "total_training_runs": len(metrics_history),
            "first_training": timestamps[0].isoformat() if timestamps else None,
            "latest_training": timestamps[-1].isoformat() if timestamps else None,
            "average_accuracy": sum(accuracies) / len(accuracies) if accuracies else 0,
            "accuracy_trend": accuracy_trend,
            "training_examples_trend": example_trend,
            "best_model": {
                "accuracy": best_model.get("accuracy") if best_model else None,
                "timestamp": best_model.get("timestamp") if best_model else None,
                "training_examples": best_model.get("training_examples") if best_model else None,
                "model_path": best_model.get("model_path") if best_model else None
            },
            "worst_model": {
                "accuracy": worst_model.get("accuracy") if worst_model else None,
                "timestamp": worst_model.get("timestamp") if worst_model else None,
                "training_examples": worst_model.get("training_examples") if worst_model else None
            },
            "current_intents": sorted(list(all_intents))
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing training trends: {e}")
        return {"error": f"Error analyzing training trends: {e}"}

def analyze_model_errors(data_path=None, best_model=True):
    """
    Analyze errors made by the model to identify improvement areas
    
    Args:
        data_path (str, optional): Path to evaluation data
        best_model (bool): Whether to use the best model instead of current
        
    Returns:
        dict: Error analysis results
    """
    try:
        # Import ML engine components
        sys.path.append(SCRIPT_DIR)
        from chatbot.ml_engine import intent_classifier
        
        # Load data
        if data_path is None:
            data_path = TRAINING_DATA_PATH
            
        if not os.path.exists(data_path):
            return {"error": f"Data not found at {data_path}"}
        
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # If using best model, find and load it
        if best_model:
            analysis = analyze_training_trends()
            best_model_path = analysis.get("best_model", {}).get("model_path")
            
            if best_model_path and os.path.exists(best_model_path):
                logger.info(f"Loading best model from {best_model_path}")
                intent_classifier.load_model(best_model_path)
            else:
                logger.warning("Best model not found, using current model")
        
        # Prepare data for evaluation
        texts = []
        true_intents = []
        
        for item in data:
            text = item.get("text")
            intent = item.get("intent")
            
            if text and intent:
                texts.append(text)
                true_intents.append(intent)
        
        # Make predictions
        predictions = []
        confidences = []
        
        for text in texts:
            result = intent_classifier.predict(text)
            predictions.append(result.get("intent"))
            confidences.append(result.get("confidence", 0))
        
        # Calculate confusion matrix and classification report
        from sklearn.metrics import confusion_matrix, classification_report
        
        # Filter out None predictions
        valid_indices = [i for i, pred in enumerate(predictions) if pred is not None]
        
        if not valid_indices:
            return {"error": "No valid predictions made"}
        
        filtered_true = [true_intents[i] for i in valid_indices]
        filtered_pred = [predictions[i] for i in valid_indices]
        
        # Generate classification report
        report = classification_report(filtered_true, filtered_pred, output_dict=True)
        
        # Find the most confused intent pairs
        cm = confusion_matrix(filtered_true, filtered_pred, labels=sorted(set(filtered_true)))
        
        # Get unique labels
        labels = sorted(set(filtered_true))
        
        # Find where the model is most confused
        confusion_pairs = []
        
        for i in range(len(labels)):
            for j in range(len(labels)):
                if i != j and cm[i, j] > 0:
                    confusion_pairs.append({
                        "true": labels[i],
                        "predicted": labels[j],
                        "count": int(cm[i, j])
                    })
        
        # Sort by count in descending order
        confusion_pairs.sort(key=lambda x: x["count"], reverse=True)
        
        # Find examples with lowest confidence
        low_confidence = []
        
        for i, text in enumerate(texts):
            pred = predictions[i]
            conf = confidences[i]
            true = true_intents[i]
            
            if pred is not None and conf < 0.7:  # Threshold for "low confidence"
                low_confidence.append({
                    "text": text,
                    "true_intent": true,
                    "predicted_intent": pred,
                    "confidence": conf,
                    "correct": pred == true
                })
        
        # Sort by confidence in ascending order
        low_confidence.sort(key=lambda x: x["confidence"])
        
        # Find intents with highest error rates
        intent_errors = {}
        for i, intent in enumerate(true_intents):
            if intent not in intent_errors:
                intent_errors[intent] = {"total": 0, "errors": 0}
            
            intent_errors[intent]["total"] += 1
            
            if predictions[i] != intent:
                intent_errors[intent]["errors"] += 1
        
        # Calculate error rates
        intent_error_rates = []
        for intent, counts in intent_errors.items():
            if counts["total"] > 0:
                error_rate = counts["errors"] / counts["total"]
                intent_error_rates.append({
                    "intent": intent,
                    "error_rate": error_rate,
                    "total": counts["total"],
                    "errors": counts["errors"]
                })
        
        # Sort by error rate in descending order
        intent_error_rates.sort(key=lambda x: x["error_rate"], reverse=True)
        
        # Prepare results
        results = {
            "overall_accuracy": report.get("accuracy", 0),
            "intent_error_rates": intent_error_rates[:5],  # Top 5 intents with highest error rates
            "confusion_pairs": confusion_pairs[:5],  # Top 5 confused intent pairs
            "low_confidence_examples": low_confidence[:10],  # Top 10 examples with lowest confidence
            "improvement_suggestions": []
        }
        
        # Generate improvement suggestions
        if intent_error_rates:
            for item in intent_error_rates[:3]:
                intent = item["intent"]
                results["improvement_suggestions"].append(
                    f"Add more training examples for intent '{intent}' (error rate: {item['error_rate']:.2f})"
                )
        
        if confusion_pairs:
            for pair in confusion_pairs[:3]:
                true_intent = pair["true"]
                pred_intent = pair["predicted"]
                results["improvement_suggestions"].append(
                    f"Clarify distinction between intents '{true_intent}' and '{pred_intent}'"
                )
        
        if low_confidence_examples:
            results["improvement_suggestions"].append(
                "Add more diverse examples for the intents with lowest confidence predictions"
            )
        
        return results
        
    except Exception as e:
        logger.error(f"Error analyzing model errors: {e}")
        return {"error": f"Error analyzing model errors: {e}"}

def main():
    """Process command line arguments and run requested actions"""
    parser = argparse.ArgumentParser(description="Train and evaluate ML models")
    
    parser.add_argument(
        "--action", 
        choices=["train", "analyze_trends", "analyze_errors", "all"],
        default="train",
        help="Action to perform"
    )
    
    parser.add_argument(
        "--data", 
        type=str,
        help="Path to training data (default: data/intent_training_data.json)"
    )
    
    parser.add_argument(
        "--test_size", 
        type=float,
        default=0.2,
        help="Portion of data to use for testing (default: 0.2)"
    )
    
    parser.add_argument(
        "--no_save", 
        action="store_true",
        help="Don't save the trained model"
    )
    
    parser.add_argument(
        "--version", 
        type=str,
        help="Custom version suffix for the model"
    )
    
    parser.add_argument(
        "--use_best_model", 
        action="store_true",
        help="Use the best model for error analysis instead of current"
    )
    
    args = parser.parse_args()
    
    if args.action == "train" or args.action == "all":
        logger.info("Starting model training and evaluation")
        results = train_and_evaluate_model(
            data_path=args.data,
            test_size=args.test_size,
            save_model=not args.no_save,
            version_suffix=args.version
        )
        
        if "error" in results:
            logger.error(f"Training failed: {results['error']}")
        else:
            metrics = results.get("metrics", {})
            logger.info(f"Training successful! Accuracy: {metrics.get('accuracy', 0):.4f}")
    
    if args.action == "analyze_trends" or args.action == "all":
        logger.info("Analyzing training history trends")
        trends = analyze_training_trends()
        
        if "error" in trends:
            logger.error(f"Trend analysis failed: {trends['error']}")
        else:
            logger.info(f"Trend analysis complete:")
            logger.info(f"- Training runs: {trends.get('total_training_runs', 0)}")
            logger.info(f"- Average accuracy: {trends.get('average_accuracy', 0):.4f}")
            logger.info(f"- Accuracy trend: {trends.get('accuracy_trend', 'unknown')}")
            
            best_accuracy = trends.get("best_model", {}).get("accuracy", 0)
            logger.info(f"- Best model accuracy: {best_accuracy:.4f}")
            
            logger.info(f"- Current intents: {', '.join(trends.get('current_intents', []))}")
    
    if args.action == "analyze_errors" or args.action == "all":
        logger.info("Analyzing model errors")
        error_analysis = analyze_model_errors(
            data_path=args.data,
            best_model=args.use_best_model
        )
        
        if "error" in error_analysis:
            logger.error(f"Error analysis failed: {error_analysis['error']}")
        else:
            logger.info(f"Error analysis complete:")
            logger.info(f"- Overall accuracy: {error_analysis.get('overall_accuracy', 0):.4f}")
            
            # Print improvement suggestions
            logger.info("Improvement suggestions:")
            for suggestion in error_analysis.get("improvement_suggestions", []):
                logger.info(f"  - {suggestion}")
            
            # Print the most confused intent pairs
            logger.info("Most confused intent pairs:")
            for pair in error_analysis.get("confusion_pairs", [])[:3]:
                logger.info(f"  - {pair['true']} confused with {pair['predicted']} ({pair['count']} times)")
    
    logger.info("Script execution complete")

if __name__ == "__main__":
    main()