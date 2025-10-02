/**
 * LeetCoach Chat Interface
 * Main interaction point for all AI assistance features
 */

class LeetCoachChat {
    constructor() {
        this.isVisible = false;
        this.isMinimized = false;
        this.currentTab = 'assistant';
        this.conversationHistory = [];
        this.userPreferences = null;
        this.assistanceTimer = null;
        this.isTyping = false;
        
        this.init();
    }

    async init() {
        console.log('Initializing LeetCoach Chat...');
        
        // Load preferences
        await this.loadPreferences();
        
        // Create chat interface
        this.createChatInterface();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Start assistance monitoring
        this.startAssistanceMonitoring();
        
        console.log('LeetCoach Chat initialized');
    }

    async loadPreferences() {
        const getLocal = () => new Promise((resolve) => chrome.storage.local.get('leetcoach_preferences', (r) => resolve(r.leetcoach_preferences || {})));
        const getSync = () => new Promise((resolve) => chrome.storage.sync.get(['leetcoach_preferences'], (r) => resolve(r.leetcoach_preferences || {})));
        const [localPrefs, syncPrefs] = await Promise.all([getLocal(), getSync()]);
        const merged = { ...syncPrefs, ...localPrefs };
        this.userPreferences = {
            assistanceDelay: 30,
            preferredLanguage: 'python',
            explanationStyle: 'detailed',
            autoActivate: true,
            includeExamples: true,
            includeEdgeCases: true,
            apiProvider: 'auto', // auto, openai, bedrock, gemini
            ...merged
        };
    }

    createChatInterface() {
        // Remove existing chat if present
        const existingChat = document.getElementById('leetcoach-chat');
        if (existingChat) {
            existingChat.remove();
        }

        // Create chat container
        this.chatContainer = document.createElement('div');
        this.chatContainer.id = 'leetcoach-chat';
        this.chatContainer.className = 'leetcoach-chat-container';
        this.chatContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 400px;
            height: 600px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            z-index: 10000;
            display: none;
            flex-direction: column;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            overflow: hidden;
        `;

        // Create chat header
        this.createChatHeader();
        
        // Create chat tabs
        this.createChatTabs();
        
        // Create chat content
        this.createChatContent();
        
        // Create chat input
        this.createChatInput();
        
        // Ensure chat can be programmatically shown by other modules
        window.leetcoachChat = this;

        // Add to page
        document.body.appendChild(this.chatContainer);
    }

    createChatHeader() {
        const header = document.createElement('div');
        header.className = 'leetcoach-chat-header';
        header.style.cssText = `
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: move;
        `;

        header.innerHTML = `
            <div class="chat-title">
                <span class="chat-icon">🧠</span>
                <span class="chat-name">LeetCoach AI</span>
                <span class="chat-status" id="chat-status">Ready</span>
            </div>
            <div class="chat-controls">
                <button class="chat-btn" id="minimize-btn" title="Minimize">−</button>
                <button class="chat-btn" id="close-btn" title="Close">×</button>
            </div>
        `;

        this.chatContainer.appendChild(header);
    }

    createChatTabs() {
        const tabsContainer = document.createElement('div');
        tabsContainer.className = 'leetcoach-chat-tabs';
        tabsContainer.style.cssText = `
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            display: flex;
        `;

        const tabs = [
            { id: 'assistant', name: 'Assistant', icon: '🤖' },
            { id: 'hints', name: 'Hints', icon: '💡' },
            { id: 'optimize', name: 'Optimize', icon: '⚡' },
            { id: 'complexity', name: 'Complexity', icon: '📊' },
            { id: 'questions', name: 'Questions', icon: '❓' },
            { id: 'settings', name: 'Settings', icon: '⚙️' }
        ];

        tabs.forEach(tab => {
            const tabElement = document.createElement('button');
            tabElement.className = `chat-tab ${tab.id === 'assistant' ? 'active' : ''}`;
            tabElement.dataset.tab = tab.id;
            tabElement.style.cssText = `
                flex: 1;
                padding: 12px 8px;
                border: none;
                background: transparent;
                cursor: pointer;
                font-size: 12px;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 4px;
                transition: all 0.2s ease;
            `;
            
            tabElement.innerHTML = `
                <span class="tab-icon">${tab.icon}</span>
                <span class="tab-name">${tab.name}</span>
            `;
            
            tabElement.addEventListener('click', () => this.switchTab(tab.id));
            tabsContainer.appendChild(tabElement);
        });

        this.chatContainer.appendChild(tabsContainer);
    }

    createChatContent() {
        const contentContainer = document.createElement('div');
        contentContainer.className = 'leetcoach-chat-content';
        contentContainer.style.cssText = `
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        `;

        // Create tab panels
        this.createTabPanels(contentContainer);
        
        // Create messages area
        this.createMessagesArea(contentContainer);

        this.chatContainer.appendChild(contentContainer);
    }

    createTabPanels(container) {
        const panels = [
            { id: 'assistant', content: this.createAssistantPanel() },
            { id: 'hints', content: this.createHintsPanel() },
            { id: 'optimize', content: this.createOptimizePanel() },
            { id: 'complexity', content: this.createComplexityPanel() },
            { id: 'questions', content: this.createQuestionsPanel() },
            { id: 'settings', content: this.createSettingsPanel() }
        ];

        panels.forEach(panel => {
            const panelElement = document.createElement('div');
            panelElement.id = `chat-panel-${panel.id}`;
            panelElement.className = `chat-panel ${panel.id === 'assistant' ? 'active' : ''}`;
            panelElement.style.cssText = `
                display: ${panel.id === 'assistant' ? 'flex' : 'none'};
                flex-direction: column;
                height: 100%;
                padding: 15px;
            `;
            panelElement.innerHTML = panel.content;
            container.appendChild(panelElement);
        });
    }

    createAssistantPanel() {
        return `
            <div class="assistant-welcome">
                <h3>Welcome to LeetCoach AI! 🚀</h3>
                <p>I'm here to help you with your LeetCode problems. I can:</p>
                <ul>
                    <li>💡 Provide hints when you're stuck</li>
                    <li>⚡ Optimize your code for better performance</li>
                    <li>📊 Analyze time and space complexity</li>
                    <li>❓ Generate interview questions</li>
                    <li>🔍 Detect edge cases and potential issues</li>
                </ul>
                <div class="quick-actions">
                    <button class="quick-btn" onclick="window.leetcoachChat?.getHint()">
                        Get Hint
                    </button>
                    <button class="quick-btn" onclick="window.leetcoachChat?.analyzeCode()">
                        Analyze Code
                    </button>
                    <button class="quick-btn" onclick="window.leetcoachChat?.getQuestions()">
                        Interview Questions
                    </button>
                </div>
            </div>
            <div class="assistance-timer" id="assistance-timer" style="display: none;">
                <div class="timer-info">
                    <span class="timer-icon">⏰</span>
                    <span class="timer-text">Assistance will be offered in <span id="timer-countdown">15</span> seconds</span>
                </div>
                <button class="timer-btn" onclick="window.leetcoachChat?.cancelTimer()">Cancel</button>
            </div>
        `;
    }

    createHintsPanel() {
        return `
            <div class="hints-controls">
                <div class="control-group">
                    <label>Hint Level:</label>
                    <select id="hint-level">
                        <option value="1">1 - Subtle</option>
                        <option value="2">2 - Gentle</option>
                        <option value="3" selected>3 - Moderate</option>
                        <option value="4">4 - Detailed</option>
                        <option value="5">5 - Explicit</option>
                    </select>
                </div>
                <button class="action-btn primary" onclick="window.leetcoachChat?.getHint()">
                    Get Hint
                </button>
            </div>
            <div class="hints-content" id="hints-content">
                <p class="placeholder">Click "Get Hint" to receive guidance for this problem.</p>
            </div>
        `;
    }

    createOptimizePanel() {
        return `
            <div class="optimize-controls">
                <div class="control-group">
                    <label>Focus Areas:</label>
                    <div class="checkbox-group">
                        <label><input type="checkbox" id="focus-time" checked> Time Complexity</label>
                        <label><input type="checkbox" id="focus-space" checked> Space Complexity</label>
                        <label><input type="checkbox" id="focus-readability"> Readability</label>
                        <label><input type="checkbox" id="focus-edge-cases"> Edge Cases</label>
                    </div>
                </div>
                <button class="action-btn primary" onclick="window.leetcoachChat?.optimizeCode()">
                    Optimize Code
                </button>
            </div>
            <div class="optimize-content" id="optimize-content">
                <p class="placeholder">Write some code and click "Optimize Code" to get suggestions.</p>
            </div>
        `;
    }

    createComplexityPanel() {
        return `
            <div class="complexity-controls">
                <button class="action-btn primary" onclick="window.leetcoachChat?.analyzeComplexity()">
                    Analyze Complexity
                </button>
            </div>
            <div class="complexity-content" id="complexity-content">
                <p class="placeholder">Click "Analyze Complexity" to get detailed analysis.</p>
            </div>
        `;
    }

    createQuestionsPanel() {
        return `
            <div class="questions-controls">
                <div class="control-group">
                    <label>Question Type:</label>
                    <select id="question-type">
                        <option value="clarifying">Clarifying Questions</option>
                        <option value="edge_case">Edge Cases</option>
                        <option value="optimization">Optimization</option>
                        <option value="deep">Deep Technical</option>
                    </select>
                </div>
                <button class="action-btn primary" onclick="window.leetcoachChat?.getQuestions()">
                    Generate Questions
                </button>
            </div>
            <div class="questions-content" id="questions-content">
                <p class="placeholder">Click "Generate Questions" to see interview-style questions.</p>
            </div>
        `;
    }

    createSettingsPanel() {
        return `
            <div class="settings-content">
                <div class="setting-group">
                    <label>Auto-Assist Delay</label>
                    <select id="assistance-delay-select" onchange="window.leetcoachChat?.updateSetting('assistanceDelay', parseInt(this.value, 10))">
                        <option value="5">5 seconds</option>
                        <option value="10">10 seconds</option>
                        <option value="15" selected>15 seconds</option>
                        <option value="30">30 seconds</option>
                        <option value="60">1 minute</option>
                        <option value="120">2 minutes</option>
                        <option value="300">5 minutes</option>
                    </select>
                </div>
                
                <div class="setting-group">
                    <label>Auto Assistance</label>
                    <div class="checkbox-group">
                        <label><input type="checkbox" id="auto-assist-enabled" checked onchange="window.leetcoachChat?.updateSetting('autoAssistEnabled', this.checked)"> Enable automatic hints when stuck</label>
                    </div>
                </div>

                <div class="setting-group">
                    <label>Preferred Language:</label>
                    <select id="preferred-language" onchange="window.leetcoachChat?.updateSetting('preferredLanguage', this.value)">
                        <option value="python">Python</option>
                        <option value="javascript">JavaScript</option>
                        <option value="java">Java</option>
                        <option value="cpp">C++</option>
                        <option value="c">C</option>
                        <option value="csharp">C#</option>
                        <option value="go">Go</option>
                        <option value="rust">Rust</option>
                        <option value="typescript">TypeScript</option>
                    </select>
                </div>
                
                <div class="setting-group">
                    <label>Explanation Style:</label>
                    <select id="explanation-style" onchange="window.leetcoachChat?.updateSetting('explanationStyle', this.value)">
                        <option value="brief">Brief</option>
                        <option value="detailed" selected>Detailed</option>
                        <option value="comprehensive">Comprehensive</option>
                    </select>
                </div>
                
                <div class="setting-group">
                    <label>API Provider:</label>
                    <select id="api-provider" onchange="window.leetcoachChat?.updateSetting('apiProvider', this.value)">
                        <option value="auto" selected>Auto-detect</option>
                        <option value="openai">OpenAI</option>
                        <option value="bedrock">AWS Bedrock</option>
                        <option value="gemini">Google Gemini</option>
                    </select>
                </div>
                
                <div class="setting-group">
                    <label>Options:</label>
                    <div class="checkbox-group">
                        <label><input type="checkbox" id="auto-activate" checked onchange="window.leetcoachChat?.updateSetting('autoActivate', this.checked)"> Auto-activate</label>
                        <label><input type="checkbox" id="include-examples" checked onchange="window.leetcoachChat?.updateSetting('includeExamples', this.checked)"> Include Examples</label>
                        <label><input type="checkbox" id="include-edge-cases" checked onchange="window.leetcoachChat?.updateSetting('includeEdgeCases', this.checked)"> Include Edge Cases</label>
                    </div>
                </div>
                
                <button class="action-btn primary" onclick="window.leetcoachChat?.saveSettings()">
                    Save Settings
                </button>
            </div>
        `;
    }

    createMessagesArea(container) {
        const messagesArea = document.createElement('div');
        messagesArea.className = 'leetcoach-messages';
        messagesArea.id = 'chat-messages';
        messagesArea.style.cssText = `
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            background: #f8f9fa;
            border-top: 1px solid #e9ecef;
            display: none;
        `;
        
        container.appendChild(messagesArea);
    }

    createChatInput() {
        const inputContainer = document.createElement('div');
        inputContainer.className = 'leetcoach-chat-input';
        inputContainer.style.cssText = `
            padding: 15px;
            border-top: 1px solid #e9ecef;
            background: white;
            display: none;
        `;

        inputContainer.innerHTML = `
            <div class="input-group">
                <input type="text" id="chat-input" placeholder="Ask me anything about your code..." 
                       style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 20px; outline: none;">
                <button id="send-btn" onclick="window.leetcoachChat?.sendMessage()" 
                        style="margin-left: 10px; padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 20px; cursor: pointer;">
                    Send
                </button>
            </div>
        `;

        this.chatContainer.appendChild(inputContainer);
    }

    setupEventListeners() {
        // Header controls
        document.getElementById('minimize-btn')?.addEventListener('click', () => this.toggleMinimize());
        document.getElementById('close-btn')?.addEventListener('click', () => this.hide());
        
        // Chat input
        document.getElementById('chat-input')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        // Settings updates
        document.getElementById('assistance-delay')?.addEventListener('input', (e) => {
            document.getElementById('delay-value').textContent = e.target.value;
        });
        
        // Make draggable
        this.makeDraggable();
    }

    makeDraggable() {
        const header = this.chatContainer.querySelector('.leetcoach-chat-header');
        let isDragging = false;
        let currentX, currentY, initialX, initialY, xOffset = 0, yOffset = 0;

        header.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('chat-btn')) return;
            
            initialX = e.clientX - xOffset;
            initialY = e.clientY - yOffset;
            isDragging = true;
            header.style.cursor = 'grabbing';
        });

        document.addEventListener('mousemove', (e) => {
            if (isDragging) {
                e.preventDefault();
                currentX = e.clientX - initialX;
                currentY = e.clientY - initialY;
                xOffset = currentX;
                yOffset = currentY;
                this.chatContainer.style.transform = `translate(${currentX}px, ${currentY}px)`;
            }
        });

        document.addEventListener('mouseup', () => {
            isDragging = false;
            header.style.cursor = 'grab';
        });
    }

    show() {
        this.chatContainer.style.display = 'flex';
        this.isVisible = true;
        this.isMinimized = false;
        
        // Focus on input if in assistant mode
        if (this.currentTab === 'assistant') {
            setTimeout(() => {
                document.getElementById('chat-input')?.focus();
            }, 100);
        }
    }

    hide() {
        this.chatContainer.style.display = 'none';
        this.isVisible = false;
    }

    toggleMinimize() {
        if (this.isMinimized) {
            this.chatContainer.style.height = '600px';
            this.chatContainer.querySelector('.leetcoach-chat-content').style.display = 'flex';
            this.isMinimized = false;
        } else {
            this.chatContainer.style.height = '60px';
            this.chatContainer.querySelector('.leetcoach-chat-content').style.display = 'none';
            this.isMinimized = true;
        }
    }

    switchTab(tabId) {
        // Update tab buttons
        this.chatContainer.querySelectorAll('.chat-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        this.chatContainer.querySelector(`[data-tab="${tabId}"]`).classList.add('active');

        // Update tab panels
        this.chatContainer.querySelectorAll('.chat-panel').forEach(panel => {
            panel.style.display = 'none';
        });
        this.chatContainer.querySelector(`#chat-panel-${tabId}`).style.display = 'flex';

        this.currentTab = tabId;

        // Show/hide messages and input based on tab
        const messagesArea = document.getElementById('chat-messages');
        const inputArea = this.chatContainer.querySelector('.leetcoach-chat-input');
        
        if (tabId === 'assistant') {
            messagesArea.style.display = 'block';
            inputArea.style.display = 'block';
        } else {
            messagesArea.style.display = 'none';
            inputArea.style.display = 'none';
        }
    }

    showChat() {
        this.show();
        this.switchTab('assistant');
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) return;

        // Add user message to chat
        this.addMessage('user', message);
        input.value = '';

        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Send message to backend
            const response = await this.sendToBackend('ask', {
                user_request: message,
                context_data: await this.getCurrentContext()
            });

            // Hide typing indicator
            this.hideTypingIndicator();

            // Add AI response to chat
            this.addMessage('ai', response.response || 'Sorry, I couldn\'t process your request.');
            
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage('ai', 'Sorry, there was an error processing your request.');
            console.error('Chat error:', error);
        }
    }

    addMessage(sender, content) {
        const messagesArea = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.style.cssText = `
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 15px;
            max-width: 80%;
            word-wrap: break-word;
            ${sender === 'user' 
                ? 'background: #667eea; color: white; margin-left: auto;' 
                : 'background: #f1f3f4; color: #333;'
            }
        `;
        
        messageDiv.innerHTML = this.formatMessage(content);
        messagesArea.appendChild(messageDiv);
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }

    formatMessage(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/```(\w+)?\n([\s\S]*?)\n```/g, '<pre><code class="language-$1">$2</code></pre>')
            .replace(/\n/g, '<br>');
    }

    showTypingIndicator() {
        const messagesArea = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'message ai typing';
        typingDiv.style.cssText = `
            margin-bottom: 15px;
            padding: 10px 15px;
            background: #f1f3f4;
            color: #666;
            border-radius: 15px;
            max-width: 80%;
        `;
        typingDiv.innerHTML = 'AI is typing...';
        messagesArea.appendChild(typingDiv);
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }

    hideTypingIndicator() {
        const typingDiv = document.getElementById('typing-indicator');
        if (typingDiv) {
            typingDiv.remove();
        }
    }

    async getCurrentContext() {
        return {
            url: window.location.href,
            title: document.title,
            userCode: this.extractUserCode(),
            problemData: this.extractProblemData(),
            timestamp: Date.now()
        };
    }

    extractUserCode() {
        try {
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
            
            return { title, difficulty, description: description.substring(0, 500), url: window.location.href };
        } catch (error) {
            console.error('Problem data extraction error:', error);
            return null;
        }
    }

    detectLanguage() {
        try {
            const langElement = document.querySelector('[data-cy="lang-select"]') || document.querySelector('.ant-select-selection-item');
            if (langElement) {
                const langText = langElement.textContent.toLowerCase();
                const langMap = {
                    'python': 'python', 'python3': 'python', 'javascript': 'javascript',
                    'java': 'java', 'c++': 'cpp', 'c': 'c', 'c#': 'csharp',
                    'go': 'go', 'rust': 'rust', 'typescript': 'typescript'
                };
                for (const [key, value] of Object.entries(langMap)) {
                    if (langText.includes(key)) return value;
                }
            }
            return 'python';
        } catch (error) {
            return 'python';
        }
    }

    checkCodeValidity(code) {
        if (!code || code.trim().length < 10) return false;
        const commonErrors = [/[{}]\s*$/, /\(\s*$/, /\[\s*$/, /['"]\s*$/, /def\s+\w+\s*\([^)]*$/, /if\s+[^:]*$/, /for\s+[^:]*$/, /while\s+[^:]*$/];
        return !commonErrors.some(pattern => pattern.test(code));
    }

    async sendToBackend(endpoint, data) {
        return new Promise((resolve) => {
            chrome.runtime.sendMessage({
                type: 'API_REQUEST',
                endpoint: `/${endpoint}`,
                data: data
            }, (resp) => {
                // Unwrap success/data or pass through error
                if (!resp) return resolve({ success: false, error: 'No response' });
                if (resp.success && resp.data) return resolve(resp.data);
                // Some routes (like /ask) may return raw success/response inside data
                return resolve(resp);
            });
        });
    }

    // Feature methods
    async getHint() {
        this.showLoading('hints-content');
        try {
            const response = await this.sendToBackend('ask', {
                user_request: 'I need a hint for this problem',
                context_data: await this.getCurrentContext()
            });
            const content = response?.response || response?.data?.response || 'No hint available';
            this.displayContent('hints-content', content);
        } catch (error) {
            this.displayContent('hints-content', 'Error getting hint', true);
        }
    }

    async optimizeCode() {
        this.showLoading('optimize-content');
        try {
            const response = await this.sendToBackend('ask', {
                user_request: 'Please optimize my code',
                context_data: await this.getCurrentContext()
            });
            const content = response?.response || response?.data?.response || 'No optimization available';
            this.displayContent('optimize-content', content);
        } catch (error) {
            this.displayContent('optimize-content', 'Error optimizing code', true);
        }
    }

    async analyzeComplexity() {
        this.showLoading('complexity-content');
        try {
            const response = await this.sendToBackend('ask', {
                user_request: 'Analyze the time and space complexity of my code',
                context_data: await this.getCurrentContext()
            });
            const content = response?.response || response?.data?.response || 'No analysis available';
            this.displayContent('complexity-content', content);
        } catch (error) {
            this.displayContent('complexity-content', 'Error analyzing complexity', true);
        }
    }

    async getQuestions() {
        this.showLoading('questions-content');
        try {
            const response = await this.sendToBackend('ask', {
                user_request: 'Generate interview questions for this problem',
                context_data: await this.getCurrentContext()
            });
            const content = response?.response || response?.data?.response || 'No questions available';
            this.displayContent('questions-content', content);
        } catch (error) {
            this.displayContent('questions-content', 'Error generating questions', true);
        }
    }

    showLoading(contentId) {
        const content = document.getElementById(contentId);
        if (content) {
            content.innerHTML = '<div class="loading">Processing...</div>';
        }
    }

    displayContent(contentId, content, isError = false) {
        const contentElement = document.getElementById(contentId);
        if (contentElement) {
            contentElement.innerHTML = `<div class="${isError ? 'error' : 'response'}">${this.formatMessage(content)}</div>`;
        }
    }

    updateSetting(key, value) {
        this.userPreferences[key] = value;
        // Sync with screen monitor if present
        if (window.leetcoachScreenMonitor && typeof window.leetcoachScreenMonitor.updatePreferences === 'function') {
            window.leetcoachScreenMonitor.updatePreferences({ [key]: value });
        }
    }

    async saveSettings() {
        await chrome.storage.sync.set({ leetcoach_preferences: this.userPreferences });
        this.showNotification('Settings saved!', 'success');
    }

    showNotification(message, type = 'info') {
        // Create notification
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            z-index: 10001;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => notification.remove(), 3000);
    }

    startAssistanceMonitoring() {
        // This will be called by the screen monitor
        setInterval(() => {
            if (this.isVisible) return;
            
            // Check if assistance is needed
            this.checkAssistanceNeed();
        }, 5000);
    }

    async checkAssistanceNeed() {
        // This will be implemented with the screen monitor integration
    }
}

// Initialize chat interface
window.leetcoachChat = new LeetCoachChat();
