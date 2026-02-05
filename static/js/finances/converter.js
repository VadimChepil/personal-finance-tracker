document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('converterForm');
    const resultDiv = document.getElementById('result');
    const resultText = document.getElementById('resultText');
    const convertBtn = document.getElementById('convertBtn');
    const swapBtn = document.getElementById('swapCurrencies');
    
    const converterUrl = form.dataset.converterUrl;

    // Currency exchange
    swapBtn.addEventListener('click', function() {
        const fromCurrency = document.getElementById('from_currency');
        const toCurrency = document.getElementById('to_currency');
        const temp = fromCurrency.value;
        fromCurrency.value = toCurrency.value;
        toCurrency.value = temp;
    });
    
    // AJAX convertation
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        convertBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Конвертація...';
        convertBtn.disabled = true;
        
        const formData = new FormData(form);
        
        fetch(converterUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const amount = formData.get('amount');
                const fromCurrency = document.getElementById('from_currency').value;
                
                resultText.innerHTML = `
                    ${amount} ${fromCurrency} = 
                    <strong>${data.converted_amount} ${data.currency}</strong>
                `;
                resultDiv.style.display = 'block';
            } else {
                resultText.innerHTML = '<span class="text-danger">Помилка конвертації. Перевірте API ключ.</span>';
                resultDiv.style.display = 'block';
            }
        })
        .catch(error => {
            resultText.innerHTML = '<span class="text-danger">Помилка сервера. Спробуйте пізніше.</span>';
            resultDiv.style.display = 'block';
        })
        .finally(() => {
            convertBtn.innerHTML = '<i class="bi bi-calculator me-2"></i>Конвертувати';
            convertBtn.disabled = false;
        });
    });
});