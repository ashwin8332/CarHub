/**
 * Theme Toggle Functionality for CarHub
 * 
 * This script handles theme toggling between light and dark modes
 * across all templates in the CarHub application.
 */

// Execute when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme
    initializeTheme();
});

/**
 * Initialize theme based on localStorage or default to dark
 */
function initializeTheme() {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return; // Skip if toggle button doesn't exist on this page
    
    const storedTheme = localStorage.getItem('theme') || 'dark';
    
    // Apply theme
    applyTheme(storedTheme);
    
    // Add click event listener to toggle button
    themeToggle.addEventListener('click', toggleTheme);
}

/**
 * Toggle between light and dark themes
 */
function toggleTheme() {
    // Add transition class to body
    document.body.classList.add('theme-transition');
    
    // Toggle theme
    const isLightTheme = document.body.classList.toggle('theme-light');
    const theme = isLightTheme ? 'light' : 'dark';
    
    // Update localStorage
    localStorage.setItem('theme', theme);
    
    // Apply theme to all elements
    applyTheme(theme);
    
    // Dispatch theme change event for other scripts
    const themeChangedEvent = new CustomEvent('themeChanged', {
        detail: { theme: theme }
    });
    document.body.dispatchEvent(themeChangedEvent);
    
    // Create a flash effect
    const flash = document.createElement('div');
    flash.className = 'theme-switch-flash';
    document.body.appendChild(flash);
    
    // Remove flash after animation
    setTimeout(() => {
        if (flash && flash.parentNode) {
            flash.parentNode.removeChild(flash);
        }
        // Remove transition class
        document.body.classList.remove('theme-transition');
    }, 500);
}

/**
 * Apply theme to all elements and update toggle icon
 */
function applyTheme(theme) {
    // Apply to body
    document.body.classList.toggle('theme-light', theme === 'light');
    
    // Update toggle button icon with animation
    updateThemeToggleIcon(theme);
    
    // Handle inline styles if present
    handleInlineStyles(theme);
}

/**
 * Update the theme toggle icon based on current theme
 */
function updateThemeToggleIcon(theme) {
    const lightIcon = document.querySelector('.light-icon');
    const darkIcon = document.querySelector('.dark-icon');
    const themeToggle = document.getElementById('themeToggle');
    
    if (!lightIcon || !darkIcon || !themeToggle) return;
    
    // Add animation class
    themeToggle.classList.add('theme-toggle-animating');
    
    // Wait for animation to start before changing icons
    setTimeout(() => {
        if (theme === 'light') {
            lightIcon.style.display = 'none';
            darkIcon.style.display = 'inline-block';
        } else {
            lightIcon.style.display = 'inline-block';
            darkIcon.style.display = 'none';
        }
        
        // Remove animation class
        setTimeout(() => {
            themeToggle.classList.remove('theme-toggle-animating');
        }, 300);
    }, 150);
}

/**
 * Handle inline styles in specific templates
 */
function handleInlineStyles(theme) {
    // Get all style tags in the document
    const styleTags = document.querySelectorAll('style');
    
    // Process each style tag
    styleTags.forEach(styleTag => {
        const originalContent = styleTag.getAttribute('data-original-content');
        
        // If this is the first time processing this tag, store the original content
        if (!originalContent) {
            styleTag.setAttribute('data-original-content', styleTag.textContent);
        }
        
        // Apply theme-specific modifications to inline styles
        if (theme === 'light') {
            // Replace dark colors with light colors
            let styleContent = originalContent || styleTag.textContent;
            
            // Background colors
            styleContent = styleContent.replace(/background:?\s*radial-gradient\(.*?#23235b.*?#0a0a1a.*?\)/g, 
                'background: radial-gradient(ellipse at top left, #f0f0f7 0%, #ffffff 100%)');
            
            styleContent = styleContent.replace(/background-color:?\s*#0a0a1a/g, 'background-color: #ffffff');
            styleContent = styleContent.replace(/background-color:?\s*#1a1a1a/g, 'background-color: #f8f8f8');
            styleContent = styleContent.replace(/background-color:?\s*#23235b/g, 'background-color: #f0f0f7');
            styleContent = styleContent.replace(/background-color:?\s*#181828/g, 'background-color: #f5f5f5');
            
            // Text colors
            styleContent = styleContent.replace(/color:?\s*#e0e6ff/g, 'color: #333333');
            styleContent = styleContent.replace(/color:?\s*#b3baff/g, 'color: #555555');
            styleContent = styleContent.replace(/color:?\s*rgba\(\s*255\s*,\s*255\s*,\s*255\s*,\s*0\.\d+\s*\)/g, 
                (match) => {
                    // Extract opacity from the rgba color
                    const opacity = parseFloat(match.match(/0\.\d+/)[0]);
                    return `color: rgba(0, 0, 0, ${opacity})`;
                });
            
            // Apply the modified styles
            styleTag.textContent = styleContent;
        } else {
            // Restore original dark theme styles
            if (originalContent) {
                styleTag.textContent = originalContent;
            }
        }
    });
}

// Apply theme on page load based on localStorage
document.addEventListener('DOMContentLoaded', function() {
    const storedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(storedTheme);
});
