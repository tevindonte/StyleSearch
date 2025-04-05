// Simple script for image upload handling
document.addEventListener('DOMContentLoaded', function() {
    console.log('Upload script loaded');
    
    // Get references to the DOM elements
    const browseButton = document.getElementById('browseButton');
    const imageInput = document.getElementById('imageInput');
    const previewContainer = document.getElementById('previewContainer');
    const imagePreview = document.getElementById('imagePreview');
    const uploadArea = document.getElementById('upload-area');
    
    // Only add event listeners if elements exist
    if (browseButton && imageInput) {
        console.log('Found upload elements');
        
        // Remove any existing event listeners (just in case)
        browseButton.replaceWith(browseButton.cloneNode(true));
        imageInput.replaceWith(imageInput.cloneNode(true));
        
        // Get the fresh elements after replacement
        const newBrowseButton = document.getElementById('browseButton');
        const newImageInput = document.getElementById('imageInput');
        
        // Add event listener to browse button
        newBrowseButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Browse button clicked');
            newImageInput.click();
        });
        
        // Add event listener to file input
        newImageInput.addEventListener('change', function() {
            console.log('File input changed');
            if (this.files && this.files[0]) {
                const file = this.files[0];
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    previewContainer.classList.remove('d-none');
                    document.getElementById('predictButton').disabled = false;
                    console.log('Image preview displayed');
                };
                
                reader.readAsDataURL(file);
            }
        });
    } else {
        console.error('Upload elements not found');
    }
});
