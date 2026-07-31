import os
import json
from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic
from sheet_tools import search_jobs, mark_status

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

TOOLS = [
    {
        "name": "search_jobs",
        "description": "Search saved job postings, optionally filtered by application status, minimum relevance score, or company name. Returns results sorted by relevance score, highest first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filter by status, e.g. 'not applied', 'applied', 'interviewing'"},
                "min_score": {"type": "integer", "description": "Minimum relevance score, 1-10"},
                "company": {"type": "string", "description": "Filter by company name (partial match)"},
                "limit": {"type": "integer", "description": "Max number of results to return, default 10"},
            },
        },
    },
    {
        "name": "mark_status",
        "description": "Update the application status of a specific job posting, identified by its id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "The unique id of the job posting"},
                "new_status": {"type": "string", "description": "The new status, e.g. 'applied', 'interviewing', 'rejected'"},
            },
            "required": ["job_id", "new_status"],
        },
    },
]

def run_tool(name, tool_input):
    """Dispatches a tool call by name to the actual Python function."""
    if name == "search_jobs":
        return search_jobs(**tool_input)
    if name == "mark_status":
        success = mark_status(**tool_input)
        return {"success": success}
    return {"error": f"unknown tool: {name}"}

def ask_agent(user_message):
    messages = [{"role": "user", "content": user_message}]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=TOOLS,
        messages=messages,
    )

    while response.stop_reason == "tool_use":
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  [Claude is calling: {block.name}({block.input})]")
                result = run_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

        messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

    final_text = "".join(block.text for block in response.content if block.type == "text")
    return final_text

if __name__ == "__main__":
    print("Job Search Agent (test mode) — type a request, or 'quit' to exit\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("quit", "exit"):
            break
        answer = ask_agent(user_input)
        print(f"\nAgent: {answer}\n")