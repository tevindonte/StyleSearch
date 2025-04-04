// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    
    // Image Upload Preview Logic
    const uploadInput = document.getElementById('imageUpload');
    const uploadArea = document.getElementById('uploadArea');
    const previewContainer = document.getElementById('previewContainer');
    const previewImage = document.getElementById('previewImage');
    
    if (uploadInput) {
        // Handle drag over events
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadArea.classList.add('highlight');
        });
        
        // Handle drag leave events
        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            uploadArea.classList.remove('highlight');
        });
        
        // Handle drop events
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadArea.classList.remove('highlight');
            
            if (e.dataTransfer.files.length) {
                uploadInput.files = e.dataTransfer.files;
                displayImagePreview(e.dataTransfer.files[0]);
            }
        });
        
        // Handle file input change
        uploadInput.addEventListener('change', function() {
            if (this.files.length) {
                displayImagePreview(this.files[0]);
            }
        });
        
        // Display image preview
        function displayImagePreview(file) {
            if (!file.type.match('image.*')) {
                alert('Please select an image file');
                return;
            }
            
            const reader = new FileReader();
            
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                previewContainer.classList.remove('d-none');
                document.getElementById('analyzeBtn').disabled = false;
            };
            
            reader.readAsDataURL(file);
        }
    }

    // Handle favorites
    const saveToFavoritesBtn = document.getElementById('saveToFavoritesBtn');
    if (saveToFavoritesBtn) {
        saveToFavoritesBtn.addEventListener('click', function() {
            const predictionId = this.getAttribute('data-prediction-id');
            if (!predictionId) {
                console.error('No prediction ID found');
                return;
            }
            
            // Send request to save favorite
            fetch('/favorites/add/' + predictionId, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update button to show saved
                    this.innerHTML = '<i class="fas fa-heart me-1"></i> Saved to Favorites';
                    this.classList.remove('btn-outline-primary');
                    this.classList.add('btn-success');
                    // Disable button to prevent multiple saves
                    this.disabled = true;
                    
                    // Show a toast notification
                    const toastContainer = document.createElement('div');
                    toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
                    toastContainer.style.zIndex = '11';
                    
                    toastContainer.innerHTML = `
                        <div class="toast align-items-center text-white bg-success border-0" role="alert" aria-live="assertive" aria-atomic="true">
                            <div class="d-flex">
                                <div class="toast-body">
                                    <i class="fas fa-check-circle me-2"></i> Saved to your favorites!
                                </div>
                                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                            </div>
                        </div>
                    `;
                    
                    document.body.appendChild(toastContainer);
                    
                    const toastEl = toastContainer.querySelector('.toast');
                    const toast = new bootstrap.Toast(toastEl);
                    toast.show();
                    
                    // Remove toast after it's hidden
                    toastEl.addEventListener('hidden.bs.toast', function() {
                        toastContainer.remove();
                    });
                } else {
                    alert('Error saving to favorites: ' + (data.message || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error saving favorite:', error);
                alert('Error saving to favorites. Please try again.');
            });
        });
    }
    
    // Style Analysis Form Submission
    const analyzeForm = document.getElementById('analyzeForm');
    const resultsContainer = document.getElementById('resultsContainer');
    const loadingSpinner = document.getElementById('loadingSpinner');
    
    if (analyzeForm) {
        analyzeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading spinner
            loadingSpinner.classList.remove('d-none');
            resultsContainer.classList.add('d-none');
            
            // Get form data
            const formData = new FormData(analyzeForm);
            
            // Send AJAX request
            fetch('/predict', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Hide loading spinner
                loadingSpinner.classList.add('d-none');
                
                if (data.error) {
                    alert('Error: ' + data.error);
                    return;
                }
                
                // Display results
                displayResults(data);
                
                // Show results container
                resultsContainer.classList.remove('d-none');
                
                // Set prediction ID for the favorites button
                if (saveToFavoritesBtn) {
                    saveToFavoritesBtn.setAttribute('data-prediction-id', data.prediction_id);
                    saveToFavoritesBtn.disabled = false;
                    saveToFavoritesBtn.innerHTML = '<i class="fas fa-heart me-1"></i> Save to Favorites';
                    saveToFavoritesBtn.classList.remove('btn-success');
                    saveToFavoritesBtn.classList.add('btn-outline-primary');
                }
                
                // Show feedback buttons
                document.getElementById('feedbackButtons').classList.remove('d-none');
                
                // Scroll to results
                resultsContainer.scrollIntoView({ behavior: 'smooth' });
            })
            .catch(error => {
                console.error('Error:', error);
                loadingSpinner.classList.add('d-none');
                alert('An error occurred during analysis. Please try again.');
            });
        });
    }
    
    // Function to display results
    function displayResults(data) {
        // Set the analyzed image
        document.getElementById('analyzedImage').src = data.image_url;
        
        // Set the primary style
        document.getElementById('primaryStyle').textContent = data.primary_style;
        
        // Clear and populate style tags
        const styleTagsContainer = document.getElementById('styleTags');
        styleTagsContainer.innerHTML = '';
        
        data.style_tags.forEach(tag => {
            const badge = document.createElement('span');
            badge.className = 'badge bg-secondary me-1 mb-1';
            badge.textContent = tag;
            styleTagsContainer.appendChild(badge);
        });
        
        // Set description
        document.getElementById('styleDescription').textContent = data.description;
        
        // Set styling tips
        document.getElementById('stylingTips').textContent = data.styling_tips;
        
        // Populate outfit combinations
        populateOutfitCombinations(data.outfit_combinations);
        
        // Populate product recommendations
        populateProductRecommendations(data.products);
        
        // Set up feedback buttons
        setupFeedbackButtons(data.prediction_id, data.primary_style);
    }
    
    // Function to populate outfit combinations
    function populateOutfitCombinations(outfits) {
        const container = document.getElementById('outfitCombinations');
        container.innerHTML = '';
        
        if (!outfits || outfits.length === 0) {
            container.innerHTML = '<p class="text-muted">No outfit combinations available.</p>';
            return;
        }
        
        // Create accordion for outfit combinations
        const accordion = document.createElement('div');
        accordion.className = 'accordion';
        accordion.id = 'outfitAccordion';
        
        outfits.forEach((outfit, index) => {
            const accordionItem = document.createElement('div');
            accordionItem.className = 'accordion-item';
            
            const headerId = `outfit-heading-${index}`;
            const collapseId = `outfit-collapse-${index}`;
            
            accordionItem.innerHTML = `
                <h2 class="accordion-header" id="${headerId}">
                    <button class="accordion-button ${index !== 0 ? 'collapsed' : ''}" type="button" data-bs-toggle="collapse" data-bs-target="#${collapseId}" aria-expanded="${index === 0 ? 'true' : 'false'}" aria-controls="${collapseId}">
                        ${outfit.name}
                    </button>
                </h2>
                <div id="${collapseId}" class="accordion-collapse collapse ${index === 0 ? 'show' : ''}" aria-labelledby="${headerId}" data-bs-parent="#outfitAccordion">
                    <div class="accordion-body">
                        <p>${outfit.description}</p>
                        <h6 class="mt-3 mb-2">Components:</h6>
                        <ul class="list-group list-group-flush mb-3">
                            ${outfit.components.map(item => `<li class="list-group-item bg-transparent">${item}</li>`).join('')}
                        </ul>
                        <div class="d-flex justify-content-between align-items-center text-muted">
                            <div><strong>Occasion:</strong> ${outfit.occasion}</div>
                            <div><strong>Statement piece:</strong> ${outfit.statement_piece}</div>
                        </div>
                        <div class="mt-2 text-muted">
                            <strong>Tip:</strong> ${outfit.styling_tip}
                        </div>
                    </div>
                </div>
            `;
            
            accordion.appendChild(accordionItem);
        });
        
        container.appendChild(accordion);
    }
    
    // Function to populate product recommendations
    function populateProductRecommendations(products) {
        const container = document.getElementById('productRecommendations');
        container.innerHTML = '';
        
        if (!products || products.length === 0) {
            container.innerHTML = '<p class="text-muted">No product recommendations available.</p>';
            return;
        }
        
        const row = document.createElement('div');
        row.className = 'row row-cols-1 row-cols-md-3 g-4';
        
        products.forEach(product => {
            const col = document.createElement('div');
            col.className = 'col';
            
            const isSample = product.is_sample || false;
            
            col.innerHTML = `
                <div class="card h-100 product-card border-0 shadow-sm">
                    <img src="${product.image_url}" class="card-img-top" alt="${product.title}">
                    <div class="card-body">
                        <h5 class="card-title">${product.title}</h5>
                        <p class="card-text">
                            <span class="fs-5 fw-bold">${product.currency} ${product.price.toFixed(2)}</span>
                        </p>
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div class="star-rating">
                                ${getStarRating(product.rating)}
                                <span class="small text-muted">(${product.reviews_count})</span>
                            </div>
                            <span class="small text-muted">Seller: ${product.seller_name}</span>
                        </div>
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="small">
                                ${product.shipping_cost > 0 ? 
                                    `+ ${product.currency} ${product.shipping_cost.toFixed(2)} shipping` : 
                                    '<span class="text-success">Free shipping</span>'}
                            </span>
                            <span class="small text-muted">${product.shipping_time}</span>
                        </div>
                    </div>
                    <div class="card-footer bg-transparent border-top-0">
                        <a href="${product.listing_url}" target="_blank" class="btn btn-outline-primary w-100${isSample ? ' disabled' : ''}">
                            ${isSample ? 'Sample Product' : 'View on eBay'}
                        </a>
                    </div>
                </div>
            `;
            
            row.appendChild(col);
        });
        
        container.appendChild(row);
    }
    
    // Function to generate star rating HTML
    function getStarRating(rating) {
        const fullStars = Math.floor(rating);
        const halfStar = rating % 1 >= 0.5;
        const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);
        
        let starsHtml = '';
        
        for (let i = 0; i < fullStars; i++) {
            starsHtml += '<i class="fas fa-star"></i> ';
        }
        
        if (halfStar) {
            starsHtml += '<i class="fas fa-star-half-alt"></i> ';
        }
        
        for (let i = 0; i < emptyStars; i++) {
            starsHtml += '<i class="far fa-star"></i> ';
        }
        
        return starsHtml;
    }
    
    // Function to set up feedback buttons
    function setupFeedbackButtons(predictionId, style) {
        const accurateBtn = document.getElementById('feedbackAccurate');
        const inaccurateBtn = document.getElementById('feedbackInaccurate');
        
        if (accurateBtn && inaccurateBtn) {
            // Reset buttons
            accurateBtn.classList.remove('btn-success', 'active');
            inaccurateBtn.classList.remove('btn-danger', 'active');
            accurateBtn.classList.add('btn-outline-success');
            inaccurateBtn.classList.add('btn-outline-danger');
            
            // Add event listeners
            accurateBtn.onclick = function() {
                submitFeedback(predictionId, style, true);
                accurateBtn.classList.remove('btn-outline-success');
                accurateBtn.classList.add('btn-success', 'active');
                inaccurateBtn.classList.remove('btn-danger', 'active');
                inaccurateBtn.classList.add('btn-outline-danger');
            };
            
            inaccurateBtn.onclick = function() {
                submitFeedback(predictionId, style, false);
                inaccurateBtn.classList.remove('btn-outline-danger');
                inaccurateBtn.classList.add('btn-danger', 'active');
                accurateBtn.classList.remove('btn-success', 'active');
                accurateBtn.classList.add('btn-outline-success');
            };
        }
    }
    
    // Function to submit feedback
    function submitFeedback(predictionId, style, isAccurate) {
        fetch('/feedback', {
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
            
            // Show feedback thank you message
            const feedbackMsg = document.getElementById('feedbackThankYou');
            if (feedbackMsg) {
                feedbackMsg.classList.remove('d-none');
                setTimeout(() => {
                    feedbackMsg.classList.add('fade-in');
                }, 10);
            }
        })
        .catch(error => {
            console.error('Error submitting feedback:', error);
        });
    }
});
