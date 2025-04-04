import os
import random
import io
import logging
import requests
import json
import base64
import uuid
import datetime
from PIL import Image
from flask import Flask, request, jsonify, render_template, flash, redirect, url_for
from flask_login import LoginManager, current_user, login_required
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy.sql import func
import json

# Import our hybrid style classifier and services
import hybrid_classifier
from db_manager import DatabaseManager
from storage_manager import StorageManager
from ebay_manager import EbayManager
from models import db, User, Prediction, Favorite, Feedback

# Import blueprints
from auth import auth_bp
from favorites import favorites_bp

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(favorites_bp)

# Initialize database, storage, and eBay API managers
db_manager = DatabaseManager()
storage_manager = StorageManager()
ebay_manager = EbayManager()

# User loader function for flask-login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def predict_style_with_openai(image):
    """
    Uses OpenAI's GPT-4o with vision capabilities to predict the fashion style of an image.
    
    Args:
        image: A PIL Image object
        
    Returns:
        A dictionary containing:
        - primary_style: The main style category
        - style_tags: Additional style tags
        - description: A detailed description of the style
        - styling_tips: Tips on how to style this outfit or item
    """
    logging.debug(f"Processing image of size: {image.size}")
    
    try:
        # Convert PIL Image to base64 string
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Create the prompt for style analysis
        prompt = """
        Analyze this fashion image and provide:
        1. The primary fashion style category 
           - DO NOT limit to common categories
           - Be very specific, creative and accurate with your categorization
           - Feel free to use niche, trendy or emerging style terms (e.g. "Dark Academia", "Cottagecore", "Y2K Revival", etc.)
        2. Additional style tags that apply to this image (at least 4-6 descriptive and specific tags)
        3. A detailed description of the style elements visible, noting colors, textures, and styling choices
        4. Styling tips or complementary items that would work well with this look
        
        Format your response as a JSON object with these keys:
        - primary_style: string (the main style category - be specific and creative)
        - style_tags: list of strings (additional style descriptors)
        - description: string (detailed style analysis)
        - styling_tips: string (recommendations)
        """
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": """You are a professional fashion stylist with expertise in identifying clothing styles and providing fashion advice.
                You specialize in identifying specific, niche, and emerging fashion styles rather than broad categories.
                You have an encyclopedic knowledge of fashion trends throughout history and across the world, including subcultures and internet aesthetics.
                You can identify subtle style elements and provide detailed, specific fashion analysis."""},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
                ]}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        logging.debug(f"OpenAI style prediction: {result}")
        
        return result
    
    except Exception as e:
        logging.error(f"Error in OpenAI style prediction: {str(e)}")
        # Fallback to basic prediction if OpenAI fails
        return {
            "primary_style": "Contemporary Casual",
            "style_tags": ["versatile", "modern", "everyday", "minimalist"],
            "description": "A fashionable outfit with contemporary elements and clean lines.",
            "styling_tips": "Pair with minimal accessories for a polished, effortless look."
        }

def generate_outfit_combinations(image, style_info):
    """
    Generate context-aware outfit combination suggestions based on the uploaded image
    
    Args:
        image: The PIL Image object of the uploaded fashion item
        style_info: Dictionary containing style analysis information
        
    Returns:
        List of outfit combinations with descriptions and components
    """
    logging.debug("Generating context-aware outfit combinations")
    try:
        # Convert PIL Image to base64 string
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Get current month and season for context awareness
        current_month = datetime.datetime.now().strftime("%B")  # Full month name
        
        # Determine current season in Northern Hemisphere (adjust as needed)
        month_num = datetime.datetime.now().month
        if 3 <= month_num <= 5:
            current_season = "Spring"
        elif 6 <= month_num <= 8:
            current_season = "Summer"
        elif 9 <= month_num <= 11:
            current_season = "Fall"
        else:
            current_season = "Winter"
            
        # Extract style attributes if available
        attributes = style_info.get('attributes', {})
        garment_type = attributes.get('garment_type', 'clothing item')
        colors = attributes.get('colors', [])
        color_description = ', '.join(colors) if colors else 'unknown colors'
        
        # Create the prompt for outfit generation with context
        prompt = f"""
        I'm looking at a fashion item/outfit with these details:
        - Primary style: {style_info.get('primary_style', 'Unknown')}
        - Style tags: {', '.join(style_info.get('style_tags', ['trendy']))}
        - Type of garment: {garment_type}
        - Colors: {color_description}
        
        Current context:
        - Month: {current_month}
        - Season: {current_season}
        
        Based on this image and the current {current_season} season, suggest 3 different complete outfit combinations that would work well with this item.
        
        For each outfit:
        1. Give it a catchy name that references the current season
        2. Provide a brief description of the overall look, mentioning how it's appropriate for the current weather
        3. List all components (4-6 items) needed for the complete look, with specific details about colors and styles
        4. Suggest specific occasions where it would be appropriate during this season
        5. Include at least one accessory recommendation
        
        Format your response as a JSON array with each outfit as an object containing:
        - name: The outfit name (include the season or a seasonal reference)
        - description: Overall look description (mention how it works for the current weather)
        - components: Array of individual clothing/accessory items with specific details
        - occasion: Where to wear this outfit (be specific about seasonal activities)
        - statement_piece: The key item that makes this outfit stand out
        - styling_tip: One practical tip for wearing this outfit effectively
        """
        
        # Call OpenAI API with enhanced prompt
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[
                {"role": "system", "content": """You are a professional fashion stylist specializing in seasonal outfit creation.
                You have an expert eye for coordination, color matching, and creating cohesive looks appropriate for specific seasons and occasions.
                You understand how to layer clothing appropriately for different weather conditions.
                When suggesting outfits, be extremely specific about items, including details like exact colors, fabric types, cuts, and styles.
                Focus on creating outfits that are practical and wearable while maintaining style."""},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
                ]}
            ],
            response_format={"type": "json_object"},
            temperature=0.7  # Slightly higher temperature for more creative outfit combinations
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        logging.debug(f"Generated outfit combinations: {result}")
        
        return result.get("outfits", [])
    
    except Exception as e:
        logging.error(f"Error generating outfit combinations: {str(e)}")
        # Return fallback outfit suggestions if OpenAI fails
        current_month = datetime.datetime.now().strftime("%B")
        
        return [
            {
                "name": f"{current_month} Weekend Casual",
                "description": "A comfortable yet stylish outfit for weekend activities in the current weather",
                "components": ["White t-shirt", "Jeans", "Sneakers", "Casual watch", "Minimal jewelry", "Light jacket"],
                "occasion": "Weekend outings, casual meetups, outdoor activities",
                "statement_piece": "Stylish sneakers",
                "styling_tip": "Roll up the jeans slightly to create a more casual, relaxed look"
            },
            {
                "name": "Seasonal Work Ensemble",
                "description": "Professional outfit suitable for office environments during this time of year",
                "components": ["Button-down shirt", "Tailored pants", "Leather shoes", "Belt", "Simple accessories", "Blazer"],
                "occasion": "Office work, business meetings, professional events",
                "statement_piece": "Well-fitted blazer",
                "styling_tip": "Keep the blazer unbuttoned for a more relaxed professional look"
            },
            {
                "name": f"{current_month} Evening Style",
                "description": "Dressy outfit for evening social events appropriate for the current season",
                "components": ["Dress shirt", "Dark jeans or slacks", "Leather boots", "Statement accessory", "Seasonal jacket"],
                "occasion": "Dinner dates, evening gatherings, special events",
                "statement_piece": "Unique statement accessory",
                "styling_tip": "Layer appropriately based on the evening temperature"
            }
        ]

def fetch_ebay_recommendations(style, limit=6, user_comments=''):
    """
    Fetch product recommendations from eBay API based on predicted style.
    
    Args:
        style: The predicted fashion style
        limit: Maximum number of products to return
        user_comments: Optional user comments to refine recommendations
        
    Returns:
        List of product recommendations with details
    """
    # Use the style name directly as the search query
    search_query = style.lower() + " fashion clothing"
    
    # If user provided comments, extract useful keywords for recommendations
    if user_comments:
        # Log the user comments
        logging.debug(f"User provided comments for recommendations: {user_comments}")
        
        try:
            # Use OpenAI to extract relevant keywords from user comments
            # This would help tailor the recommendations more accurately
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[
                    {"role": "system", "content": """You are a fashion search query expert.
                    Extract relevant fashion search keywords from user comments.
                    Focus on extracting:
                    - Specific item types (jeans, dresses, etc.)
                    - Size preferences or measurements
                    - Color preferences
                    - Material preferences
                    - Occasion needs
                    - Brand preferences
                    - Price preferences
                    - Specific style elements
                    Return only the most relevant keywords as a comma-separated list."""},
                    {"role": "user", "content": f"Extract fashion search keywords from this comment: {user_comments}"}
                ],
                max_tokens=100
            )
            
            # Get the extracted keywords
            extracted_keywords = response.choices[0].message.content.strip()
            
            if extracted_keywords:
                # Enhance search query with extracted keywords
                search_query = f"{search_query} {extracted_keywords}"
                logging.debug(f"Enhanced search query based on user comments: {search_query}")
        except Exception as e:
            logging.error(f"Error processing user comments for recommendations: {str(e)}")
            # Continue with the original search query if there's an error
    
    logging.debug(f"Searching for products with query: {search_query}")
    
    try:
        # Check if eBay API connection is available
        if ebay_manager.connection_available:
            # Use eBay API to get real product recommendations
            logging.info(f"Using eBay API to search for products with style: {style}")
            products = ebay_manager.search_products(style, user_comments, limit)
            
            # If we got results from eBay API, return them
            if products:
                logging.info(f"Found {len(products)} products from eBay API")
                return products
            else:
                logging.warning("No products found from eBay API, falling back to sample data")
        else:
            logging.warning("eBay API connection not available, using sample data")
        
        # Fallback to sample data if eBay API fails or returns no results
        items = generate_sample_products(style, limit, search_query)
        return items
        
    except Exception as e:
        logging.error(f"Error fetching eBay recommendations: {str(e)}")
        # Fallback to sample data in case of any errors
        return generate_sample_products(style, limit, search_query)
def generate_sample_products(style, limit=6, search_query=None):
    """
    Generate sample product data for proof-of-concept.
    
    Args:
        style: The predicted fashion style
        limit: Maximum number of products to generate
        search_query: Optional enhanced search query from user comments
        
    Returns:
        List of product dictionaries
    """
    # Common fashion items that can work for any style
    common_items = [
        'Top', 'Jacket', 'Pants', 'Dress', 'Skirt', 'Shirt', 
        'Sweater', 'Jeans', 'Blazer', 'Coat', 'Shoes', 'Boots', 
        'Accessories', 'Bag', 'Hat', 'Scarf'
    ]
    
    # If we have a search query from user comments, try to extract items from it
    custom_items = []
    if search_query and search_query != style.lower() + " fashion clothing":
        # Log that we're using an enhanced search query
        logging.debug(f"Generating products with enhanced query: {search_query}")
        
        try:
            # Use OpenAI to extract item types from the search query
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[
                    {"role": "system", "content": "You are a fashion item classifier that extracts specific garment types from search queries."},
                    {"role": "user", "content": f"Extract up to 5 specific fashion item types from this search query. Return ONLY the item types as a comma-separated list, no explanations: {search_query}"}
                ],
                max_tokens=50
            )
            
            # Get the extracted item types
            extracted_items = response.choices[0].message.content.strip().split(",")
            custom_items = [item.strip() for item in extracted_items if item.strip()]
            
            logging.debug(f"Extracted custom items from query: {custom_items}")
        except Exception as e:
            logging.error(f"Error extracting custom items from query: {str(e)}")
    
    # Use custom items if we have them, otherwise use common items
    item_types = custom_items if custom_items else common_items
    
    # Generate the requested number of sample products
    products = []
    for i in range(limit):
        # Select a random item type from our options
        item_type = random.choice(item_types)
        
        # Generate descriptive title with style and item type
        title = f"{style} {item_type} - Fashion Statement Piece"
        
        # Generate a price between $19.99 and $149.99
        price = round(random.uniform(19.99, 149.99), 2)
        
        # Generate random rating between 3 and 5 stars (in half-star increments)
        rating = round(random.uniform(3, 5) * 2) / 2
        
        # Generate random number of reviews
        reviews = random.randint(5, 500)
        
        # Generate random seller info
        seller_name = f"Fashion{random.choice(['Trend', 'Style', 'Chic', 'Vogue', 'Elite'])}Store"
        seller_rating = round(random.uniform(93, 100), 1)
        
        # Generate random shipping info
        shipping_cost = random.choice([0, 4.99, 7.99])
        shipping_time = f"{random.randint(2, 7)} days"
        
        # Create product dictionary
        product = {
            'title': title,
            'price': price,
            'currency': 'USD',
            'image_url': f"https://placehold.co/300x300/1e1e1e/cccccc?text={item_type}",
            'listing_url': '#',  # Placeholder URL
            'rating': rating,
            'reviews_count': reviews,
            'seller_name': seller_name,
            'seller_rating': seller_rating,
            'shipping_cost': shipping_cost,
            'shipping_time': shipping_time,
            'is_sample': True  # Flag to indicate this is a sample product
        }
        
        products.append(product)
    
    return products

# Store a prediction in the database (SQL)
def store_prediction_in_db(style_info, image_path):
    """Store the prediction in the SQL database"""
    try:
        # Create a new prediction record
        prediction_id = str(uuid.uuid4())
        
        # Get user_id if user is authenticated
        user_id = current_user.id if current_user.is_authenticated else None
        
        # Convert style tags to a JSON string
        style_tags_json = json.dumps(style_info.get('style_tags', []))
        
        # Calculate confidence score (placeholder)
        confidence_score = random.randint(70, 95)  # Just a placeholder for now
        
        # Create new prediction
        new_prediction = Prediction(
            id=prediction_id,
            user_id=user_id,
            image_path=image_path,
            primary_style=style_info.get('primary_style', 'Unknown'),
            style_tags=style_tags_json,
            confidence_score=confidence_score
        )
        
        db.session.add(new_prediction)
        db.session.commit()
        
        return prediction_id
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error storing prediction in database: {str(e)}")
        return None

@app.route('/')
def index():
    """Render the home page"""
    # Example style categories to display
    style_categories = [
        "Y2K Revival", "Dark Academia", "Cottagecore", "Minimalist Scandinavian",
        "Streetwear Urban", "Boho Chic", "Vintage Americana", "High Fashion Avant-Garde",
        "Classic Preppy", "Gothic Romantic", "Asian Streetwear Fusion", "Cyberpunk Techwear"
    ]
    
    return render_template('index.html', style_categories=style_categories)

@app.route('/predict', methods=['POST'])
def predict():
    """
    Process the uploaded image and return a style prediction using hybrid classification
    
    Returns:
        JSON response with predicted style or error message
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'error': 'No selected image file'}), 400
        
        # Get optional user comments
        user_comments = request.form.get('user_comments', '')
        logging.debug(f"User provided comments: {user_comments}")
        
        # Open and process the image
        image = Image.open(image_file)
        
        # Call our hybrid classifier to analyze the image
        style_info = hybrid_classifier.classify_fashion_style(image)
        logging.debug(f"Hybrid classifier result: {style_info}")
        
        # Generate outfit combinations based on the style analysis
        outfits = generate_outfit_combinations(image, style_info)
        
        # Store the image in cloud storage if needed
        storage_result = storage_manager.store_image(image)
        
        # Check if storage was successful
        if storage_result and storage_result.get('success'):
            # Use the public URL from storage
            image_url = storage_result.get('public_url')
            image_id = storage_result.get('image_id')
            
            logging.debug(f"Image stored successfully. URL: {image_url}, ID: {image_id}")
            
            # Store metadata about the image in MongoDB
            metadata = {
                'image_id': image_id,
                'storage_path': storage_result.get('storage_path'),
                'upload_timestamp': datetime.datetime.now().isoformat(),
                'file_size': storage_result.get('file_size'),
                'dimensions': storage_result.get('dimensions')
            }
            db_manager.store_image_metadata(metadata)
            
            # Store the style prediction result in MongoDB
            prediction_data = {
                'prediction_id': str(uuid.uuid4()),
                'image_id': image_id,
                'primary_style': style_info.get('primary_style'),
                'style_tags': style_info.get('style_tags', []),
                'confidence_score': random.randint(70, 95),  # Placeholder confidence score
                'attributes': style_info.get('attributes', {}),
                'timestamp': datetime.datetime.now().isoformat()
            }
            db_manager.store_style_prediction(prediction_data)
            
            # Also store in SQL database for user accounts functionality
            prediction_id = store_prediction_in_db(style_info, image_url)
            if not prediction_id:
                prediction_id = prediction_data['prediction_id']
        else:
            # If storage failed, use a placeholder URL and ID
            logging.warning("Image storage failed, using placeholder values")
            image_url = "https://placehold.co/600x400/1e1e1e/cccccc?text=Image+Storage+Failed"
            prediction_id = str(uuid.uuid4())
        
        # Fetch product recommendations based on predicted style
        products = fetch_ebay_recommendations(
            style_info.get('primary_style'), 
            limit=6,
            user_comments=user_comments
        )
        
        # Prepare and return the response
        response = {
            'prediction_id': prediction_id,
            'primary_style': style_info.get('primary_style'),
            'style_tags': style_info.get('style_tags', []),
            'description': style_info.get('description', ''),
            'styling_tips': style_info.get('styling_tips', ''),
            'image_url': image_url,
            'attributes': style_info.get('attributes', {}),
            'outfit_combinations': outfits,
            'products': products,
            'confidence_score': style_info.get('confidence_score', 85)  # Default confidence score
        }
        
        return jsonify(response)
    
    except Exception as e:
        logging.error(f"Error in style prediction: {str(e)}")
        return jsonify({'error': f'Style prediction failed: {str(e)}'}), 500

@app.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    Store user feedback about style prediction accuracy
    
    Expects JSON object with:
    - prediction_id: Unique identifier for the prediction
    - style: The predicted style
    - is_accurate: Boolean indicating if prediction was accurate
    
    Returns:
        Success message
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No feedback data provided'}), 400
        
        prediction_id = data.get('prediction_id')
        predicted_style = data.get('style')
        is_accurate = data.get('is_accurate')
        
        if not all([prediction_id, predicted_style, isinstance(is_accurate, bool)]):
            return jsonify({'error': 'Missing required feedback data'}), 400
        
        # Store feedback in MongoDB
        feedback_data = {
            'prediction_id': prediction_id,
            'predicted_style': predicted_style,
            'is_accurate': is_accurate,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        db_manager.store_feedback(feedback_data)
        
        # Also store in SQL database
        try:
            # Check if prediction exists
            prediction = Prediction.query.get(prediction_id)
            if prediction:
                # Check if feedback already exists
                existing_feedback = Feedback.query.filter_by(prediction_id=prediction_id).first()
                
                if existing_feedback:
                    # Update existing feedback
                    existing_feedback.is_accurate = is_accurate
                else:
                    # Create new feedback
                    feedback = Feedback(
                        prediction_id=prediction_id,
                        is_accurate=is_accurate
                    )
                    db.session.add(feedback)
                
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error storing feedback in SQL database: {str(e)}")
        
        return jsonify({'message': 'Feedback recorded successfully'})
    
    except Exception as e:
        logging.error(f"Error submitting feedback: {str(e)}")
        return jsonify({'error': f'Feedback submission failed: {str(e)}'}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """
    Get statistics about feedback and style predictions
    
    Returns:
        JSON with statistics
    """
    try:
        # Get stats from MongoDB
        mongo_stats = db_manager.get_feedback_stats()
        
        # Get SQL stats
        sql_stats = {}
        try:
            # Most popular styles
            popular_styles = db.session.query(
                Prediction.primary_style, 
                func.count(Prediction.id).label('count')
            ).group_by(Prediction.primary_style).order_by(func.count(Prediction.id).desc()).limit(5).all()
            
            sql_stats['popular_styles'] = [
                {'style': style, 'count': count} for style, count in popular_styles
            ]
            
            # Accuracy rate
            total_feedback = Feedback.query.count()
            accurate_feedback = Feedback.query.filter_by(is_accurate=True).count()
            accuracy_rate = round((accurate_feedback / total_feedback) * 100, 1) if total_feedback > 0 else 0
            
            sql_stats['accuracy_rate'] = accuracy_rate
            sql_stats['total_predictions'] = Prediction.query.count()
            sql_stats['total_feedback'] = total_feedback
            
        except Exception as e:
            logging.error(f"Error fetching SQL stats: {str(e)}")
        
        # Combine stats
        combined_stats = {**mongo_stats, **sql_stats}
        
        return jsonify(combined_stats)
    
    except Exception as e:
        logging.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': f'Failed to retrieve statistics: {str(e)}'}), 500

# Create necessary database tables when the app starts
with app.app_context():
    db.create_all()
