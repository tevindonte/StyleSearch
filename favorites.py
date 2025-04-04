from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from models import Favorite, Prediction, db
import json

# Create blueprint for favorites routes
favorites_bp = Blueprint('favorites', __name__)

@favorites_bp.route('/favorites')
@login_required
def list_favorites():
    """Display user's saved favorite styles"""
    favorites = Favorite.query.filter_by(user_id=current_user.id).order_by(Favorite.added_at.desc()).all()
    return render_template('favorites/list.html', title='Saved Favorites', favorites=favorites)

@favorites_bp.route('/favorites/add/<prediction_id>', methods=['POST'])
@login_required
def add_favorite(prediction_id):
    """Add a prediction to user's favorites"""
    # Check if prediction exists
    prediction = Prediction.query.get_or_404(prediction_id)
    
    # Check if already in favorites
    existing = Favorite.query.filter_by(user_id=current_user.id, prediction_id=prediction_id).first()
    if existing:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'Already in favorites'}), 400
        flash('Style already in your favorites', 'warning')
        return redirect(url_for('favorites.list_favorites'))
    
    # Add to favorites
    try:
        notes = request.form.get('notes', '')
        favorite = Favorite(user_id=current_user.id, prediction_id=prediction_id, notes=notes)
        db.session.add(favorite)
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'success', 'message': 'Added to favorites'})
        
        flash('Style added to your favorites!', 'success')
        return redirect(url_for('favorites.list_favorites'))
    
    except SQLAlchemyError as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'Database error'}), 500
        
        flash('Could not add to favorites', 'danger')
        return redirect(url_for('index'))

@favorites_bp.route('/favorites/remove/<favorite_id>', methods=['POST'])
@login_required
def remove_favorite(favorite_id):
    """Remove a style from user's favorites"""
    favorite = Favorite.query.get_or_404(favorite_id)
    
    # Verify ownership
    if favorite.user_id != current_user.id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
        flash('You do not have permission to remove this favorite', 'danger')
        return redirect(url_for('favorites.list_favorites'))
    
    # Remove from favorites
    try:
        db.session.delete(favorite)
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'success', 'message': 'Removed from favorites'})
        
        flash('Style removed from your favorites', 'info')
        return redirect(url_for('favorites.list_favorites'))
    
    except SQLAlchemyError:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'Database error'}), 500
        
        flash('Could not remove from favorites', 'danger')
        return redirect(url_for('favorites.list_favorites'))

@favorites_bp.route('/favorites/update/<favorite_id>', methods=['POST'])
@login_required
def update_favorite(favorite_id):
    """Update notes for a favorite"""
    favorite = Favorite.query.get_or_404(favorite_id)
    
    # Verify ownership
    if favorite.user_id != current_user.id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
        flash('You do not have permission to update this favorite', 'danger')
        return redirect(url_for('favorites.list_favorites'))
    
    # Update notes
    try:
        favorite.notes = request.form.get('notes', '')
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'success', 'message': 'Notes updated'})
        
        flash('Favorite updated successfully', 'success')
        return redirect(url_for('favorites.list_favorites'))
    
    except SQLAlchemyError:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'Database error'}), 500
        
        flash('Could not update favorite', 'danger')
        return redirect(url_for('favorites.list_favorites'))