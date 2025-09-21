// Transactions page functionality
// Session check for transactions page
fetch('/api/auth/current', { credentials: 'include' })
    .then(res => res.json())
    .then(data => {
        if (!data.user) {
            window.location.href = 'login.html';
        }
    })
    .catch(() => {
        window.location.href = 'login.html';
    });
let currentPage = 0;
const transactionsPerPage = 20;
let currentFilters = {};

document.addEventListener('DOMContentLoaded', function() {
    initializeTransactionsPage();
});

async function initializeTransactionsPage() {
    try {
        // Initialize filters
        initializeFilters();
        
        // Load initial transactions
        await loadTransactions();
        
        // Set up pagination
        setupPagination();
        
    } catch (error) {
        console.error('Error initializing transactions page:', error);
        showError('Failed to load transactions page. Please refresh and try again.');
    }
}

function initializeFilters() {
    // Add event listeners for filter controls
    const fromDateInput = document.getElementById('fromDate');
    const toDateInput = document.getElementById('toDate');
    const categoryFilter = document.getElementById('categoryFilter');
    const vendorFilter = document.getElementById('vendorFilter');
    const searchButton = document.getElementById('searchButton');
    const clearButton = document.getElementById('clearButton');
    
    if (searchButton) {
        searchButton.addEventListener('click', applyFilters);
    }
    
    if (clearButton) {
        clearButton.addEventListener('click', clearFilters);
    }
    
    // Auto-search on Enter key
    [fromDateInput, toDateInput, categoryFilter, vendorFilter].forEach(input => {
        if (input) {
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    applyFilters();
                }
            });
        }
    });
}

async function loadTransactions(page = 0) {
    try {
        showLoading('transactionsTableBody', true);
        
        // Build query parameters
        const params = new URLSearchParams({
            limit: transactionsPerPage,
            offset: page * transactionsPerPage,
            ...currentFilters
        });
        
        // Call transactions API
        const url = `transactions?${params.toString()}`;
        const data = await API.apiCall('transactions', {
            method: 'GET'
        });
        
        // Update table
        updateTransactionsTable(data.items || []);
        
        // Update pagination
        updatePagination(data.total || 0, page);
        
        // Update summary stats
        updateTransactionsSummary(data.items || [], data.total || 0);
        
    } catch (error) {
        console.error('Error loading transactions:', error);
        showError('Failed to load transactions. Please try again.');
        updateTransactionsTable([]);
    } finally {
        showLoading('transactionsTableBody', false);
    }
}

function updateTransactionsTable(transactions) {
    const tableBody = getOrCreateTableBody();
    
    if (transactions.length === 0) {
        tableBody.innerHTML = `
            <tr class="border-b border-gray-200">
                <td colspan="6" class="py-8 text-center text-gray-500">
                    <div class="flex flex-col items-center">
                        <span class="material-symbols-outlined text-6xl text-gray-300 mb-4">receipt_long</span>
                        <p class="text-lg mb-2">No transactions found</p>
                        <p class="text-sm">Try adjusting your filters or <a href="upload.html" class="text-blue-600 hover:underline">upload a receipt</a></p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    const rows = transactions.map(transaction => `
        <tr class="border-b border-gray-200 hover:bg-gray-50">
            <td class="py-3 px-2">
                <div class="font-mono text-xs text-gray-500">${transaction.id ? transaction.id.substring(0, 8) + '...' : 'N/A'}</div>
            </td>
            <td class="py-3 px-2">
                <div class="font-medium">${transaction.vendor_name || 'Unknown Vendor'}</div>
                <div class="text-sm text-gray-500">${formatDate(transaction.invoice_date)}</div>
            </td>
            <td class="py-3 px-2">
                <div class="font-semibold ${getAmountColor(transaction.amount)}">${formatCurrency(transaction.amount || 0)}</div>
                <div class="text-xs text-gray-500">${transaction.currency || 'MYR'}</div>
            </td>
            <td class="py-3 px-2">
                <span class="inline-block ${getCategoryColor(transaction.category_name)} px-2 py-1 rounded text-sm">
                    ${transaction.category_name || 'Uncategorized'}
                </span>
            </td>
            <td class="py-3 px-2">
                <span class="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                    ${transaction.type || 'expense'}
                </span>
            </td>
            <td class="py-3 px-2">
                <div class="flex space-x-2">
                    ${transaction.document_url ? 
                        `<a href="${transaction.document_url}" target="_blank" class="text-blue-600 hover:text-blue-900" title="View Receipt">
                            <span class="material-symbols-outlined text-sm">visibility</span>
                        </a>` : ''
                    }
                    <button onclick="editTransaction('${transaction.id}')" class="text-gray-600 hover:text-gray-900" title="Edit">
                        <span class="material-symbols-outlined text-sm">edit</span>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    tableBody.innerHTML = rows;
}

function getOrCreateTableBody() {
    let tableBody = document.getElementById('transactionsTableBody');
    if (!tableBody) {
        // Update the existing table structure
        const existingTable = document.querySelector('.recent_order table tbody');
        if (existingTable) {
            existingTable.id = 'transactionsTableBody';
            
            // Update headers
            const headers = document.querySelectorAll('.recent_order table thead th');
            const newHeaders = ['ID', 'Vendor & Date', 'Amount', 'Category', 'Type', 'Actions'];
            headers.forEach((header, index) => {
                if (newHeaders[index]) {
                    header.textContent = newHeaders[index];
                }
            });
            
            // Add missing headers if needed
            const headerRow = document.querySelector('.recent_order table thead tr');
            while (headers.length < newHeaders.length) {
                const th = document.createElement('th');
                th.className = 'text-left pb-2';
                th.textContent = newHeaders[headers.length];
                headerRow.appendChild(th);
            }
            
            return existingTable;
        }
    }
    return tableBody;
}

function updateTransactionsSummary(transactions, total) {
    // Calculate summary statistics
    const totalAmount = transactions.reduce((sum, t) => sum + (parseFloat(t.amount) || 0), 0);
    const categories = [...new Set(transactions.map(t => t.category_name).filter(Boolean))];
    
    // Update or create summary section
    let summarySection = document.getElementById('transactionsSummary');
    if (!summarySection) {
        summarySection = document.createElement('div');
        summarySection.id = 'transactionsSummary';
        summarySection.className = 'bg-white p-4 rounded-lg shadow-sm mb-6';
        
        const titleSection = document.querySelector('.titledate');
        if (titleSection) {
            titleSection.insertAdjacentElement('afterend', summarySection);
        }
    }
    
    summarySection.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="text-center">
                <div class="text-2xl font-bold text-blue-600">${total}</div>
                <div class="text-sm text-gray-500">Total Transactions</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold text-red-600">${formatCurrency(totalAmount)}</div>
                <div class="text-sm text-gray-500">Total Amount</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold text-green-600">${categories.length}</div>
                <div class="text-sm text-gray-500">Categories</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold text-purple-600">${totalAmount > 0 ? formatCurrency(totalAmount / transactions.length) : formatCurrency(0)}</div>
                <div class="text-sm text-gray-500">Average Amount</div>
            </div>
        </div>
    `;
}

function setupPagination() {
    // Add pagination controls if they don't exist
    let paginationSection = document.getElementById('paginationControls');
    if (!paginationSection) {
        paginationSection = document.createElement('div');
        paginationSection.id = 'paginationControls';
        paginationSection.className = 'flex justify-between items-center mt-6';
        
        const recentOrderSection = document.querySelector('.recent_order');
        if (recentOrderSection) {
            recentOrderSection.appendChild(paginationSection);
        }
    }
}

function updatePagination(total, currentPageNum) {
    const totalPages = Math.ceil(total / transactionsPerPage);
    const paginationSection = document.getElementById('paginationControls');
    
    if (!paginationSection || totalPages <= 1) {
        if (paginationSection) paginationSection.innerHTML = '';
        return;
    }
    
    const startItem = (currentPageNum * transactionsPerPage) + 1;
    const endItem = Math.min((currentPageNum + 1) * transactionsPerPage, total);
    
    paginationSection.innerHTML = `
        <div class="text-sm text-gray-500">
            Showing ${startItem}-${endItem} of ${total} transactions
        </div>
        <div class="flex space-x-2">
            <button 
                onclick="changePage(${currentPageNum - 1})" 
                ${currentPageNum === 0 ? 'disabled' : ''}
                class="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                Previous
            </button>
            <span class="px-3 py-1 text-sm">
                Page ${currentPageNum + 1} of ${totalPages}
            </span>
            <button 
                onclick="changePage(${currentPageNum + 1})" 
                ${currentPageNum >= totalPages - 1 ? 'disabled' : ''}
                class="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                Next
            </button>
        </div>
    `;
}

async function changePage(newPage) {
    if (newPage < 0) return;
    currentPage = newPage;
    await loadTransactions(currentPage);
}

async function applyFilters() {
    // Get filter values
    const fromDate = document.getElementById('fromDate')?.value;
    const toDate = document.getElementById('toDate')?.value;
    const category = document.getElementById('categoryFilter')?.value;
    const vendor = document.getElementById('vendorFilter')?.value;
    
    // Update current filters
    currentFilters = {};
    if (fromDate) currentFilters.from = fromDate;
    if (toDate) currentFilters.to = toDate;
    if (category) currentFilters.category = category;
    if (vendor) currentFilters.vendor = vendor;
    
    // Reset to first page and reload
    currentPage = 0;
    await loadTransactions(currentPage);
}

function clearFilters() {
    // Clear all filter inputs
    const inputs = ['fromDate', 'toDate', 'categoryFilter', 'vendorFilter'];
    inputs.forEach(id => {
        const element = document.getElementById(id);
        if (element) element.value = '';
    });
    
    // Clear filters and reload
    currentFilters = {};
    currentPage = 0;
    loadTransactions(currentPage);
}

function editTransaction(transactionId) {
    // For MVP, just show alert
    alert(`Edit transaction functionality will be implemented in next version.\nTransaction ID: ${transactionId}`);
}

// Utility functions (reuse from dashboard.js)
function formatCurrency(amount) {
    if (typeof amount !== 'number') {
        amount = parseFloat(amount) || 0;
    }
    return 'RM ' + amount.toLocaleString('en-MY', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
    });
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown Date';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-MY');
    } catch {
        return dateString;
    }
}

function getAmountColor(amount) {
    return amount > 0 ? 'text-red-600' : 'text-gray-600';
}

function getCategoryColor(category) {
    const colors = {
        'Food & Beverage': 'bg-orange-100 text-orange-800',
        'Transportation': 'bg-blue-100 text-blue-800', 
        'Utilities': 'bg-green-100 text-green-800',
        'Office Supplies': 'bg-purple-100 text-purple-800',
        'Others': 'bg-gray-100 text-gray-800'
    };
    return colors[category] || colors['Others'];
}