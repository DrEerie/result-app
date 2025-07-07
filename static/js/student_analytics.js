/**
 * Student Analytics Dashboard JavaScript
 * Handles chart rendering, tab switching, and report generation
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tabs
    initializeTabs();
    
    // Initialize charts if data is available
    renderCharts();
    
    // Initialize report generation
    initializeReportGeneration();
    
    // Initialize filters
    initializeFilters();
});

/**
 * Initialize tab switching functionality
 */
function initializeTabs() {
    const tabButtons = document.querySelectorAll('[data-tab-target]');
    const tabContents = document.querySelectorAll('[data-tab-content]');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const target = document.querySelector(button.dataset.tabTarget);
            
            // Hide all tab contents
            tabContents.forEach(content => {
                content.classList.add('hidden');
            });
            
            // Remove active class from all tab buttons
            tabButtons.forEach(btn => {
                btn.classList.remove('bg-blue-500', 'text-white');
                btn.classList.add('bg-gray-200', 'text-gray-700');
            });
            
            // Show the selected tab content
            target.classList.remove('hidden');
            
            // Add active class to the clicked button
            button.classList.remove('bg-gray-200', 'text-gray-700');
            button.classList.add('bg-blue-500', 'text-white');
        });
    });
}

/**
 * Render all charts for the student analytics dashboard
 */
function renderCharts() {
    // Performance Overview Chart
    renderPerformanceOverviewChart();
    
    // Subject Comparison Chart
    renderSubjectComparisonChart();
    
    // Performance Trends Chart
    renderPerformanceTrendsChart();
}

/**
 * Render the performance overview chart (radar chart)
 */
function renderPerformanceOverviewChart() {
    const overviewChartElement = document.getElementById('performanceOverviewChart');
    if (!overviewChartElement) return;
    
    // Get data from the data attribute
    const chartData = JSON.parse(overviewChartElement.dataset.chartData || '{}');
    if (!chartData.labels || !chartData.datasets) return;
    
    // Create radar chart
    new Chart(overviewChartElement, {
        type: 'radar',
        data: {
            labels: chartData.labels,
            datasets: chartData.datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: {
                        display: true
                    },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.raw + '%';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Render the subject comparison chart (bar chart)
 */
function renderSubjectComparisonChart() {
    const comparisonChartElement = document.getElementById('subjectComparisonChart');
    if (!comparisonChartElement) return;
    
    // Get data from the data attribute
    const chartData = JSON.parse(comparisonChartElement.dataset.chartData || '{}');
    if (!chartData.labels || !chartData.datasets) return;
    
    // Create bar chart
    new Chart(comparisonChartElement, {
        type: 'bar',
        data: {
            labels: chartData.labels,
            datasets: chartData.datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Marks (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Subjects'
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.raw + '%';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Render the performance trends chart (line chart)
 */
function renderPerformanceTrendsChart() {
    const trendsChartElement = document.getElementById('performanceTrendsChart');
    if (!trendsChartElement) return;
    
    // Get data from the data attribute
    const chartData = JSON.parse(trendsChartElement.dataset.chartData || '{}');
    if (!chartData.labels || !chartData.datasets) return;
    
    // Create line chart
    new Chart(trendsChartElement, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: chartData.datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Average Marks (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time Period'
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.raw + '%';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Initialize report generation functionality
 */
function initializeReportGeneration() {
    const generateReportBtn = document.getElementById('generateReportBtn');
    const reportStatusElement = document.getElementById('reportStatus');
    const downloadReportBtn = document.getElementById('downloadReportBtn');
    const reportModal = document.getElementById('reportModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    
    if (!generateReportBtn || !reportStatusElement || !downloadReportBtn || !reportModal || !closeModalBtn) return;
    
    // Open modal when generate report button is clicked
    generateReportBtn.addEventListener('click', function() {
        reportModal.classList.remove('hidden');
        reportStatusElement.textContent = 'Preparing to generate report...';
        reportStatusElement.className = 'text-blue-500';
        downloadReportBtn.classList.add('hidden');
        
        // Get student ID, academic year, and term from data attributes
        const studentId = this.dataset.studentId;
        const academicYear = this.dataset.academicYear;
        const term = this.dataset.term;
        
        if (!studentId || !academicYear || !term) {
            reportStatusElement.textContent = 'Error: Missing required parameters';
            reportStatusElement.className = 'text-red-500';
            return;
        }
        
        // Start report generation
        generateReport(studentId, academicYear, term);
    });
    
    // Close modal when close button is clicked
    closeModalBtn.addEventListener('click', function() {
        reportModal.classList.add('hidden');
    });
    
    // Close modal when clicking outside the modal content
    reportModal.addEventListener('click', function(event) {
        if (event.target === reportModal) {
            reportModal.classList.add('hidden');
        }
    });
}

/**
 * Generate a student analytics report
 * @param {string} studentId - The student ID
 * @param {string} academicYear - The academic year
 * @param {string} term - The term
 */
function generateReport(studentId, academicYear, term) {
    const reportStatusElement = document.getElementById('reportStatus');
    const downloadReportBtn = document.getElementById('downloadReportBtn');
    
    if (!reportStatusElement || !downloadReportBtn) return;
    
    // Update status
    reportStatusElement.textContent = 'Generating report...';
    reportStatusElement.className = 'text-blue-500';
    
    // Make API request to generate report
    fetch(`/api/student-analytics/generate-report?student_id=${studentId}&academic_year=${academicYear}&term=${term}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.task_id) {
            // Start polling for task status
            pollReportStatus(data.task_id, studentId);
        } else {
            reportStatusElement.textContent = 'Error: Failed to start report generation';
            reportStatusElement.className = 'text-red-500';
        }
    })
    .catch(error => {
        console.error('Error generating report:', error);
        reportStatusElement.textContent = 'Error: Failed to generate report';
        reportStatusElement.className = 'text-red-500';
    });
}

/**
 * Poll for report generation task status
 * @param {string} taskId - The task ID
 * @param {string} studentId - The student ID
 */
function pollReportStatus(taskId, studentId) {
    const reportStatusElement = document.getElementById('reportStatus');
    const downloadReportBtn = document.getElementById('downloadReportBtn');
    
    if (!reportStatusElement || !downloadReportBtn) return;
    
    // Poll for task status every 2 seconds
    const pollInterval = setInterval(function() {
        fetch(`/api/student-analytics/report-status?task_id=${taskId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'PENDING' || data.status === 'STARTED') {
                reportStatusElement.textContent = 'Report generation in progress...';
                reportStatusElement.className = 'text-blue-500';
            } else if (data.status === 'SUCCESS') {
                clearInterval(pollInterval);
                reportStatusElement.textContent = 'Report generated successfully!';
                reportStatusElement.className = 'text-green-500';
                
                // Show download button
                downloadReportBtn.classList.remove('hidden');
                downloadReportBtn.href = `/api/student-analytics/download-report?task_id=${taskId}&student_id=${studentId}`;
            } else if (data.status === 'FAILURE') {
                clearInterval(pollInterval);
                reportStatusElement.textContent = 'Error: Report generation failed';
                reportStatusElement.className = 'text-red-500';
            }
        })
        .catch(error => {
            console.error('Error checking report status:', error);
            clearInterval(pollInterval);
            reportStatusElement.textContent = 'Error: Failed to check report status';
            reportStatusElement.className = 'text-red-500';
        });
    }, 2000);
    
    // Stop polling after 2 minutes (120 seconds) to prevent infinite polling
    setTimeout(function() {
        clearInterval(pollInterval);
        if (reportStatusElement.textContent.includes('in progress')) {
            reportStatusElement.textContent = 'Report generation is taking longer than expected. Please check back later.';
            reportStatusElement.className = 'text-yellow-500';
        }
    }, 120000);
}

/**
 * Initialize filters functionality
 */
function initializeFilters() {
    const filterForm = document.getElementById('filterForm');
    if (!filterForm) return;
    
    filterForm.addEventListener('submit', function(event) {
        event.preventDefault();
        
        // Get form values
        const academicYear = document.getElementById('academicYear').value;
        const term = document.getElementById('term').value;
        
        // Get student ID from the form data attribute
        const studentId = filterForm.dataset.studentId;
        
        if (!studentId || !academicYear || !term) {
            alert('Please select all filter options');
            return;
        }
        
        // Redirect to the filtered URL
        window.location.href = `/dashboard/student-analytics/${studentId}?academic_year=${academicYear}&term=${term}`;
    });
}