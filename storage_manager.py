"""
Storage Manager for Fashion Style Analyzer

This module handles cloud storage operations for storing uploaded images
using Backblaze B2 as the storage provider.
"""

import os
import io
import uuid
import logging
import boto3
from botocore.exceptions import ClientError
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Backblaze B2 connection details
B2_KEY_ID = os.environ.get('BACKBLAZE_KEY_ID')
B2_APPLICATION_KEY = os.environ.get('BACKBLAZE_APPLICATION_KEY')
B2_BUCKET_NAME = os.environ.get('BACKBLAZE_BUCKET_NAME')
B2_ENDPOINT = os.environ.get('BACKBLAZE_ENDPOINT')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageManager:
    """Manages cloud storage operations for the Fashion Style Analyzer app."""
    
    def __init__(self):
        """Initialize the storage connection."""
        try:
            # Initialize S3 client (Backblaze B2 uses S3-compatible API)
            self.s3_client = boto3.client(
                service_name='s3',
                endpoint_url=f'https://{B2_ENDPOINT}',
                aws_access_key_id=B2_KEY_ID,
                aws_secret_access_key=B2_APPLICATION_KEY
            )
            
            # Verify connection by listing buckets
            self.s3_client.list_buckets()
            logger.info("Successfully connected to Backblaze B2 storage")
            
            # Verify bucket exists
            buckets = [bucket['Name'] for bucket in self.s3_client.list_buckets()['Buckets']]
            if B2_BUCKET_NAME not in buckets:
                logger.warning(f"Bucket {B2_BUCKET_NAME} not found. Will attempt to create it.")
                self.s3_client.create_bucket(Bucket=B2_BUCKET_NAME)
                logger.info(f"Created bucket {B2_BUCKET_NAME}")
                
        except ClientError as e:
            logger.error(f"Failed to connect to Backblaze B2: {e}")
            self.s3_client = None
        except Exception as e:
            logger.error(f"Error initializing storage: {e}")
            self.s3_client = None
    
    def store_image(self, image, image_format='JPEG'):
        """
        Store an image in Backblaze B2 storage.
        
        Args:
            image: PIL Image object
            image_format: Format to save the image in (JPEG, PNG, etc.)
            
        Returns:
            Dictionary containing:
                - image_id: Generated unique ID for the image
                - storage_path: Path where image is stored
                - public_url: URL to access the image
                - dimensions: Image dimensions (width, height)
                - file_size: Size of the stored image in bytes
                - success: Boolean indicating if operation was successful
        """
        if not self.s3_client:
            logger.error("Storage connection not available")
            return {"success": False, "error": "Storage connection not available"}
        
        try:
            # Generate unique ID for the image
            image_id = str(uuid.uuid4())
            
            # Define storage path with folder structure
            import datetime
            current_date = datetime.datetime.now().strftime('%Y/%m/%d')
            storage_path = f"uploads/{current_date}/{image_id}.{image_format.lower()}"
            
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format=image_format)
            img_byte_arr.seek(0)
            file_size = img_byte_arr.getbuffer().nbytes
            
            # Upload to Backblaze B2
            self.s3_client.upload_fileobj(
                img_byte_arr, 
                B2_BUCKET_NAME, 
                storage_path,
                ExtraArgs={'ContentType': f'image/{image_format.lower()}'}
            )
            
            # Generate a public URL for the image
            public_url = f"https://{B2_ENDPOINT}/{B2_BUCKET_NAME}/{storage_path}"
            
            logger.info(f"Image stored successfully with ID: {image_id}")
            
            return {
                "image_id": image_id,
                "storage_path": storage_path,
                "public_url": public_url,
                "dimensions": image.size,
                "file_size": file_size,
                "success": True
            }
            
        except ClientError as e:
            logger.error(f"Failed to store image: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error storing image: {e}")
            return {"success": False, "error": str(e)}
    
    def retrieve_image(self, storage_path):
        """
        Retrieve an image from Backblaze B2 storage.
        
        Args:
            storage_path: Path where image is stored
            
        Returns:
            PIL Image object or None if retrieval failed
        """
        if not self.s3_client:
            logger.error("Storage connection not available")
            return None
        
        try:
            # Download the image from Backblaze B2
            response = self.s3_client.get_object(Bucket=B2_BUCKET_NAME, Key=storage_path)
            img_data = response['Body'].read()
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(img_data))
            logger.info(f"Image retrieved successfully from {storage_path}")
            
            return image
            
        except ClientError as e:
            logger.error(f"Failed to retrieve image: {e}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving image: {e}")
            return None
    
    def delete_image(self, storage_path):
        """
        Delete an image from Backblaze B2 storage.
        
        Args:
            storage_path: Path where image is stored
            
        Returns:
            Boolean indicating if deletion was successful
        """
        if not self.s3_client:
            logger.error("Storage connection not available")
            return False
        
        try:
            # Delete the image from Backblaze B2
            self.s3_client.delete_object(Bucket=B2_BUCKET_NAME, Key=storage_path)
            logger.info(f"Image deleted successfully from {storage_path}")
            
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete image: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting image: {e}")
            return False