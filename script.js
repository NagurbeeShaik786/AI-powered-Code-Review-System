class CodeReviewApp {
    constructor() {
        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        this.codeEditor = document.getElementById('code-editor');
        this.languageSelect = document.getElementById('language');
        this.analyzeBtn = document.getElementById('analyze-btn');
        this.loading = document.getElementById('loading');
        this.results = document.getElementById('results');
        this.errorMessage = document.getElementById('error-message');
        this.summary = document.getElementById('summary');
        this.bugsList = document.getElementById('bugs-list');
        this.warningsList = document.getElementById('warnings-list');
        this.suggestionsList = document.getElementById('suggestions-list');
    }

    bindEvents() {
        this.analyzeBtn.addEventListener('click', () => this.analyzeCode());
        
        // Add sample code based on language selection
        this.languageSelect.addEventListener('change', () => this.loadSampleCode());
        
        // Load initial sample code
        this.loadSampleCode();
    }

    loadSampleCode() {
        const language = this.languageSelect.value;
        const samples = {
            python: `# Sample Python code with issues
def calculate_average(numbers):
    total = 0
    for i in range(len(numbers)):
        total += numbers[i]
    return total / len(numbers)

# Missing error handling
result = calculate_average([1, 2, 3, 4, 5])
print("Average:", result)

# Unused variable
unused_var = "This variable is never used"

# Poor naming convention
def f(x, y):
    return x + y`,

            javascript: `// Sample JavaScript code with issues
function calculateAverage(numbers) {
    var total = 0;
    for (var i = 0; i < numbers.length; i++) {
        total += numbers[i]
    }
    return total / numbers.length;
}

// Using == instead of ===
if (result == "5") {
    console.log("Result is 5");
}

// Missing semicolon and using var
var result = calculateAverage([1, 2, 3, 4, 5])
console.log("Average: " + result);

// Function that could be arrow function
function add(a, b) {
    return a + b;
}`
        };

        this.codeEditor.value = samples[language] || '';
    }

    async analyzeCode() {
        const code = this.codeEditor.value.trim();
        const language = this.languageSelect.value;

        if (!code) {
            this.showError('Please enter some code to analyze.');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    code: code,
                    language: language
                })
            });

            const data = await response.json();

            if (data.success) {
                this.displayResults(data.results);
            } else {
                this.showError(data.error || 'An error occurred during analysis.');
            }
        } catch (error) {
            this.showError('Failed to connect to the analysis service. Please try again.');
            console.error('Analysis error:', error);
        }
    }

    showLoading() {
        this.hideAll();
        this.loading.style.display = 'flex';
        this.analyzeBtn.disabled = true;
        this.analyzeBtn.textContent = 'Analyzing...';
    }

    hideAll() {
        this.loading.style.display = 'none';
        this.results.style.display = 'none';
        this.errorMessage.style.display = 'none';
    }

    showError(message) {
        this.hideAll();
        this.errorMessage.textContent = message;
        this.errorMessage.style.display = 'block';
        this.resetButton();
    }

    resetButton() {
        this.analyzeBtn.disabled = false;
        this.analyzeBtn.textContent = '🔍 Analyze Code';
    }

    displayResults(results) {
        this.hideAll();
        this.results.style.display = 'block';
        this.resetButton();

        // Display summary
        this.summary.textContent = results.summary || 'Analysis completed';

        // Display issues
        this.displayIssues(this.bugsList, results.bugs, 'No bugs found! 🎉');
        this.displayIssues(this.warningsList, results.warnings, 'No warnings found! ✨');
        this.displayIssues(this.suggestionsList, results.suggestions, 'No suggestions at this time! 👍');
    }

    displayIssues(container, issues, emptyMessage) {
        container.innerHTML = '';

        if (!issues || issues.length === 0) {
            const emptyDiv = document.createElement('div');
            emptyDiv.className = 'empty-state';
            emptyDiv.textContent = emptyMessage;
            container.appendChild(emptyDiv);
            return;
        }

        issues.forEach(issue => {
            const issueDiv = document.createElement('div');
            issueDiv.className = 'issue-item';

            const locationDiv = document.createElement('div');
            locationDiv.className = 'issue-location';
            locationDiv.textContent = `Line ${issue.line}${issue.column ? `, Column ${issue.column}` : ''}`;

            const messageDiv = document.createElement('div');
            messageDiv.className = 'issue-message';
            messageDiv.textContent = issue.message;

            issueDiv.appendChild(locationDiv);
            issueDiv.appendChild(messageDiv);

            if (issue.type || issue.symbol || issue.code) {
                const typeDiv = document.createElement('div');
                typeDiv.className = 'issue-type';
                typeDiv.textContent = issue.type || issue.symbol || issue.code;
                issueDiv.appendChild(typeDiv);
            }

            container.appendChild(issueDiv);
        });
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CodeReviewApp();
});