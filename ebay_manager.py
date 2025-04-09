"""
eBay API Manager for Fashion Style Analyzer

This module handles eBay API operations for fetching product recommendations
based on predicted fashion styles.
"""

import os
import logging
import json
import datetime
from ebaysdk.finding import Connection as Finding
from ebaysdk.exception import ConnectionError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# eBay API credentials from environment
EBAY_APP_ID = os.environ.get('EBAY_APP_ID')
EBAY_CERT_ID = os.environ.get('EBAY_CERT_ID') 
EBAY_DEV_ID = os.environ.get('EBAY_DEV_ID')

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

        # Rate limiting tracking
        self.request_count = 0
        self.last_request_time = datetime.datetime.now()
        self.max_requests_per_hour = 5000  # eBay standard API limit
        self.cooldown_active = False
        self.cooldown_until = None

        # Debug eBay API credentials from environment 
        self._debug_ebay_credentials()

        try:
            # Initialize eBay Finding API client with production credentials
            self.api = Finding(
                domain='svcs.ebay.com',  # Always use production domain
                appid=EBAY_APP_ID,
                certid=EBAY_CERT_ID,
                devid=EBAY_DEV_ID,
                config_file=None,
                siteid='EBAY-US'
            )
            logger.info("Initialized eBay API client in production mode")

            # Skip test call to save API quota
            self.connection_available = True
            logger.info("eBay API client initialized (skipping test call)")

        except ConnectionError as e:
            logger.error(f"Failed to initialize eBay API client: {e}")
            self.api = None
            self.connection_available = False
        except Exception as e:
            logger.error(f"Error setting up eBay API client: {e}")
            self.api = None
            self.connection_available = False

    def _debug_ebay_credentials(self):
        """Debug eBay API credentials to identify configuration issues."""
        # Log credentials from environment variables (partial for security)
        app_id = os.environ.get('EBAY_APP_ID', 'Not set')
        cert_id = os.environ.get('EBAY_CERT_ID', 'Not set')
        dev_id = os.environ.get('EBAY_DEV_ID', 'Not set')

        # Only log the first and last 5 characters of each credential for security
        if len(app_id) > 10:
            masked_app_id = f"{app_id[:5]}...{app_id[-5:]}"
        else:
            masked_app_id = "Too short to mask"

        if len(cert_id) > 10:
            masked_cert_id = f"{cert_id[:5]}...{cert_id[-5:]}"
        else:
            masked_cert_id = "Too short to mask"

        if len(dev_id) > 10:
            masked_dev_id = f"{dev_id[:5]}...{dev_id[-5:]}"
        else:
            masked_dev_id = "Too short to mask"

        logger.info(f"eBay credentials from environment: App ID: {masked_app_id}, Cert ID: {masked_cert_id}, Dev ID: {masked_dev_id}")
        logger.info(f"Using hard-coded production eBay credentials for reliability")

    def _check_rate_limit(self):
        """
        Check if we're within API rate limits

        Returns:
            Boolean indicating if we can make another request
        """
        now = datetime.datetime.now()

        # If in cooldown period, check if it's finished
        if self.cooldown_active and self.cooldown_until is not None:
            if now < self.cooldown_until:
                logger.warning(f"API in cooldown until {self.cooldown_until}")
                return False
            else:
                # Cooldown period over, reset counters with longer cooldown
                logger.info("API cooldown period ended, resetting counters with extended cooldown")
                self.cooldown_active = False
                self.request_count = 0 
                self.last_request_time = now
                self.max_requests_per_hour = max(100, self.max_requests_per_hour // 2)  # Reduce limit
                logger.info(f"Adjusted rate limit to {self.max_requests_per_hour} requests per hour")

        # Check if an hour has passed since the first request
        hour_ago = now - datetime.timedelta(hours=1)
        if self.last_request_time < hour_ago:
            # Reset the counter if an hour has passed
            self.request_count = 0
            self.last_request_time = now

        # Check if we've hit the limit
        if self.request_count >= self.max_requests_per_hour:
            logger.warning("API rate limit reached, entering cooldown")
            # Implement exponential backoff with longer initial duration
            if not hasattr(self, 'cooldown_duration'):
                self.cooldown_duration = 15  # Start with 15 minutes
            else:
                self.cooldown_duration = min(120, self.cooldown_duration * 2)  # Double duration, max 2 hours

            self.cooldown_active = True
            self.cooldown_until = now + datetime.timedelta(minutes=self.cooldown_duration)
            self.max_requests_per_hour = max(50, self.max_requests_per_hour // 2)  # Reduce hourly limit more aggressively
            logger.warning(f"Rate limit reached. Entering {self.cooldown_duration}-minute cooldown. New hourly limit: {self.max_requests_per_hour}")
            return False

        # Increment the counter and allow the request
        self.request_count += 1
        return True

    # Simple in-memory cache for product searches
    _cache = {}
    _cache_ttl = 1800  # 30 minutes cache TTL

    def search_products(self, style, user_comments='', limit=6):
        """
        Search for fashion products on eBay with caching.

        Args:
            style: Primary fashion style to search for  
            user_comments: Optional user comments for refining search
            limit: Maximum number of products to return

        Returns:
            List of product dictionaries with details
        """
        if not self.connection_available or self.api is None:
            logger.error("eBay API connection not available")
            return []

        # Generate cache key
        cache_key = f"{style}:{limit}"
        
        # Check cache
        now = datetime.datetime.now()
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if (now - cached_time).total_seconds() < self._cache_ttl:
                logger.info(f"Returning cached results for {style}")
                return cached_data

        # Create the search query with better keyword optimization for fashion
        search_query = f"{style} clothing fashion"

        # Enhance search with keywords from user comments if available
        if user_comments:
            logger.info(f"Enhancing search with user comments: {user_comments}")
            # Extract key terms from user comments
            search_query += f" {user_comments}"

        logger.info(f"Searching eBay for: {search_query}")

        try:
            # Check rate limiting before making request
            if not self._check_rate_limit():
                logger.warning("Rate limit reached, skipping eBay API call")
                return []

            # Make the API call to eBay Finding API with improved parameters
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
                    {'name': 'ListingType', 'value': 'FixedPrice'},
                    {'name': 'AvailableTo', 'value': 'US'},  # Focus on US shipping
                    {'name': 'FreeShippingOnly', 'value': 'true'},  # Prefer free shipping
                    {'name': 'MaxPrice', 'value': '200.0', 'paramName': 'Currency', 'paramValue': 'USD'}  # Reasonable price cap
                ],
                'outputSelector': ['SellerInfo', 'GalleryInfo', 'StoreInfo', 'ShippingInfo']
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

                    # Extract higher quality images when available
                    image_url = item.get('galleryURL', 'https://placehold.co/200x150/2a2a2a/ffffff?text=No+Image')
                    if 'pictureURLLarge' in item:
                        image_url = item['pictureURLLarge']
                    elif 'pictureURLSuperSize' in item:
                        image_url = item['pictureURLSuperSize']

                    # Format price with currency symbol
                    price_value = float(item['sellingStatus']['currentPrice']['value'])
                    currency = item['sellingStatus']['currentPrice']['_currencyId']
                    formatted_price = f"${price_value:.2f}" if currency == 'USD' else f"{price_value:.2f} {currency}"

                    # Get shipping information
                    shipping_cost = item.get('shippingInfo', {}).get('shippingServiceCost', {}).get('value', '0.00')
                    shipping_cost_float = float(shipping_cost) if shipping_cost != 'Unknown' else 0.0
                    free_shipping = shipping_cost_float <= 0

                    # Check if there's a store
                    has_store = 'storeInfo' in item and 'storeName' in item['storeInfo']
                    store_name = item.get('storeInfo', {}).get('storeName', '') if has_store else ''

                    # Enhanced product object
                    product = {
                        'id': item_id,
                        'title': item['title'],
                        'price': formatted_price,
                        'price_value': price_value,
                        'currency': currency,
                        'image': image_url,
                        'url': affiliate_url,  # Use URL with affiliate tracking
                        'location': item.get('location', 'Unknown'),
                        'condition': item.get('condition', {}).get('conditionDisplayName', 'New'),
                        'seller': item.get('sellerInfo', {}).get('sellerUserName', 'Unknown'),
                        'seller_rating': item.get('sellerInfo', {}).get('positiveFeedbackPercent', 'N/A'),
                        'shipping_type': item.get('shippingInfo', {}).get('shippingType', 'Standard'),
                        'shipping_cost': shipping_cost,
                        'free_shipping': free_shipping,
                        'has_store': has_store,
                        'store_name': store_name
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

            # Cache successful results
            if products:
                self._cache[cache_key] = (now, products)
                logger.info(f"Cached {len(products)} products for {style}")
            return products

        except ConnectionError as e:
            logger.error(f"eBay API connection error: {e}")
            # Return cached results if available when API fails
            if cache_key in self._cache:
                _, cached_data = self._cache[cache_key]
                logger.info("Returning cached results due to API error")
                return cached_data
            return []
        except Exception as e:
            logger.error(f"Error searching eBay products: {e}")
            # Return cached results if available when API fails
            if cache_key in self._cache:
                _, cached_data = self._cache[cache_key]
                logger.info("Returning cached results due to error")
                return cached_data
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
        if not self.connection_available or self.api is None:
            logger.error("eBay API connection not available")
            return []

        logger.info(f"Searching for items similar to {item_id}")

        try:
            # Check rate limiting before making request
            if not self._check_rate_limit():
                logger.warning("Rate limit reached, skipping eBay API call")
                return []

            # Make the API call to eBay Finding API with improved parameters
            response = self.api.execute('findItemsByProduct', {
                'productId': item_id,
                'paginationInput': {
                    'entriesPerPage': limit,
                    'pageNumber': 1
                },
                'itemFilter': [
                    {'name': 'Condition', 'value': 'New'},
                    {'name': 'AvailableTo', 'value': 'US'},
                    {'name': 'ListingType', 'value': 'FixedPrice'}
                ],
                'outputSelector': ['SellerInfo', 'GalleryInfo', 'ShippingInfo']
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

                    # Extract higher quality images when available
                    image_url = item.get('galleryURL', 'https://placehold.co/200x150/2a2a2a/ffffff?text=No+Image')
                    if 'pictureURLLarge' in item:
                        image_url = item['pictureURLLarge']
                    elif 'pictureURLSuperSize' in item:
                        image_url = item['pictureURLSuperSize']

                    # Format price with currency symbol
                    price_value = float(item['sellingStatus']['currentPrice']['value'])
                    currency = item['sellingStatus']['currentPrice']['_currencyId']
                    formatted_price = f"${price_value:.2f}" if currency == 'USD' else f"{price_value:.2f} {currency}"

                    # Get shipping information
                    shipping_cost = item.get('shippingInfo', {}).get('shippingServiceCost', {}).get('value', '0.00')
                    shipping_cost_float = float(shipping_cost) if shipping_cost != 'Unknown' else 0.0
                    free_shipping = shipping_cost_float <= 0

                    # Check if there's a store
                    has_store = 'storeInfo' in item and 'storeName' in item['storeInfo']
                    store_name = item.get('storeInfo', {}).get('storeName', '') if has_store else ''

                    # Enhanced product object
                    product = {
                        'id': similar_item_id,
                        'title': item['title'],
                        'price': formatted_price,
                        'price_value': price_value,
                        'currency': currency,
                        'image': image_url,
                        'url': affiliate_url,  # Use URL with affiliate tracking
                        'location': item.get('location', 'Unknown'),
                        'condition': item.get('condition', {}).get('conditionDisplayName', 'New'),
                        'seller': item.get('sellerInfo', {}).get('sellerUserName', 'Unknown'),
                        'seller_rating': item.get('sellerInfo', {}).get('positiveFeedbackPercent', 'N/A'),
                        'shipping_type': item.get('shippingInfo', {}).get('shippingType', 'Standard'),
                        'shipping_cost': shipping_cost,
                        'free_shipping': free_shipping,
                        'has_store': has_store,
                        'store_name': store_name,
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