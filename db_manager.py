"""
MongoDB Database Manager for Fashion Style Analyzer

This module handles database operations for storing user feedback,
image metadata, and style analysis results.
"""

import os
import datetime
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection string
MONGODB_URI = os.environ.get('MONGODB_URI')
MONGODB_DB = os.environ.get('MONGODB_DB', 'style')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages MongoDB database operations for the Fashion Style Analyzer app."""
    
    def __init__(self):
        """Initialize the database connection."""
        try:
            self.client = MongoClient(MONGODB_URI)
            # Ping the database to verify connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
            # Set up database and collections
            self.db = self.client[MONGODB_DB]
            self.feedback_collection = self.db['user_feedback']
            self.images_collection = self.db['image_metadata']
            self.style_predictions_collection = self.db['style_predictions']
            
            # Create indexes for better query performance
            self.feedback_collection.create_index("prediction_id")
            self.images_collection.create_index("image_id")
            self.style_predictions_collection.create_index("prediction_id")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
        except OperationFailure as e:
            logger.error(f"MongoDB authentication failed: {e}")
            self.client = None
    
    def store_feedback(self, feedback_data):
        """
        Store user feedback about style prediction accuracy.
        
        Args:
            feedback_data: Dictionary containing:
                - prediction_id: Unique identifier for the prediction
                - predicted_style: The style that was predicted
                - is_accurate: Boolean indicating if prediction was accurate
                - timestamp: When feedback was provided
                
        Returns:
            Boolean indicating if operation was successful
        """
        if not self.client:
            logger.error("Database connection not available")
            return False
        
        try:
            # Add a timestamp if not provided
            if 'timestamp' not in feedback_data:
                feedback_data['timestamp'] = datetime.datetime.now().isoformat()
                
            # Insert feedback
            result = self.feedback_collection.insert_one(feedback_data)
            logger.info(f"Feedback stored with ID: {result.inserted_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing feedback: {e}")
            return False
    
    def store_image_metadata(self, image_metadata):
        """
        Store metadata about an uploaded image.
        
        Args:
            image_metadata: Dictionary containing:
                - image_id: Unique identifier for the image
                - storage_path: Path/URL where image is stored
                - upload_timestamp: When image was uploaded
                - file_size: Size of the image in bytes
                - dimensions: Image dimensions (width, height)
                
        Returns:
            Boolean indicating if operation was successful
        """
        if not self.client:
            logger.error("Database connection not available")
            return False
        
        try:
            # Add a timestamp if not provided
            if 'upload_timestamp' not in image_metadata:
                image_metadata['upload_timestamp'] = datetime.datetime.now().isoformat()
                
            result = self.images_collection.insert_one(image_metadata)
            logger.info(f"Image metadata stored with ID: {result.inserted_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing image metadata: {e}")
            return False
    
    def store_style_prediction(self, prediction_data):
        """
        Store a style prediction result.
        
        Args:
            prediction_data: Dictionary containing:
                - prediction_id: Unique identifier for the prediction
                - image_id: ID of the analyzed image
                - primary_style: Main predicted style
                - style_tags: List of style tags
                - confidence_score: Confidence in the prediction
                - attributes: Detected garment attributes
                - timestamp: When prediction was made
                
        Returns:
            Boolean indicating if operation was successful
        """
        if not self.client:
            logger.error("Database connection not available")
            return False
        
        try:
            # Add a timestamp if not provided
            if 'timestamp' not in prediction_data:
                prediction_data['timestamp'] = datetime.datetime.now().isoformat()
                
            result = self.style_predictions_collection.insert_one(prediction_data)
            logger.info(f"Style prediction stored with ID: {result.inserted_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing style prediction: {e}")
            return False
    
    def get_feedback_stats(self):
        """
        Get statistics about user feedback.
        
        Returns:
            Dictionary with feedback statistics
        """
        if not self.client:
            logger.error("Database connection not available")
            return {"error": "Database connection not available"}
        
        try:
            # Count total feedback entries
            total_feedback = self.feedback_collection.count_documents({})
            
            # Count accurate predictions
            accurate_predictions = self.feedback_collection.count_documents({"is_accurate": True})
            
            # Calculate accuracy percentage
            accuracy_percentage = (accurate_predictions / total_feedback * 100) if total_feedback > 0 else 0
            
            # Get the most common accurate and inaccurate styles
            accurate_styles_pipeline = [
                {"$match": {"is_accurate": True}},
                {"$group": {"_id": "$predicted_style", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            
            inaccurate_styles_pipeline = [
                {"$match": {"is_accurate": False}},
                {"$group": {"_id": "$predicted_style", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 5}
            ]
            
            accurate_styles = list(self.feedback_collection.aggregate(accurate_styles_pipeline))
            inaccurate_styles = list(self.feedback_collection.aggregate(inaccurate_styles_pipeline))
            
            return {
                "total_feedback": total_feedback,
                "accurate_predictions": accurate_predictions,
                "inaccurate_predictions": total_feedback - accurate_predictions,
                "accuracy_percentage": accuracy_percentage,
                "most_accurate_styles": accurate_styles,
                "most_inaccurate_styles": inaccurate_styles
            }
        except Exception as e:
            logger.error(f"Error getting feedback stats: {e}")
            return {"error": str(e)}

    def get_style_history(self, limit=10):
        """
        Get recent style predictions.
        
        Args:
            limit: Maximum number of predictions to return
            
        Returns:
            List of recent style predictions
        """
        if not self.client:
            logger.error("Database connection not available")
            return []
        
        try:
            # Get recent predictions sorted by timestamp
            recent_predictions = list(
                self.style_predictions_collection.find(
                    {}, 
                    {'_id': 0}
                ).sort('timestamp', -1).limit(limit)
            )
            
            return recent_predictions
        except Exception as e:
            logger.error(f"Error getting style history: {e}")
            return []
    
    def close(self):
        """Close the database connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")