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
    
    // Only add event listeners if elements exist
    if (browseButton && imageInput) {
        console.log('Found upload elements');
        
        // Add event listener to browse button
        browseButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Browse button clicked');
            imageInput.click();
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
                        errorMessage.textContent = data.error;
                        errorAlert.classList.remove('d-none');
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
        updateProductRecommendations(data.recommendations || []);
        
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
                        <a href="${product.listing_url || '#'}" target="_blank" class="btn btn-outline-primary w-100${product.is_sample ? ' disabled' : ''}">
                            ${product.is_sample ? 'Sample Product' : 'View on eBay'}
                        </a>
                    </div>
                </div>
            `;
            
            container.appendChild(col);
        });
    }
    
    // Function to generate star rating HTML
    function getStarRating(rating) {
        const fullStars = Math.floor(rating);
        const halfStar = rating % 1 >= 0.5;
        const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);
        
        let starsHtml = '';
        
        for (let i = 0; i < fullStars; i++) {
            starsHtml += '<i class="fas fa-star text-warning"></i> ';
        }
        
        if (halfStar) {
            starsHtml += '<i class="fas fa-star-half-alt text-warning"></i> ';
        }
        
        for (let i = 0; i < emptyStars; i++) {
            starsHtml += '<i class="far fa-star text-warning"></i> ';
        }
        
        return starsHtml;
    }
    
    // Function to set up feedback buttons
    function setupFeedbackButtons(predictionId, style) {
        const accurateBtn = document.getElementById('accurateBtn');
        const inaccurateBtn = document.getElementById('inaccurateBtn');
        const feedbackThanks = document.getElementById('feedbackThanks');
        
        if (accurateBtn && inaccurateBtn) {
            // Reset buttons
            accurateBtn.classList.remove('btn-success');
            inaccurateBtn.classList.remove('btn-danger');
            accurateBtn.classList.add('btn-outline-success');
            inaccurateBtn.classList.add('btn-outline-danger');
            if (feedbackThanks) feedbackThanks.classList.add('d-none');
            
            // Add event listeners
            accurateBtn.onclick = function() {
                submitFeedback(predictionId, style, true);
                accurateBtn.classList.remove('btn-outline-success');
                accurateBtn.classList.add('btn-success');
                inaccurateBtn.classList.remove('btn-danger');
                inaccurateBtn.classList.add('btn-outline-danger');
                if (feedbackThanks) feedbackThanks.classList.remove('d-none');
            };
            
            inaccurateBtn.onclick = function() {
                submitFeedback(predictionId, style, false);
                inaccurateBtn.classList.remove('btn-outline-danger');
                inaccurateBtn.classList.add('btn-danger');
                accurateBtn.classList.remove('btn-success');
                accurateBtn.classList.add('btn-outline-success');
                if (feedbackThanks) feedbackThanks.classList.remove('d-none');
            };
        }
    }
    
    // Function to submit feedback
    function submitFeedback(predictionId, style, isAccurate) {
        fetch('/submit-feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
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
        })
        .catch(error => {
            console.error('Error submitting feedback:', error);
        });
    }
});
