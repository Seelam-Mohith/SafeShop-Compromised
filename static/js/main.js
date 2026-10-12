// Main JavaScript - basic client-side interactions
document.addEventListener('DOMContentLoaded', function() {
    // Search form submission from navbar
    const searchForms = document.querySelectorAll('form.search-box');
    searchForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const input = form.querySelector('input[name="q"]');
            if (input && !input.value.trim()) {
                // Allow empty to just go to products page? Or prevent - but spec says search works
                // For better UX, allow normal navigation
            }
        });
    });
});
