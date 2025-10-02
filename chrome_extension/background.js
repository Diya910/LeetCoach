/**
 * Background script for LeetCoach Chrome extension.
 * Handles extension lifecycle, API communication, and cross-tab coordination.
 */

// Extension configuration
const CONFIG = {
  API_BASE_URL: 'http://localhost:8000/api',
  STORAGE_KEYS: {
    USER_PREFERENCES: 'leetcoach_preferences',
    SESSION_DATA: 'leetcoach_session',
    CACHE: 'leetcoach_cache'
  },
  CACHE_DURATION: 5 * 60 * 1000, // 5 minutes
};

// Extension state
let extensionState = {
  isActive: false,
  currentTab: null,
  apiHealth: 'unknown'
};

/**
 * Extension installation and startup
 */
chrome.runtime.onInstalled.addListener(async (details) => {
  console.log('LeetCoach extension installed:', details.reason);
  
  // Initialize default preferences
  const defaultPreferences = {
    userId: generateUserId(),
    preferredLanguage: 'python',
    explanationStyle: 'detailed',
    includeExamples: true,
    includeEdgeCases: true,
    apiEndpoint: CONFIG.API_BASE_URL,
    autoActivate: true
  };
  
  // Store default preferences if not exists
  const stored = await chrome.storage.local.get(CONFIG.STORAGE_KEYS.USER_PREFERENCES);
  if (!stored[CONFIG.STORAGE_KEYS.USER_PREFERENCES]) {
    await chrome.storage.local.set({
      [CONFIG.STORAGE_KEYS.USER_PREFERENCES]: defaultPreferences
    });
  }
  
  // Check API health
  await checkApiHealth();
});

/**
 * Handle extension startup
 */
chrome.runtime.onStartup.addListener(async () => {
  console.log('LeetCoach extension starting up...');
  await checkApiHealth();
});

/**
 * Handle tab updates
 */
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    if (isLeetCodeProblemPage(tab.url)) {
      console.log('LeetCode problem page detected:', tab.url);
      extensionState.currentTab = tabId;
      
      // Auto-activate if enabled
      const preferences = await getPreferences();
      if (preferences.autoActivate) {
        await activateOnTab(tabId);
      }
    }
  }
});

/**
 * Handle messages from content script and popup
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Background received message:', message.type);
  
  switch (message.type) {
    case 'GET_PREFERENCES':
      handleGetPreferences(sendResponse);
      return true; // Keep channel open for async response
      
    case 'UPDATE_PREFERENCES':
      handleUpdatePreferences(message.preferences, sendResponse);
      return true;
      
    case 'API_REQUEST':
      handleApiRequest(message.endpoint, message.data, sendResponse, message.method);
      return true;
      
    case 'GET_PROBLEM_DATA':
      if (sender && sender.tab && typeof sender.tab.id === 'number') {
        handleGetProblemData(sender.tab.id, sendResponse);
      } else {
        console.warn('GET_PROBLEM_DATA called without a tab context');
        sendResponse({ success: false, error: 'No active tab context' });
      }
      return true;
      
    case 'CACHE_SET':
      handleCacheSet(message.key, message.data, sendResponse);
      return true;
      
    case 'CACHE_GET':
      handleCacheGet(message.key, sendResponse);
      return true;
      
    case 'HEALTH_CHECK':
      handleHealthCheck(sendResponse);
      return true;

    case 'GET_USER_HISTORY':
      handleGetUserHistory(sendResponse);
      return true;
      
    case 'ANALYZE_SCREEN':
      handleAnalyzeScreen(message.data, sendResponse);
      return true;
      
    case 'ANALYZE_ASSISTANCE_NEED':
      handleAnalyzeAssistanceNeed(message.data, sendResponse);
      return true;
      
    default:
      console.warn('Unknown message type:', message.type);
      sendResponse({ error: 'Unknown message type' });
  }
});

/**
 * Utility Functions
 */

function generateUserId() {
  return 'user_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
}

function isLeetCodeProblemPage(url) {
  return url.includes('leetcode.com/problems/') || 
         url.includes('leetcode.com/contest/') && url.includes('/problems/');
}

async function activateOnTab(tabId) {
  try {
    await chrome.scripting.executeScript({
      target: { tabId },
      function: () => {
        if (window.leetCoachContentScript) {
          window.leetCoachContentScript.activate();
        }
      }
    });
  } catch (error) {
    console.error('Failed to activate on tab:', error);
  }
}

async function checkApiHealth() {
  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/health`);
    if (response.ok) {
      extensionState.apiHealth = 'healthy';
      console.log('API health check passed');
    } else {
      // Treat non-200 as degraded rather than failure so extension UI keeps working
      extensionState.apiHealth = 'degraded';
      console.warn('API health check degraded:', response.status);
    }
  } catch (error) {
    extensionState.apiHealth = 'unreachable';
    console.error('API health check error:', error);
  }
}

/**
 * Message Handlers
 */

async function handleGetPreferences(sendResponse) {
  try {
    const preferences = await getPreferences();
    sendResponse({ success: true, preferences });
  } catch (error) {
    console.error('Failed to get preferences:', error);
    sendResponse({ success: false, error: error.message });
  }
}

async function handleUpdatePreferences(preferences, sendResponse) {
  try {
    await chrome.storage.local.set({
      [CONFIG.STORAGE_KEYS.USER_PREFERENCES]: preferences
    });
    sendResponse({ success: true });
  } catch (error) {
    console.error('Failed to update preferences:', error);
    sendResponse({ success: false, error: error.message });
  }
}

async function handleApiRequest(endpoint, data, sendResponse, method = 'POST') {
  try {
    const preferences = await getPreferences();
    const url = `${preferences.apiEndpoint || CONFIG.API_BASE_URL}${endpoint}`;
    
    const fetchOptions = {
      method,
      headers: { 'Content-Type': 'application/json' }
    };

    let finalUrl = url;
    if (method === 'GET') {
      const params = new URLSearchParams();
      if (data && typeof data === 'object') {
        Object.entries(data).forEach(([key, value]) => {
          if (value !== undefined && value !== null) params.append(key, String(value));
        });
      }
      finalUrl = params.toString() ? `${url}?${params.toString()}` : url;
      delete fetchOptions.headers['Content-Type'];
    } else {
      fetchOptions.body = JSON.stringify(data);
    }

    const response = await fetch(finalUrl, fetchOptions);
    
    let result;
    try {
      result = await response.json();
    } catch (e) {
      // If response is not JSON, create a simple error object
      result = { error: `HTTP ${response.status}: ${response.statusText}` };
    }
    
    if (response.ok) {
      sendResponse({ success: true, data: result });
    } else {
      // Enhanced error handling
      let errorMessage = 'API request failed';
      if (response.status === 401) {
        errorMessage = 'Authentication failed. Please check your API keys in the .env file.';
      } else if (response.status === 500) {
        errorMessage = 'Server error. Please check if the backend is running and configured properly.';
      } else if (result && result.error) {
        errorMessage = result.error;
      } else {
        errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      }
      sendResponse({ success: false, error: errorMessage });
    }
  } catch (error) {
    console.error('API request failed:', error);
    sendResponse({ success: false, error: error.message });
  }
}

async function handleGetUserHistory(sendResponse) {
  try {
    // Avoid hitting vector DB endpoints when they may be unavailable; return empty history.
    // This keeps the extension responsive even if Pinecone is not configured.
    sendResponse({ history: [] });
  } catch (e) {
    console.error('Failed to fetch user history:', e);
    sendResponse({ history: [] });
  }
}

async function handleGetProblemData(tabId, sendResponse) {
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId },
      function: () => {
        if (window.leetCoachContentScript) {
          return window.leetCoachContentScript.extractProblemData();
        }
        return null;
      }
    });
    
    const problemData = results[0]?.result;
    if (problemData) {
      sendResponse({ success: true, data: problemData });
    } else {
      sendResponse({ success: false, error: 'Failed to extract problem data' });
    }
  } catch (error) {
    console.error('Failed to get problem data:', error);
    sendResponse({ success: false, error: error.message });
  }
}

async function handleCacheSet(key, data, sendResponse) {
  try {
    const cache = await getCache();
    cache[key] = {
      data,
      timestamp: Date.now()
    };
    
    await chrome.storage.local.set({
      [CONFIG.STORAGE_KEYS.CACHE]: cache
    });
    
    sendResponse({ success: true });
  } catch (error) {
    console.error('Failed to set cache:', error);
    sendResponse({ success: false, error: error.message });
  }
}

async function handleCacheGet(key, sendResponse) {
  try {
    const cache = await getCache();
    const cached = cache[key];
    
    if (cached && (Date.now() - cached.timestamp) < CONFIG.CACHE_DURATION) {
      sendResponse({ success: true, data: cached.data });
    } else {
      sendResponse({ success: false, error: 'Cache miss or expired' });
    }
  } catch (error) {
    console.error('Failed to get cache:', error);
    sendResponse({ success: false, error: error.message });
  }
}

async function handleHealthCheck(sendResponse) {
  await checkApiHealth();
  sendResponse({
    success: true,
    data: {
      extensionActive: extensionState.isActive,
      apiHealth: extensionState.apiHealth,
      currentTab: extensionState.currentTab,
      version: chrome.runtime.getManifest().version
    }
  });
}

async function handleAnalyzeScreen(data, sendResponse) {
  try {
    const preferences = await getPreferences();
    const url = `${preferences.apiEndpoint || CONFIG.API_BASE_URL}/screen/analyze`;
    
    const formData = new FormData();
    formData.append('image_data', data.imageData);
    formData.append('url', data.url);
    formData.append('timestamp', data.timestamp.toString());
    
    const response = await fetch(url, {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    
    if (response.ok) {
      sendResponse({ success: true, data: result });
    } else {
      sendResponse({ success: false, error: result.error || 'Screen analysis failed' });
    }
  } catch (error) {
    console.error('Screen analysis failed:', error);
    sendResponse({ success: false, error: error.message });
  }
}

async function handleAnalyzeAssistanceNeed(data, sendResponse) {
  try {
    const preferences = await getPreferences();
    const url = `${preferences.apiEndpoint || CONFIG.API_BASE_URL}/screen/assistance-need`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    const result = await response.json();
    
    if (response.ok) {
      sendResponse({ success: true, data: result });
    } else {
      sendResponse({ success: false, error: result.error || 'Assistance analysis failed' });
    }
  } catch (error) {
    console.error('Assistance analysis failed:', error);
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * Storage Utilities
 */

async function getPreferences() {
  const result = await chrome.storage.local.get(CONFIG.STORAGE_KEYS.USER_PREFERENCES);
  return result[CONFIG.STORAGE_KEYS.USER_PREFERENCES] || {};
}

async function getCache() {
  const result = await chrome.storage.local.get(CONFIG.STORAGE_KEYS.CACHE);
  return result[CONFIG.STORAGE_KEYS.CACHE] || {};
}

/**
 * Cleanup old cache entries periodically
 */
setInterval(async () => {
  try {
    const cache = await getCache();
    const now = Date.now();
    let cleaned = false;
    
    for (const key in cache) {
      if (now - cache[key].timestamp > CONFIG.CACHE_DURATION) {
        delete cache[key];
        cleaned = true;
      }
    }
    
    if (cleaned) {
      await chrome.storage.local.set({
        [CONFIG.STORAGE_KEYS.CACHE]: cache
      });
      console.log('Cache cleaned');
    }
  } catch (error) {
    console.error('Cache cleanup failed:', error);
  }
}, CONFIG.CACHE_DURATION);

console.log('LeetCoach background script loaded');
