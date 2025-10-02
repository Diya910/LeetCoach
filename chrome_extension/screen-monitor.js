/**
 * Screen Monitoring Service for LeetCoach
 * Monitors user behavior and detects when assistance is needed
 */

class ScreenMonitor {
    constructor() {
        this.isMonitoring = false;
        this.assistanceTimer = null;
        this.userPreferences = null;
        this.lastActivity = Date.now();
        this.stuckDetection = {
            noCodeChange: 0,
            noScrollChange: 0,
            noClickChange: 0,
            errorCount: 0
        };
        // Screen capture removed: rely on DOM-based monitoring to avoid permissions and heavy payloads
        this.leetcodeDetector = new LeetCodeDetector();
        
        this.init();
    }

    async init() {
        console.log('Initializing Screen Monitor...');
        
        // Load user preferences
        await this.loadPreferences();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Start monitoring if auto-activate is enabled
        if (this.userPreferences?.autoActivate) {
            this.startMonitoring();
        }
        
        console.log('Screen Monitor initialized');
    }

    async loadPreferences() {
        // Prefer local storage (used by background), fallback to sync
        const getLocal = () => new Promise((resolve) => chrome.storage.local.get('leetcoach_preferences', (r) => resolve(r.leetcoach_preferences || {})));
        const getSync = () => new Promise((resolve) => chrome.storage.sync.get(['leetcoach_preferences'], (r) => resolve(r.leetcoach_preferences || {})));
        const [localPrefs, syncPrefs] = await Promise.all([getLocal(), getSync()]);
        const merged = { ...syncPrefs, ...localPrefs };
        this.userPreferences = {
            assistanceDelay: 30, // default seconds
            preferredLanguage: 'python',
            explanationStyle: 'detailed',
            autoActivate: true,
            autoAssistEnabled: true,
            includeExamples: true,
            includeEdgeCases: true,
            ...merged
        };
    }

    setupEventListeners() {
        // Monitor user activity
        document.addEventListener('mousemove', () => this.updateActivity());
        document.addEventListener('keydown', () => this.updateActivity());
        document.addEventListener('click', () => this.updateActivity());
        document.addEventListener('scroll', () => this.updateActivity());
        
        // Monitor code editor changes
        this.setupCodeEditorMonitoring();
        
        // Monitor page visibility
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseMonitoring();
            } else {
                this.resumeMonitoring();
            }
        });
    }

    setupCodeEditorMonitoring() {
        // Monitor Monaco editor changes
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' || mutation.type === 'characterData') {
                    this.onCodeChange();
                }
            });
        });

        // Observe editor container
        const editorContainer = document.querySelector('.monaco-editor') || 
                               document.querySelector('.CodeMirror') ||
                               document.querySelector('[data-mode-id]');
        
        if (editorContainer) {
            observer.observe(editorContainer, {
                childList: true,
                subtree: true,
                characterData: true
            });
        }
    }

    updateActivity() {
        this.lastActivity = Date.now();
        this.resetStuckDetection();
    }

    onCodeChange() {
        this.lastActivity = Date.now();
        this.stuckDetection.noCodeChange = 0;
        this.stuckDetection.errorCount = 0;
    }

    resetStuckDetection() {
        this.stuckDetection = {
            noCodeChange: 0,
            noScrollChange: 0,
            noClickChange: 0,
            errorCount: 0
        };
    }

    startMonitoring() {
        if (this.isMonitoring) return;
        
        console.log('Starting screen monitoring...');
        this.isMonitoring = true;
        this.lastActivity = Date.now();
        
        // Start assistance timer
        this.startAssistanceTimer();
        
        // Start stuck detection
        this.startStuckDetection();
        
        // DOM-based monitoring only; no screen capture
        // Optionally, schedule lightweight DOM analysis tick
        this.startDomAnalysis();

        // Start test result detection
        this.startTestResultDetection();
    }

    stopMonitoring() {
        if (!this.isMonitoring) return;
        
        console.log('Stopping screen monitoring...');
        this.isMonitoring = false;
        
        if (this.assistanceTimer) {
            clearInterval(this.assistanceTimer);
            this.assistanceTimer = null;
        }
    }

    pauseMonitoring() {
        if (this.assistanceTimer) {
            clearInterval(this.assistanceTimer);
        }
    }

    resumeMonitoring() {
        if (this.isMonitoring && !this.assistanceTimer) {
            this.startAssistanceTimer();
        }
    }

    startAssistanceTimer() {
        const delayMs = Math.max(5, (this.userPreferences?.assistanceDelay || 30)) * 1000;
        
        this.assistanceTimer = setInterval(() => {
            this.checkIfAssistanceNeeded();
        }, delayMs);
    }

    startStuckDetection() {
        setInterval(() => {
            if (!this.isMonitoring) return;
            
            const now = Date.now();
            const timeSinceActivity = now - this.lastActivity;
            
            // Update stuck detection metrics
            if (timeSinceActivity > 30000) { // 30 seconds
                this.stuckDetection.noCodeChange++;
                this.stuckDetection.noScrollChange++;
                this.stuckDetection.noClickChange++;
            }
            
            // Check if user is stuck
            if (this.isUserStuck()) {
                this.triggerAssistance('stuck_detection');
            }
        }, 5000); // Check every 5 seconds
    }

    isUserStuck() {
        const { noCodeChange, noScrollChange, noClickChange, errorCount } = this.stuckDetection;
        
        // User is stuck if:
        // - No code changes for 2+ minutes
        // - No activity for 1+ minute
        // - Multiple errors detected
        return noCodeChange >= 6 || // 6 * 30s = 3 minutes (increased threshold)
               noScrollChange >= 4 || // 4 * 30s = 2 minutes (increased threshold)
               errorCount >= 5; // Increased error threshold
    }

    startDomAnalysis() {
        const tick = async () => {
            if (!this.isMonitoring) return;
            try {
                const context = await this.getCurrentContext();
                const needs = await this.analyzeAssistanceNeed(context);
                if (needs) {
                    this.triggerAssistance('dom_analysis', context);
                }
            } catch (e) {
                console.warn('DOM analysis tick error:', e);
            } finally {
                setTimeout(tick, this.isUserStuck() ? 60000 : 120000);
            }
        };
        setTimeout(tick, 30000);
    }

    // Screen capture removed

    async analyzeProblemContext(screenData) {
        if (!screenData) return;
        
        try {
            // Send screen data to backend for analysis
            const response = await this.sendScreenForAnalysis(screenData);
            
            if (response.success) {
                this.handleProblemAnalysis(response.data);
            }
        } catch (error) {
            console.error('Problem analysis error:', error);
        }
    }

    // Screen analysis endpoint not used anymore; purely DOM-based

    // Problem analysis via image removed

    async checkIfAssistanceNeeded() {
        if (!this.isMonitoring) return;
        
        try {
            // Get current page context
            const context = await this.getCurrentContext();
            
            // Analyze if assistance is needed
            const needsAssistance = await this.analyzeAssistanceNeed(context);
            
            if (needsAssistance) {
                this.triggerAssistance('timer_based', context);
            }
        } catch (error) {
            console.error('Assistance check error:', error);
        }
    }

    async getCurrentContext() {
        return {
            url: window.location.href,
            title: document.title,
            timeOnPage: Date.now() - this.lastActivity,
            userCode: this.extractUserCode(),
            problemData: this.extractProblemData(),
            stuckMetrics: { ...this.stuckDetection },
            timestamp: Date.now()
        };
    }

    extractUserCode() {
        try {
            // Try to get code from Monaco editor
            if (window.monaco && window.monaco.editor) {
                const editors = window.monaco.editor.getEditors();
                if (editors.length > 0) {
                    return {
                        code: editors[0].getValue(),
                        language: this.detectLanguage(),
                        isWorking: this.checkCodeValidity(editors[0].getValue())
                    };
                }
            }
            
            // Fallback: try to get from DOM
            const editorElement = document.querySelector('.monaco-editor textarea') ||
                                document.querySelector('.CodeMirror-code');
            
            if (editorElement) {
                return {
                    code: editorElement.value || editorElement.textContent,
                    language: this.detectLanguage(),
                    isWorking: false
                };
            }
            
            return null;
        } catch (error) {
            console.error('Code extraction error:', error);
            return null;
        }
    }

    extractProblemData() {
        try {
            const title = document.querySelector('h1[data-cy="question-title"]')?.textContent?.trim() || '';
            const difficulty = document.querySelector('[diff]')?.textContent?.trim() || 'Unknown';
            const description = document.querySelector('[data-track-load="description_content"]')?.textContent?.trim() || '';
            
            return {
                title,
                difficulty,
                description: description.substring(0, 500),
                url: window.location.href
            };
        } catch (error) {
            console.error('Problem data extraction error:', error);
            return null;
        }
    }

    detectLanguage() {
        try {
            const langElement = document.querySelector('[data-cy="lang-select"]') ||
                              document.querySelector('.ant-select-selection-item');
            
            if (langElement) {
                const langText = langElement.textContent.toLowerCase();
                const langMap = {
                    'python': 'python',
                    'python3': 'python',
                    'javascript': 'javascript',
                    'java': 'java',
                    'c++': 'cpp',
                    'c': 'c',
                    'c#': 'csharp',
                    'go': 'go',
                    'rust': 'rust',
                    'typescript': 'typescript'
                };
                
                for (const [key, value] of Object.entries(langMap)) {
                    if (langText.includes(key)) {
                        return value;
                    }
                }
            }
            
            return 'python'; // Default
        } catch (error) {
            console.error('Language detection error:', error);
            return 'python';
        }
    }

    checkCodeValidity(code) {
        // Basic code validity check
        if (!code || code.trim().length < 10) return false;
        
        // Check for common syntax errors
        const hasSyntaxErrors = this.detectSyntaxErrors(code);
        return !hasSyntaxErrors;
    }

    detectSyntaxErrors(code) {
        // Basic syntax error detection
        const commonErrors = [
            /[{}]\s*$/, // Unclosed braces
            /\(\s*$/, // Unclosed parentheses
            /\[\s*$/, // Unclosed brackets
            /['"]\s*$/, // Unclosed strings
            /def\s+\w+\s*\([^)]*$/, // Incomplete function definition
            /if\s+[^:]*$/, // Incomplete if statement
            /for\s+[^:]*$/, // Incomplete for loop
            /while\s+[^:]*$/ // Incomplete while loop
        ];
        
        return commonErrors.some(pattern => pattern.test(code));
    }

    async analyzeAssistanceNeed(context) {
        try {
            // Send context to backend for AI analysis
            const response = await this.sendContextForAnalysis(context);
            return response?.data?.needs_assistance || false;
        } catch (error) {
            console.error('Assistance analysis error:', error);
            return false;
        }
    }

    async sendContextForAnalysis(context) {
        return new Promise((resolve) => {
            chrome.runtime.sendMessage({
                type: 'ANALYZE_ASSISTANCE_NEED',
                data: context
            }, (response) => {
                resolve(response || { success: false, data: { needs_assistance: false } });
            });
        });
    }

    triggerAssistance(triggerType, context = null) {
        console.log(`Triggering assistance: ${triggerType}`, context);
        
        // Show assistance notification
        this.showAssistanceNotification(triggerType, context);
        
        // Auto assist (e.g., auto-hint) if enabled
        if (this.userPreferences?.autoAssistEnabled) {
            // Try immediately; if chat not ready, retry shortly
            const tryAssist = () => {
                if (window.leetcoachChat && typeof window.leetcoachChat.getHint === 'function') {
                    window.leetcoachChat.getHint();
                    if (window.leetcoachChat.show) {
                        window.leetcoachChat.show();
                        window.leetcoachChat.switchTab && window.leetcoachChat.switchTab('hints');
                    }
                } else {
                    setTimeout(tryAssist, 1000);
                }
            };
            tryAssist();
        }

        // Update stuck detection
        this.stuckDetection.errorCount++;
        
        // Reset timer to avoid spam
        this.resetAssistanceTimer();
    }

    showAssistanceNotification(triggerType, context) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'leetcoach-assistance-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">🤖</div>
                <div class="notification-text">
                    <div class="notification-title">Need Help?</div>
                    <div class="notification-message">I noticed you might be stuck. Click to get assistance!</div>
                </div>
                <div class="notification-actions">
                    <button class="notification-btn primary" id="leetcoach-get-help-btn">
                        Get Help
                    </button>
                    <button class="notification-btn secondary" id="leetcoach-dismiss-help-btn">
                        Dismiss
                    </button>
                </div>
            </div>
        `;
        
        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            z-index: 10000;
            max-width: 350px;
            animation: slideIn 0.3s ease-out;
        `;
        
        // Add to page
        document.body.appendChild(notification);

        // Wire events (avoid inline handlers to bypass page CSP)
        const helpBtn = notification.querySelector('#leetcoach-get-help-btn');
        const dismissBtn = notification.querySelector('#leetcoach-dismiss-help-btn');
        if (helpBtn) {
            helpBtn.addEventListener('click', async () => {
                // Show chat and switch to hints
                const tryOpen = () => {
                    if (window.leetcoachChat) {
                        window.leetcoachChat.show();
                        window.leetcoachChat.switchTab && window.leetcoachChat.switchTab('hints');
                        // Optionally auto-get hint when opened
                        if (this.userPreferences?.autoAssistEnabled && typeof window.leetcoachChat.getHint === 'function') {
                            window.leetcoachChat.getHint();
                        }
                        notification.remove();
                    } else {
                        setTimeout(tryOpen, 300);
                    }
                };
                tryOpen();
            });
        }
        if (dismissBtn) {
            dismissBtn.addEventListener('click', () => {
                notification.remove();
            });
        }
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 10000);
    }

    resetAssistanceTimer() {
        if (this.assistanceTimer) {
            clearInterval(this.assistanceTimer);
            this.startAssistanceTimer();
        }
    }

    updatePreferences(newPreferences) {
        this.userPreferences = { ...this.userPreferences, ...newPreferences };
        
        // Save to storage
        chrome.storage.sync.set({ leetcoach_preferences: this.userPreferences });
        chrome.storage.local.set({ leetcoach_preferences: this.userPreferences });
        
        // Restart timer with new delay
        if (this.assistanceTimer) {
            clearInterval(this.assistanceTimer);
            this.startAssistanceTimer();
        }
    }

    startTestResultDetection() {
        // Poll for LeetCode test result indicators
        const check = () => {
            if (!this.isMonitoring) return;
            const text = document.body?.innerText || '';
            if (/wrong answer|time limit exceeded|runtime error|memory limit/i.test(text)) {
                this.triggerAssistance('test_failed');
            } else if (/accepted\s*$/i.test(text) || /All test cases passed/i.test(text)) {
                // Offer to show more solutions/approaches
                if (window.leetcoachChat) {
                    window.leetcoachChat.show();
                    window.leetcoachChat.switchTab && window.leetcoachChat.switchTab('solution');
                    window.leetcoachChat.showNotification && window.leetcoachChat.showNotification('Congrats! Want to see other solutions or optimizations?', 'info');
                }
                this.resetAssistanceTimer();
            }
        };
        setInterval(check, 5000);
    }
}

// LeetCode-specific detector
class LeetCodeDetector {
    constructor() {
        this.leetcodePatterns = [
            /leetcode\.com\/problems/,
            /leetcode\.com\/contest/,
            /two-sum/i,
            /add-two-numbers/i,
            /longest-substring/i
        ];
    }

    async analyzeScreen(screenData) {
        if (!screenData) return false;
        
        // Check URL patterns
        if (this.leetcodePatterns.some(pattern => pattern.test(window.location.href))) {
            return true;
        }
        
        // Check for LeetCode-specific elements
        const leetcodeElements = [
            'h1[data-cy="question-title"]',
            '[data-track-load="description_content"]',
            '.monaco-editor',
            '[data-cy="lang-select"]'
        ];
        
        return leetcodeElements.some(selector => document.querySelector(selector));
    }
}

// Initialize screen monitor
window.leetcoachScreenMonitor = new ScreenMonitor();
