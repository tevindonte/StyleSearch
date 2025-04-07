// upload.js - Handles image upload and style prediction functionality

document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const uploadForm = document.getElementById('uploadForm');
    const imageUpload = document.getElementById('imageUpload');
    const uploadPreview = document.getElementById('uploadPreview');
    const previewContainer = document.getElementById('previewContainer');
    const dragDropArea = document.getElementById('dragDropArea');
    const userCommentsField = document.getElementById('userComments');
    const uploadProgress = document.getElementById('uploadProgress');
    const uploadButton = document.getElementById('uploadButton');
    const uploadButtonText = document.getElementById('uploadButtonText');
    const uploadSpinner = document.getElementById('uploadSpinner');
    
    // Results containers
    const introSection = document.getElementById('introSection');
    const resultsSection = document.getElementById('resultsSection');
    const loadingSection = document.getElementById('loadingSection');
    const errorContainer = document.getElementById('errorContainer');
    
    // Check if file upload is supported
    if (window.File && window.FileReader && window.FileList && window.Blob) {
        console.log("File API is supported in this browser");
    } else {
        console.warn("File API is not fully supported in this browser");
    }
    
    // Initialize WebSocket for real-time updates
    let socket;
    try {
        // Only initialize WebSocket if the browser supports it and we're not in a test environment
        if (window.WebSocket && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
            socket = new WebSocket(`${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/ws`);
            
            socket.onopen = function(e) {
                console.log("WebSocket connection established");
            };
            
            socket.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    console.log("WebSocket message received:", data);
                    
                    if (data.type === 'processing_update') {
                        updateProcessingStatus(data.step, data.progress);
                    }
                } catch (e) {
                    console.error("Error parsing WebSocket message:", e);
                }
            };
            
            socket.onerror = function(error) {
                console.error("WebSocket error:", error);
            };
            
            socket.onclose = function(event) {
                console.log("WebSocket connection closed", event);
            };
        }
    } catch (e) {
        console.warn("WebSocket initialization failed:", e);
    }
    
    // Set up the image upload preview functionality
    if (imageUpload) {
        imageUpload.addEventListener('change', previewImage);
    }
    
    // Set up drag and drop functionality
    if (dragDropArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dragDropArea.addEventListener(eventName, preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dragDropArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dragDropArea.addEventListener(eventName, unhighlight, false);
        });
        
        dragDropArea.addEventListener('drop', handleDrop, false);
    }
    
    // Set up the form submission
    if (uploadForm) {
        uploadForm.addEventListener('submit', submitForm);
    }
    
    // Helper functions
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight() {
        dragDropArea.classList.add('highlight');
    }
    
    function unhighlight() {
        dragDropArea.classList.remove('highlight');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            imageUpload.files = files;
            previewImage();
        }
    }
    
    function previewImage() {
        previewContainer.style.display = 'block';
        
        const file = imageUpload.files[0];
        if (file) {
            // Validate file type
            const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
            if (!validTypes.includes(file.type)) {
                showError("Please upload a valid image file (JPEG, PNG, GIF, or WebP).");
                return;
            }
            
            // Validate file size (max 5MB)
            const maxSize = 5 * 1024 * 1024; // 5MB in bytes
            if (file.size > maxSize) {
                showError("Please upload an image smaller than 5MB.");
                return;
            }
            
            // Create file reader to read and display the image
            const reader = new FileReader();
            reader.onload = function(e) {
                uploadPreview.src = e.target.result;
                uploadPreview.classList.remove('d-none');
                
                // Enable the upload button
                uploadButton.disabled = false;
                
                // Hide any previous errors
                errorContainer.classList.add('d-none');
            };
            reader.onerror = function() {
                showError("Error reading the image file. Please try another image.");
            };
            reader.readAsDataURL(file);
        }
    }
    
    function submitForm(e) {
        e.preventDefault();
        
        // Check if file is selected
        if (!imageUpload.files || imageUpload.files.length === 0) {
            showError("Please select an image to upload.");
            return;
        }
        
        // Hide any previous errors
        errorContainer.classList.add('d-none');
        
        // Show loading section
        introSection.classList.add('d-none');
        loadingSection.classList.remove('d-none');
        
        // Disable submit button and show spinner
        uploadButton.disabled = true;
        uploadButtonText.textContent = 'Analyzing...';
        uploadSpinner.classList.remove('d-none');
        
        // Start progress animation
        startProgressAnimation();
        
        // Get user comments if any
        const userComments = userCommentsField ? userCommentsField.value : '';
        
        // Create form data
        const formData = new FormData();
        formData.append('image', imageUpload.files[0]);
        if (userComments) {
            formData.append('user_comments', userComments);
        }
        
        // Make AJAX request to predict API
        fetch('/predict', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Network response was not ok');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Success:', data);
            // Display results
            updateResults(data);
            // Set up feedback buttons
            setupFeedbackButtons(data.prediction_id, data.primary_style);
            // Hide loading section and show results
            loadingSection.classList.add('d-none');
            resultsSection.classList.remove('d-none');
            // Scroll to results section
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        })
        .catch(error => {
            console.error('Error:', error);
            // Show error and hide loading section
            showError(error.message);
            loadingSection.classList.add('d-none');
            introSection.classList.remove('d-none');
            // Reset upload button
            uploadButton.disabled = false;
            uploadButtonText.textContent = 'Analyze Style';
            uploadSpinner.classList.add('d-none');
        });
    }
    
    function startProgressAnimation() {
        let progress = 0;
        const interval = setInterval(() => {
            progress += 1;
            if (progress > 95) {
                clearInterval(interval);
                return;
            }
            uploadProgress.style.width = `${progress}%`;
            uploadProgress.setAttribute('aria-valuenow', progress);
        }, 100);
    }
    
    function updateProcessingStatus(step, progress) {
        const statusElement = document.getElementById('processingStatus');
        if (statusElement) {
            statusElement.innerHTML = step;
        }
        
        if (progress && uploadProgress) {
            uploadProgress.style.width = `${progress}%`;
            uploadProgress.setAttribute('aria-valuenow', progress);
        }
    }
    
    function showError(message) {
        errorContainer.classList.remove('d-none');
        errorContainer.innerHTML = `<div class="alert alert-danger">${message}</div>`;
    }
    
    function updateResults(data) {
        // Update primary style
        if (document.getElementById('primaryStyle')) {
            document.getElementById('primaryStyle').textContent = data.primary_style || 'Unknown Style';
        }
        
        // Update style tags
        updateStyleTags(data.style_tags || []);
        
        // Update description
        if (document.getElementById('styleDescription')) {
            document.getElementById('styleDescription').textContent = data.description || 'No description available.';
        }
        
        // Update styling tips
        if (document.getElementById('stylingTips')) {
            document.getElementById('stylingTips').textContent = data.styling_tips || 'No styling tips available.';
        }
        
        // Update attributes
        updateAttributes(data.attributes || {});
        
        // Update outfit combinations
        updateOutfitCombinations(data.outfit_combinations || []);
        
        // Update product recommendations
        updateProductRecommendations(data.products || data.recommendations || []);
        
        // Update the uploaded image
        if (document.getElementById('resultImage')) {
            document.getElementById('resultImage').src = data.image_url;
        }
    }
    
    // Function to update style tags
    function updateStyleTags(tags) {
        const container = document.getElementById('styleTags');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (!tags || tags.length === 0) {
            container.innerHTML = '<span class="badge bg-secondary me-1">No tags</span>';
            return;
        }
        
        tags.forEach(tag => {
            const badge = document.createElement('span');
            badge.className = 'badge bg-info me-1 mb-1';
            badge.textContent = tag;
            container.appendChild(badge);
        });
    }
    
    // Function to update attributes
    function updateAttributes(attributes) {
        const container = document.getElementById('attributesContainer');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (!attributes || Object.keys(attributes).length === 0) {
            container.innerHTML = '<p class="text-muted">No detailed attributes available.</p>';
            return;
        }
        
        // Sort attributes by category
        const categories = {};
        for (const [key, value] of Object.entries(attributes)) {
            const category = key.split('_')[0];
            if (!categories[category]) {
                categories[category] = [];
            }
            categories[category].push({ key, value });
        }
        
        // Create accordion for each category
        let accordionHtml = '';
        let index = 0;
        
        for (const [category, attrs] of Object.entries(categories)) {
            const headingId = `heading${index}`;
            const collapseId = `collapse${index}`;
            const isFirst = index === 0;
            
            const accordionItem = document.createElement('div');
            accordionItem.className = 'accordion-item';
            
            accordionItem.innerHTML = `
                <h2 class="accordion-header" id="${headingId}">
                    <button class="accordion-button ${isFirst ? '' : 'collapsed'}" type="button" 
                            data-bs-toggle="collapse" data-bs-target="#${collapseId}" 
                            aria-expanded="${isFirst ? 'true' : 'false'}" aria-controls="${collapseId}">
                        ${category.charAt(0).toUpperCase() + category.slice(1)} Attributes
                    </button>
                </h2>
                <div id="${collapseId}" class="accordion-collapse collapse ${isFirst ? 'show' : ''}" 
                     aria-labelledby="${headingId}" data-bs-parent="#attributesAccordion">
                    <div class="accordion-body">
                        <ul class="list-group list-group-flush">
                            ${attrs.map(attr => `
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    <span>${attr.key.split('_').slice(1).join(' ').charAt(0).toUpperCase() + attr.key.split('_').slice(1).join(' ').slice(1)}</span>
                                    <span class="badge bg-primary rounded-pill">${attr.value}</span>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            `;
            
            container.appendChild(accordionItem);
            index++;
        }
    }
    
    // Function to update outfit combinations
    function updateOutfitCombinations(outfits) {
        const container = document.getElementById('outfitCombinationsContainer');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (!outfits || outfits.length === 0) {
            container.innerHTML = '<p class="text-muted">No outfit combinations available.</p>';
            return;
        }
        
        outfits.forEach((outfit, index) => {
            const accordionItem = document.createElement('div');
            accordionItem.className = 'accordion-item';
            
            const headingId = `outfitHeading${index}`;
            const collapseId = `outfitCollapse${index}`;
            const isFirst = index === 0;
            
            accordionItem.innerHTML = `
                <h2 class="accordion-header" id="${headingId}">
                    <button class="accordion-button ${isFirst ? '' : 'collapsed'}" type="button" 
                            data-bs-toggle="collapse" data-bs-target="#${collapseId}" 
                            aria-expanded="${isFirst ? 'true' : 'false'}" aria-controls="${collapseId}">
                        ${outfit.name || `Outfit Combination ${index + 1}`}
                    </button>
                </h2>
                <div id="${collapseId}" class="accordion-collapse collapse ${isFirst ? 'show' : ''}" 
                     aria-labelledby="${headingId}" data-bs-parent="#outfitCombinationsAccordion">
                    <div class="accordion-body">
                        <p>${outfit.description || 'No description available.'}</p>
                        <ul class="list-group list-group-flush mb-3">
                            ${outfit.components ? outfit.components.map(component => `
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    <span>${component.item}</span>
                                    <span class="badge bg-secondary rounded-pill">${component.type || 'Item'}</span>
                                </li>
                            `).join('') : ''}
                        </ul>
                        ${outfit.styling_tip ? `<p class="mb-0"><strong>Styling Tip:</strong> ${outfit.styling_tip}</p>` : ''}
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
        
        // Check if the first product is an error message
        if (products.length === 1 && products[0].is_error_message) {
            const errorMessage = products[0];
            
            container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-warning" role="alert">
                        <h4 class="alert-heading">${errorMessage.title || 'API Error'}</h4>
                        <p>${errorMessage.description || 'There was an error fetching product recommendations.'}</p>
                        <hr>
                        <p class="mb-0">Please try again later to see real product recommendations.</p>
                    </div>
                </div>
            `;
            return;
        }
        
        products.forEach(product => {
            const col = document.createElement('div');
            col.className = 'col';
            
            // Use image instead of image_url for consistency
            const imageUrl = product.image || product.image_url || '';
            
            col.innerHTML = `
                <div class="card h-100 border-0">
                    <img src="${imageUrl}" class="card-img-top" alt="${product.title || 'Product'}" onerror="this.src='${product.fallback_image || '/static/images/placeholder.jpg'}'">
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
                            ${product.seller ? `<span class="small text-muted">Seller: ${product.seller}</span>` : ''}
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
                        <a href="${product.url || '#'}" class="btn btn-primary btn-sm w-100" ${product.url && product.url !== '#' ? 'target="_blank"' : ''}>
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
        
        // Show the feedback section
        document.getElementById('feedbackSection').classList.remove('d-none');
        
        // Set up click handlers
        accurateBtn.onclick = function() {
            submitFeedback(predictionId, style, true);
        };
        
        inaccurateBtn.onclick = function() {
            submitFeedback(predictionId, style, false);
        };
    }
    
    // Function to submit feedback
    function submitFeedback(predictionId, style, isAccurate) {
        const feedbackData = {
            prediction_id: predictionId,
            style: style,
            is_accurate: isAccurate
        };
        
        fetch('/submit_feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(feedbackData),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Feedback submitted:', data);
            // Show thanks message
            document.getElementById('feedbackThanks').classList.remove('d-none');
            // Disable buttons
            document.getElementById('accurateBtn').disabled = true;
            document.getElementById('inaccurateBtn').disabled = true;
        })
        .catch((error) => {
            console.error('Error submitting feedback:', error);
        });
    }
});
