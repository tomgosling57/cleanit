// static/js/timetable_scrolling.js

let currentScrollAnimation = null;

function smoothScrollTo(element, targetScrollLeft, duration) {
    const startScrollLeft = element.scrollLeft;
    const distance = targetScrollLeft - startScrollLeft;
    const startTime = performance.now();

    if (currentScrollAnimation) {
        cancelAnimationFrame(currentScrollAnimation);
    }

    function animateScroll(currentTime) {
        const elapsedTime = currentTime - startTime;
        const progress = Math.min(elapsedTime / duration, 1);
        const easedProgress = 0.5 - Math.cos(progress * Math.PI) / 2; // Ease-in-out function

        element.scrollLeft = startScrollLeft + distance * easedProgress;

        if (progress < 1) {
            currentScrollAnimation = requestAnimationFrame(animateScroll);
        } else {
            currentScrollAnimation = null;
        }
    }
    currentScrollAnimation = requestAnimationFrame(animateScroll);
}

function initTimetableScrolling() {
    const teamColumnsContainer = document.getElementById('team-columns-container');
    const scrollLeftButton = document.getElementById('scroll-left-button');
    const scrollRightButton = document.getElementById('scroll-right-button');

    if (teamColumnsContainer && scrollLeftButton && scrollRightButton) {
        const scrollAmount = 300; // Adjust scroll amount as needed
        const scrollDuration = 300; // Adjust duration as needed (milliseconds)
        let currentTargetScrollLeft = teamColumnsContainer.scrollLeft;

        scrollLeftButton.addEventListener('click', () => {
            currentTargetScrollLeft -= scrollAmount;
            smoothScrollTo(teamColumnsContainer, currentTargetScrollLeft, scrollDuration);
        });

        scrollRightButton.addEventListener('click', () => {
            currentTargetScrollLeft += scrollAmount;
            smoothScrollTo(teamColumnsContainer, currentTargetScrollLeft, scrollDuration);
        });

        // Initialize currentTargetScrollLeft when the container is swapped by HTMX
        htmx.on("htmx:afterSwap", (event) => {
            if (event.detail.target.id === 'team-timetable-view') {
                currentTargetScrollLeft = teamColumnsContainer.scrollLeft;
            }
        });

    } else {
        console.warn('Timetable scrolling elements not found. Skipping initialization.');
    }
}

// Make function globally available
window.initTimetableScrolling = initTimetableScrolling;