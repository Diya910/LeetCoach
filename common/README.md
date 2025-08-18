# LeetCoach - AI-Powered Coding Assistant

A modular AI-powered coding assistant that integrates with LeetCode to provide intelligent hints, code optimization, complexity analysis, and interview preparation.

## 🚀 Features

### Core Capabilities
- **Progressive Hints**: Get hints at 5 different levels of detail
- **Code Optimization**: Receive suggestions to improve time/space complexity and readability
- **Complexity Analysis**: Detailed time and space complexity analysis with explanations
- **Solution Explanations**: Comprehensive explanations with multiple approaches
- **Interview Questions**: Generate counter questions and deep technical questions
- **Personalization**: Learns from your coding patterns and preferences

### Technical Highlights
- **Multi-Agent Architecture**: Specialized AI agents for different tasks
- **Dual LLM Support**: OpenAI GPT-4 and AWS Bedrock Claude
- **Vector Database**: Pinecone for long-term user context storage
- **Chrome Extension**: Seamless integration with LeetCode
- **RESTful API**: FastAPI backend with comprehensive endpoints

## 🏗️ Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Chrome Extension  │    │   FastAPI Backend   │    │   Vector Database   │
│                     │    │                     │    │                     │
│ ┌─────────────────┐ │    │ ┌─────────────────┐ │    │ ┌─────────────────┐ │
│ │  Content Script │ │◄──►│ │   Orchestrator  │ │◄──►│ │    Pinecone     │ │
│ └─────────────────┘ │    │ └─────────────────┘ │    │ └─────────────────┘ │
│ ┌─────────────────┐ │    │ ┌─────────────────┐ │    │                     │
│ │ Background Script│ │    │ │  6 Specialized  │ │    │                     │
│ └─────────────────┘ │    │ │     Agents      │ │    │                     │
│ ┌─────────────────┐ │    │ └─────────────────┘ │    │                     │
│ │   Popup UI      │ │    │ ┌─────────────────┐ │    │                     │
│ └─────────────────┘ │    │ │  LLM Providers  │ │    │                     │
└─────────────────────┘    │ │ (OpenAI/Bedrock)│ │    │                     │
                           │ └─────────────────┘ │    │                     │
                           └─────────────────────┘    └─────────────────────┘
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Node.js (for Chrome extension development)
- API keys for OpenAI and/or AWS Bedrock
- Pinecone account (optional, for user personalization)

### Backend Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/leetcoach.git
   cd leetcoach
   ```

2. **Install Python dependencies**:
   ```bash
   cd backend/app
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Start the backend server**:
   ```bash
   python main.py
   ```

   The server will be available at `http://localhost:8000`

### Chrome Extension Setup

1. **Open Chrome Extensions**:
   - Navigate to `chrome://extensions/`
   - Enable "Developer mode"

2. **Load the extension**:
   - Click "Load unpacked"
   - Select the `chrome_extension/` directory

3. **Verify installation**:
   - The LeetCoach icon should appear in your extensions toolbar
   - Navigate to any LeetCode problem to test

## 🎯 Usage

### Getting Started

1. **Navigate to LeetCode**: Open any problem on leetcode.com
2. **Activate Extension**: The LeetCoach panel will automatically appear
3. **Choose Your Action**:
   - **Hints**: Get progressive hints to guide your thinking
   - **Optimize**: Improve your existing code
   - **Analyze**: Understand complexity of your solution
   - **Solutions**: See comprehensive solution explanations
   - **Questions**: Practice with interview-style questions

### Example Workflow

1. **Read the Problem**: Start with any LeetCode problem
2. **Get a Hint**: If stuck, request a Level 1-2 hint
3. **Write Your Solution**: Implement your approach
4. **Optimize**: Use the optimization agent to improve your code
5. **Analyze Complexity**: Understand the time/space trade-offs
6. **Practice Questions**: Generate interview questions for deeper understanding

## 🔧 Configuration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# AWS Bedrock Configuration (optional)
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1

# Pinecone Configuration (optional)
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment_here

# Application Settings
DEFAULT_LLM_PROVIDER=openai
LOG_LEVEL=INFO
API_PORT=8000
```

### User Preferences

- **Preferred Language**: Python, JavaScript, Java, C++, etc.
- **Explanation Style**: Brief, Detailed, or Comprehensive
- **Auto-activation**: Automatically show panel on LeetCode
- **Focus Areas**: Customize optimization priorities

## 📚 API Documentation

### Core Endpoints

- `POST /api/hint` - Get progressive hints
- `POST /api/optimize` - Optimize existing code
- `POST /api/complexity` - Analyze time/space complexity
- `POST /api/solution` - Get comprehensive solutions
- `POST /api/counter-questions` - Generate clarifying questions
- `POST /api/deep-questions` - Generate advanced technical questions

### User Management

- `GET /api/user/{user_id}/preferences` - Retrieve user preferences
- `POST /api/user/{user_id}/preferences` - Update preferences
- `GET /api/user/{user_id}/history` - Get interaction history

Full API documentation is available at `http://localhost:8000/docs` when the server is running.

## 🧪 Development

### Running Tests

```bash
# Backend tests
cd backend/app
pytest tests/

# Extension tests (if applicable)
cd chrome_extension
npm test
```

### Development Tools

- **Streamlit Admin**: `streamlit run backend/streamlit_app/app.py`
- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/api/health`

### Code Quality

```bash
# Python formatting
black backend/app/
isort backend/app/
flake8 backend/app/

# JavaScript formatting
cd chrome_extension
npx prettier --write .
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow existing code structure and patterns
- Add comprehensive tests for new features
- Update documentation for API changes
- Use type hints in Python code
- Follow semantic commit messages

## 📊 Monitoring & Analytics

- **Request/Response Timing**: Track API performance
- **Success Rates**: Monitor agent reliability
- **Usage Patterns**: Understand user behavior
- **Error Tracking**: Comprehensive error reporting

## 🔒 Security

- **API Key Management**: Secure environment variable handling
- **Input Validation**: Pydantic schema validation
- **CORS Configuration**: Restricted to extension and localhost
- **Rate Limiting**: Configurable request limits
- **Data Privacy**: User data encrypted and optionally stored

## 📈 Roadmap

### Upcoming Features
- [ ] Multi-language solution generation
- [ ] Advanced debugging assistance
- [ ] Code review and best practices
- [ ] Contest mode for competitive programming
- [ ] Team collaboration features
- [ ] Mobile app integration

### Technical Improvements
- [ ] Caching layer for faster responses
- [ ] Advanced context understanding
- [ ] Custom model fine-tuning
- [ ] Real-time collaboration
- [ ] Offline mode support

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Anthropic for Claude via AWS Bedrock
- Pinecone for vector database services
- LeetCode for providing the platform
- The open-source community for inspiration and tools

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/leetcoach/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/leetcoach/discussions)
- **Email**: support@leetcoach.dev

---

**Happy Coding! 🚀**
