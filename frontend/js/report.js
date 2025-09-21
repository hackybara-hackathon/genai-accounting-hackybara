// Authentication is handled by navbar.js, so no need to check here

// Reusable API helper
const API = {
	endpoints: {
		generateReport: 'https://<api-id>.execute-api.<region>.amazonaws.com/prod/generate-financial-report',
		listReports: 'https://<api-id>.execute-api.<region>.amazonaws.com/prod/list-reports'
	},
	async apiCall(endpoint, options = {}) {
		const url = this.endpoints[endpoint];
		const res = await fetch(url, options);
		return res.json();
	}
};

document.addEventListener('DOMContentLoaded', () => {
	// Generate Report button handler
	const genBtn = document.getElementById('generateReportBtn');
	if (genBtn) {
		genBtn.addEventListener('click', async () => {
			genBtn.disabled = true;
			genBtn.textContent = 'Generating...';
			try {
				const data = await API.apiCall('generateReport', { method: 'POST' });
				if (data.status === 'success' || data.success) {
					alert('Report generated!');
					loadReports();
				} else {
					alert('Failed to generate report: ' + (data.error || 'Unknown error'));
				}
			} catch (err) {
				alert('Error: ' + err.message);
			}
			genBtn.disabled = false;
			genBtn.textContent = 'Generate Report';
		});
	}

	// Load reports table
	async function loadReports() {
		const tbody = document.getElementById('reportTableBody');
		if (!tbody) return;
		tbody.innerHTML = '<tr><td colspan="4">Loading...</td></tr>';
		try {
			const data = await API.apiCall('listReports');
			if (data.reports && data.reports.length) {
				tbody.innerHTML = data.reports.map(r => `
					<tr class="border-b border-gray-200">
						<td class="py-3">${r.id || ''}</td>
						<td class="py-3">${r.name || ''}</td>
						<td class="py-3"><a href="${r.url}" target="_blank" class="text-blue-600 underline">Download</a></td>
						<td class="py-3">${new Date(r.created_at).toLocaleString()}</td>
					</tr>
				`).join('');
			} else {
				tbody.innerHTML = '<tr><td colspan="4">No reports found.</td></tr>';
			}
		} catch (err) {
			tbody.innerHTML = `<tr><td colspan=4>Error loading reports: ${err.message}</td></tr>`;
		}
	}

	loadReports();
});
