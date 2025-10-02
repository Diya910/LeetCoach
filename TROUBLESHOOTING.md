# LeetCoach Troubleshooting Guide

## Common Issues and Solutions

### 1. Screen Sharing Keeps Prompting

**Problem**: The extension keeps asking to share screen repeatedly.

**Solution**: 
- The screen monitor frequency has been reduced from 10 seconds to 30 seconds
- Stuck detection thresholds have been increased to reduce false positives
- Make sure you're on a LeetCode problem page for the extension to work properly

### 2. "Get Hint" Not Working

**Problem**: Clicking "Get Hint" shows no response or error messages.

**Possible Causes & Solutions**:

#### A. Backend Not Running
```bash
# Make sure the backend is running
cd LeetCoach
python start_backend.py
```

#### B. API Keys Not Configured
1. Copy the example environment file:
   ```bash
   cd LeetCoach/backend
   copy env.example .env
   ```

2. Edit `.env` file and add your API keys:
   ```
   # For OpenAI (recommended)
   DEFAULT_LLM_PROVIDER=openai
   OPENAI_API_KEY=your_actual_api_key_here
   
   # For AWS Bedrock
   DEFAULT_LLM_PROVIDER=bedrock
   AWS_ACCESS_KEY_ID=your_aws_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret
   
   # For Google Gemini
   DEFAULT_LLM_PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_key
   ```

#### C. CORS Issues
Make sure your `.env` file includes:
```
CORS_ORIGINS=["chrome-extension://*", "http://localhost:3000", "https://leetcode.com"]
```

### 3. Tesseract OCR Errors

**Problem**: "tesseract is not installed or it's not in your PATH" error.

**Solution**:
1. Run the setup script:
   ```bash
   python setup_tesseract.py
   ```

2. Or install manually:
   - Download Tesseract from: https://github.com/UB-Mannheim/tesseract/releases
   - Install it (default path: `C:\Program Files\Tesseract-OCR\`)
   - Add to PATH or the extension will auto-detect common paths

### 4. File Size Limit Errors

**Problem**: "Part exceeded maximum size of 1024KB" error.

**Solution**: 
- The extension now automatically compresses large images
- Images are resized to max 1920x1080 and compressed to JPEG quality 70%
- This should resolve the 1024KB limit issue

### 5. 401 Unauthorized Errors

**Problem**: Authentication failed errors in the logs.

**Solutions**:
1. **Check API Keys**: Make sure your `.env` file has valid API keys
2. **Check Provider**: Ensure `DEFAULT_LLM_PROVIDER` matches your configured keys
3. **Test API Keys**: Verify your API keys work independently

### 6. Extension Not Loading on LeetCode

**Problem**: The LeetCoach panel doesn't appear on LeetCode pages.

**Solutions**:
1. **Refresh the page** after installing the extension
2. **Check if you're on a problem page**: The extension only works on LeetCode problem pages
3. **Check browser console** for errors (F12 → Console)
4. **Reload the extension** in Chrome Extensions page

### 7. Backend Connection Issues

**Problem**: Extension can't connect to the backend.

**Solutions**:
1. **Check if backend is running**: Visit http://localhost:8000/docs
2. **Check firewall**: Make sure port 8000 is not blocked
3. **Check CORS settings**: Ensure CORS_ORIGINS includes chrome-extension://*

## Quick Diagnostic Steps

### 1. Check Backend Health
```bash
curl http://localhost:8000/api/health
```
Should return: `{"status": "healthy"}`

### 2. Check Extension Logs
1. Open Chrome DevTools (F12)
2. Go to Console tab
3. Look for LeetCoach-related errors

### 3. Check Backend Logs
Look at the terminal where you started the backend for error messages.

### 4. Test API Keys
```bash
# Test OpenAI
curl -H "Authorization: Bearer YOUR_OPENAI_KEY" https://api.openai.com/v1/models

# Test with your backend
curl -X POST http://localhost:8000/api/agents/hint \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "problem": {"title": "Test", "description": "Test"}, "hint_level": 1}'
```

## Environment Setup

### Required Files
1. `.env` file in `LeetCoach/backend/` with API keys
2. Tesseract OCR installed
3. Python dependencies installed

### Dependencies
```bash
cd LeetCoach/backend
pip install -r requirements.txt
```

### Chrome Extension
1. Load the extension from `LeetCoach/chrome_extension/` folder
2. Make sure it's enabled
3. Refresh LeetCode pages

## Still Having Issues?

1. **Check the logs** in both browser console and backend terminal
2. **Verify all dependencies** are installed correctly
3. **Test with a simple LeetCode problem** first
4. **Make sure you're using a supported browser** (Chrome/Edge)

## Getting Help

If you're still having issues:
1. Check the browser console for specific error messages
2. Check the backend logs for API errors
3. Verify your API keys are working
4. Make sure all dependencies are installed

The most common issue is missing or incorrect API keys in the `.env` file.
