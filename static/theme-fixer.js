/**
 * Theme Fixer for CarHub
 * 
 * This script handles special fixes for the light theme
 * to ensure consistent styling across templates with inline styles
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we need to apply light theme fixes
    const isLightTheme = localStorage.getItem('theme') === 'light';
    if (isLightTheme) {
        applyLightThemeFixes();
    }
    
    // Listen for theme changes
    document.body.addEventListener('themeChanged', function(event) {
        const newTheme = event.detail.theme;
        if (newTheme === 'light') {
            applyLightThemeFixes();
        } else {
            removeLightThemeFixes();
        }
    });
});

/**
 * Apply fixes for light theme to elements that might have inline styles
 */
function applyLightThemeFixes() {
    // 1. Find all video elements with filter attributes
    const videos = document.querySelectorAll('video');
    videos.forEach(video => {
        if (video.style.filter && video.style.filter.includes('brightness')) {
            video.setAttribute('data-original-filter', video.style.filter);
            video.style.filter = 'brightness(0.8) contrast(1.2) saturate(1.0)';
        }
    });
    
    // 2. Find elements with specific background colors set inline
    const darkBackgroundElements = document.querySelectorAll('[style*="background-color"]');
    darkBackgroundElements.forEach(element => {
        const style = element.getAttribute('style');
        if (style.includes('#0a0a1a') || style.includes('#181828') || 
            style.includes('#23235b') || style.includes('rgb(10, 10, 26)')) {
            element.setAttribute('data-original-bg', element.style.backgroundColor);
            element.style.backgroundColor = '#ffffff';
        }
    });
    
    // 3. Find elements with dark text colors
    const lightTextElements = document.querySelectorAll('[style*="color"]');
    lightTextElements.forEach(element => {
        const style = element.getAttribute('style');
        if (style.includes('#e0e6ff') || style.includes('#b3baff') || 
            style.includes('rgb(224, 230, 255)') || style.includes('rgb(179, 186, 255)')) {
            element.setAttribute('data-original-color', element.style.color);
            element.style.color = '#333333';
        }
    });
    
    // 4. Find gradients that need modification
    const gradientBackgrounds = document.querySelectorAll('[style*="radial-gradient"], [style*="linear-gradient"]');
    gradientBackgrounds.forEach(element => {
        const style = element.getAttribute('style');
        if (style.includes('#0a0a1a') || style.includes('#181828') || 
            style.includes('#23235b') || style.includes('rgba(0, 0, 0,')) {
            element.setAttribute('data-original-gradient', element.style.background);
            element.style.background = 'radial-gradient(ellipse at top left, #f0f0f7 0%, #ffffff 100%)';
        }
    });
}

/**
 * Remove light theme fixes when switching back to dark theme
 */
function removeLightThemeFixes() {
    // 1. Restore video filters
    const videos = document.querySelectorAll('video[data-original-filter]');
    videos.forEach(video => {
        const originalFilter = video.getAttribute('data-original-filter');
        if (originalFilter) {
            video.style.filter = originalFilter;
        }
    });
    
    // 2. Restore background colors
    const bgElements = document.querySelectorAll('[data-original-bg]');
    bgElements.forEach(element => {
        const originalBg = element.getAttribute('data-original-bg');
        if (originalBg) {
            element.style.backgroundColor = originalBg;
        }
    });
    
    // 3. Restore text colors
    const colorElements = document.querySelectorAll('[data-original-color]');
    colorElements.forEach(element => {
        const originalColor = element.getAttribute('data-original-color');
        if (originalColor) {
            element.style.color = originalColor;
        }
    });
    
    // 4. Restore gradients
    const gradientElements = document.querySelectorAll('[data-original-gradient]');
    gradientElements.forEach(element => {
        const originalGradient = element.getAttribute('data-original-gradient');
        if (originalGradient) {
            element.style.background = originalGradient;
        }
    });
}
