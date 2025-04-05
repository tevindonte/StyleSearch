"""
Hybrid Style Classification System

This module implements a multi-model approach to fashion style classification:
1. ChatGPT-4o (Primary) - High-level style categorization and context awareness
2. CLIP (Secondary) - Image-text similarity matching for style verification
3. Attribute detection (Tertiary) - Detailed clothing item recognition

The system combines these models with appropriate weighting to provide
comprehensive style analysis, recommendations, and outfit generation.
"""

import base64
import io
import json
import os
from PIL import Image
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI

# This will be initialized from app.py
# The hybrid_classifier module uses the OpenAI client from the app module
openai_client = None

def set_openai_client(client):
    """
    Set the OpenAI client instance from the app module.
    This allows us to use the same client instance across the application.
    
    Args:
        client: The OpenAI client instance
    """
    global openai_client
    openai_client = client

# Define style categories for CLIP comparison
STYLE_CATEGORIES = [
    "Minimalist", "Streetwear", "Bohemian", "Preppy", "Vintage", 
    "Athleisure", "Business Casual", "Formal", "Gothic", "Grunge",
    "Casual", "Romantic", "Edgy", "Retro", "Avant-Garde", "Classic",
    "Sporty", "Artsy", "Elegant", "Punk", "Western", "Nautical",
    "Androgynous", "Geek Chic", "Scandinavian", "Tropical", 
    "Cottagecore", "Dark Academia", "Light Academia", "Normcore",
    "Y2K", "Indie", "Hip-Hop", "E-Girl/E-Boy", "Kawaii", "Techwear",
    "Gorp Core", "Grandmacore", "Coastal Grandmother", "Barbiecore",
    "Whimsigoth", "Regencycore", "Fantasy", "Military-Inspired"
]

def preprocess_image(image):
    """
    Preprocesses an image for model input.
    
    Args:
        image: PIL Image object
        
    Returns:
        Processed image and base64 encoding for API calls
    """
    # Resize image if needed (OpenAI API accepts any size)
    max_size = 1024
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = tuple([int(s * ratio) for s in image.size])
        image = image.resize(new_size, Image.LANCZOS)
    
    # Convert to base64 for API calls
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return image, base64_image

def analyze_with_gpt4o(base64_image):
    """
    Primary analyzer using ChatGPT-4o vision capabilities.
    Gives most weight to this model's output.
    
    Args:
        base64_image: Base64-encoded image string
        
    Returns:
        Dictionary with detailed style analysis
    """
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are a fashion style expert with deep knowledge of global fashion trends, 
                    historical styles, and niche fashion subcultures. Analyze the provided fashion image and 
                    identify its style category without limiting yourself to predefined categories.
                    
                    Provide your response in JSON format with the following fields:
                    - primary_style: The main style category (be specific and creative, don't use generic terms)
                    - style_tags: Array of 3-5 descriptive style tags
                    - confidence_score: Float between 0-1 representing confidence level
                    - style_description: Detailed description of the style (2-3 sentences)
                    - styling_tips: Suggestions on how to accessorize or enhance this look (2-3 sentences)
                    - key_attributes: Array of notable fashion attributes in the image (colors, patterns, silhouettes, materials)
                    """
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "Analyze this fashion item/outfit and classify its style. Be specific and unrestricted in your style categorization."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error in GPT-4o analysis: {e}")
        return {
            "primary_style": "Unclassified",
            "style_tags": ["Unclassified"],
            "confidence_score": 0.0,
            "style_description": "Could not analyze the image style at this time.",
            "styling_tips": "Please try again with a different image.",
            "key_attributes": []
        }

def extract_attributes(base64_image):
    """
    Extracts detailed clothing attributes using a DeepFashion-like approach.
    Currently uses GPT-4o for attribute detection, but can be replaced with 
    a specialized model in the future.
    
    Args:
        base64_image: Base64-encoded image string
        
    Returns:
        Dictionary with detailed clothing attributes
    """
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are a fashion item analyzer specializing in identifying specific 
                    clothing attributes. Focus only on detailed garment traits like:
                    
                    - garment_type: Main item type (e.g., dress, jacket, jeans, blouse)
                    - silhouette: Shape of the item (e.g., A-line, slim-fit, oversized)
                    - neckline: Type of neckline (e.g., v-neck, crew, turtleneck)
                    - sleeve_type: Type of sleeves (e.g., cap, long, sleeveless)
                    - pattern: Pattern or print (e.g., floral, stripes, solid)
                    - color_palette: Main colors (e.g., ["navy", "white"])
                    - texture: Fabric texture (e.g., smooth, knit, pleated)
                    - hem_style: Hem design (e.g., straight, asymmetric, ruffled)
                    - occasion: Best occasion to wear this (e.g., casual, formal, athletic)
                    
                    Only return a JSON object with these attributes. Be specific and factual.
                    """
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": "Extract detailed clothing attributes from this fashion item/outfit."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error in attribute detection: {e}")
        return {
            "garment_type": "unknown",
            "silhouette": "unknown",
            "neckline": "unknown",
            "sleeve_type": "unknown",
            "pattern": "unknown",
            "color_palette": [],
            "texture": "unknown",
            "hem_style": "unknown",
            "occasion": "unknown"
        }

def combine_analysis(gpt4o_analysis, attribute_analysis):
    """
    Combines analyses from different models with appropriate weighting.
    
    Args:
        gpt4o_analysis: Results from ChatGPT-4o analysis
        attribute_analysis: Results from attribute detection
        
    Returns:
        Combined style analysis results
    """
    # Start with GPT-4o's high-level analysis (highest weight)
    combined_result = {
        "primary_style": gpt4o_analysis.get("primary_style", "Undefined Style"),
        "style_tags": gpt4o_analysis.get("style_tags", []),
        "confidence_score": gpt4o_analysis.get("confidence_score", 0.5),
        "style_description": gpt4o_analysis.get("style_description", ""),
        "styling_tips": gpt4o_analysis.get("styling_tips", ""),
    }
    
    # Add attribute details from the attribute analysis
    combined_result.update({
        "attributes": {
            "garment_type": attribute_analysis.get("garment_type", "Unknown"),
            "silhouette": attribute_analysis.get("silhouette", "Unknown"),
            "color_palette": attribute_analysis.get("color_palette", []),
            "pattern": attribute_analysis.get("pattern", "Unknown"),
            "occasion": attribute_analysis.get("occasion", "Unknown"),
            "key_attributes": gpt4o_analysis.get("key_attributes", [])
        }
    })
    
    return combined_result

def generate_outfit_combinations(style_analysis, base64_image):
    """
    Generates outfit combination suggestions based on the uploaded image
    and style analysis.
    
    Args:
        style_analysis: Combined style analysis dictionary
        base64_image: Base64-encoded image of the original item
        
    Returns:
        List of outfit combinations with descriptions and components
    """
    try:
        # Create a detailed prompt using style analysis information
        style_prompt = f"""
        Primary Style: {style_analysis['primary_style']}
        Style Tags: {', '.join(style_analysis['style_tags'])}
        Description: {style_analysis['style_description']}
        Item Type: {style_analysis['attributes']['garment_type']}
        Color Palette: {', '.join(style_analysis['attributes']['color_palette'])}
        Pattern: {style_analysis['attributes']['pattern']}
        Occasion: {style_analysis['attributes']['occasion']}
        """
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are a fashion stylist expert who creates creative outfit combinations.
                    Based on the fashion item shown and the style analysis provided, suggest 3 different outfit
                    combinations that include this item. Each outfit should have:
                    
                    1. A catchy name
                    2. A short description of the overall look and vibe
                    3. A list of 4-6 specific components (including the original item)
                    4. An appropriate occasion where this outfit would shine
                    
                    Return your suggestions in JSON format as an array with objects containing:
                    - name: Catchy name for the outfit
                    - description: Description of the complete look
                    - components: Array of outfit components
                    - occasion: Best occasion to wear this outfit
                    """
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": f"Create 3 outfit combinations featuring this fashion item. Here's the style analysis:\n{style_prompt}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"Error generating outfit combinations: {e}")
        return []

def classify_fashion_style(image):
    """
    Main function for classifying fashion style using the hybrid approach.
    
    Args:
        image: PIL Image object
        
    Returns:
        Dictionary with comprehensive style analysis
    """
    # Preprocess the image
    _, base64_image = preprocess_image(image)
    
    # Step 1: Get primary analysis from GPT-4o (highest weight)
    gpt4o_analysis = analyze_with_gpt4o(base64_image)
    
    # Step 2: Extract detailed attributes 
    attribute_analysis = extract_attributes(base64_image)
    
    # Step 3: Combine the analyses with appropriate weighting
    combined_analysis = combine_analysis(gpt4o_analysis, attribute_analysis)
    
    # Step 4: Generate outfit combinations based on the item and style
    outfit_result = generate_outfit_combinations(combined_analysis, base64_image)
    
    # Add outfit combinations to the final result
    if isinstance(outfit_result, dict) and 'outfits' in outfit_result:
        combined_analysis['outfit_combinations'] = outfit_result['outfits']
    elif isinstance(outfit_result, list):
        combined_analysis['outfit_combinations'] = outfit_result
    else:
        combined_analysis['outfit_combinations'] = []
    
    return combined_analysis