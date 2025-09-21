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





## Inspiration
With TaskSync, we wanted to create a way for teams to collaborate, split up work, and track progress of assignments effortlessly without the need for endless chat threads and complexity of heavy project management tools. The idea was to create something fast, efficient, and collaborative that facilitates communication between school assignments, work projects, or anyone working together on a shared goal. 

## What it does
TaskSync lets people create rooms, invite members, and sync tasks in real time. It allows the host/higher up to create assignments with ease and convenience, especially when the groups become significantly large. Each room acts as a shared workspace, letting members add, update, and track certain tasks while staying aligned with the rest of the team. Its simple, easy to learn, and designed to break down the hardships of working together so that teams can focus on getting things done. 

## How we built it
We used Flask for the backend API, React for the front end, and MongoDB for our database. Room and Task data are stored in a database for longevity and we used Flask-CORS for cross platform functionality. We created our own Video Calling Software that transcribed speech stated by each user in the meeting. Then, TaskSync passes the transcriptions through Cerebras AI to summarize and create tasks for each user depending on what was stated through the meeting. TaskSync also integrates GitHub by assigning and creating branches and repositories for each person to work on for a given assignment.
## Challenges we ran into
Initially, integrating with Zoom, Google Meets, and Microsoft Teams felt more viable due to the large amount of people already using these softwares everyday. However, integrating these softwares came with costs that we could not pay for at the moment. This lead us to creating our own software for Video Meetings.

## Accomplishments that we're proud of
We are really proud of the integration of many softwares and individuality in our project. Our project uses Github, Gmail, and our own Video Meeting Software. In our project, we use Github OAuth and API to track users' updates and contributions to team repositories to see how much progress they've made on given assignments. On top of this we use the Github API to create and assign repositories and branches to certain users for the assignments they are assigned.
## What we learned
From this project, we learned how to push past and resolve lots of network issues regarding connections with MongoDB and our backend Flask APIs.

## What's next for TaskSync
In the future, we plan on adding priority dates, calendar updates, and a mobile application. 
