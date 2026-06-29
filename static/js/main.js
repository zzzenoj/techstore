// Update total price preview on order page
const qtyInput = document.getElementById('quantity');
const totalPreview = document.getElementById('total-preview');

if (qtyInput && totalPreview) {
    const price = parseFloat(qtyInput.dataset.price);
    qtyInput.addEventListener('input', () => {
        const qty = parseInt(qtyInput.value) || 1;
        const total = (price * qty).toLocaleString('ru-RU', {maximumFractionDigits: 0});
        totalPreview.innerHTML = `Итого: <strong>${total} ₽</strong>`;
    });
}
