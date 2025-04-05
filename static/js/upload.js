// Simple script for image upload handling
document.addEventListener('DOMContentLoaded', function() {
    console.log('Upload script loaded');
    
    // Get references to the DOM elements
    const browseButton = document.getElementById('browseButton');
    const imageInput = document.getElementById('imageInput');
    const previewContainer = document.getElementById('previewContainer');
    const imagePreview = document.getElementById('imagePreview');
    const uploadArea = document.getElementById('upload-area');
    const predictButton = document.getElementById('predictButton');
    const removePreviewBtn = document.getElementById('removePreviewBtn');
    const uploadForm = document.getElementById('uploadForm');
    const resultsCard = document.getElementById('resultsCard');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');
    const apiKeyStatus = document.getElementById('apiKeyStatus');
    const apiKeyStatusMessage = document.getElementById('apiKeyStatusMessage');
    const refreshApiKeyBtn = document.getElementById('refreshApiKeyBtn');
    
    // Flag to prevent multiple event triggering
    let isEventInProgress = false;
    
    // Only add event listeners if elements exist
    if (browseButton && imageInput) {
        console.log('Found upload elements');
        
        // Add event listener to browse button - using once option to prevent multiple events
        browseButton.addEventListener('click', function handleBrowseClick(e) {
            if (isEventInProgress) return;
            
            isEventInProgress = true;
            e.preventDefault();
            e.stopPropagation();
            console.log('Browse button clicked');
            
            // Use setTimeout to prevent multiple dialogs
            setTimeout(() => {
                imageInput.click();
                // Reset flag after a short delay
                setTimeout(() => {
                    isEventInProgress = false;
                }, 500);
            }, 10);
        });
        
        // Add event listener to file input
        imageInput.addEventListener('change', function() {
            console.log('File input changed');
            if (this.files && this.files[0]) {
                const file = this.files[0];
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    previewContainer.classList.remove('d-none');
                    predictButton.disabled = false;
                    console.log('Image preview displayed');
                };
                
                reader.readAsDataURL(file);
            }
        });
        
        // Add event listener to refresh API key button
        if (refreshApiKeyBtn) {
            refreshApiKeyBtn.addEventListener('click', function() {
                // Show loading state
                refreshApiKeyBtn.disabled = true;
                refreshApiKeyBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...';
                
                // Call the refresh endpoint
                fetch('/refresh-openai', {
                    method: 'GET'
                })
                .then(response => response.json())
                .then(data => {
                    console.log('API key refresh response:', data);
                    
                    if (data.status === 'success') {
                        // Update UI to show success
                        apiKeyStatus.classList.remove('alert-warning', 'alert-danger');
                        apiKeyStatus.classList.add('alert-success');
                        apiKeyStatusMessage.textContent = 'OpenAI API connection refreshed successfully.';
                        
                        // Hide after a delay
                        setTimeout(() => {
                            apiKeyStatus.classList.add('d-none');
                        }, 5000);
                    } else {
                        // Update UI to show error
                        apiKeyStatus.classList.remove('alert-warning', 'alert-success');
                        apiKeyStatus.classList.add('alert-danger');
                        apiKeyStatusMessage.textContent = data.message || 'Failed to refresh API connection.';
                    }
                })
                .catch(error => {
                    console.error('Error refreshing API key:', error);
                    apiKeyStatus.classList.remove('alert-warning', 'alert-success');
                    apiKeyStatus.classList.add('alert-danger');
                    apiKeyStatusMessage.textContent = 'Error occurred while refreshing API connection.';
                })
                .finally(() => {
                    // Reset button state
                    refreshApiKeyBtn.disabled = false;
                    refreshApiKeyBtn.innerHTML = '<i class="fas fa-sync-alt me-1"></i>Refresh API Connection';
                });
            });
        }
        
        // Add event listener to remove preview button
        if (removePreviewBtn) {
            removePreviewBtn.addEventListener('click', function() {
                previewContainer.classList.add('d-none');
                imageInput.value = '';
                predictButton.disabled = true;
            });
        }
        
        // Add event listener to predict button
        if (predictButton) {
            predictButton.addEventListener('click', function() {
                if (!imageInput.files || !imageInput.files.length) {
                    alert('Please select an image first');
                    return;
                }
                
                // Show loading indicator
                loadingIndicator.classList.remove('d-none');
                resultsCard.classList.add('d-none');
                errorAlert.classList.add('d-none');
                
                // Get form data
                const formData = new FormData();
                formData.append('image', imageInput.files[0]);
                
                // Add user comments if any
                const userComments = document.getElementById('userComments');
                if (userComments && userComments.value) {
                    formData.append('user_comments', userComments.value);
                }
                
                console.log('Submitting prediction request');
                
                // Send AJAX request
                fetch('/predict', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Received prediction response', data);
                    // Hide loading indicator
                    loadingIndicator.classList.add('d-none');
                    
                    if (data.error) {
                        // Check if the error is related to OpenAI API key
                        if (data.error.includes('OpenAI') || data.error.includes('API key') || data.error.includes('quota')) {
                            // Show API key status alert
                            apiKeyStatus.classList.remove('d-none', 'alert-success');
                            apiKeyStatus.classList.add('alert-warning');
                            apiKeyStatusMessage.textContent = data.error;
                        } else {
                            errorMessage.textContent = data.error;
                            errorAlert.classList.remove('d-none');
                        }
                        return;
                    }
                    
                    // Update the results card with the prediction data
                    updateResultsCard(data);
                    
                    // Show results card
                    resultsCard.classList.remove('d-none');
                    
                    // Scroll to results
                    resultsCard.scrollIntoView({ behavior: 'smooth' });
                })
                .catch(error => {
                    console.error('Error:', error);
                    loadingIndicator.classList.add('d-none');
                    errorMessage.textContent = 'An error occurred during analysis. Please try again.';
                    errorAlert.classList.remove('d-none');
                });
            });
        }
    } else {
        console.error('Upload elements not found');
    }
    
    // Function to update results card with prediction data
    function updateResultsCard(data) {
        // Set the predicted style
        document.getElementById('predictedStyle').textContent = data.primary_style || 'Unknown Style';
        
        // Update style description
        const styleDescription = document.getElementById('styleDescription');
        if (styleDescription) {
            styleDescription.innerHTML = `<p>${data.description || 'No description available.'}</p>`;
        }
        
        // Show attributes section if available
        if (data.attributes && Object.keys(data.attributes).length > 0) {
            // Update the attributes list
            const attributesList = document.getElementById('attributesList');
            if (attributesList) {
                attributesList.innerHTML = '';
                
                for (const category in data.attributes) {
                    const col = document.createElement('div');
                    col.className = 'col-md-6';
                    
                    const card = document.createElement('div');
                    card.className = 'card bg-dark bg-opacity-25 mb-2';
                    
                    const cardHeader = document.createElement('div');
                    cardHeader.className = 'card-header';
                    cardHeader.innerHTML = `<h6 class="mb-0">${category}</h6>`;
                    
                    const cardBody = document.createElement('div');
                    cardBody.className = 'card-body py-2';
                    
                    const list = document.createElement('ul');
                    list.className = 'list-unstyled mb-0';
                    
                    // Add each attribute in this category
                    data.attributes[category].forEach(attr => {
                        const item = document.createElement('li');
                        item.className = 'small';
                        item.innerHTML = `<i class="fas fa-check-circle text-success me-1"></i> ${attr}`;
                        list.appendChild(item);
                    });
                    
                    cardBody.appendChild(list);
                    card.appendChild(cardHeader);
                    card.appendChild(cardBody);
                    col.appendChild(card);
                    attributesList.appendChild(col);
                }
            }
            
            // Update confidence score
            const confidenceScore = document.getElementById('confidenceScore');
            if (confidenceScore) {
                confidenceScore.textContent = `${data.confidence_score || 0}% confidence`;
            }
            
            // Show attributes section
            const attributesSection = document.getElementById('attributesSection');
            if (attributesSection) {
                attributesSection.classList.remove('d-none');
            }
        }
        
        // Update outfit combinations
        updateOutfitCombinations(data.outfit_combinations || []);
        
        // Update product recommendations
        updateProductRecommendations(data.products || data.recommendations || []);
        
        // Setup feedback and favorites
        if (data.prediction_id) {
            // Set prediction ID for favorites button
            const saveToFavoritesBtn = document.getElementById('saveToFavoritesBtn');
            if (saveToFavoritesBtn) {
                saveToFavoritesBtn.setAttribute('data-prediction-id', data.prediction_id);
                saveToFavoritesBtn.disabled = false;
                saveToFavoritesBtn.classList.remove('btn-success');
                saveToFavoritesBtn.classList.add('btn-outline-primary');
                saveToFavoritesBtn.innerHTML = '<i class="fas fa-heart me-1"></i> Save to Favorites';
            }
            
            // Setup feedback buttons
            setupFeedbackButtons(data.prediction_id, data.primary_style);
            
            // Show feedback section
            const feedbackButtons = document.getElementById('feedbackButtons');
            if (feedbackButtons) {
                feedbackButtons.classList.remove('d-none');
            }
        }
        
        // Setup try another button
        const tryAnotherBtn = document.getElementById('tryAnotherBtn');
        if (tryAnotherBtn) {
            tryAnotherBtn.addEventListener('click', function() {
                // Reset form and hide results
                if (uploadForm) uploadForm.reset();
                resultsCard.classList.add('d-none');
                previewContainer.classList.add('d-none');
                errorAlert.classList.add('d-none');
                const feedbackButtons = document.getElementById('feedbackButtons');
                if (feedbackButtons) feedbackButtons.classList.add('d-none');
                const feedbackThanks = document.getElementById('feedbackThanks');
                if (feedbackThanks) feedbackThanks.classList.add('d-none');
                
                // Scroll to top
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }
    }
    
    // Function to update outfit combinations
    function updateOutfitCombinations(combinations) {
        const container = document.getElementById('outfitCombinationsContainer');
        if (!container) return;
        
        // Clear placeholder content
        container.innerHTML = '';
        
        if (!combinations || combinations.length === 0) {
            container.innerHTML = '<p class="text-muted">No outfit combinations available.</p>';
            return;
        }
        
        combinations.forEach((outfit, index) => {
            const accordionItem = document.createElement('div');
            accordionItem.className = 'accordion-item bg-dark';
            
            const headerId = `outfit-heading-${index}`;
            const collapseId = `outfit-collapse-${index}`;
            
            accordionItem.innerHTML = `
                <h2 class="accordion-header" id="${headerId}">
                    <button class="accordion-button ${index !== 0 ? 'collapsed' : ''}" type="button" data-bs-toggle="collapse" data-bs-target="#${collapseId}" aria-expanded="${index === 0 ? 'true' : 'false'}" aria-controls="${collapseId}">
                        ${outfit.name || 'Outfit Combination ' + (index + 1)}
                    </button>
                </h2>
                <div id="${collapseId}" class="accordion-collapse collapse ${index === 0 ? 'show' : ''}" aria-labelledby="${headerId}" data-bs-parent="#outfitCombinationsContainer">
                    <div class="accordion-body">
                        <p>${outfit.description || ''}</p>
                        <h6 class="mt-3 mb-2">Components:</h6>
                        <ul class="list-group list-group-flush mb-3">
                            ${outfit.components ? outfit.components.map(item => `<li class="list-group-item bg-dark border-secondary">${item}</li>`).join('') : ''}
                        </ul>
                        ${outfit.occasion ? `
                        <div class="d-flex justify-content-between align-items-center text-muted small">
                            <div><strong>Occasion:</strong> ${outfit.occasion}</div>
                            ${outfit.statement_piece ? `<div><strong>Statement piece:</strong> ${outfit.statement_piece}</div>` : ''}
                        </div>
                        ` : ''}
                        ${outfit.styling_tip ? `
                        <div class="mt-2 text-muted small">
                            <strong>Tip:</strong> ${outfit.styling_tip}
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
            
            container.appendChild(accordionItem);
        });
    }
    
    // Function to update product recommendations
    function updateProductRecommendations(products) {
        const container = document.getElementById('productsContainer');
        if (!container) return;
        
        // Clear placeholder content
        container.innerHTML = '';
        
        if (!products || products.length === 0) {
            container.innerHTML = '<p class="text-muted">No product recommendations available.</p>';
            return;
        }
        
        products.forEach(product => {
            const col = document.createElement('div');
            col.className = 'col';
            
            col.innerHTML = `
                <div class="card h-100 border-0">
                    <img src="${product.image_url || ''}" class="card-img-top" alt="${product.title || 'Product'}" onerror="this.src='${product.fallback_image || '/static/images/placeholder.jpg'}'">
                    <div class="card-body">
                        <h5 class="card-title">${product.title || 'Product Title'}</h5>
                        <p class="card-text">
                            <span class="fs-5 fw-bold">${product.currency || '$'} ${typeof product.price === 'number' ? product.price.toFixed(2) : product.price || '0.00'}</span>
                        </p>
                        ${product.rating ? `
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div class="star-rating">
                                ${getStarRating(product.rating)}
                                <span class="small text-muted">(${product.reviews_count || 0})</span>
                            </div>
                            ${product.seller_name ? `<span class="small text-muted">Seller: ${product.seller_name}</span>` : ''}
                        </div>
                        ` : ''}
                        ${product.shipping_cost !== undefined ? `
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="small">
                                ${product.shipping_cost > 0 ? 
                                    `+ ${product.currency || '$'} ${typeof product.shipping_cost === 'number' ? product.shipping_cost.toFixed(2) : product.shipping_cost} shipping` : 
                                    '<span class="text-success">Free shipping</span>'}
                            </span>
                            ${product.shipping_time ? `<span class="small text-muted">${product.shipping_time}</span>` : ''}
                        </div>
                        ` : ''}
                    </div>
                    <div class="card-footer bg-transparent border-top-0">
                        <a href="${product.url || '#'}" class="btn btn-primary btn-sm w-100" target="_blank">
                            <i class="fas fa-shopping-cart me-1"></i>Buy Now
                        </a>
                    </div>
                </div>
            `;
            
            container.appendChild(col);
        });
    }
    
    // Function to generate star rating
    function getStarRating(rating) {
        // Normalize rating to a 0-5 scale
        const normalizedRating = Math.max(0, Math.min(5, parseFloat(rating)));
        
        // Calculate full and half stars
        const fullStars = Math.floor(normalizedRating);
        const halfStar = normalizedRating % 1 >= 0.5 ? 1 : 0;
        const emptyStars = 5 - fullStars - halfStar;
        
        // Generate HTML
        let html = '';
        
        // Full stars
        for (let i = 0; i < fullStars; i++) {
            html += '<i class="fas fa-star text-warning"></i>';
        }
        
        // Half star if needed
        if (halfStar) {
            html += '<i class="fas fa-star-half-alt text-warning"></i>';
        }
        
        // Empty stars
        for (let i = 0; i < emptyStars; i++) {
            html += '<i class="far fa-star text-warning"></i>';
        }
        
        return html;
    }
    
    // Function to set up feedback buttons
    function setupFeedbackButtons(predictionId, style) {
        const accurateBtn = document.getElementById('accurateBtn');
        const inaccurateBtn = document.getElementById('inaccurateBtn');
        const feedbackThanks = document.getElementById('feedbackThanks');
        
        if (!accurateBtn || !inaccurateBtn || !feedbackThanks) return;
        
        // Reset state
        accurateBtn.disabled = false;
        inaccurateBtn.disabled = false;
        feedbackThanks.classList.add('d-none');
        
        // Add event listeners
        accurateBtn.onclick = function() {
            submitFeedback(predictionId, style, true);
        };
        
        inaccurateBtn.onclick = function() {
            submitFeedback(predictionId, style, false);
        };
    }
    
    // Function to submit feedback
    function submitFeedback(predictionId, style, isAccurate) {
        const accurateBtn = document.getElementById('accurateBtn');
        const inaccurateBtn = document.getElementById('inaccurateBtn');
        const feedbackThanks = document.getElementById('feedbackThanks');
        
        // Disable buttons during submission
        accurateBtn.disabled = true;
        inaccurateBtn.disabled = true;
        
        fetch('/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prediction_id: predictionId,
                style: style,
                is_accurate: isAccurate
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Feedback submitted:', data);
            
            // Show thank you message
            feedbackThanks.classList.remove('d-none');
            
            // Keep buttons disabled to prevent multiple submissions
        })
        .catch(error => {
            console.error('Error submitting feedback:', error);
            
            // Re-enable buttons if there was an error
            accurateBtn.disabled = false;
            inaccurateBtn.disabled = false;
        });
    }
    
    // Function to save to favorites
    if (document.getElementById('saveToFavoritesBtn')) {
        document.getElementById('saveToFavoritesBtn').addEventListener('click', function() {
            const predictionId = this.getAttribute('data-prediction-id');
            if (!predictionId) return;
            
            const button = this;
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Saving...';
            
            fetch(`/favorites/add/${predictionId}`, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                console.log('Saved to favorites:', data);
                
                if (data.success) {
                    button.classList.remove('btn-outline-primary');
                    button.classList.add('btn-success');
                    button.innerHTML = '<i class="fas fa-heart me-1"></i> Saved to Favorites';
                } else {
                    button.disabled = false;
                    button.innerHTML = '<i class="fas fa-heart me-1"></i> Save to Favorites';
                    console.error('Error saving to favorites:', data.error);
                }
            })
            .catch(error => {
                console.error('Error saving to favorites:', error);
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-heart me-1"></i> Save to Favorites';
            });
        });
    }
});
