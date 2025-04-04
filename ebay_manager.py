"""
eBay API Manager for Fashion Style Analyzer

This module handles eBay API operations for fetching product recommendations
based on predicted fashion styles.
"""

import os
import logging
import json
from ebaysdk.finding import Connection as Finding
from ebaysdk.exception import ConnectionError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# eBay API credentials
EBAY_APP_ID = os.environ.get('EBAY_APP_ID')
EBAY_CERT_ID = os.environ.get('EBAY_CERT_ID')
EBAY_DEV_ID = os.environ.get('EBAY_DEV_ID')
EBAY_SANDBOX_MODE = os.environ.get('EBAY_SANDBOX_MODE', 'True').lower() in ('true', '1', 't')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EbayManager:
    """Manages eBay API operations for the Fashion Style Analyzer app."""
    
    def __init__(self):
        """Initialize the eBay API connection."""
        # eBay Partner Network (EPN) tracking information
        self.ebay_affiliate_id = os.environ.get('EBAY_AFFILIATE_ID', '12345678')
        self.ebay_affiliate_campaign_id = os.environ.get('EBAY_CAMPAIGN_ID', 'fashion-style')
        self.ebay_affiliate_custom_id = os.environ.get('EBAY_CUSTOM_ID', 'styledeeplearn')
        
        try:
            # Initialize eBay Finding API client
            self.api = Finding(
                domain='svcs.sandbox.ebay.com' if EBAY_SANDBOX_MODE else 'svcs.ebay.com',
                appid=EBAY_APP_ID,
                config_file=None
            )
            logger.info(f"Initialized eBay API client (Sandbox mode: {EBAY_SANDBOX_MODE})")
            self.connection_available = True
            
        except ConnectionError as e:
            logger.error(f"Failed to initialize eBay API client: {e}")
            self.api = None
            self.connection_available = False
        except Exception as e:
            logger.error(f"Error setting up eBay API client: {e}")
            self.api = None
            self.connection_available = False
    
    def search_products(self, style, user_comments='', limit=6):
        """
        Search for fashion products on eBay.
        
        Args:
            style: Primary fashion style to search for
            user_comments: Optional user comments for refining search
            limit: Maximum number of products to return
            
        Returns:
            List of product dictionaries with details
        """
        if not self.connection_available:
            logger.error("eBay API connection not available")
            return []
        
        # Create the search query
        search_query = f"{style} fashion"
        
        # Enhance search with keywords from user comments if available
        if user_comments:
            logger.info(f"Enhancing search with user comments: {user_comments}")
            search_query += f" {user_comments}"
        
        logger.info(f"Searching eBay for: {search_query}")
        
        try:
            # Make the API call to eBay Finding API
            response = self.api.execute('findItemsAdvanced', {
                'keywords': search_query,
                'categoryId': '11450',  # eBay category ID for Clothing, Shoes & Accessories
                'sortOrder': 'BestMatch',
                'paginationInput': {
                    'entriesPerPage': limit,
                    'pageNumber': 1
                },
                'itemFilter': [
                    {'name': 'Condition', 'value': 'New'},
                    {'name': 'ListingType', 'value': 'FixedPrice'}
                ],
                'outputSelector': ['SellerInfo', 'GalleryInfo']
            })
            
            # Parse the response
            response_dict = response.dict()
            
            # Check if any items were found
            if 'searchResult' not in response_dict or 'item' not in response_dict['searchResult']:
                logger.warning(f"No items found for query: {search_query}")
                return []
            
            # Extract items from the response
            items = response_dict['searchResult']['item']
            logger.info(f"Found {len(items)} items for {search_query}")
            
            # Format products for our application
            products = []
            for item in items:
                try:
                    # Extract product details and add affiliate tracking to URL
                    item_id = item['itemId']
                    original_url = item['viewItemURL']
                    affiliate_url = self.add_affiliate_tracking(original_url, item_id, style)
                    
                    product = {
                        'id': item_id,
                        'title': item['title'],
                        'price': f"{item['sellingStatus']['currentPrice']['value']} {item['sellingStatus']['currentPrice']['_currencyId']}",
                        'currency': item['sellingStatus']['currentPrice']['_currencyId'],
                        'image': item.get('galleryURL', 'https://placehold.co/200x150/2a2a2a/ffffff?text=No+Image'),
                        'url': affiliate_url,  # Use URL with affiliate tracking
                        'location': item.get('location', 'Unknown'),
                        'condition': item.get('condition', {}).get('conditionDisplayName', 'New'),
                        'seller': item.get('sellerInfo', {}).get('sellerUserName', 'Unknown'),
                        'seller_rating': item.get('sellerInfo', {}).get('positiveFeedbackPercent', 'N/A'),
                        'shipping_type': item.get('shippingInfo', {}).get('shippingType', 'Unknown'),
                        'shipping_cost': item.get('shippingInfo', {}).get('shippingServiceCost', {}).get('value', 'Unknown')
                    }
                    
                    # Add star rating (hardcoded since eBay doesn't provide this in the Finding API)
                    seller_rating = item.get('sellerInfo', {}).get('positiveFeedbackPercent', 0)
                    if seller_rating:
                        try:
                            rating = float(seller_rating) / 20  # Convert percent to 0-5 scale
                            product['rating'] = min(5, max(0, rating))
                        except (ValueError, TypeError):
                            product['rating'] = 4.0  # Default rating
                    else:
                        product['rating'] = 4.0  # Default rating
                    
                    # Add reviews count (not available in eBay API, using dummy value)
                    product['reviews'] = 0
                    
                    products.append(product)
                except Exception as e:
                    logger.error(f"Error parsing product data: {e}")
                    continue
            
            return products
            
        except ConnectionError as e:
            logger.error(f"eBay API connection error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching eBay products: {e}")
            return []
    
    def add_affiliate_tracking(self, url, item_id=None, style=None):
        """
        Add eBay Partner Network (EPN) affiliate tracking parameters to a URL.
        
        Args:
            url: Original eBay URL
            item_id: Optional item ID for tracking specific items
            style: Optional style for campaign tracking
            
        Returns:
            URL with affiliate tracking parameters
        """
        if not url:
            return url
            
        # Add affiliate tracking parameters
        tracking_params = {
            'mkrid': self.ebay_affiliate_id,
            'campid': self.ebay_affiliate_campaign_id,
            'customid': self.ebay_affiliate_custom_id
        }
        
        # Add item ID if provided
        if item_id:
            tracking_params['mkcid'] = f'item-{item_id}'
            
        # Add style if provided
        if style:
            style_tag = style.lower().replace(' ', '-')
            tracking_params['mkevt'] = f'style-{style_tag}'
            
        # Add tracking parameters to URL
        if '?' in url:
            affiliate_url = url + '&'
        else:
            affiliate_url = url + '?'
            
        # Append parameters
        param_strings = [f"{key}={value}" for key, value in tracking_params.items()]
        affiliate_url += '&'.join(param_strings)
        
        return affiliate_url
    
    def get_similar_items(self, item_id, limit=6):
        """
        Get similar items to a specific eBay item.
        
        Args:
            item_id: eBay item ID to find similar items for
            limit: Maximum number of similar items to return
            
        Returns:
            List of similar product dictionaries
        """
        if not self.connection_available:
            logger.error("eBay API connection not available")
            return []
        
        logger.info(f"Searching for items similar to {item_id}")
        
        try:
            # Make the API call to eBay Finding API
            response = self.api.execute('findItemsByProduct', {
                'productId': item_id,
                'paginationInput': {
                    'entriesPerPage': limit,
                    'pageNumber': 1
                }
            })
            
            # Parse the response
            response_dict = response.dict()
            
            # Check if any items were found
            if 'searchResult' not in response_dict or 'item' not in response_dict['searchResult']:
                logger.warning(f"No similar items found for item ID: {item_id}")
                return []
            
            # Extract items from the response
            items = response_dict['searchResult']['item']
            logger.info(f"Found {len(items)} similar items for {item_id}")
            
            # Format products for our application
            products = []
            for item in items:
                try:
                    # Extract product details and add affiliate tracking to URL
                    similar_item_id = item['itemId']
                    original_url = item['viewItemURL']
                    affiliate_url = self.add_affiliate_tracking(original_url, similar_item_id, None)
                    
                    product = {
                        'id': similar_item_id,
                        'title': item['title'],
                        'price': f"{item['sellingStatus']['currentPrice']['value']} {item['sellingStatus']['currentPrice']['_currencyId']}",
                        'currency': item['sellingStatus']['currentPrice']['_currencyId'],
                        'image': item.get('galleryURL', 'https://placehold.co/200x150/2a2a2a/ffffff?text=No+Image'),
                        'url': affiliate_url,  # Use URL with affiliate tracking
                        'rating': 4.0,  # Default rating (not available in eBay API)
                        'reviews': 0  # Default reviews count (not available in eBay API)
                    }
                    products.append(product)
                except Exception as e:
                    logger.error(f"Error parsing similar product data: {e}")
                    continue
            
            return products
            
        except ConnectionError as e:
            logger.error(f"eBay API connection error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error finding similar items: {e}")
            return []