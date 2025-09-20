# TaskSync

A collaborative task management application with real-time video calls and AI-powered task extraction.

## Environment Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your actual API keys and configuration:
   - `FLASK_SECRET_KEY`: A secure secret key for Flask sessions
   - `ASSEMBLYAI_API_KEY`: Your AssemblyAI API key for audio transcription
   - `CEREBRAS_API_KEY`: Your Cerebras API key for AI interactions
   - `MONGO_URI`: Your MongoDB connection string
   - `GITHUB_TOKEN`: (Optional) Your GitHub personal access token

## Installation

1. Create and activate a virtual environment:
   ```bash
   python -m venv tasksync_venv
   source tasksync_venv/bin/activate  # On Windows: tasksync_venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables (see Environment Setup above)

4. Run the application:
   ```bash
   python app.py
   ```

## Important Security Notes

- Never commit your `.env` file to version control
- Use strong, unique API keys and secrets
- Regularly rotate your API keys
- The `.env.example` file shows the required environment variables but contains placeholder values