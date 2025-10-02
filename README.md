# LeetCoach - AI-Powered LeetCode Assistant

LeetCoach is a comprehensive Chrome extension that provides intelligent AI assistance for LeetCode problem solving. It features screen monitoring, dynamic assistance timing, multi-provider AI support, and a rich chat interface.

## 🚀 Features

### Core Features
- **Screen Monitoring**: Automatically detects when you're stuck and offers assistance
- **Configurable Assistance Timer**: Set assistance delay from 5 seconds to 5 minutes
- **Multi-Provider AI Support**: Works with OpenAI, AWS Bedrock, and Google Gemini
- **Floating Chat Interface**: Access all features through an intuitive chat window
- **Real-time Code Analysis**: Detects errors and provides optimization suggestions
- **Complexity Analysis**: Analyzes time and space complexity of your solutions
- **Edge Case Detection**: Identifies potential edge cases and interview questions
- **Progressive Hints**: Provides hints at different levels of detail
- **Interview Preparation**: Generates interview-style questions and scenarios

### AI Capabilities
- **Dynamic Agent Routing**: Intelligently selects the best AI agent for your needs
- **Context-Aware Assistance**: Understands your current problem and code state
- **Multi-Language Support**: Works with Python, JavaScript, Java, C++, and more
- **Code Optimization**: Suggests improvements for performance and readability
- **Solution Explanations**: Provides detailed explanations of different approaches

## 🛠️ Installation

### Prerequisites
- Chrome browser (version 88+)
- Python 3.8+ (for backend)
- At least one AI provider API key (OpenAI, AWS Bedrock, or Google Gemini)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd LeetCoach
   ```

2. **Install Python dependencies**
   ```bash
   cd backend
   pip install -r app/requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the `backend` directory:
   ```env
   # Choose your preferred AI provider
   DEFAULT_LLM_PROVIDER=bedrock  # or openai, gemini
   
   # OpenAI Configuration (if using OpenAI)
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4-turbo-preview
   
   # AWS Bedrock Configuration (if using Bedrock)
   AWS_ACCESS_KEY_ID=your_aws_access_key_here
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
   AWS_REGION=us-east-1
   BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
   
   # Google Gemini Configuration (if using Gemini)
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-1.5-pro
   
   # Optional: Pinecone for vector storage
   PINECONE_API_KEY=your_pinecone_key_here
   PINECONE_ENVIRONMENT=your_pinecone_env_here
   PINECONE_INDEX_NAME=leetcoach-user-context
   
   # Application settings
   API_HOST=0.0.0.0
   API_PORT=8000
   LOG_LEVEL=INFO
   ```

4. **Start the backend server**
   ```bash
   cd backend
   python -m app.main
   ```
   
   The API will be available at `http://localhost:8000`

### Chrome Extension Setup

1. **Load the extension**
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select the `chrome_extension` folder

2. **Configure the extension**
   - Click on the LeetCoach extension icon
   - Set your preferred language and assistance settings
   - The extension will automatically detect available AI providers

## 🎯 Usage

### Basic Usage

1. **Navigate to a LeetCode problem**
   - Go to any LeetCode problem page
   - The extension will automatically detect the problem

2. **Access the chat interface**
   - Click the LeetCoach icon in your browser toolbar
   - Or wait for the assistance notification to appear

3. **Get help**
   - Use the chat interface to ask questions
   - Click on different tabs for specific features:
     - **Assistant**: General AI chat
     - **Hints**: Progressive hints for the problem
     - **Optimize**: Code optimization suggestions
     - **Complexity**: Time/space complexity analysis
     - **Questions**: Interview-style questions
     - **Settings**: Configure your preferences

### Advanced Features

#### Screen Monitoring
- The extension automatically monitors your screen for signs that you're stuck
- Adjust the assistance delay in settings (5 seconds to 5 minutes)
- Get proactive notifications when help is needed

#### Multi-Provider AI
- The extension automatically uses the best available AI provider
- Switch between providers in settings if needed
- Fallback to alternative providers if one fails

#### Code Analysis
- Real-time error detection in your code
- Automatic complexity analysis
- Optimization suggestions based on your current solution

## ⚙️ Configuration

### User Preferences

Access settings through the chat interface:

- **Assistance Delay**: How long to wait before offering help (5s - 5min)
- **Preferred Language**: Your coding language preference
- **Explanation Style**: Brief, detailed, or comprehensive
- **API Provider**: Auto-detect, OpenAI, Bedrock, or Gemini
- **Auto-activate**: Automatically start monitoring on LeetCode pages

### AI Provider Setup

#### OpenAI
1. Get an API key from [OpenAI](https://platform.openai.com/api-keys)
2. Add `OPENAI_API_KEY` to your `.env` file
3. Set `DEFAULT_LLM_PROVIDER=openai`

#### AWS Bedrock
1. Set up AWS credentials
2. Add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` to your `.env` file
3. Set `DEFAULT_LLM_PROVIDER=bedrock`

#### Google Gemini
1. Get an API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add `GEMINI_API_KEY` to your `.env` file
3. Set `DEFAULT_LLM_PROVIDER=gemini`

## 🔧 Development

### Project Structure
```
LeetCoach/
├── backend/
│   ├── app/
│   │   ├── agents/          # AI agent implementations
│   │   ├── providers/       # LLM provider clients
│   │   ├── routers/         # API endpoints
│   │   └── utils/           # Utility functions
│   └── requirements.txt
├── chrome_extension/
│   ├── content.js           # Main content script
│   ├── background.js        # Background service worker
│   ├── chat-interface.js    # Chat UI implementation
│   ├── screen-monitor.js    # Screen monitoring service
│   └── styles.css           # Extension styles
└── README.md
```

### Adding New Features

1. **Backend**: Add new endpoints in `routers/`
2. **Agents**: Create new AI agents in `agents/`
3. **Frontend**: Add UI components in the Chrome extension files
4. **Integration**: Update the orchestrator to route to new agents

### Testing

```bash
# Backend tests
cd backend
pytest

# Extension testing
# Load the extension in Chrome and test on LeetCode pages
```

## 🐛 Troubleshooting

### Common Issues

1. **Extension not loading**
   - Check that all files are in the correct directory
   - Ensure manifest.json is valid
   - Check Chrome console for errors

2. **API connection failed**
   - Verify the backend server is running
   - Check your API keys are correct
   - Ensure CORS settings allow the extension

3. **Screen monitoring not working**
   - Grant screen capture permissions
   - Check that you're on a LeetCode problem page
   - Verify the extension is active

4. **AI responses not working**
   - Check your API provider configuration
   - Verify API keys are valid and have sufficient credits
   - Check backend logs for errors

### Debug Mode

Enable debug logging by setting `LOG_LEVEL=DEBUG` in your `.env` file.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Open an issue on GitHub
- Review the backend logs for error details

## 🔮 Roadmap

- [ ] Support for more programming languages
- [ ] Integration with other coding platforms
- [ ] Advanced code visualization
- [ ] Collaborative features
- [ ] Mobile app companion
- [ ] Custom AI model training

---

**Happy Coding! 🚀**

LeetCoach is designed to make your LeetCode journey more efficient and educational. Whether you're preparing for technical interviews or just want to improve your problem-solving skills, LeetCoach is here to help!