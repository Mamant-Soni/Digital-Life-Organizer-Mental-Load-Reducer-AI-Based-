"""
Digital Life Organizer + Mental Load Reducer
AI-powered personal assistant using Claude API

Requirements:
    pip install anthropic colorama

Usage:
    python digital_life_organizer.py
"""

import anthropic
import json
import os
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init(autoreset=True)

# ─────────────────────────────────────────────
#  DATA STORAGE  (saved to a local JSON file)
# ─────────────────────────────────────────────

DATA_FILE = "my_life_data.json"

def load_data():
    """Load saved tasks, notes, and goals from file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"tasks": [], "goals": [], "notes": [], "mood_log": []}

def save_data(data):
    """Save everything to file so it persists between sessions."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ─────────────────────────────────────────────
#  TASK MANAGER
# ─────────────────────────────────────────────

def add_task(data, title, priority="medium", category="personal"):
    """Add a new task to the list."""
    task = {
        "id": len(data["tasks"]) + 1,
        "title": title,
        "priority": priority,       # low / medium / high
        "category": category,       # personal / work / health / family
        "done": False,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    data["tasks"].append(task)
    save_data(data)
    print(Fore.GREEN + f"\n✓ Task added: '{title}' [{priority} priority]")

def complete_task(data, task_id):
    """Mark a task as done."""
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["done"] = True
            save_data(data)
            print(Fore.GREEN + f"\n✓ Task #{task_id} marked as done!")
            return
    print(Fore.RED + f"\n✗ Task #{task_id} not found.")

def show_tasks(data):
    """Display all pending tasks."""
    pending = [t for t in data["tasks"] if not t["done"]]
    if not pending:
        print(Fore.YELLOW + "\n  No pending tasks. You're all caught up!")
        return

    print(Fore.CYAN + "\n── YOUR TASKS ─────────────────────────────")
    priority_colors = {"high": Fore.RED, "medium": Fore.YELLOW, "low": Fore.GREEN}
    for task in pending:
        color = priority_colors.get(task["priority"], Fore.WHITE)
        print(f"  [{task['id']}] {color}{task['title']}{Style.RESET_ALL}"
              f"  ({task['category']}) — {task['priority']} priority")
    print(Fore.CYAN + "────────────────────────────────────────────")

# ─────────────────────────────────────────────
#  GOAL TRACKER
# ─────────────────────────────────────────────

def add_goal(data, goal_text, deadline=""):
    """Add a life goal."""
    goal = {
        "id": len(data["goals"]) + 1,
        "goal": goal_text,
        "deadline": deadline,
        "progress": 0,            # 0–100 percent
        "created": datetime.now().strftime("%Y-%m-%d")
    }
    data["goals"].append(goal)
    save_data(data)
    print(Fore.GREEN + f"\n✓ Goal saved: '{goal_text}'")

def show_goals(data):
    """Display all goals with progress bars."""
    if not data["goals"]:
        print(Fore.YELLOW + "\n  No goals yet. Add one to get started!")
        return

    print(Fore.CYAN + "\n── YOUR GOALS ─────────────────────────────")
    for g in data["goals"]:
        bar_filled = int(g["progress"] / 10)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)
        deadline_str = f"  (by {g['deadline']})" if g["deadline"] else ""
        print(f"  [{g['id']}] {g['goal']}{deadline_str}")
        print(f"       [{bar}] {g['progress']}%")
    print(Fore.CYAN + "────────────────────────────────────────────")

# ─────────────────────────────────────────────
#  MOOD LOGGER
# ─────────────────────────────────────────────

def log_mood(data, mood, note=""):
    """Log today's mood (1–10 scale)."""
    entry = {
        "mood": mood,
        "note": note,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    data["mood_log"].append(entry)
    save_data(data)

    emoji = "😊" if mood >= 7 else "😐" if mood >= 4 else "😞"
    print(Fore.GREEN + f"\n✓ Mood logged: {mood}/10 {emoji}")

def show_mood_summary(data):
    """Show average mood over recent logs."""
    if not data["mood_log"]:
        print(Fore.YELLOW + "\n  No mood entries yet.")
        return
    recent = data["mood_log"][-7:]          # last 7 entries
    avg = sum(e["mood"] for e in recent) / len(recent)
    print(Fore.CYAN + f"\n── MOOD SUMMARY (last {len(recent)} entries) ──")
    for entry in recent:
        bar = "■" * entry["mood"] + "□" * (10 - entry["mood"])
        print(f"  {entry['date']}  [{bar}] {entry['mood']}/10"
              + (f"  — {entry['note']}" if entry["note"] else ""))
    print(f"\n  Average mood: {avg:.1f}/10")
    print(Fore.CYAN + "────────────────────────────────────────────")

# ─────────────────────────────────────────────
#  AI CHATBOT  (Claude API)
# ─────────────────────────────────────────────

def build_system_prompt(data):
    """Build a system prompt that includes the user's current data."""
    pending_tasks = [t for t in data["tasks"] if not t["done"]]
    recent_moods  = data["mood_log"][-3:] if data["mood_log"] else []
    avg_mood = (
        sum(e["mood"] for e in recent_moods) / len(recent_moods)
        if recent_moods else None
    )

    context = f"""You are a warm, supportive AI life coach and personal organizer.
Your role is to help reduce mental load, organize tasks, and support emotional wellbeing.

Here is the user's current data:

PENDING TASKS ({len(pending_tasks)} total):
{json.dumps(pending_tasks, indent=2) if pending_tasks else "None"}

GOALS:
{json.dumps(data['goals'], indent=2) if data['goals'] else "None"}

RECENT MOOD:
{f"Average: {avg_mood:.1f}/10 based on {len(recent_moods)} recent entries" if avg_mood else "No mood data yet"}

Your behaviour guidelines:
- Be concise, warm, and practical
- When the user seems stressed, acknowledge it before giving advice
- Help prioritize tasks when asked
- Suggest healthy habits and mental load reduction strategies
- If mood is low (below 5), gently check in on wellbeing
- You can add, suggest, or summarize tasks and goals in conversation
- Keep responses under 150 words unless the user asks for more detail
"""
    return context

def chat_with_ai(data, conversation_history):
    """Send a message to Claude and get a response."""
    client = anthropic.Anthropic()

    system_prompt = build_system_prompt(data)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system_prompt,
        messages=conversation_history
    )
    return response.content[0].text

# ─────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────

def print_banner():
    print(Fore.CYAN + """
╔══════════════════════════════════════════════╗
║   🧠  DIGITAL LIFE ORGANIZER                ║
║       Mental Load Reducer · AI Powered      ║
╚══════════════════════════════════════════════╝
""")

def print_menu():
    print(Fore.CYAN + "\n── MENU ────────────────────────────────────")
    print("  1. Chat with AI coach")
    print("  2. View my tasks")
    print("  3. Add a task")
    print("  4. Complete a task")
    print("  5. View my goals")
    print("  6. Add a goal")
    print("  7. Log my mood")
    print("  8. View mood summary")
    print("  0. Exit")
    print(Fore.CYAN + "────────────────────────────────────────────")

def main():
    print_banner()
    data = load_data()
    conversation_history = []   # keeps track of the chat session

    print(Fore.YELLOW + "  Tip: Start by chatting with your AI coach (option 1)")
    print(Fore.YELLOW + "  or add your first task (option 3).")

    while True:
        print_menu()
        choice = input(Fore.WHITE + "\n  Enter choice: ").strip()

        # ── AI CHAT ──────────────────────────────
        if choice == "1":
            print(Fore.CYAN + "\n── AI COACH (type 'back' to return to menu) ──")
            print(Fore.YELLOW + "  Ask anything: prioritize tasks, reduce stress,")
            print(Fore.YELLOW + "  plan your week, or just vent!")
            print()

            while True:
                user_input = input(Fore.WHITE + "You: ").strip()
                if user_input.lower() in ("back", "exit", "quit", ""):
                    break

                conversation_history.append({"role": "user", "content": user_input})

                print(Fore.YELLOW + "\nAI Coach: ", end="", flush=True)
                try:
                    reply = chat_with_ai(data, conversation_history)
                    print(Fore.GREEN + reply)
                    conversation_history.append({"role": "assistant", "content": reply})
                except Exception as e:
                    print(Fore.RED + f"Error connecting to AI: {e}")
                    print(Fore.YELLOW + "Make sure your ANTHROPIC_API_KEY is set.")
                    conversation_history.pop()
                print()

        # ── VIEW TASKS ───────────────────────────
        elif choice == "2":
            show_tasks(data)

        # ── ADD TASK ─────────────────────────────
        elif choice == "3":
            title = input("\n  Task title: ").strip()
            if not title:
                print(Fore.RED + "  Task title cannot be empty.")
                continue
            print("  Priority (low / medium / high) [medium]: ", end="")
            priority = input().strip().lower() or "medium"
            print("  Category (personal / work / health / family) [personal]: ", end="")
            category = input().strip().lower() or "personal"
            add_task(data, title, priority, category)

        # ── COMPLETE TASK ────────────────────────
        elif choice == "4":
            show_tasks(data)
            try:
                task_id = int(input("\n  Enter task ID to mark done: ").strip())
                complete_task(data, task_id)
            except ValueError:
                print(Fore.RED + "  Please enter a valid number.")

        # ── VIEW GOALS ───────────────────────────
        elif choice == "5":
            show_goals(data)

        # ── ADD GOAL ─────────────────────────────
        elif choice == "6":
            goal_text = input("\n  Your goal: ").strip()
            if not goal_text:
                print(Fore.RED + "  Goal cannot be empty.")
                continue
            deadline = input("  Deadline (e.g. 2026-12-31) or press Enter to skip: ").strip()
            add_goal(data, goal_text, deadline)

        # ── LOG MOOD ─────────────────────────────
        elif choice == "7":
            try:
                mood = int(input("\n  Rate your mood (1 = very low, 10 = great): ").strip())
                if not 1 <= mood <= 10:
                    raise ValueError
                note = input("  Add a note (optional): ").strip()
                log_mood(data, mood, note)
            except ValueError:
                print(Fore.RED + "  Please enter a number between 1 and 10.")

        # ── MOOD SUMMARY ─────────────────────────
        elif choice == "8":
            show_mood_summary(data)

        # ── EXIT ─────────────────────────────────
        elif choice == "0":
            print(Fore.CYAN + "\n  Take care of yourself. See you next time! 👋\n")
            break

        else:
            print(Fore.RED + "  Invalid choice. Please enter a number from the menu.")

if __name__ == "__main__":
    main()
