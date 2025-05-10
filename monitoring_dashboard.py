# monitoring_dashboard.py
# Web dashboard for monitoring chatbot performance

import os
import json
import logging
import datetime
import pandas as pd
import numpy as np
from pathlib import Path
from flask import Flask, render_template, jsonify, request

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("monitoring")

# Path constants
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
METRICS_FILE = os.path.join(DATA_DIR, "training_metrics.json")
FEEDBACK_DIR = os.path.join(DATA_DIR, "feedback")
APPROVED_FILE = os.path.join(FEEDBACK_DIR, "approved_examples.json")
REJECTED_FILE = os.path.join(FEEDBACK_DIR, "rejected_examples.json")
LOG_FILE = "chatbot.log"

# Create Flask app
app = Flask(__name__)

@app.route('/')
def index():
    """Render the main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/metrics')
def api_metrics():
    """Return training metrics data"""
    try:
        if os.path.exists(METRICS_FILE):
            with open(METRICS_FILE, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
            return jsonify(metrics)
        else:
            return jsonify([])
    except Exception as e:
        logger.error(f"Error loading metrics: {e}")
        return jsonify({"error": str(e)})

@app.route('/api/feedback')
def api_feedback():
    """Return feedback data"""
    try:
        feedback_data = {
            "approved": [],
            "rejected": []
        }
        
        if os.path.exists(APPROVED_FILE):
            with open(APPROVED_FILE, 'r', encoding='utf-8') as f:
                feedback_data["approved"] = json.load(f)
        
        if os.path.exists(REJECTED_FILE):
            with open(REJECTED_FILE, 'r', encoding='utf-8') as f:
                feedback_data["rejected"] = json.load(f)
                
        # Calculate summary statistics
        stats = {
            "total_feedback": len(feedback_data["approved"]) + len(feedback_data["rejected"]),
            "approved_count": len(feedback_data["approved"]),
            "rejected_count": len(feedback_data["rejected"]),
            "approval_rate": 0
        }
        
        if stats["total_feedback"] > 0:
            stats["approval_rate"] = stats["approved_count"] / stats["total_feedback"]
        
        # Group by intent
        intent_counts = {}
        for entry in feedback_data["approved"] + feedback_data["rejected"]:
            intent = entry.get("intent", "unknown")
            quality = entry.get("quality", "unknown")
            
            if intent not in intent_counts:
                intent_counts[intent] = {"good": 0, "bad": 0, "total": 0}
            
            intent_counts[intent]["total"] += 1
            if quality == "good":
                intent_counts[intent]["good"] += 1
            elif quality == "bad":
                intent_counts[intent]["bad"] += 1
        
        # Calculate approval rates by intent
        intent_stats = []
        for intent, counts in intent_counts.items():
            if counts["total"] > 0:
                approval_rate = counts["good"] / counts["total"]
                intent_stats.append({
                    "intent": intent,
                    "good": counts["good"],
                    "bad": counts["bad"],
                    "total": counts["total"],
                    "approval_rate": approval_rate
                })
        
        # Sort by total count
        intent_stats.sort(key=lambda x: x["total"], reverse=True)
        
        return jsonify({
            "stats": stats,
            "intent_stats": intent_stats,
            "recent_approved": feedback_data["approved"][-10:],
            "recent_rejected": feedback_data["rejected"][-10:]
        })
        
    except Exception as e:
        logger.error(f"Error loading feedback data: {e}")
        return jsonify({"error": str(e)})

@app.route('/api/logs')
def api_logs():
    """Return recent log entries"""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                log_lines = f.readlines()
            
            # Parse log lines
            log_entries = []
            for line in log_lines[-200:]:  # Last 200 lines
                try:
                    parts = line.strip().split(' - ', 3)
                    if len(parts) >= 4:
                        timestamp = parts[0]
                        module = parts[1]
                        level = parts[2]
                        message = parts[3]
                        
                        log_entries.append({
                            "timestamp": timestamp,
                            "module": module,
                            "level": level,
                            "message": message
                        })
                except:
                    # Skip malformed lines
                    continue
            
            return jsonify(log_entries)
        else:
            return jsonify([])
    except Exception as e:
        logger.error(f"Error loading logs: {e}")
        return jsonify({"error": str(e)})

@app.route('/api/conversations')
def api_conversations():
    """Return recent conversations"""
    try:
        # This is just placeholder data - in a real implementation,
        # you would load this from a database or conversation logs
        sample_conversations = [
            {
                "id": "conv1",
                "user_id": "user123",
                "timestamp": "2025-05-08T14:25:30.123",
                "exchanges": [
                    {"user": "Hello there", "bot": "Hi! How can I help you today?"},
                    {"user": "What's the weather like?", "bot": "I'd be happy to check the weather for you. Which city are you interested in?"},
                    {"user": "New York", "bot": "The weather in New York is currently 72°F and partly cloudy with a light breeze."}
                ],
                "metrics": {
                    "duration": 45,
                    "turns": 3,
                    "avg_response_time": 0.8
                }
            },
            {
                "id": "conv2",
                "user_id": "user456",
                "timestamp": "2025-05-08T15:10:45.678",
                "exchanges": [
                    {"user": "Hi, I need help", "bot": "Hello! I'm here to help. What do you need assistance with?"},
                    {"user": "My name is Sarah", "bot": "Nice to meet you, Sarah! I'll remember your name. How can I help you today?"},
                    {"user": "What can you do?", "bot": "I can chat with you about various topics, remember your preferences, check the weather, and more. Is there something specific you'd like to know about?"},
                    {"user": "No thanks, goodbye", "bot": "Alright, Sarah! Have a great day. Feel free to chat anytime!"}
                ],
                "metrics": {
                    "duration": 90,
                    "turns": 4,
                    "avg_response_time": 1.2
                }
            }
        ]
        return jsonify(sample_conversations)
    except Exception as e:
        logger.error(f"Error loading conversations: {e}")
        return jsonify({"error": str(e)})

@app.route('/api/intents')
def api_intents():
    """Return intent distribution and performance"""
    try:
        # Load training data to get intent distribution
        training_data_path = os.path.join(DATA_DIR, "intent_training_data.json")
        intent_distribution = {}
        
        if os.path.exists(training_data_path):
            with open(training_data_path, 'r', encoding='utf-8') as f:
                training_data = json.load(f)
                
                # Count examples per intent
                for item in training_data:
                    intent = item.get("intent")
                    if intent:
                        if intent not in intent_distribution:
                            intent_distribution[intent] = 0
                        intent_distribution[intent] += 1
        
        # Convert to list format for easier consumption by charts
        intent_counts = [{"intent": intent, "count": count} for intent, count in intent_distribution.items()]
        intent_counts.sort(key=lambda x: x["count"], reverse=True)
        
        # Get performance from metrics if available
        intent_performance = []
        if os.path.exists(METRICS_FILE):
            with open(METRICS_FILE, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
                
                if metrics and len(metrics) > 0:
                    # Get the most recent metrics
                    latest_metrics = metrics[-1]
                    
                    # Extract intent-specific metrics if available
                    report = latest_metrics.get("report", {})
                    for intent, stats in report.items():
                        if isinstance(stats, dict) and "f1-score" in stats:
                            intent_performance.append({
                                "intent": intent,
                                "precision": stats.get("precision", 0),
                                "recall": stats.get("recall", 0),
                                "f1_score": stats.get("f1-score", 0)
                            })
        
        return jsonify({
            "distribution": intent_counts,
            "performance": intent_performance
        })
    except Exception as e:
        logger.error(f"Error loading intent data: {e}")
        return jsonify({"error": str(e)})

@app.route('/api/entities')
def api_entities():
    """Return entity extraction statistics"""
    try:
        # This is placeholder data - in a real implementation,
        # you would collect and store entity extraction statistics
        entity_stats = [
            {"type": "location", "count": 285, "accuracy": 0.92},
            {"type": "date", "count": 173, "accuracy": 0.88},
            {"type": "person_name", "count": 124, "accuracy": 0.95},
            {"type": "time", "count": 87, "accuracy": 0.91},
            {"type": "favorite_color", "count": 52, "accuracy": 0.98},
            {"type": "favorite_food", "count": 45, "accuracy": 0.93},
            {"type": "email", "count": 23, "accuracy": 0.99},
            {"type": "phone", "count": 18, "accuracy": 0.97},
            {"type": "organization", "count": 14, "accuracy": 0.85}
        ]
        return jsonify(entity_stats)
    except Exception as e:
        logger.error(f"Error loading entity stats: {e}")
        return jsonify({"error": str(e)})

@app.route('/api/performance')
def api_performance():
    """Return performance metrics over time"""
    try:
        # This is placeholder data - in a real implementation,
        # you would collect and store performance metrics
        now = datetime.datetime.now()
        performance_data = []
        
        # Generate 14 days of sample data
        for i in range(14):
            date = (now - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            performance_data.append({
                "date": date,
                "avg_response_time": round(random.uniform(0.5, 2.0), 2),
                "requests": random.randint(100, 500),
                "accuracy": round(random.uniform(0.75, 0.95), 2),
                "user_rating": round(random.uniform(3.5, 4.8), 1)
            })
        
        # Sort by date
        performance_data.sort(key=lambda x: x["date"])
        
        return jsonify(performance_data)
    except Exception as e:
        logger.error(f"Error loading performance data: {e}")
        return jsonify({"error": str(e)})

# Create the HTML template
@app.route('/templates/dashboard.html')
def dashboard_template():
    """Return the dashboard HTML template"""
    dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatbot Monitoring Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/chart.js@4.0.0/dist/chart.min.css">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
            padding-top: 20px;
        }
        .card {
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        .card-header {
            background-color: #4A90E2;
            color: white;
            font-weight: bold;
            border-radius: 10px 10px 0 0;
        }
        .metric-card {
            text-align: center;
            padding: 15px;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #4A90E2;
        }
        .metric-label {
            font-size: 0.9rem;
            color: #6c757d;
        }
        .chart-container {
            position: relative;
            height: 300px;
            width: 100%;
        }
        .log-entry {
            border-bottom: 1px solid #e9ecef;
            padding: 8px 0;
        }
        .badge-info {
            background-color: #17a2b8;
        }
        .badge-warning {
            background-color: #ffc107;
            color: #212529;
        }
        .badge-error {
            background-color: #dc3545;
        }
        .conversation-card {
            border-left: 4px solid #4A90E2;
            margin-bottom: 15px;
        }
        .user-message {
            background-color: #e9ecef;
            border-radius: 10px;
            padding: 8px 12px;
            margin: 5px 0;
        }
        .bot-message {
            background-color: #d1ecf1;
            border-radius: 10px;
            padding: 8px 12px;
            margin: 5px 0;
        }
        .refresh-btn {
            float: right;
            font-size: 0.8rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">Chatbot Monitoring Dashboard</h1>
        
        <div class="row">
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="metric-value" id="total-conversations">--</div>
                    <div class="metric-label">Total Conversations</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="metric-value" id="avg-accuracy">--</div>
                    <div class="metric-label">Average Accuracy</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="metric-value" id="avg-response-time">--</div>
                    <div class="metric-label">Avg Response Time (s)</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="metric-value" id="user-satisfaction">--</div>
                    <div class="metric-label">User Satisfaction</div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        Performance Over Time
                        <button class="btn btn-sm btn-light refresh-btn" onclick="loadPerformanceData()">
                            <i class="bi bi-arrow-clockwise"></i> Refresh
                        </button>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="performance-chart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        Intent Distribution
                        <button class="btn btn-sm btn-light refresh-btn" onclick="loadIntentData()">
                            <i class="bi bi-arrow-clockwise"></i> Refresh
                        </button>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="intent-chart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        User Feedback
                        <button class="btn btn-sm btn-light refresh-btn" onclick="loadFeedbackData()">
                            <i class="bi bi-arrow-clockwise"></i> Refresh
                        </button>
                    </div>
                    <div class="card-body">
                        <div class="row mb-3">
                            <div class="col-6">
                                <div class="card bg-success text-white">
                                    <div class="card-body text-center">
                                        <h3 id="approved-count">--</h3>
                                        <small>Positive Feedback</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="card bg-danger text-white">
                                    <div class="card-body text-center">
                                        <h3 id="rejected-count">--</h3>
                                        <small>Negative Feedback</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="chart-container" style="height: 200px;">
                            <canvas id="feedback-chart"></canvas>
                        </div>
                        
                        <h5 class="mt-3">Recent Problematic Responses:</h5>
                        <div id="recent-rejected" class="mt-2" style="max-height: 200px; overflow-y: auto;">
                            <div class="text-center text-muted">Loading...</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        Entity Extraction Performance
                        <button class="btn btn-sm btn-light refresh-btn" onclick="loadEntityData()">
                            <i class="bi bi-arrow-clockwise"></i> Refresh
                        </button>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="entity-chart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        Recent Conversations
                        <button class="btn btn-sm btn-light refresh-btn" onclick="loadConversations()">
                            <i class="bi bi-arrow-clockwise"></i> Refresh
                        </button>
                    </div>
                    <div class="card-body">
                        <div id="conversations-container" style="max-height: 400px; overflow-y: auto;">
                            <div class="text-center text-muted">Loading conversations...</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        System Logs
                        <button class="btn btn-sm btn-light refresh-btn" onclick="loadLogs()">
                            <i class="bi bi-arrow-clockwise"></i> Refresh
                        </button>
                    </div>
                    <div class="card-body">
                        <div id="logs-container" style="max-height: 400px; overflow-y: auto;">
                            <div class="text-center text-muted">Loading logs...</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        Model Training History
                        <button class="btn btn-sm btn-light refresh-btn" onclick="loadMetrics()">
                            <i class="bi bi-arrow-clockwise"></i> Refresh
                        </button>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="training-chart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer class="mt-4 mb-4 text-center text-muted">
            <small>&copy; 2025 Wicked Chatbot Monitoring Dashboard</small>
        </footer>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.0.0/dist/chart.umd.min.js"></script>
    <script>
        // Charts objects
        let performanceChart = null;
        let intentChart = null;
        let feedbackChart = null;
        let entityChart = null;
        let trainingChart = null;
        
        // Main function to load all data
        function loadAllData() {
            loadPerformanceData();
            loadIntentData();
            loadFeedbackData();
            loadEntityData();
            loadConversations();
            loadLogs();
            loadMetrics();
        }
        
        // Load performance data
        function loadPerformanceData() {
            fetch('/api/performance')
                .then(response => response.json())
                .then(data => {
                    updatePerformanceMetrics(data);
                    updatePerformanceChart(data);
                })
                .catch(error => console.error('Error loading performance data:', error));
        }
        
        // Update performance metrics
        function updatePerformanceMetrics(data) {
            if (data.length > 0) {
                const latest = data[data.length - 1];
                
                // Update metric cards
                document.getElementById('total-conversations').textContent = 
                    data.reduce((total, day) => total + day.requests, 0).toLocaleString();
                
                document.getElementById('avg-accuracy').textContent = 
                    (data.reduce((total, day) => total + day.accuracy, 0) / data.length).toFixed(2);
                
                document.getElementById('avg-response-time').textContent = 
                    (data.reduce((total, day) => total + day.avg_response_time, 0) / data.length).toFixed(2);
                
                document.getElementById('user-satisfaction').textContent = 
                    (data.reduce((total, day) => total + day.user_rating, 0) / data.length).toFixed(1);
            }
        }
        
        // Update performance chart
        function updatePerformanceChart(data) {
            const ctx = document.getElementById('performance-chart').getContext('2d');
            
            const labels = data.map(day => day.date);
            const accuracyData = data.map(day => day.accuracy);
            const responseTimeData = data.map(day => day.avg_response_time);
            
            if (performanceChart) {
                performanceChart.destroy();
            }
            
            performanceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Accuracy',
                            data: accuracyData,
                            borderColor: '#4A90E2',
                            backgroundColor: 'rgba(74, 144, 226, 0.1)',
                            yAxisID: 'y',
                            tension: 0.3
                        },
                        {
                            label: 'Response Time (s)',
                            data: responseTimeData,
                            borderColor: '#F39C12',
                            backgroundColor: 'rgba(243, 156, 18, 0.1)',
                            yAxisID: 'y1',
                            tension: 0.3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            min: 0,
                            max: 1,
                            title: {
                                display: true,
                                text: 'Accuracy'
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            min: 0,
                            title: {
                                display: true,
                                text: 'Response Time (s)'
                            },
                            grid: {
                                drawOnChartArea: false
                            }
                        }
                    }
                }
            });
        }
        
        // Load intent data
        function loadIntentData() {
            fetch('/api/intents')
                .then(response => response.json())
                .then(data => {
                    updateIntentChart(data);
                })
                .catch(error => console.error('Error loading intent data:', error));
        }
        
        // Update intent chart
        function updateIntentChart(data) {
            const ctx = document.getElementById('intent-chart').getContext('2d');
            
            const distribution = data.distribution || [];
            
            // Sort by count and take top 10
            const top10 = distribution.slice(0, 10);
            
            const labels = top10.map(item => item.intent);
            const counts = top10.map(item => item.count);
            
            if (intentChart) {
                intentChart.destroy();
            }
            
            intentChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Training Examples',
                            data: counts,
                            backgroundColor: 'rgba(74, 144, 226, 0.7)',
                            borderColor: '#4A90E2',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Number of Examples'
                            }
                        }
                    }
                }
            });
        }
        
        // Load feedback data
        function loadFeedbackData() {
            fetch('/api/feedback')
                .then(response => response.json())
                .then(data => {
                    updateFeedbackStats(data);
                    updateFeedbackChart(data);
                    updateRecentRejected(data);
                })
                .catch(error => console.error('Error loading feedback data:', error));
        }
        
        // Update feedback statistics
        function updateFeedbackStats(data) {
            const stats = data.stats || {};
            
            document.getElementById('approved-count').textContent = stats.approved_count || 0;
            document.getElementById('rejected-count').textContent = stats.rejected_count || 0;
        }
        
        // Update feedback chart
        function updateFeedbackChart(data) {
            const ctx = document.getElementById('feedback-chart').getContext('2d');
            
            const intentStats = data.intent_stats || [];
            
            // Sort by total count and take top 5
            const top5 = intentStats.slice(0, 5);
            
            const labels = top5.map(item => item.intent);
            const goodData = top5.map(item => item.good);
            const badData = top5.map(item => item.bad);
            
            if (feedbackChart) {
                feedbackChart.destroy();
            }
            
            feedbackChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Positive Feedback',
                            data: goodData,
                            backgroundColor: 'rgba(40, 167, 69, 0.7)',
                            borderColor: '#28a745',
                            borderWidth: 1
                        },
                        {
                            label: 'Negative Feedback',
                            data: badData,
                            backgroundColor: 'rgba(220, 53, 69, 0.7)',
                            borderColor: '#dc3545',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Feedback Count'
                            },
                            stacked: true
                        },
                        x: {
                            stacked: true
                        }
                    }
                }
            });
        }
        
        // Update recent rejected feedback
        function updateRecentRejected(data) {
            const recentRejected = data.recent_rejected || [];
            const container = document.getElementById('recent-rejected');
            
            if (recentRejected.length === 0) {
                container.innerHTML = '<div class="text-center text-muted">No negative feedback yet</div>';
                return;
            }
            
            let html = '';
            
            for (const item of recentRejected) {
                const date = new Date(item.timestamp).toLocaleString();
                
                html += `
                    <div class="log-entry">
                        <div><strong>User:</strong> ${item.user_input}</div>
                        <div><strong>Bot:</strong> ${item.response}</div>
                        <div><small class="text-muted">Intent: ${item.intent || 'Unknown'} | ${date}</small></div>
                    </div>
                `;
            }
            
            container.innerHTML = html;
        }
        
        // Load entity data
        function loadEntityData() {
            fetch('/api/entities')
                .then(response => response.json())
                .then(data => {
                    updateEntityChart(data);
                })
                .catch(error => console.error('Error loading entity data:', error));
        }
        
        // Update entity chart
        function updateEntityChart(data) {
            const ctx = document.getElementById('entity-chart').getContext('2d');
            
            // Sort by count and take all
            const sortedData = [...data].sort((a, b) => b.count - a.count);
            
            const labels = sortedData.map(item => item.type);
            const counts = sortedData.map(item => item.count);
            const accuracies = sortedData.map(item => item.accuracy * 100);
            
            if (entityChart) {
                entityChart.destroy();
            }
            
            entityChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Extracted Count',
                            data: counts,
                            backgroundColor: 'rgba(74, 144, 226, 0.7)',
                            borderColor: '#4A90E2',
                            borderWidth: 1,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Accuracy (%)',
                            data: accuracies,
                            backgroundColor: 'rgba(40, 167, 69, 0.7)',
                            borderColor: '#28a745',
                            borderWidth: 1,
                            type: 'line',
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Extraction Count'
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            beginAtZero: true,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Accuracy (%)'
                            },
                            grid: {
                                drawOnChartArea: false
                            }
                        }
                    }
                }
            });
        }
        
        // Load conversations
        function loadConversations() {
            fetch('/api/conversations')
                .then(response => response.json())
                .then(data => {
                    updateConversations(data);
                })
                .catch(error => console.error('Error loading conversations:', error));
        }
        
        // Update conversations
        function updateConversations(data) {
            const container = document.getElementById('conversations-container');
            
            if (data.length === 0) {
                container.innerHTML = '<div class="text-center text-muted">No conversations yet</div>';
                return;
            }
            
            let html = '';
            
            for (const conversation of data) {
                const date = new Date(conversation.timestamp).toLocaleString();
                
                html += `
                    <div class="conversation-card p-3">
                        <div class="d-flex justify-content-between mb-2">
                            <div><strong>User ID:</strong> ${conversation.user_id}</div>
                            <div><small class="text-muted">${date}</small></div>
                        </div>
                        <div class="mb-2">
                            <strong>Exchanges:</strong> ${conversation.exchanges.length} | 
                            <strong>Duration:</strong> ${conversation.metrics.duration}s
                        </div>
                        <div>
                `;
                
                // Add the first 3 exchanges
                const displayExchanges = conversation.exchanges.slice(0, 3);
                
                for (const exchange of displayExchanges) {
                    html += `
                        <div class="user-message">${exchange.user}</div>
                        <div class="bot-message">${exchange.bot}</div>
                    `;
                }
                
                // Add ellipsis if there are more exchanges
                if (conversation.exchanges.length > 3) {
                    html += `<div class="text-center text-muted">... ${conversation.exchanges.length - 3} more exchanges</div>`;
                }
                
                html += `
                        </div>
                    </div>
                `;
            }
            
            container.innerHTML = html;
        }
        
        // Load logs
        function loadLogs() {
            fetch('/api/logs')
                .then(response => response.json())
                .then(data => {
                    updateLogs(data);
                })
                .catch(error => console.error('Error loading logs:', error));
        }
        
        // Update logs
        function updateLogs(data) {
            const container = document.getElementById('logs-container');
            
            if (data.length === 0) {
                container.innerHTML = '<div class="text-center text-muted">No logs available</div>';
                return;
            }
            
            let html = '';
            
            // Reverse to show newest first
            const recentLogs = [...data].reverse().slice(0, 50);
            
            for (const log of recentLogs) {
                let badgeClass = 'bg-secondary';
                
                if (log.level === 'INFO') {
                    badgeClass = 'bg-info';
                } else if (log.level === 'WARNING') {
                    badgeClass = 'bg-warning text-dark';
                } else if (log.level === 'ERROR') {
                    badgeClass = 'bg-danger';
                }
                
                html += `
                    <div class="log-entry">
                        <div>
                            <span class="badge ${badgeClass}">${log.level}</span>
                            <small class="text-muted">${log.timestamp} | ${log.module}</small>
                        </div>
                        <div>${log.message}</div>
                    </div>
                `;
            }
            
            container.innerHTML = html;
        }
        
        // Load metrics
        function loadMetrics() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    updateTrainingChart(data);
                })
                .catch(error => console.error('Error loading metrics:', error));
        }
        
        // Update training chart
        function updateTrainingChart(data) {
            const ctx = document.getElementById('training-chart').getContext('2d');
            
            if (data.length === 0) {
                if (trainingChart) {
                    trainingChart.destroy();
                }
                trainingChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: ['No Data'],
                        datasets: [{
                            label: 'No training data available',
                            data: [0],
                            backgroundColor: 'rgba(200, 200, 200, 0.7)'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
                return;
            }
            
            const timestamps = data.map(item => {
                const date = new Date(item.timestamp);
                return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            });
            
            const accuracies = data.map(item => item.accuracy);
            const examples = data.map(item => item.training_examples);
            
            if (trainingChart) {
                trainingChart.destroy();
            }
            
            trainingChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: timestamps,
                    datasets: [
                        {
                            label: 'Accuracy',
                            data: accuracies,
                            borderColor: '#4A90E2',
                            backgroundColor: 'rgba(74, 144, 226, 0.1)',
                            yAxisID: 'y',
                            tension: 0.3
                        },
                        {
                            label: 'Training Examples',
                            data: examples,
                            borderColor: '#28a745',
                            backgroundColor: 'rgba(40, 167, 69, 0.1)',
                            yAxisID: 'y1',
                            tension: 0.3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            min: 0,
                            max: 1,
                            title: {
                                display: true,
                                text: 'Accuracy'
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            min: 0,
                            title: {
                                display: true,
                                text: 'Training Examples'
                            },
                            grid: {
                                drawOnChartArea: false
                            }
                        }
                    }
                }
            });
        }
        
        // Load all data on page load
        window.addEventListener('load', loadAllData);
        
        // Reload data every 5 minutes
        setInterval(loadAllData, 5 * 60 * 1000);
    </script>
</body>
</html>
    """
    return dashboard_html

# Add this for importing random in the /api/performance endpoint
import random

if __name__ == "__main__":
    # Run the dashboard on a different port than the main app
    app.run(host="127.0.0.1", port=5001, debug=True)