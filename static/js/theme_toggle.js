document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.querySelector('.theme-toggle');
    const body = document.body;

    // Pobierz zapisany motyw z pamięci przeglądarki
    const currentTheme = localStorage.getItem('theme');

    // Ustaw jasny motyw i odpowiedni stan ikony, jeśli był wcześniej wybrany
    if (currentTheme === 'light') {
        body.classList.add('light-theme');
        themeToggle.classList.add('theme-toggle--toggled'); // Zmienia wygląd ikony
    }

    // Obsługa kliknięcia
    themeToggle.addEventListener('click', () => {
        // Przełącz motyw strony
        body.classList.toggle('light-theme');
        
        // Przełącz stan (animację) ikony
        themeToggle.classList.toggle('theme-toggle--toggled');
        
        // Zapisz wybór, sprawdzając obecność klasy na body
        const theme = body.classList.contains('light-theme') ? 'light' : 'dark';
        localStorage.setItem('theme', theme);
    });
});