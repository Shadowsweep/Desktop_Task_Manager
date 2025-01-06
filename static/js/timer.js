let countdown;
let minutes = 25;
let seconds = 0;

function startTimer() {
    if (countdown) return; // Prevent multiple timers
    countdown = setInterval(() => {
        if (seconds === 0 && minutes === 0) {
            clearInterval(countdown);
            countdown = null;
            alert("Time's up!");
        } else if (seconds === 0) {
            minutes--;
            seconds = 59;
        } else {
            seconds--;
        }
        updateClock();
    }, 1000);
}

function resetTimer() {
    clearInterval(countdown);
    countdown = null;
    minutes = 25;
    seconds = 0;
    updateClock();
}

function updateClock() {
    document.getElementById('minutes').textContent = minutes.toString().padStart(2, '0');
    document.getElementById('seconds').textContent = seconds.toString().padStart(2, '0');
}
