
function handleDragBar(){
    const sidebar = document.getElementById('sidebar');
    const resizer = document.getElementById('resizer');
    let isResizing = false;

    resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        document.body.style.cursor = 'col-resize';
        e.preventDefault(); // Zapobiega oznaczaniu tekstu myszką
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        
        // Obliczamy % szerokości na podstawie pozycji kursora (e.clientX)
        let newWidth = (e.clientX / document.body.clientWidth) * 100;
        
        // Granice przeciągania: minimum 10%, maksimum 50%
        if (newWidth > 10 && newWidth < 50) {
            sidebar.style.width = `${newWidth}%`;
        }
    });

    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            document.body.style.cursor = 'default';
        }
    });
}


function handleMatchSelection(){
    const matchItems = document.querySelectorAll('.match-item');
    const matchDetails = document.querySelectorAll('.match-details');
    const placeholder = document.getElementById('placeholder');

    matchItems.forEach(item => {
        item.addEventListener('click', () => {
            // Ukryj tekst powitalny ("Wybierz mecz z listy...")
            if(placeholder) placeholder.style.display = 'none';

            // Zwiń wszystkie dotychczas otwarte tabele
            matchDetails.forEach(detail => detail.style.display = 'none');

            // Pobierz ID docelowego diva i wyświetl go
            const targetId = item.getAttribute('data-target');
            const targetElement = document.getElementById(targetId);
            if(targetElement) {
                targetElement.style.display = 'block';
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Obsługa przeciągania (zmiana szerokości lewego panelu)
    handleDragBar();
    
    // 2. Obsługa kliknięć w listę meczy
    handleMatchSelection();
    
});