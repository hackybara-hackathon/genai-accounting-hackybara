
// Dashboard functionality - loads real financial data
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
});

async function loadDashboardData() {
    try {
        showLoading('dashboardContent', true);
        
        // Load summary data from API
        const summaryData = await API.apiCall('summary');
        
        // Update KPIs
        updateKPIs(summaryData.kpis);
        
        // Update category breakdown
        updateCategoryBreakdown(summaryData.by_category_90d);
        
        // Load recent transactions
        await loadRecentTransactions();
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showError('Failed to load dashboard data. Please try refreshing the page.');
    } finally {
        showLoading('dashboardContent', false);
    }
}

function updateKPIs(kpis) {
    // Update Total Expenses
    const expenseElement = document.querySelector('.expenses .left h1');
    if (expenseElement && kpis.total_expense !== undefined) {
        expenseElement.textContent = formatCurrency(kpis.total_expense);
    }
    
    // Update Receipt Count (using as "sales" for now) 
    const salesElement = document.querySelector('.sales .left h1');
    if (salesElement && kpis.receipt_count !== undefined) {
        salesElement.textContent = kpis.receipt_count;
    }
    
    // Update the sales title to reflect receipt count
    const salesTitle = document.querySelector('.sales .left h3');
    if (salesTitle) {
        salesTitle.textContent = 'Total Receipts';
    }
    
    // Update Average per Receipt (using as "income" for now)
    const incomeElement = document.querySelector('.income .left h1');
    if (incomeElement && kpis.avg_per_receipt !== undefined) {
        incomeElement.textContent = formatCurrency(kpis.avg_per_receipt);
    }
    
    // Update the income title to reflect average
    const incomeTitle = document.querySelector('.income .left h3');
    if (incomeTitle) {
        incomeTitle.textContent = 'Avg per Receipt';
    }
    
    // Update progress percentages based on top category
    updateProgressBars(kpis);
}

function updateProgressBars(kpis) {
    // Simple progress calculation based on data availability
    const expenseProgress = kpis.total_expense > 0 ? Math.min(90, Math.max(10, kpis.total_expense / 1000)) : 0;
    const receiptProgress = kpis.receipt_count > 0 ? Math.min(90, Math.max(10, kpis.receipt_count * 10)) : 0;
    const avgProgress = kpis.avg_per_receipt > 0 ? Math.min(90, Math.max(10, kpis.avg_per_receipt / 10)) : 0;
    
    // Update progress circles (simplified - just update the percentage text)
    const progressNumbers = document.querySelectorAll('.progress .number');
    if (progressNumbers.length >= 3) {
        progressNumbers[0].textContent = Math.round(receiptProgress) + '%';
        progressNumbers[1].textContent = Math.round(expenseProgress) + '%';
        progressNumbers[2].textContent = Math.round(avgProgress) + '%';
    }
}

function updateCategoryBreakdown(categories) {
    // For now, we'll display the top category in the existing layout
    // In a full implementation, you might add a chart here
    if (categories && categories.length > 0) {
        const topCategory = categories[0];
        console.log('Top spending category:', topCategory);
        
        // You could add a new section to display this data
        addCategorySection(categories);
    }
}

function addCategorySection(categories) {
    // Add category breakdown after insights section
    const insightsSection = document.querySelector('.insights');
    if (!insightsSection) return;
    
    // Check if category section already exists
    let categorySection = document.getElementById('categoryBreakdown');
    if (!categorySection) {
        categorySection = document.createElement('div');
        categorySection.id = 'categoryBreakdown';
        categorySection.className = 'bg-white p-6 rounded-lg shadow-sm mb-6';
        
        insightsSection.insertAdjacentElement('afterend', categorySection);
    }
    
    // Build category HTML
    let categoryHTML = '<h2 class="text-xl font-bold mb-4">Spending by Category (Last 90 Days)</h2>';
    
    if (categories.length === 0) {
        categoryHTML += '<p class="text-gray-500">No spending data available yet. Upload some receipts to see your spending breakdown!</p>';
    } else {
        categoryHTML += '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">';
        
        categories.slice(0, 6).forEach(category => {
            const percentage = categories.length > 1 ? 
                Math.round((category.total / categories[0].total) * 100) : 100;
                
            categoryHTML += `
                <div class="border border-gray-200 rounded-lg p-4">
                    <div class="flex justify-between items-center mb-2">
                        <h3 class="font-medium text-gray-700">${category.category}</h3>
                        <span class="text-sm text-gray-500">${percentage}%</span>
                    </div>
                    <p class="text-lg font-bold text-gray-900">${formatCurrency(category.total)}</p>
                    <div class="w-full bg-gray-200 rounded-full h-2 mt-2">
                        <div class="bg-blue-600 h-2 rounded-full" style="width: ${percentage}%"></div>
                    </div>
                </div>
            `;
        });
        
        categoryHTML += '</div>';
    }
    
    categorySection.innerHTML = categoryHTML;
}

async function loadRecentTransactions() {
    try {
        // Load recent transactions (limit to 5 for dashboard)
        const transactionData = await API.apiCall('transactions', {
            method: 'GET'
        });
        
        const transactions = transactionData.items || [];
        updateRecentTransactionsTable(transactions.slice(0, 5));
        
    } catch (error) {
        console.error('Error loading recent transactions:', error);
        // Don't show error for transactions as it's not critical for dashboard
    }
}

function updateRecentTransactionsTable(transactions) {
    // Update the existing table in the current HTML structure
    const existingTable = document.querySelector('.recent_order table tbody');
    if (!existingTable) return;
    
    // Update table headers to match financial data
    const headers = document.querySelectorAll('.recent_order table thead th');
    if (headers.length >= 4) {
        headers[0].textContent = 'Transaction ID';
        headers[1].textContent = 'Vendor';
        headers[2].textContent = 'Amount';
        headers[3].textContent = 'Category';
    }
    
    // Update the section title
    const sectionTitle = document.querySelector('.recent_order h1');
    if (sectionTitle) {
        sectionTitle.textContent = 'Recent Transactions';
    }
    
    if (transactions.length === 0) {
        existingTable.innerHTML = `
            <tr class="border-b border-gray-200">
                <td colspan="4" class="py-6 text-center text-gray-500">
                    No transactions yet. <a href="upload.html" class="text-blue-600 hover:underline">Upload your first receipt!</a>
                </td>
            </tr>
        `;
        return;
    }
    
    const rows = transactions.map(transaction => `
        <tr class="border-b border-gray-200">
            <td class="py-3 font-mono text-sm">${transaction.id ? transaction.id.substring(0, 8) + '...' : 'N/A'}</td>
            <td class="py-3">${transaction.vendor_name || 'Unknown Vendor'}</td>
            <td class="py-3 font-semibold ${getAmountColor(transaction.amount)}">${formatCurrency(transaction.amount || 0)}</td>
            <td class="py-3">
                <span class="inline-block ${getCategoryColor(transaction.category_name)} px-2 py-1 rounded text-sm">
                    ${transaction.category_name || 'Uncategorized'}
                </span>
            </td>
        </tr>
    `).join('');
    
    existingTable.innerHTML = rows;
}

// Utility functions
function formatCurrency(amount) {
    if (typeof amount !== 'number') {
        amount = parseFloat(amount) || 0;
    }
    return 'RM ' + amount.toLocaleString('en-MY', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
    });
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