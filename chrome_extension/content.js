/**
 * Content script for LeetCoach Chrome extension.
 * Injected into LeetCode pages to scrape problem data and integrate UI.
 */

(function() {
  'use strict';

  // Prevent multiple injections
  if (window.leetCoachContentScript) {
    return;
  }

  console.log('LeetCoach content script loading...');

  /**
   * Main content script class
   */
  class LeetCoachContentScript {
    constructor() {
      this.isActive = false;
      this.panel = null;
      this.problemData = null;
      this.userCode = null;
      this.observers = [];
      
      this.init();
    }

    async init() {
      console.log('Initializing LeetCoach content script...');
      
      // Wait for page to be ready
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => this.setup());
      } else {
        this.setup();
      }
    }

    async setup() {
      try {
        // Extract initial problem data
        this.problemData = this.extractProblemData();
        
        if (this.problemData) {
          console.log('Problem detected:', this.problemData.title);
          
          // Create UI panel
          this.createPanel();
          
          // Set up observers for code changes
          this.setupCodeObserver();
          
          // Mark as active
          this.isActive = true;
          
          console.log('LeetCoach content script ready');
        } else {
          console.log('No LeetCode problem detected on this page');
        }
      } catch (error) {
        console.error('Failed to setup content script:', error);
      }
    }

    /**
     * Extract problem data from LeetCode page
     */
    extractProblemData() {
      try {
        // Problem title
        const titleElement = document.querySelector('h1[data-cy="question-title"]') ||
                           document.querySelector('.css-v3d350') ||
                           document.querySelector('[data-cy="question-title"]');
        const title = titleElement?.textContent?.trim() || '';

        // Problem description
        const descriptionElement = document.querySelector('[data-track-load="description_content"]') ||
                                 document.querySelector('.content__u3I1 .question-content') ||
                                 document.querySelector('.question-content');
        const description = descriptionElement?.textContent?.trim() || '';

        // Difficulty
        const difficultyElement = document.querySelector('[diff]') ||
                                document.querySelector('.css-10o4wqw') ||
                                document.querySelector('[data-difficulty]');
        const difficulty = difficultyElement?.textContent?.trim() || 
                         difficultyElement?.getAttribute('diff') || 'Unknown';

        // Tags
        const tagElements = document.querySelectorAll('[data-cy="topic-tag"]') ||
                          document.querySelectorAll('.topic-tag');
        const tags = Array.from(tagElements).map(el => el.textContent.trim());

        // Examples
        const examples = this.extractExamples();

        // Constraints
        const constraints = this.extractConstraints();

        if (!title) {
          return null; // Not a problem page
        }

        return {
          title,
          description,
          difficulty,
          tags,
          examples,
          constraints,
          url: window.location.href
        };
      } catch (error) {
        console.error('Failed to extract problem data:', error);
        return null;
      }
    }

    /**
     * Extract examples from problem description
     */
    extractExamples() {
      const examples = [];
      
      try {
        // Look for example sections
        const exampleElements = document.querySelectorAll('strong:contains("Example")') ||
                              document.querySelectorAll('p:contains("Example")');
        
        exampleElements.forEach((element, index) => {
          const exampleText = element.parentElement?.textContent || '';
          const inputMatch = exampleText.match(/Input:\s*(.+)/);
          const outputMatch = exampleText.match(/Output:\s*(.+)/);
          const explanationMatch = exampleText.match(/Explanation:\s*(.+)/);
          
          if (inputMatch && outputMatch) {
            examples.push({
              input: inputMatch[1].trim(),
              output: outputMatch[1].trim(),
              explanation: explanationMatch ? explanationMatch[1].trim() : ''
            });
          }
        });
      } catch (error) {
        console.error('Failed to extract examples:', error);
      }
      
      return examples;
    }

    /**
     * Extract constraints from problem description
     */
    extractConstraints() {
      const constraints = [];
      
      try {
        // Look for constraints section
        const constraintsElement = document.querySelector('strong:contains("Constraints")') ||
                                 document.querySelector('p:contains("Constraints")');
        
        if (constraintsElement) {
          const constraintsText = constraintsElement.parentElement?.textContent || '';
          const lines = constraintsText.split('\n');
          
          lines.forEach(line => {
            const trimmed = line.trim();
            if (trimmed && !trimmed.includes('Constraints') && trimmed.length > 3) {
              constraints.push(trimmed);
            }
          });
        }
      } catch (error) {
        console.error('Failed to extract constraints:', error);
      }
      
      return constraints;
    }

    /**
     * Extract user's code from the editor
     */
    extractUserCode() {
      try {
        // Try to find Monaco editor
        const monacoEditor = document.querySelector('.monaco-editor textarea') ||
                           document.querySelector('.CodeMirror-code') ||
                           document.querySelector('[data-mode-id]');
        
        if (monacoEditor) {
          // Get code from Monaco editor
          const code = monacoEditor.value || 
                      monacoEditor.textContent ||
                      this.getMonacoEditorContent();
          
          // Detect language
          const language = this.detectLanguage();
          
          if (code && code.trim()) {
            this.userCode = {
              code: code.trim(),
              language: language,
              is_working: false // We don't know if it's working yet
            };
            
            return this.userCode;
          }
        }
        
        return null;
      } catch (error) {
        console.error('Failed to extract user code:', error);
        return null;
      }
    }

    /**
     * Get content from Monaco editor using its API
     */
    getMonacoEditorContent() {
      try {
        // Try to access Monaco editor instance
        if (window.monaco && window.monaco.editor) {
          const editors = window.monaco.editor.getEditors();
          if (editors.length > 0) {
            return editors[0].getValue();
          }
        }
        
        // Fallback: try to get from DOM
        const lines = document.querySelectorAll('.monaco-editor .view-line');
        return Array.from(lines).map(line => line.textContent).join('\n');
      } catch (error) {
        console.error('Failed to get Monaco editor content:', error);
        return '';
      }
    }

    /**
     * Detect programming language from UI
     */
    detectLanguage() {
      try {
        // Look for language selector
        const langSelector = document.querySelector('[data-cy="lang-select"]') ||
                           document.querySelector('.ant-select-selection-item') ||
                           document.querySelector('.language-picker');
        
        if (langSelector) {
          const langText = langSelector.textContent.toLowerCase();
          
          // Map LeetCode language names to our enum values
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
        console.error('Failed to detect language:', error);
        return 'python';
      }
    }

    /**
     * Create the LeetCoach UI panel
     */
    createPanel() {
      try {
        // Remove existing panel
        if (this.panel) {
          this.panel.remove();
        }

        // Create panel container
        this.panel = document.createElement('div');
        this.panel.id = 'leetcoach-panel';
        this.panel.className = 'leetcoach-panel';
        
        // Panel HTML
        this.panel.innerHTML = `
          <div class="leetcoach-header">
            <div class="leetcoach-logo">
              <span class="leetcoach-icon">🧠</span>
              <span class="leetcoach-title">LeetCoach</span>
            </div>
            <div class="leetcoach-controls">
              <button id="leetcoach-minimize" class="leetcoach-btn-icon" title="Minimize">−</button>
              <button id="leetcoach-close" class="leetcoach-btn-icon" title="Close">×</button>
            </div>
          </div>
          
          <div class="leetcoach-content">
            <div class="leetcoach-tabs">
              <button class="leetcoach-tab active" data-tab="hints">Hints</button>
              <button class="leetcoach-tab" data-tab="optimize">Optimize</button>
              <button class="leetcoach-tab" data-tab="complexity">Complexity</button>
              <button class="leetcoach-tab" data-tab="solution">Solution</button>
              <button class="leetcoach-tab" data-tab="questions">Questions</button>
            </div>
            
            <div class="leetcoach-tab-content">
              <div id="leetcoach-hints" class="leetcoach-tab-panel active">
                <div class="leetcoach-hint-controls">
                  <label for="hint-level">Hint Level:</label>
                  <select id="hint-level">
                    <option value="1">1 - Subtle</option>
                    <option value="2">2 - Gentle</option>
                    <option value="3" selected>3 - Moderate</option>
                    <option value="4">4 - Detailed</option>
                    <option value="5">5 - Explicit</option>
                  </select>
                  <button id="get-hint" class="leetcoach-btn-primary">Get Hint</button>
                </div>
                <div id="hint-content" class="leetcoach-content-area">
                  <p class="leetcoach-placeholder">Click "Get Hint" to receive a hint for this problem.</p>
                </div>
              </div>
              
              <div id="leetcoach-optimize" class="leetcoach-tab-panel">
                <div class="leetcoach-optimize-controls">
                  <button id="optimize-code" class="leetcoach-btn-primary">Optimize My Code</button>
                  <div class="leetcoach-checkbox-group">
                    <label><input type="checkbox" id="focus-time" checked> Time Complexity</label>
                    <label><input type="checkbox" id="focus-space" checked> Space Complexity</label>
                    <label><input type="checkbox" id="focus-readability"> Readability</label>
                  </div>
                </div>
                <div id="optimize-content" class="leetcoach-content-area">
                  <p class="leetcoach-placeholder">Write some code and click "Optimize My Code" to get suggestions.</p>
                </div>
              </div>
              
              <div id="leetcoach-complexity" class="leetcoach-tab-panel">
                <div class="leetcoach-complexity-controls">
                  <button id="analyze-complexity" class="leetcoach-btn-primary">Analyze Complexity</button>
                </div>
                <div id="complexity-content" class="leetcoach-content-area">
                  <p class="leetcoach-placeholder">Write some code and click "Analyze Complexity" to get analysis.</p>
                </div>
              </div>
              
              <div id="leetcoach-solution" class="leetcoach-tab-panel">
                <div class="leetcoach-solution-controls">
                  <button id="get-solution" class="leetcoach-btn-primary">Get Solution</button>
                  <div class="leetcoach-checkbox-group">
                    <label><input type="checkbox" id="multiple-approaches" checked> Multiple Approaches</label>
                    <label><input type="checkbox" id="optimal-solution" checked> Optimal Solution</label>
                    <label><input type="checkbox" id="trade-offs" checked> Trade-offs</label>
                  </div>
                </div>
                <div id="solution-content" class="leetcoach-content-area">
                  <p class="leetcoach-placeholder">Click "Get Solution" to see detailed solution explanations.</p>
                </div>
              </div>
              
              <div id="leetcoach-questions" class="leetcoach-tab-panel">
                <div class="leetcoach-questions-controls">
                  <select id="question-type">
                    <option value="clarifying">Clarifying Questions</option>
                    <option value="edge_case">Edge Cases</option>
                    <option value="optimization">Optimization</option>
                    <option value="deep">Deep Questions</option>
                  </select>
                  <button id="get-questions" class="leetcoach-btn-primary">Get Questions</button>
                </div>
                <div id="questions-content" class="leetcoach-content-area">
                  <p class="leetcoach-placeholder">Click "Get Questions" to see interview-style questions.</p>
                </div>
              </div>
            </div>
            
            <div class="leetcoach-loading" id="leetcoach-loading" style="display: none;">
              <div class="leetcoach-spinner"></div>
              <span>Processing...</span>
            </div>
          </div>
        `;

        // Insert panel into page
        document.body.appendChild(this.panel);

        // Set up event listeners
        this.setupPanelEvents();

        console.log('LeetCoach panel created');
      } catch (error) {
        console.error('Failed to create panel:', error);
      }
    }

    /**
     * Set up event listeners for the panel
     */
    setupPanelEvents() {
      // Tab switching
      this.panel.querySelectorAll('.leetcoach-tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
          const tabName = e.target.dataset.tab;
          this.switchTab(tabName);
        });
      });

      // Close and minimize buttons
      document.getElementById('leetcoach-close')?.addEventListener('click', () => {
        this.panel.style.display = 'none';
      });

      document.getElementById('leetcoach-minimize')?.addEventListener('click', () => {
        this.panel.classList.toggle('minimized');
      });

      // Action buttons
      document.getElementById('get-hint')?.addEventListener('click', () => this.getHint());
      document.getElementById('optimize-code')?.addEventListener('click', () => this.optimizeCode());
      document.getElementById('analyze-complexity')?.addEventListener('click', () => this.analyzeComplexity());
      document.getElementById('get-solution')?.addEventListener('click', () => this.getSolution());
      document.getElementById('get-questions')?.addEventListener('click', () => this.getQuestions());

      // Make panel draggable
      this.makePanelDraggable();
    }

    /**
     * Switch between tabs
     */
    switchTab(tabName) {
      // Update tab buttons
      this.panel.querySelectorAll('.leetcoach-tab').forEach(tab => {
        tab.classList.remove('active');
      });
      this.panel.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

      // Update tab panels
      this.panel.querySelectorAll('.leetcoach-tab-panel').forEach(panel => {
        panel.classList.remove('active');
      });
      this.panel.querySelector(`#leetcoach-${tabName}`).classList.add('active');
    }

    /**
     * Make panel draggable
     */
    makePanelDraggable() {
      const header = this.panel.querySelector('.leetcoach-header');
      let isDragging = false;
      let currentX;
      let currentY;
      let initialX;
      let initialY;
      let xOffset = 0;
      let yOffset = 0;

      header.addEventListener('mousedown', (e) => {
        if (e.target.classList.contains('leetcoach-btn-icon')) return;
        
        initialX = e.clientX - xOffset;
        initialY = e.clientY - yOffset;

        if (e.target === header || header.contains(e.target)) {
          isDragging = true;
          header.style.cursor = 'grabbing';
        }
      });

      document.addEventListener('mousemove', (e) => {
        if (isDragging) {
          e.preventDefault();
          currentX = e.clientX - initialX;
          currentY = e.clientY - initialY;

          xOffset = currentX;
          yOffset = currentY;

          this.panel.style.transform = `translate(${currentX}px, ${currentY}px)`;
        }
      });

      document.addEventListener('mouseup', () => {
        initialX = currentX;
        initialY = currentY;
        isDragging = false;
        header.style.cursor = 'grab';
      });
    }

    /**
     * Set up observer for code changes
     */
    setupCodeObserver() {
      try {
        // Observe changes in the editor area
        const editorContainer = document.querySelector('.monaco-editor') ||
                              document.querySelector('.CodeMirror') ||
                              document.querySelector('[data-mode-id]');

        if (editorContainer) {
          const observer = new MutationObserver(() => {
            // Debounce code extraction
            clearTimeout(this.codeUpdateTimeout);
            this.codeUpdateTimeout = setTimeout(() => {
              this.extractUserCode();
            }, 1000);
          });

          observer.observe(editorContainer, {
            childList: true,
            subtree: true,
            characterData: true
          });

          this.observers.push(observer);
        }
      } catch (error) {
        console.error('Failed to setup code observer:', error);
      }
    }

    /**
     * Show loading state
     */
    showLoading() {
      document.getElementById('leetcoach-loading').style.display = 'flex';
    }

    /**
     * Hide loading state
     */
    hideLoading() {
      document.getElementById('leetcoach-loading').style.display = 'none';
    }

    /**
     * Display content in a tab panel
     */
    displayContent(tabId, content, isError = false) {
      const contentArea = document.getElementById(`${tabId}-content`);
      if (contentArea) {
        contentArea.innerHTML = '';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = isError ? 'leetcoach-error' : 'leetcoach-response';
        
        if (typeof content === 'string') {
          contentDiv.innerHTML = this.formatMarkdown(content);
        } else {
          contentDiv.innerHTML = this.formatResponse(content);
        }
        
        contentArea.appendChild(contentDiv);
      }
    }

    /**
     * Format markdown-like content
     */
    formatMarkdown(text) {
      return text
        .replace(/```(\w+)?\n([\s\S]*?)\n```/g, '<pre><code class="language-$1">$2</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/^/, '<p>')
        .replace(/$/, '</p>');
    }

    /**
     * Format API response
     */
    formatResponse(response) {
      if (response.error) {
        return `<div class="leetcoach-error">Error: ${response.error}</div>`;
      }
      
      return this.formatMarkdown(response.response || 'No content available');
    }

    /**
     * API call methods
     */
    async getHint() {
      try {
        this.showLoading();
        
        const hintLevel = parseInt(document.getElementById('hint-level').value);
        const userCode = this.extractUserCode();
        
        // Use dynamic endpoint with natural language request
        const contextData = {
          user_id: await this.getUserId(),
          problem: this.problemData,
          user_code: userCode,
          page_context: this.getPageContext(),
          user_history: await this.getUserHistory()
        };

        const userRequest = `I need a hint for this problem. I'm at hint level ${hintLevel}. ${userCode ? 'I have some code written but' : 'I haven\'t started coding yet and'} I need guidance.`;

        const response = await this.makeDynamicApiCall(userRequest, contextData);
        
        if (response.success) {
          this.displayContent('leetcoach-hints', response.data);
        } else {
          this.displayContent('leetcoach-hints', response.error, true);
        }
      } catch (error) {
        this.displayContent('leetcoach-hints', error.message, true);
      } finally {
        this.hideLoading();
      }
    }

    async optimizeCode() {
      try {
        this.showLoading();
        
        const userCode = this.extractUserCode();
        if (!userCode) {
          this.displayContent('leetcoach-optimize', 'Please write some code first!', true);
          return;
        }

        const focusAreas = [];
        if (document.getElementById('focus-time').checked) focusAreas.push('time_complexity');
        if (document.getElementById('focus-space').checked) focusAreas.push('space_complexity');
        if (document.getElementById('focus-readability').checked) focusAreas.push('readability');

        const contextData = {
          user_id: await this.getUserId(),
          problem: this.problemData,
          user_code: userCode,
          page_context: this.getPageContext(),
          user_history: await this.getUserHistory()
        };

        const userRequest = `Please optimize my code. Focus on: ${focusAreas.join(', ')}. ${userCode.is_working ? 'My code works but I want to improve it.' : 'My code has issues that need fixing.'}`;

        const response = await this.makeDynamicApiCall(userRequest, contextData);
        
        if (response.success) {
          this.displayContent('leetcoach-optimize', response.data);
        } else {
          this.displayContent('leetcoach-optimize', response.error, true);
        }
      } catch (error) {
        this.displayContent('leetcoach-optimize', error.message, true);
      } finally {
        this.hideLoading();
      }
    }

    async analyzeComplexity() {
      try {
        this.showLoading();
        
        const userCode = this.extractUserCode();
        if (!userCode) {
          this.displayContent('leetcoach-complexity', 'Please write some code first!', true);
          return;
        }

        const request = {
          user_id: await this.getUserId(),
          problem: this.problemData,
          user_code: userCode,
          analyze_time: true,
          analyze_space: true,
          include_explanation: true
        };

        const response = await this.makeApiCall('/complexity', request);
        
        if (response.success) {
          this.displayContent('leetcoach-complexity', response.data);
        } else {
          this.displayContent('leetcoach-complexity', response.error, true);
        }
      } catch (error) {
        this.displayContent('leetcoach-complexity', error.message, true);
      } finally {
        this.hideLoading();
      }
    }

    async getSolution() {
      try {
        this.showLoading();

        const request = {
          user_id: await this.getUserId(),
          problem: this.problemData,
          include_multiple_approaches: document.getElementById('multiple-approaches').checked,
          include_optimal_solution: document.getElementById('optimal-solution').checked,
          explain_trade_offs: document.getElementById('trade-offs').checked
        };

        const response = await this.makeApiCall('/solution', request);
        
        if (response.success) {
          this.displayContent('leetcoach-solution', response.data);
        } else {
          this.displayContent('leetcoach-solution', response.error, true);
        }
      } catch (error) {
        this.displayContent('leetcoach-solution', error.message, true);
      } finally {
        this.hideLoading();
      }
    }

    async getQuestions() {
      try {
        this.showLoading();
        
        const questionType = document.getElementById('question-type').value;
        const userCode = this.extractUserCode();

        let endpoint, request;

        if (questionType === 'deep') {
          endpoint = '/deep-questions';
          request = {
            user_id: await this.getUserId(),
            problem: this.problemData,
            user_code: userCode,
            difficulty_level: 'medium',
            focus_area: null
          };
        } else {
          endpoint = '/counter-questions';
          request = {
            user_id: await this.getUserId(),
            problem: this.problemData,
            user_code: userCode,
            question_type: questionType,
            num_questions: 5
          };
        }

        const response = await this.makeApiCall(endpoint, request);
        
        if (response.success) {
          this.displayContent('leetcoach-questions', response.data);
        } else {
          this.displayContent('leetcoach-questions', response.error, true);
        }
      } catch (error) {
        this.displayContent('leetcoach-questions', error.message, true);
      } finally {
        this.hideLoading();
      }
    }

    /**
     * Make API call through background script
     */
    async makeApiCall(endpoint, data) {
      return new Promise((resolve) => {
        chrome.runtime.sendMessage({
          type: 'API_REQUEST',
          endpoint: endpoint,
          data: data
        }, (response) => {
          resolve(response);
        });
      });
    }

    /**
     * Make dynamic API call with natural language processing
     */
    async makeDynamicApiCall(userRequest, contextData) {
      return new Promise((resolve) => {
        chrome.runtime.sendMessage({
          type: 'API_REQUEST',
          endpoint: '/ask',
          data: {
            user_request: userRequest,
            context_data: contextData
          }
        }, (response) => {
          resolve(response);
        });
      });
    }

    /**
     * Get current page context
     */
    getPageContext() {
      return {
        url: window.location.href,
        time_spent_minutes: this.getTimeSpentOnPage(),
        attempts: this.getAttemptCount(),
        focus_area: this.getCurrentFocusArea(),
        scroll_position: window.scrollY,
        active_tab: document.querySelector('.leetcoach-tab.active')?.dataset.tab || 'hints'
      };
    }

    /**
     * Get time spent on current page
     */
    getTimeSpentOnPage() {
      if (!this.pageStartTime) {
        this.pageStartTime = Date.now();
      }
      return Math.floor((Date.now() - this.pageStartTime) / (1000 * 60));
    }

    /**
     * Get attempt count (rough estimate)
     */
    getAttemptCount() {
      // Simple heuristic based on code changes
      const currentCode = this.extractUserCode();
      if (!this.lastCodeSnapshot) {
        this.lastCodeSnapshot = currentCode?.code || '';
        this.attemptCount = 1;
      } else if (currentCode && currentCode.code !== this.lastCodeSnapshot) {
        this.attemptCount = (this.attemptCount || 1) + 1;
        this.lastCodeSnapshot = currentCode.code;
      }
      return this.attemptCount || 1;
    }

    /**
     * Get current focus area based on user behavior
     */
    getCurrentFocusArea() {
      const activeTab = document.querySelector('.leetcoach-tab.active');
      if (activeTab) {
        return activeTab.dataset.tab;
      }
      
      // Analyze where user might be focusing based on code
      const userCode = this.extractUserCode();
      if (!userCode || !userCode.code) {
        return 'getting_started';
      } else if (userCode.code.length < 100) {
        return 'basic_implementation';
      } else if (userCode.is_working === false) {
        return 'debugging';
      } else {
        return 'optimization';
      }
    }

    /**
     * Get user history from storage
     */
    async getUserHistory() {
      return new Promise((resolve) => {
        chrome.runtime.sendMessage({
          type: 'GET_USER_HISTORY'
        }, (response) => {
          resolve(response?.history || []);
        });
      });
    }

    /**
     * Get user ID from preferences
     */
    async getUserId() {
      return new Promise((resolve) => {
        chrome.runtime.sendMessage({
          type: 'GET_PREFERENCES'
        }, (response) => {
          resolve(response.preferences?.userId || 'anonymous');
        });
      });
    }

    /**
     * Activate the extension
     */
    activate() {
      if (this.panel) {
        this.panel.style.display = 'block';
      }
    }

    /**
     * Deactivate the extension
     */
    deactivate() {
      if (this.panel) {
        this.panel.style.display = 'none';
      }
    }

    /**
     * Cleanup
     */
    destroy() {
      this.observers.forEach(observer => observer.disconnect());
      if (this.panel) {
        this.panel.remove();
      }
    }
  }

  // Initialize content script
  window.leetCoachContentScript = new LeetCoachContentScript();

  console.log('LeetCoach content script loaded');
})();
