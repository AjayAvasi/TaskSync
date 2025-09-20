TRANSCRIPT_ANALYSIS_PROMPT = """
Read the following transcript of a team meeting. Get familiar with the team members and their roles. Then, based on the discussion, identify and assign tasks to each team member. Ensure that each task is specific, actionable, and has a clear deadline. If a task is already assigned to someone in the transcript, keep that assignment. If not, assign it based on the team member's role and expertise.
The tasks should alawys be assigned by the team manager if they are mentioned in the transcript.

The output should be a JSON array of tasks with the following structure:
[
{
"task_title": "Title of the task",
"task_description": "Detailed description of the task",
"assignee": "Name of the team member assigned to the task",
"assignee_github": "GitHub username of the assignee",
"due_date": "Due date in YYYY-MM-DD format is available or leave blank"
},
...
]

Do not assign tasks to the manager. Only assign tasks to employees. If a task is mentioned without an assignee, assign it to the most relevant employee based on their role. If no suitable employee is available, do not assign the task.
"""

COMMIT_ANALYSIS_PROMPT = """
You are an expert project manager. Based on the following commit diffs, provide a concise summary of the progress made on the task titled "{task_title}" with the description "{task_description}".
If the commits indicate that the task is completed, state that the task is completed. If the commits show partial progress, describe what has been accomplished and what remains to be done. If there are no relevant changes, state that no progress has been made.
The response should be in JSON format as follows:
{{
"task_title": "Title of the task",
"progress_summary": "Concise summary of the progress made on the task",
"progress": "some progress out of 100%"
}}
"""