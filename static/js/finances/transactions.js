document.addEventListener('DOMContentLoaded', function () {
    // Auto-fill date fields if empty
    const dateToField = document.getElementById('date_to');
    if (dateToField && !dateToField.value) {
        dateToField.value = new Date().toISOString().split('T')[0];
    }

    const dateFromField = document.getElementById('date_from');
    if (dateFromField && !dateFromField.value) {
        const firstDay = new Date();
        firstDay.setDate(1);
        dateFromField.value = firstDay.toISOString().split('T')[0];
    }

    // Category and subcategory dropdown elements
    const categorySelect = document.getElementById('category');
    const subcategorySelect = document.getElementById('subcategory');

    // Exit if elements don't exist
    if (!categorySelect || !subcategorySelect) return;

    // Store all subcategory options for filtering
    const allSubOptions = Array.from(subcategorySelect.options);

    function filterSubcategories(categoryId) {
        subcategorySelect.innerHTML = '';

        // Placeholder
        const placeholder = document.createElement('option');
        placeholder.value = '';
        placeholder.textContent = 'Всі підкатегорії';
        subcategorySelect.appendChild(placeholder);

        allSubOptions.forEach(option => {
            if (!option.dataset.parent) return;
            if (option.dataset.parent === categoryId) {
                subcategorySelect.appendChild(option);
            }
        });
    }

    // Page initialization
    if (categorySelect.value) {
        filterSubcategories(categorySelect.value);

        // Set subcategory if already selected via GET parameters
        const selectedSub = allSubOptions.find(opt => opt.selected);
        if (selectedSub && selectedSub.dataset.parent === categorySelect.value) {
            subcategorySelect.value = selectedSub.value;
        }
    }

    // Category selection handler
    categorySelect.addEventListener('change', function () {
        const categoryId = this.value;
        subcategorySelect.value = '';

        if (categoryId) {
            filterSubcategories(categoryId);
        } else {
            // If category is reset - show all subcategories
            subcategorySelect.innerHTML = '';
            allSubOptions.forEach(opt => subcategorySelect.appendChild(opt));
        }
    });

    // Subcategory selection handler
    subcategorySelect.addEventListener('change', function () {
        const option = this.options[this.selectedIndex];
        const parentId = option?.dataset.parent;

        if (parentId) {
            categorySelect.value = parentId;
            filterSubcategories(parentId);
            subcategorySelect.value = option.value;
        }
    });
});
