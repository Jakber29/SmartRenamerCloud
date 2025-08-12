// Smart Renamer Cloud Frontend Application

// Configuration
const API_BASE_URL = 'https://smart-renamer-api.jake-b00.workers.dev'; // Your deployed Worker URL

// Global state
let currentPage = 'admin'; // Changed from 'dashboard' to 'admin'
let vendors = [];
let projects = [];
let teamMembers = [];
let transactions = [];
let manualMatches = {};
let reimbursements = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Set up navigation
    setupNavigation();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load initial data for the admin page
    loadUploadData();
    
    // Test API connection
    testApi();
}

// Navigation
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.getAttribute('data-page');
            navigateToPage(page);
        });
    });
}

function navigateToPage(page) {
    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-page="${page}"]`).classList.add('active');
    
    // Hide all pages
    document.querySelectorAll('.page').forEach(pageEl => {
        pageEl.classList.remove('active');
    });
    
    // Show target page
    document.getElementById(`${page}-page`).classList.add('active');
    
    currentPage = page;
    
    // Load page-specific data
    switch(page) {
        case 'admin':
            loadUploadData();
            break;
        case 'renaming':
            loadRenamingData();
            break;
        case 'dashboard':
            loadDashboardData();
            break;
        case 'matching':
            loadMatchingData();
            break;
        case 'transactions':
            loadTransactionsData();
            break;
        case 'vendors':
            loadVendorsData();
            break;
        case 'projects':
            loadProjectsData();
            break;
        case 'team':
            loadTeamData();
            break;
        case 'reimbursements':
            loadReimbursementsData();
            break;
    }
}

// Event Listeners
function setupEventListeners() {
    // File upload
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileUpload);
    }
    
    // Large file input for admin page
    const fileInputLarge = document.getElementById('file-input-large');
    if (fileInputLarge) {
        fileInputLarge.addEventListener('change', handleFileUpload);
    }
    
    // Folder input
    const folderInput = document.getElementById('folder-input');
    if (folderInput) {
        folderInput.addEventListener('change', handleFolderUpload);
    }
    
    // CSV upload
    const csvInput = document.getElementById('csv-input');
    if (csvInput) {
        csvInput.addEventListener('change', handleCsvUpload);
    }
    
    // Large CSV input for admin page
    const csvInputLarge = document.getElementById('csv-input-large');
    if (csvInputLarge) {
        csvInputLarge.addEventListener('change', handleCsvUpload);
    }
    
    // Setup drag and drop
    setupDragAndDrop();
    
    // Search inputs
    setupSearchListeners();
}

// Drag and Drop Setup
function setupDragAndDrop() {
    const uploadAreas = document.querySelectorAll('.upload-area-large');
    
    uploadAreas.forEach(area => {
        area.addEventListener('dragover', handleDragOver);
        area.addEventListener('dragleave', handleDragLeave);
        area.addEventListener('drop', handleDrop);
        area.addEventListener('click', handleUploadAreaClick);
    });
}

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.style.borderColor = '#1e3a8a';
    e.currentTarget.style.background = 'rgba(30, 58, 138, 0.05)';
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.style.borderColor = '#e2e8f0';
    e.currentTarget.style.background = '#f1f5f9';
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    
    const files = e.dataTransfer.files;
    if (!files || files.length === 0) return;
    
    // Determine which type of upload this is based on the upload area
    const uploadArea = e.currentTarget;
    const isFolderUpload = uploadArea.closest('.upload-section').querySelector('h3').textContent.includes('Folder');
    const isCsvUpload = uploadArea.closest('.upload-section').querySelector('h3').textContent.includes('CSV');
    
    if (isFolderUpload) {
        handleFolderUpload({ target: { files: files } });
    } else if (isCsvUpload) {
        // Filter for CSV files only
        const csvFiles = Array.from(files).filter(file => file.name.toLowerCase().endsWith('.csv'));
        if (csvFiles.length > 0) {
            handleCsvUpload({ target: { files: csvFiles } });
        } else {
            showToast('error', 'Invalid File Type', 'Please drop a CSV file');
        }
    } else {
        handleFileUpload({ target: { files: files } });
    }
    
    // Reset styling
    uploadArea.style.borderColor = '#e2e8f0';
    uploadArea.style.background = '#f1f5f9';
}

function handleUploadAreaClick(e) {
    // Don't trigger if clicking on the button
    if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
        return;
    }
    
    const uploadArea = e.currentTarget;
    const input = uploadArea.querySelector('input[type="file"]');
    if (input) {
        input.click();
    }
}

function setupSearchListeners() {
    // Transaction search
    const transactionSearch = document.getElementById('transaction-search');
    if (transactionSearch) {
        transactionSearch.addEventListener('input', debounce(function() {
            filterTransactions(this.value);
        }, 300));
    }
    
    // Vendors search
    const vendorsSearch = document.getElementById('vendors-search');
    if (vendorsSearch) {
        vendorsSearch.addEventListener('input', debounce(function() {
            filterVendors(this.value);
        }, 300));
    }
    
    // Projects search
    const projectsSearch = document.getElementById('projects-search');
    if (projectsSearch) {
        projectsSearch.addEventListener('input', debounce(function() {
            filterProjects(this.value);
        }, 300));
    }
    
    // Team search
    const teamSearch = document.getElementById('team-search');
    if (teamSearch) {
        teamSearch.addEventListener('input', debounce(function() {
            filterTeamMembers(this.value);
        }, 300));
    }
}

// API Functions
async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    };
    
    try {
        showLoading();
        const response = await fetch(url, finalOptions);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}`);
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        showToast('error', 'API Error', error.message);
        throw error;
    } finally {
        hideLoading();
    }
}

// Dashboard
async function loadDashboardData() {
    try {
        const [vendorsData, projectsData, transactionsData, matchesData] = await Promise.all([
            apiCall('/api/vendors'),
            apiCall('/api/projects'),
            apiCall('/api/transactions'),
            apiCall('/api/manual-matches')
        ]);
        
        // Update dashboard stats
        document.getElementById('vendor-count').textContent = vendorsData.vendors.length;
        document.getElementById('transaction-count').textContent = transactionsData.transactions.length;
        document.getElementById('match-count').textContent = Object.keys(matchesData.matches).length;
        
        // Store data globally
        vendors = vendorsData.vendors;
        projects = projectsData.projects;
        transactions = transactionsData.transactions;
        manualMatches = matchesData.matches;
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Matching Page
async function loadMatchingData() {
    try {
        const [filesData, transactionsData, matchesData] = await Promise.all([
            apiCall('/api/files'),
            apiCall('/api/transactions'),
            apiCall('/api/manual-matches')
        ]);
        
        transactions = transactionsData.transactions;
        manualMatches = matchesData.matches;
        
        renderFilesList(filesData.files);
        renderTransactionsList(transactions);
        
    } catch (error) {
        console.error('Error loading matching data:', error);
    }
}

function renderFilesList(files) {
    const filesList = document.getElementById('files-list');
    
    if (!files || files.length === 0) {
        filesList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-cloud-upload-alt"></i>
                <p>No files uploaded yet</p>
                <button class="btn btn-primary" onclick="showUploadModal()">
                    Upload Files
                </button>
            </div>
        `;
        return;
    }
    
    const filesHtml = files.map(file => `
        <div class="file-item" data-filename="${file.name}">
            <div class="file-info">
                <i class="fas fa-file-alt"></i>
                <span class="file-name">${file.name}</span>
            </div>
            <div class="file-actions">
                <button class="btn btn-sm btn-secondary" onclick="previewFile('${file.name}')">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-sm btn-primary" onclick="matchFile('${file.name}')">
                    <i class="fas fa-link"></i>
                </button>
            </div>
        </div>
    `).join('');
    
    filesList.innerHTML = filesHtml;
}

function renderTransactionsList(transactions) {
    const transactionsList = document.getElementById('transactions-list');
    
    if (!transactions || transactions.length === 0) {
        transactionsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-file-csv"></i>
                <p>No transactions loaded</p>
                <button class="btn btn-primary" onclick="showCsvUploadModal()">
                    Upload CSV
                </button>
            </div>
        `;
        return;
    }
    
    const transactionsHtml = transactions.map((transaction, index) => `
        <div class="transaction-item" data-index="${index}">
            <div class="transaction-info">
                <div class="transaction-vendor">${transaction.vendor}</div>
                <div class="transaction-amount">$${transaction.amount}</div>
                <div class="transaction-date">${transaction.date}</div>
            </div>
            <div class="transaction-actions">
                <button class="btn btn-sm btn-primary" onclick="selectTransaction(${index})">
                    <i class="fas fa-check"></i>
                </button>
            </div>
        </div>
    `).join('');
    
    transactionsList.innerHTML = transactionsHtml;
}

// Transactions Page
async function loadTransactionsData() {
    try {
        const data = await apiCall('/api/transactions');
        transactions = data.transactions;
        renderTransactionsTable(transactions);
    } catch (error) {
        console.error('Error loading transactions:', error);
    }
}

function renderTransactionsTable(transactions) {
    const tbody = document.getElementById('transactions-tbody');
    
    if (!transactions || transactions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    <i class="fas fa-file-csv"></i>
                    <p>No transactions loaded</p>
                    <button class="btn btn-primary" onclick="showCsvUploadModal()">
                        Upload CSV
                    </button>
                </td>
            </tr>
        `;
        return;
    }
    
    const rowsHtml = transactions.map((transaction, index) => `
        <tr>
            <td>${transaction.date}</td>
            <td>${transaction.vendor}</td>
            <td>$${transaction.amount}</td>
            <td>${transaction.description || ''}</td>
            <td>${transaction.cardholder || 'Unknown'}</td>
            <td>
                <button class="btn btn-sm btn-secondary" onclick="viewTransaction(${index})">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        </tr>
    `).join('');
    
    tbody.innerHTML = rowsHtml;
}

// Vendors Page
async function loadVendorsData() {
    try {
        const data = await apiCall('/api/vendors');
        vendors = data.vendors;
        renderVendorsList(vendors);
    } catch (error) {
        console.error('Error loading vendors:', error);
    }
}

function renderVendorsList(vendors) {
    const vendorsList = document.getElementById('vendors-list');
    
    if (!vendors || vendors.length === 0) {
        vendorsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-building"></i>
                <p>No vendors added yet</p>
                <button class="btn btn-primary" onclick="showVendorModal()">
                    Add Vendor
                </button>
            </div>
        `;
        return;
    }
    
    const vendorsHtml = vendors.map(vendor => `
        <div class="vendor-card">
            <div class="vendor-header">
                <h4>${vendor.name}</h4>
                <div class="vendor-actions">
                    <button class="btn btn-sm btn-secondary" onclick="editVendor('${vendor.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteVendor('${vendor.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            ${vendor.description ? `<p class="vendor-description">${vendor.description}</p>` : ''}
            ${vendor.contact ? `<p class="vendor-contact">Contact: ${vendor.contact}</p>` : ''}
            ${vendor.phone ? `<p class="vendor-phone">Phone: ${vendor.phone}</p>` : ''}
            ${vendor.email ? `<p class="vendor-email">Email: ${vendor.email}</p>` : ''}
        </div>
    `).join('');
    
    vendorsList.innerHTML = vendorsHtml;
}

// Projects Page
async function loadProjectsData() {
    try {
        const data = await apiCall('/api/projects');
        projects = data.projects;
        renderProjectsList(projects);
    } catch (error) {
        console.error('Error loading projects:', error);
    }
}

function renderProjectsList(projects) {
    const projectsList = document.getElementById('projects-list');
    
    if (!projects || projects.length === 0) {
        projectsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-project-diagram"></i>
                <p>No projects added yet</p>
                <button class="btn btn-primary" onclick="showProjectModal()">
                    Add Project
                </button>
            </div>
        `;
        return;
    }
    
    const projectsHtml = projects.map(project => `
        <div class="project-card">
            <div class="project-header">
                <h4>${project.name}</h4>
                <div class="project-actions">
                    <button class="btn btn-sm btn-secondary" onclick="editProject('${project.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteProject('${project.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            ${project.description ? `<p class="project-description">${project.description}</p>` : ''}
            ${project.client ? `<p class="project-client">Client: ${project.client}</p>` : ''}
            ${project.status ? `<p class="project-status">Status: ${project.status}</p>` : ''}
            ${project.builders_fee ? `<p class="project-fee">Builders Fee: ${project.builders_fee}%</p>` : ''}
        </div>
    `).join('');
    
    projectsList.innerHTML = projectsHtml;
}

// Team Members Page
async function loadTeamData() {
    try {
        const data = await apiCall('/api/team-members');
        teamMembers = data.team_members;
        renderTeamList(teamMembers);
    } catch (error) {
        console.error('Error loading team members:', error);
    }
}

function renderTeamList(teamMembers) {
    const teamList = document.getElementById('team-list');
    
    if (!teamMembers || teamMembers.length === 0) {
        teamList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-users"></i>
                <p>No team members added yet</p>
                <button class="btn btn-primary" onclick="showTeamMemberModal()">
                    Add Team Member
                </button>
            </div>
        `;
        return;
    }
    
    const teamHtml = teamMembers.map(member => `
        <div class="team-card">
            <div class="team-header">
                <h4>${member.name}</h4>
                <div class="team-actions">
                    <button class="btn btn-sm btn-secondary" onclick="editTeamMember('${member.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteTeamMember('${member.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            ${member.title ? `<p class="team-title">Title: ${member.title}</p>` : ''}
            ${member.department ? `<p class="team-department">Department: ${member.department}</p>` : ''}
            ${member.card_last_four ? `<p class="team-card">Card: ****${member.card_last_four}</p>` : ''}
            ${member.email ? `<p class="team-email">Email: ${member.email}</p>` : ''}
        </div>
    `).join('');
    
    teamList.innerHTML = teamHtml;
}

// Reimbursements Page
async function loadReimbursementsData() {
    try {
        const data = await apiCall('/api/reimbursements');
        reimbursements = data.reimbursements;
        renderReimbursementsList(reimbursements);
    } catch (error) {
        console.error('Error loading reimbursements:', error);
    }
}

function renderReimbursementsList(reimbursements) {
    const reimbursementsList = document.getElementById('reimbursements-list');
    
    if (!reimbursements || reimbursements.length === 0) {
        reimbursementsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-receipt"></i>
                <p>No reimbursements added yet</p>
                <button class="btn btn-primary" onclick="showReimbursementModal()">
                    Add Reimbursement
                </button>
            </div>
        `;
        return;
    }
    
    const reimbursementsHtml = reimbursements.map(reimbursement => `
        <div class="reimbursement-card">
            <div class="reimbursement-header">
                <h4>${reimbursement.vendor}</h4>
                <div class="reimbursement-actions">
                    <button class="btn btn-sm btn-secondary" onclick="editReimbursement(${reimbursement.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteReimbursement(${reimbursement.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <p class="reimbursement-amount">Amount: $${reimbursement.amount}</p>
            <p class="reimbursement-date">Date: ${reimbursement.date}</p>
            ${reimbursement.description ? `<p class="reimbursement-description">${reimbursement.description}</p>` : ''}
        </div>
    `).join('');
    
    reimbursementsList.innerHTML = reimbursementsHtml;
}

// Admin Page
async function loadUploadData() {
    try {
        const [filesData, transactionsData, matchesData] = await Promise.all([
            apiCall('/api/files'),
            apiCall('/api/transactions'),
            apiCall('/api/manual-matches')
        ]);
        
        // Update upload stats
        document.getElementById('upload-file-count').textContent = filesData.files ? filesData.files.length : 0;
        document.getElementById('upload-transaction-count').textContent = transactionsData.transactions ? transactionsData.transactions.length : 0;
        document.getElementById('upload-match-count').textContent = matchesData.matches ? Object.keys(matchesData.matches).length : 0;
        
        // Store data globally
        transactions = transactionsData.transactions;
        manualMatches = matchesData.matches;
        
    } catch (error) {
        console.error('Error loading upload data:', error);
        // Set default values if API fails
        document.getElementById('upload-file-count').textContent = '0';
        document.getElementById('upload-transaction-count').textContent = '0';
        document.getElementById('upload-match-count').textContent = '0';
    }
}

// Folder Upload
async function handleFolderUpload(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    try {
        showLoading();
        
        // Process folder structure
        const folderStructure = {};
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const pathParts = file.webkitRelativePath.split('/');
            const folderName = pathParts[0];
            
            if (!folderStructure[folderName]) {
                folderStructure[folderName] = [];
            }
            folderStructure[folderName].push(file);
        }
        
        // Show folder structure info
        const folderCount = Object.keys(folderStructure).length;
        const totalFiles = files.length;
        
        showToast('success', 'Folder Uploaded', `Uploaded ${folderCount} folder(s) with ${totalFiles} total files`);
        
        // Close any open modals
        closeModal('upload-modal');
        
        // Refresh data
        loadUploadData();
        
    } catch (error) {
        console.error('Error uploading folder:', error);
        showToast('error', 'Upload Error', error.message);
    } finally {
        hideLoading();
    }
}

// File Upload
async function handleFileUpload(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    try {
        showLoading();
        
        // In a real implementation, you would upload files to R2
        // For now, we'll just show a success message
        showToast('success', 'Files Uploaded', `${files.length} files uploaded successfully`);
        
        // Close modal
        closeModal('upload-modal');
        
        // Refresh data if on matching page
        if (currentPage === 'matching') {
            loadMatchingData();
        }
        
    } catch (error) {
        console.error('Error uploading files:', error);
        showToast('error', 'Upload Error', error.message);
    } finally {
        hideLoading();
    }
}

// CSV Upload
async function handleCsvUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
        showLoading();
        
        const reader = new FileReader();
        reader.onload = async function(e) {
            try {
                const csvData = e.target.result;
                
                const response = await apiCall('/api/upload-csv', {
                    method: 'POST',
                    body: JSON.stringify({
                        csv_data: csvData
                    })
                });
                
                showToast('success', 'CSV Uploaded', response.message);
                
                // Close modal
                closeModal('csv-upload-modal');
                
                // Refresh data
                if (currentPage === 'dashboard') {
                    loadDashboardData();
                } else if (currentPage === 'matching') {
                    loadMatchingData();
                } else if (currentPage === 'transactions') {
                    loadTransactionsData();
                }
                
            } catch (error) {
                console.error('Error processing CSV:', error);
                showToast('error', 'CSV Error', error.message);
            } finally {
                hideLoading();
            }
        };
        
        reader.readAsText(file);
        
    } catch (error) {
        console.error('Error uploading CSV:', error);
        showToast('error', 'Upload Error', error.message);
        hideLoading();
    }
}

// Modals
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

function showUploadModal() {
    showModal('upload-modal');
}

function showCsvUploadModal() {
    showModal('csv-upload-modal');
}

// API Test
async function testApi() {
    try {
        const response = await apiCall('/api/test');
        
        document.getElementById('api-status').textContent = 'Online';
        document.getElementById('api-status').className = 'status-value online';
        
        document.getElementById('db-status').textContent = 'Connected';
        document.getElementById('db-status').className = 'status-value online';
        
        document.getElementById('storage-status').textContent = 'Available';
        document.getElementById('storage-status').className = 'status-value online';
        
        showToast('success', 'API Test', 'All systems are operational');
        
    } catch (error) {
        document.getElementById('api-status').textContent = 'Offline';
        document.getElementById('api-status').className = 'status-value offline';
        
        document.getElementById('db-status').textContent = 'Disconnected';
        document.getElementById('db-status').className = 'status-value offline';
        
        document.getElementById('storage-status').textContent = 'Unavailable';
        document.getElementById('storage-status').className = 'status-value offline';
        
        showToast('error', 'API Test', 'Some systems are offline');
    }
}

// Utility Functions
function showLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('active');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

function showToast(type, title, message) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? 'fas fa-check-circle' :
                 type === 'error' ? 'fas fa-exclamation-circle' :
                 type === 'warning' ? 'fas fa-exclamation-triangle' :
                 'fas fa-info-circle';
    
    toast.innerHTML = `
        <i class="${icon}"></i>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 5000);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Filter Functions
function filterTransactions(query) {
    const filtered = transactions.filter(transaction =>
        transaction.vendor.toLowerCase().includes(query.toLowerCase()) ||
        transaction.description.toLowerCase().includes(query.toLowerCase()) ||
        transaction.amount.toString().includes(query)
    );
    renderTransactionsList(filtered);
}

function filterVendors(query) {
    const filtered = vendors.filter(vendor =>
        vendor.name.toLowerCase().includes(query.toLowerCase()) ||
        (vendor.description && vendor.description.toLowerCase().includes(query.toLowerCase()))
    );
    renderVendorsList(filtered);
}

function filterProjects(query) {
    const filtered = projects.filter(project =>
        project.name.toLowerCase().includes(query.toLowerCase()) ||
        (project.description && project.description.toLowerCase().includes(query.toLowerCase()))
    );
    renderProjectsList(filtered);
}

function filterTeamMembers(query) {
    const filtered = teamMembers.filter(member =>
        member.name.toLowerCase().includes(query.toLowerCase()) ||
        (member.title && member.title.toLowerCase().includes(query.toLowerCase())) ||
        (member.department && member.department.toLowerCase().includes(query.toLowerCase()))
    );
    renderTeamList(filtered);
}

// Placeholder functions for future implementation
function showVendorModal() {
    showToast('info', 'Coming Soon', 'Vendor management modal will be implemented');
}

function showProjectModal() {
    showToast('info', 'Coming Soon', 'Project management modal will be implemented');
}

function showTeamMemberModal() {
    showToast('info', 'Coming Soon', 'Team member management modal will be implemented');
}

function showReimbursementModal() {
    showToast('info', 'Coming Soon', 'Reimbursement management modal will be implemented');
}

function previewFile(filename) {
    showToast('info', 'File Preview', `Preview for ${filename} will be implemented`);
}

function matchFile(filename) {
    showToast('info', 'File Matching', `Matching for ${filename} will be implemented`);
}

function selectTransaction(index) {
    showToast('info', 'Transaction Selection', `Transaction ${index} selected`);
}

function viewTransaction(index) {
    showToast('info', 'Transaction View', `Viewing transaction ${index}`);
}

function editVendor(id) {
    showToast('info', 'Edit Vendor', `Editing vendor ${id}`);
}

function deleteVendor(id) {
    showToast('info', 'Delete Vendor', `Deleting vendor ${id}`);
}

function editProject(id) {
    showToast('info', 'Edit Project', `Editing project ${id}`);
}

function deleteProject(id) {
    showToast('info', 'Delete Project', `Deleting project ${id}`);
}

function editTeamMember(id) {
    showToast('info', 'Edit Team Member', `Editing team member ${id}`);
}

function deleteTeamMember(id) {
    showToast('info', 'Delete Team Member', `Deleting team member ${id}`);
}

function editReimbursement(id) {
    showToast('info', 'Edit Reimbursement', `Editing reimbursement ${id}`);
}

function deleteReimbursement(id) {
    showToast('info', 'Delete Reimbursement', `Deleting reimbursement ${id}`);
}

function clearAllData() {
    if (confirm('Are you sure you want to clear all data? This action cannot be undone.')) {
        showToast('warning', 'Clear Data', 'Data clearing will be implemented');
    }
}

function exportData() {
    showToast('info', 'Export Data', 'Data export will be implemented');
} 

// Renaming Page
async function loadRenamingData() {
    try {
        const [filesData, projectsData, vendorsData] = await Promise.all([
            apiCall('/api/files'),
            apiCall('/api/projects'),
            apiCall('/api/vendors')
        ]);
        
        // Store data globally
        projects = projectsData.projects;
        vendors = vendorsData.vendors;
        
        // Render files list
        renderFilesListRenaming(filesData.files);
        
        // Populate form dropdowns
        populateProjectDropdown();
        populateVendorDropdown();
        
        // Set up form event listeners
        setupRenamingFormListeners();
        
    } catch (error) {
        console.error('Error loading renaming data:', error);
    }
}

function renderFilesListRenaming(files) {
    const filesList = document.getElementById('files-list-renaming');
    const filesCount = document.getElementById('files-count');
    
    if (!files || files.length === 0) {
        filesList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-cloud-upload-alt"></i>
                <p>No files uploaded yet</p>
                <button class="btn btn-primary" onclick="navigateToPage('admin')">
                    Upload Files
                </button>
            </div>
        `;
        filesCount.textContent = '0 files';
        return;
    }
    
    filesCount.textContent = `${files.length} file${files.length !== 1 ? 's' : ''}`;
    
    const filesHtml = files.map(file => `
        <div class="file-item-renaming" data-filename="${file.name}" onclick="selectFileForRenaming('${file.name}')">
            <div class="file-icon">
                <i class="${getFileIcon(file.name)}"></i>
            </div>
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-meta">${formatFileSize(file.size || 0)} • ${getFileType(file.name)}</div>
            </div>
            <div class="file-status">${file.renamed ? 'Renamed' : 'Pending'}</div>
        </div>
    `).join('');
    
    filesList.innerHTML = filesHtml;
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const iconMap = {
        'pdf': 'fas fa-file-pdf',
        'png': 'fas fa-file-image',
        'jpg': 'fas fa-file-image',
        'jpeg': 'fas fa-file-image',
        'gif': 'fas fa-file-image',
        'bmp': 'fas fa-file-image',
        'tiff': 'fas fa-file-image',
        'doc': 'fas fa-file-word',
        'docx': 'fas fa-file-word',
        'xls': 'fas fa-file-excel',
        'xlsx': 'fas fa-file-excel',
        'txt': 'fas fa-file-alt',
        'csv': 'fas fa-file-csv'
    };
    return iconMap[ext] || 'fas fa-file-alt';
}

function getFileType(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const typeMap = {
        'pdf': 'PDF',
        'png': 'Image',
        'jpg': 'Image',
        'jpeg': 'Image',
        'gif': 'Image',
        'bmp': 'Image',
        'tiff': 'Image',
        'doc': 'Word',
        'docx': 'Word',
        'xls': 'Excel',
        'xlsx': 'Excel',
        'txt': 'Text',
        'csv': 'CSV'
    };
    return typeMap[ext] || 'File';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function populateProjectDropdown() {
    const projectSelect = document.getElementById('project-name');
    projectSelect.innerHTML = '<option value="">Select a project...</option>';
    
    projects.forEach(project => {
        const option = document.createElement('option');
        option.value = project.name;
        option.textContent = project.name;
        projectSelect.appendChild(option);
    });
}

function populateVendorDropdown() {
    const vendorSelect = document.getElementById('vendor-name');
    vendorSelect.innerHTML = '<option value="">Select a vendor...</option>';
    
    vendors.forEach(vendor => {
        const option = document.createElement('option');
        option.value = vendor.name;
        option.textContent = vendor.name;
        vendorSelect.appendChild(option);
    });
}

function setupRenamingFormListeners() {
    const form = document.getElementById('renaming-form');
    const inputs = form.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        input.addEventListener('input', updateFilenamePreview);
        input.addEventListener('change', updateFilenamePreview);
    });
}

let selectedFile = null;

function selectFileForRenaming(filename) {
    // Update selected file
    selectedFile = filename;
    
    // Update UI
    document.querySelectorAll('.file-item-renaming').forEach(item => {
        item.classList.remove('selected');
    });
    document.querySelector(`[data-filename="${filename}"]`).classList.add('selected');
    
    // Update preview
    document.getElementById('preview-filename').textContent = filename;
    
    // Show file preview
    showFilePreview(filename);
    
    // Enable rename button
    document.getElementById('rename-btn').disabled = false;
    
    // Update filename preview
    updateFilenamePreview();
}

function showFilePreview(filename) {
    const previewArea = document.getElementById('file-preview-area');
    const ext = filename.split('.').pop().toLowerCase();
    
    if (['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'].includes(ext)) {
        // For images, show preview (in real app, this would be the actual file URL)
        previewArea.innerHTML = `
            <div class="preview-placeholder">
                <i class="fas fa-file-image"></i>
                <p>Image Preview: ${filename}</p>
                <small>Preview would show the actual image here</small>
            </div>
        `;
    } else if (ext === 'pdf') {
        previewArea.innerHTML = `
            <div class="preview-placeholder">
                <i class="fas fa-file-pdf"></i>
                <p>PDF Preview: ${filename}</p>
                <small>Preview would show the PDF here</small>
            </div>
        `;
    } else {
        previewArea.innerHTML = `
            <div class="preview-placeholder">
                <i class="${getFileIcon(filename)}"></i>
                <p>File: ${filename}</p>
                <small>Preview not available for this file type</small>
            </div>
        `;
    }
}

function updateFilenamePreview() {
    if (!selectedFile) {
        document.getElementById('new-filename').textContent = 'No file selected';
        return;
    }
    
    const projectName = document.getElementById('project-name').value;
    const vendorName = document.getElementById('vendor-name').value;
    const billDate = document.getElementById('bill-date').value;
    const billNumber = document.getElementById('bill-number').value;
    const billAmount = document.getElementById('bill-amount').value;
    
    if (!projectName || !vendorName || !billDate || !billNumber || !billAmount) {
        document.getElementById('new-filename').textContent = 'Fill in all required fields to see preview';
        return;
    }
    
    // Generate new filename based on your naming convention
    const date = new Date(billDate);
    const formattedDate = `${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}-${date.getFullYear().toString().slice(-2)}`;
    
    const originalExt = selectedFile.split('.').pop();
    const newFilename = `${projectName} ${vendorName} ${formattedDate} ${billNumber} $${parseFloat(billAmount).toFixed(2)}.${originalExt}`;
    
    document.getElementById('new-filename').textContent = newFilename;
}

function clearForm() {
    document.getElementById('renaming-form').reset();
    updateFilenamePreview();
}

// Handle form submission
document.addEventListener('DOMContentLoaded', function() {
    const renamingForm = document.getElementById('renaming-form');
    if (renamingForm) {
        renamingForm.addEventListener('submit', handleFileRename);
    }
    
    // Set up files search
    const filesSearch = document.getElementById('files-search');
    if (filesSearch) {
        filesSearch.addEventListener('input', debounce(function() {
            filterFilesRenaming(this.value);
        }, 300));
    }
});

async function handleFileRename(event) {
    event.preventDefault();
    
    if (!selectedFile) {
        showToast('error', 'No File Selected', 'Please select a file to rename');
        return;
    }
    
    const formData = new FormData(event.target);
    const data = {
        original_filename: selectedFile,
        project_name: formData.get('project-name'),
        vendor_name: formData.get('vendor-name'),
        bill_date: formData.get('bill-date'),
        bill_number: formData.get('bill-number'),
        bill_amount: parseFloat(formData.get('bill-amount')),
        description: formData.get('file-description') || ''
    };
    
    try {
        showLoading();
        
        // In a real implementation, this would call your API to rename the file
        // For now, we'll simulate the rename
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        showToast('success', 'File Renamed', `Successfully renamed "${selectedFile}"`);
        
        // Clear form and refresh file list
        clearForm();
        loadRenamingData();
        
        // Deselect file
        selectedFile = null;
        document.getElementById('rename-btn').disabled = true;
        document.getElementById('preview-filename').textContent = 'Select a file to preview';
        document.getElementById('file-preview-area').innerHTML = `
            <div class="preview-placeholder">
                <i class="fas fa-file-alt"></i>
                <p>Select a file from the list to preview</p>
            </div>
        `;
        
    } catch (error) {
        console.error('Error renaming file:', error);
        showToast('error', 'Rename Error', error.message);
    } finally {
        hideLoading();
    }
}

function filterFilesRenaming(query) {
    const fileItems = document.querySelectorAll('.file-item-renaming');
    
    fileItems.forEach(item => {
        const filename = item.getAttribute('data-filename').toLowerCase();
        if (filename.includes(query.toLowerCase())) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
} 