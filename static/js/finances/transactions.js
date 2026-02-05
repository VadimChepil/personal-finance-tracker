document.addEventListener('DOMContentLoaded', function() {
    // Automatically fill in today's date in the “to” field
    const dateToField = document.getElementById('date_to');
    if (dateToField && !dateToField.value) {
        const today = new Date().toISOString().split('T')[0];
        dateToField.value = today;
    }
    
    // Automatically fill in the beginning of the month in the “from” field
    const dateFromField = document.getElementById('date_from');
    if (dateFromField && !dateFromField.value) {
        const firstDay = new Date();
        firstDay.setDate(1);
        const firstDayStr = firstDay.toISOString().split('T')[0];
        dateFromField.value = firstDayStr;
    }
});
