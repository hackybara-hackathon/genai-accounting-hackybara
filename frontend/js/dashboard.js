
async function loadOrders() {
  try {
    const response = await fetch('/api/dashboard/data');
    const orders = await response.json();
    const tableBody = document.getElementById('ordersTableBody');
    tableBody.innerHTML = "";

    orders.forEach(order => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${order.id}</td>
        <td>${order.product_name}</td>
        <td>${order.status}</td>
      `;
      tableBody.appendChild(tr);
    });
  } catch (err) {
    console.error(err);
  }
}