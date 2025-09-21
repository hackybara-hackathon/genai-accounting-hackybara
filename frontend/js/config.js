// API Configuration for GenAI Accounting System
class APIConfig {
    constructor() {
        // Default to local development - update this after deployment
        this.baseURL = this.getBaseURL();
        this.endpoints = {
            classify: '/classify',
            transactions: '/transactions', 
            summary: '/summary',
            reportMonthly: '/report/monthly',
            forecast: '/forecast',
            insights: '/insights'
        };
    }

    getBaseURL() {
        // Check if we're in production (deployed to S3/CloudFront)
        if (window.location.hostname.includes('amazonaws.com') || 
            window.location.hostname.includes('cloudfront.net')) {
            // Updated with your actual API Gateway URL
            return 'https://xfnv4mgb64.execute-api.ap-southeast-1.amazonaws.com/prod';
        }
        
        // For local development with the FastAPI backend
        if (window.location.hostname === 'localhost' || 
            window.location.hostname === '127.0.0.1') {
            return 'http://localhost:8000';
        }
        
        // Updated with your actual API Gateway URL
        return 'https://xfnv4mgb64.execute-api.ap-southeast-1.amazonaws.com/prod';
    }

    getEndpoint(name) {
        return this.baseURL + this.endpoints[name];
    }

    // Helper method to make API calls with proper error handling
    async apiCall(endpoint, options = {}) {
        const url = this.getEndpoint(endpoint);
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            
            if (!response.ok) {
                throw new Error(`API call failed: ${response.status} ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API call to ${endpoint} failed:`, error);
            throw error;
        }
    }

    // Method to update the base URL after deployment
    updateBaseURL(newBaseURL) {
        this.baseURL = newBaseURL;
        console.log('API base URL updated to:', newBaseURL);
    }
}

// Global API instance
window.API = new APIConfig();

// Helper function to display user-friendly error messages
function showError(message, containerId = 'errorContainer') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                <strong>Error:</strong> ${message}
            </div>
        `;
    } else {
        alert('Error: ' + message);
    }
}

// Helper function to show loading states
function showLoading(containerId, show = true) {
    const container = document.getElementById(containerId);
    if (container) {
        if (show) {
            container.innerHTML = `
                <div class="flex justify-center items-center py-8">
                    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                    <span class="ml-3 text-gray-600">Loading...</span>
                </div>
            `;
        } else {
            container.innerHTML = '';
        }
    }
}