/**
 * Popup script for LeetCoach Chrome extension.
 * Handles user interactions and preferences management.
 */

class LeetCoachPopup {
    constructor() {
        this.preferences = {};
        this.stats = {};
        this.currentTab = null;
        
        this.init();
    }

    async init() {
        console.log('Initializing LeetCoach popup...');
        
        // Load preferences and stats
        await this.loadPreferences();
        await this.loadStats();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Update UI
        this.updateUI();
        
        // Check status
        await this.checkStatus();
        
        console.log('LeetCoach popup initialized');
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Quick action buttons
        document.getElementById('activate-btn')?.addEventListener('click', () => this.activatePanel());
        document.getElementById('refresh-btn')?.addEventListener('click', () => this.refreshData());
        document.getElementById('get-hint-btn')?.addEventListener('click', () => this.getQuickHint());
        document.getElementById('analyze-btn')?.addEventListener('click', () => this.analyzeCode());

        // Preference controls
        document.getElementById('language-select')?.addEventListener('change', (e) => {
            this.preferences.preferredLanguage = e.target.value;
        });

        document.getElementById('explanation-style')?.addEventListener('change', (e) => {
            this.preferences.explanationStyle = e.target.value;
        });

        document.getElementById('include-examples')?.addEventListener('change', (e) => {
            this.preferences.includeExamples = e.target.checked;
        });

        document.getElementById('include-edge-cases')?.addEventListener('change', (e) => {
            this.preferences.includeEdgeCases = e.target.checked;
        });

        document.getElementById('auto-activate')?.addEventListener('change', (e) => {
            this.preferences.autoActivate = e.target.checked;
        });

        document.getElementById('api-endpoint')?.addEventListener('change', (e) => {
            this.preferences.apiEndpoint = e.target.value;
        });

        // Save preferences button
        document.getElementById('save-preferences')?.addEventListener('click', () => this.savePreferences());

        // Footer links
        document.getElementById('help-link')?.addEventListener('click', () => this.showHelp());
        document.getElementById('feedback-link')?.addEventListener('click', () => this.showFeedback());
        document.getElementById('settings-link')?.addEventListener('click', () => this.showSettings());
    }

    /**
     * Load user preferences
     */
    async loadPreferences() {
        try {
            const response = await this.sendMessage({ type: 'GET_PREFERENCES' });
            if (response.success) {
                this.preferences = response.preferences;
                console.log('Preferences loaded:', this.preferences);
            }
        } catch (error) {
            console.error('Failed to load preferences:', error);
            this.showError('Failed to load preferences');
        }
    }

    /**
     * Save user preferences
     */
    async savePreferences() {
        try {
            this.showLoading(true);
            
            const response = await this.sendMessage({
                type: 'UPDATE_PREFERENCES',
                preferences: this.preferences
            });
            
            if (response.success) {
                this.showSuccess('Preferences saved successfully!');
            } else {
                this.showError('Failed to save preferences');
            }
        } catch (error) {
            console.error('Failed to save preferences:', error);
            this.showError('Failed to save preferences');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Load usage statistics
     */
    async loadStats() {
        try {
            // Get user history to calculate stats
            const userId = this.preferences.userId || 'anonymous';
            const response = await this.sendMessage({
                type: 'API_REQUEST',
                endpoint: `/user/${userId}/history`,
                data: { limit: 100 },
                method: 'GET'
            });

            if (response.success && response.data) {
                this.calculateStats(response.data);
            }
        } catch (error) {
            console.error('Failed to load stats:', error);
            // Use default stats
            this.stats = {
                hintsCount: 0,
                problemsCount: 0,
                optimizationsCount: 0,
                solutionsCount: 0
            };
        }
    }

    /**
     * Calculate statistics from history
     */
    calculateStats(history) {
        this.stats = {
            hintsCount: history.filter(h => h.type === 'hint').length,
            problemsCount: new Set(history.map(h => h.problem_title)).size,
            optimizationsCount: history.filter(h => h.type === 'optimize').length,
            solutionsCount: history.filter(h => h.type === 'solution').length
        };
    }

    /**
     * Update UI with current data
     */
    updateUI() {
        // Update preferences form
        if (this.preferences.preferredLanguage) {
            const langSelect = document.getElementById('language-select');
            if (langSelect) langSelect.value = this.preferences.preferredLanguage;
        }

        if (this.preferences.explanationStyle) {
            const styleSelect = document.getElementById('explanation-style');
            if (styleSelect) styleSelect.value = this.preferences.explanationStyle;
        }

        const includeExamples = document.getElementById('include-examples');
        if (includeExamples) includeExamples.checked = this.preferences.includeExamples !== false;

        const includeEdgeCases = document.getElementById('include-edge-cases');
        if (includeEdgeCases) includeEdgeCases.checked = this.preferences.includeEdgeCases !== false;

        const autoActivate = document.getElementById('auto-activate');
        if (autoActivate) autoActivate.checked = this.preferences.autoActivate !== false;

        const apiEndpoint = document.getElementById('api-endpoint');
        if (apiEndpoint) apiEndpoint.value = this.preferences.apiEndpoint || 'http://localhost:8000/api';

        // Update stats
        document.getElementById('hints-count').textContent = this.stats.hintsCount || 0;
        document.getElementById('problems-count').textContent = this.stats.problemsCount || 0;
        document.getElementById('optimizations-count').textContent = this.stats.optimizationsCount || 0;
        document.getElementById('solutions-count').textContent = this.stats.solutionsCount || 0;

        // Update version
        const manifest = chrome.runtime.getManifest();
        document.getElementById('version').textContent = `v${manifest.version}`;
    }

    /**
     * Check extension and API status
     */
    async checkStatus() {
        try {
            // Get current tab
            const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
            this.currentTab = tabs[0];

            // Check if on LeetCode
            const isLeetCode = this.currentTab.url && 
                              (this.currentTab.url.includes('leetcode.com/problems/') ||
                               this.currentTab.url.includes('leetcode.com/contest/'));

            // Check extension health
            const healthResponse = await this.sendMessage({ type: 'HEALTH_CHECK' });

            let statusClass = 'status-section';
            let statusTitle = 'Extension Status';
            let statusDetails = '';

            if (healthResponse.success) {
                const health = healthResponse.data;
                
                if (isLeetCode) {
                    if (health.apiHealth === 'healthy') {
                        statusClass += '';
                        statusTitle = 'Ready';
                        statusDetails = 'Extension is active and API is healthy';
                    } else {
                        statusClass += ' warning';
                        statusTitle = 'API Issues';
                        statusDetails = `Extension active but API is ${health.apiHealth}`;
                    }
                } else {
                    statusClass += ' warning';
                    statusTitle = 'Not on LeetCode';
                    statusDetails = 'Navigate to a LeetCode problem to use the extension';
                }
            } else {
                statusClass += ' error';
                statusTitle = 'Extension Error';
                statusDetails = 'Extension is not working properly';
            }

            // Update status UI
            const statusSection = document.getElementById('status-section');
            statusSection.className = statusClass;
            document.querySelector('.status-title').textContent = statusTitle;
            document.getElementById('status-details').textContent = statusDetails;

            // Enable/disable action buttons based on status
            const actionButtons = document.querySelectorAll('.action-btn');
            actionButtons.forEach(btn => {
                if (btn.id !== 'save-preferences') {
                    btn.disabled = !isLeetCode || (healthResponse.success && healthResponse.data.apiHealth !== 'healthy');
                }
            });

        } catch (error) {
            console.error('Failed to check status:', error);
            
            const statusSection = document.getElementById('status-section');
            statusSection.className = 'status-section error';
            document.querySelector('.status-title').textContent = 'Status Check Failed';
            document.getElementById('status-details').textContent = 'Unable to determine extension status';
        }
    }

    /**
     * Quick action methods
     */
    async activatePanel() {
        try {
            if (!this.currentTab) return;

            await chrome.scripting.executeScript({
                target: { tabId: this.currentTab.id },
                function: () => {
                    if (window.leetCoachContentScript) {
                        window.leetCoachContentScript.activate();
                    }
                }
            });

            this.showSuccess('Panel activated!');
        } catch (error) {
            console.error('Failed to activate panel:', error);
            this.showError('Failed to activate panel');
        }
    }

    async refreshData() {
        try {
            this.showLoading(true);
            
            // Reload preferences and stats
            await this.loadPreferences();
            await this.loadStats();
            
            // Update UI
            this.updateUI();
            
            // Recheck status
            await this.checkStatus();
            
            this.showSuccess('Data refreshed!');
        } catch (error) {
            console.error('Failed to refresh data:', error);
            this.showError('Failed to refresh data');
        } finally {
            this.showLoading(false);
        }
    }

    async getQuickHint() {
        try {
            if (!this.currentTab) return;

            // Switch to content script and trigger hint
            await chrome.scripting.executeScript({
                target: { tabId: this.currentTab.id },
                function: () => {
                    if (window.leetCoachContentScript) {
                        window.leetCoachContentScript.activate();
                        // Switch to hints tab and trigger hint
                        setTimeout(() => {
                            const hintTab = document.querySelector('[data-tab="hints"]');
                            if (hintTab) hintTab.click();
                            
                            setTimeout(() => {
                                const hintBtn = document.getElementById('get-hint');
                                if (hintBtn) hintBtn.click();
                            }, 100);
                        }, 100);
                    }
                }
            });

            this.showSuccess('Getting hint...');
        } catch (error) {
            console.error('Failed to get hint:', error);
            this.showError('Failed to get hint');
        }
    }

    async analyzeCode() {
        try {
            if (!this.currentTab) return;

            // Switch to content script and trigger analysis
            await chrome.scripting.executeScript({
                target: { tabId: this.currentTab.id },
                function: () => {
                    if (window.leetCoachContentScript) {
                        window.leetCoachContentScript.activate();
                        // Switch to complexity tab and trigger analysis
                        setTimeout(() => {
                            const complexityTab = document.querySelector('[data-tab="complexity"]');
                            if (complexityTab) complexityTab.click();
                            
                            setTimeout(() => {
                                const analyzeBtn = document.getElementById('analyze-complexity');
                                if (analyzeBtn) analyzeBtn.click();
                            }, 100);
                        }, 100);
                    }
                }
            });

            this.showSuccess('Analyzing code...');
        } catch (error) {
            console.error('Failed to analyze code:', error);
            this.showError('Failed to analyze code');
        }
    }

    /**
     * Footer link handlers
     */
    showHelp() {
        chrome.tabs.create({
            url: 'https://github.com/leetcoach/extension/wiki/help'
        });
    }

    showFeedback() {
        chrome.tabs.create({
            url: 'https://github.com/leetcoach/extension/issues/new'
        });
    }

    showSettings() {
        // Focus on preferences section
        document.querySelector('.preferences-section').scrollIntoView({
            behavior: 'smooth'
        });
    }

    /**
     * UI utility methods
     */
    showLoading(show) {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = show ? 'block' : 'none';
        }
    }

    showError(message) {
        const errorEl = document.getElementById('error-message');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
            
            // Hide after 5 seconds
            setTimeout(() => {
                errorEl.style.display = 'none';
            }, 5000);
        }
    }

    showSuccess(message) {
        const successEl = document.getElementById('success-message');
        if (successEl) {
            successEl.textContent = message;
            successEl.style.display = 'block';
            
            // Hide after 3 seconds
            setTimeout(() => {
                successEl.style.display = 'none';
            }, 3000);
        }
    }

    /**
     * Send message to background script
     */
    async sendMessage(message) {
        return new Promise((resolve) => {
            chrome.runtime.sendMessage(message, (response) => {
                resolve(response || { success: false, error: 'No response' });
            });
        });
    }
}

// Initialize popup when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new LeetCoachPopup();
});
