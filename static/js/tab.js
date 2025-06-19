const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');
            
            // Remove active state from all buttons
            tabButtons.forEach(btn => {
                btn.classList.remove('bg-[#003b73]','text-white');
                btn.classList.add('text-gray-600', 'hover:text-blue-500', 'hover:bg-gray-50');
            });
            
            // Add active state to clicked button
            button.classList.remove('bg-white','text-gray-600', 'hover:text-blue-500', 'hover:bg-gray-50');
            button.classList.add('bg-[#003b73]','text-white','rounded-t-lg');
            
            // Hide all tab contents
            tabContents.forEach(content => {
                content.classList.add('hidden');
            });
            
            // Show target tab content
            document.getElementById(targetTab).classList.remove('hidden');
        });
    });