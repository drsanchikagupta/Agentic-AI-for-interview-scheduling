import anthropic
import json
import os
from datetime import datetime, timedelta

# Initialize Anthropic Client
client = anthropic.Anthropic()

# --- Tool Definitions ---
tools = [
    {
        "name": "get_calendar_availability",
        "description": "Check the recruiter's availability for a specific date or general week.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_date": {"type": "string", "description": "ISO format date, e.g., '2026-04-22'"}
            },
            "required": ["query_date"]
        }
    },
    {
        "name": "send_email",
        "description": "Send a formal email to the candidate to propose times or escalate to a human.",
        "input_schema": {
            "type": "object",
            "properties": {
                "recipient": {"type": "string"},
                "body": {"type": "string"},
                "subject": {"type": "string"}
            },
            "required": ["recipient", "body", "subject"]
        }
    }
]

# --- Tool Implementations (Simulated for Local Run) ---
def get_calendar_availability(query_date):
    # Simulated logic: Recruiter is busy today but free April 27-28
    if "2026-04-22" in query_date:
        return {"status": "unavailable", "reason": "Existing interview conflict"}
    return {"status": "available", "slots": ["12:00 PM", "1:30 PM", "3:00 PM"]}

def send_email(recipient, body, subject):
    return {"status": "sent", "to": recipient, "timestamp": datetime.now().isoformat()}

def run_tool(name, inputs):
    if name == "get_calendar_availability":
        return get_calendar_availability(inputs["query_date"])
    elif name == "send_email":
        return send_email(inputs["recipient"], inputs["body"], inputs["subject"])
    return {"error": f"Unknown tool: {name}"}

# --- The Agentic System Prompt ---
SYSTEM_PROMPT = """You are an Interview Scheduler Agent. Your goal is to find common available times.
- Log your reasoning inside <thought> tags.
- HARD LIMIT: You must conclude in 10 steps.
- ESCALATION RULES: 
    1. If a candidate suggests a time > 15 days out, stop and escalate to human.
    2. If no response is detected within 24 hours, stop and escalate to human.
    3. Do not guess or make assumptions. 
- FORMAT: Output tool calls clearly or provide a final 'Escalated' or 'Resolved' summary."""

def scheduling_agent(user_request):
    print(f"\n🚀 Starting Agentic Workflow...")
    messages = [{"role": "user", "content": user_request}]
    max_steps = 10
    step = 0

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620", # Updated for 2026 compatibility
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        tools=tools,
        messages=messages,
    )

    while response.stop_reason == "tool_use" and step < max_steps:
        step += 1
        print(f"\n--- Step {step}/10 ---")
        
        tool_results = []
        for block in response.content:
            if hasattr(block, "text") and block.text:
                print(f"💭 Thought: {block.text}")
            
            if block.type == "tool_use":
                print(f"🔧 Action: [{block.name}]")
                result = run_tool(block.name, block.input)
                print(f"👁️ Observation: {json.dumps(result)}")
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

    final_text = "".join([b.text for b in response.content if hasattr(b, "text")])
    print(f"\n✅ FINAL OUTCOME: {final_text}")
    if step >= max_steps:
        print("⚠️ HARD STOP: Maximum steps reached. Escalating to human.")

# --- Execution ---
if __name__ == "__main__":
    # Test Scenario 1: Conflict and Re-scheduling
    scheduling_agent("Candidate Sanchika wants to meet on 2026-04-22 at 1PM. If busy, find next available.")

    # Test Scenario 2: Escalation (Simulated via prompt context)
    # scheduling_agent("The candidate just replied they can only meet in June (45 days out).")
