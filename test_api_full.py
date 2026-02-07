import requests
import json
import uuid
import time
from datetime import datetime, timedelta, timezone

# Configuration
BASE_URL = "http://127.0.0.1:8000/api"
LOG_FILE = "api_test_log.json"

# Provided Credentials
ACCESS_TOKEN = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjRkYjg1ZGY5LTc5NDItNGFjMy04MzQzLWU2MjY4ZGVlYmMwNyIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3BteXN5dG11c3F1bmtlbnh6b3FtLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJiZTIyYTJjMy02N2YzLTQ3NTYtYTljNi05NTZhMDE1Y2I0ZWEiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzcwNTAyNjIzLCJpYXQiOjE3NzA0OTkwMjMsImVtYWlsIjoidGFtZXphbmRyZXMxOTFAZ21haWwuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJhdmF0YXJfdXJsIjoiQW5kcmVzVGFtZXo1IiwiZW1haWwiOiJ0YW1lemFuZHJlczE5MUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZnVsbF9uYW1lIjoiSm9zZSBBbmRyZXMgVGFtZXogT3J0ZWdhIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiJiZTIyYTJjMy02N2YzLTQ3NTYtYTljNi05NTZhMDE1Y2I0ZWEifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc3MDQ5OTAyM31dLCJzZXNzaW9uX2lkIjoiMzM5ZDhkZTQtMjYzOS00NTRiLWEzMjMtNDhhNmY1NzhiY2IzIiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.YS4ov2rhycxsAZByGpfPzEirkviP1ossNEY18_UclIH9D-8dsDRj62B-T_jncbdl7OQ46rnQbR2G2v7BaT9HIw"

# Logging Storage
request_logs = []

def log_request(method, endpoint, payload=None, response=None, status_code=None):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "request": {
            "method": method,
            "url": f"{BASE_URL}{endpoint}",
            "payload": payload
        },
        "response": {
            "status_code": status_code,
            "body": response
        }
    }
    request_logs.append(entry)

def make_request(method, endpoint, **kwargs):
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "POST":
            r = requests.post(url, **kwargs)
        elif method == "GET":
            r = requests.get(url, **kwargs)
        elif method == "PATCH":
            r = requests.patch(url, **kwargs)
        elif method == "DELETE":
            r = requests.delete(url, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        try:
            resp_json = r.json()
        except:
            resp_json = r.text

        log_request(method, endpoint, kwargs.get("json"), resp_json, r.status_code)
        return r
    except Exception as e:
        print(f"❌ Error in request {method} {endpoint}: {e}")
        log_request(method, endpoint, kwargs.get("json"), str(e), 0)
        return None

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
YELLOW = "\033[93m"

def print_log(msg, success=True):
    color = GREEN if success else RED
    symbol = "✅" if success else "❌"
    print(f"{color}{symbol} {msg}{RESET}")

def run_tests():
    print(f"{YELLOW}🚀 Starting Comprehensive API Integration Tests...{RESET}\n")
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        # 2. Tags
        print("\n--- 🏷️  Tags ---")
        tag_name = f"TestTag_{uuid.uuid4().hex[:6]}"
        r = make_request("POST", "/tags/", json={"name": tag_name, "color": "#FF5733"}, headers=headers)
        if not r or r.status_code != 201:
            print_log(f"Create Tag failed: {r.text if r else 'No response'}", False)
            return
        tag_id = r.json()["id"]
        print_log(f"Tag created: {tag_name}")

        # 3. Tasks (with Reminder)
        print("\n--- ✅ Tasks & Reminders ---")
        due_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        task_payload = {
            "title": "Integration Test Task",
            "description": "Testing full flow",
            "priority": "alta",
            "due_date": due_date,
            "reminders": [{"unit": "minutes", "value": 30}]
        }
        r = make_request("POST", "/tasks/", json=task_payload, headers=headers)
        if not r or r.status_code != 201:
            print_log(f"Create Task failed: {r.text if r else 'No response'}", False)
            return
        task_id = r.json()["id"]
        print_log(f"Task created: {task_id}")
        
        # Verify Reminder creation via Task response
        task_data = r.json()
        if task_data.get("reminders_data") and len(task_data["reminders_data"]) > 0:
            print_log("Reminder created automatically with Task")
        else:
            print_log("Reminder NOT created with Task", False)

        # 4. Notes
        print("\n--- 📝 Notes ---")
        r = make_request("POST", "/notes/", json={"title": "Test Note", "content": "Linked note content"}, headers=headers)
        if not r or r.status_code != 201:
            print_log(f"Create Note failed: {r.text if r else 'No response'}", False)
            return
        note_id = r.json()["id"]
        print_log(f"Note created: {note_id}")

        # 5. Events
        print("\n--- 📅 Events ---")
        start_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        end_time = (datetime.now(timezone.utc) + timedelta(days=2, hours=1)).isoformat()
        r = make_request("POST", "/events/", json={
            "title": "Test Event", 
            "start_time": start_time, 
            "end_time": end_time
        }, headers=headers)
        if not r or r.status_code != 201:
            print_log(f"Create Event failed: {r.text if r else 'No response'}", False)
            return
        event_id = r.json()["id"]
        print_log(f"Event created: {event_id}")

        # 6. Linking
        print("\n--- 🔗 Linking Entities ---")
        
            # Task -> Note
        r = make_request("POST", "/tasks/notes", json={"task_id": task_id, "note_id": note_id}, headers=headers)
        if r and r.status_code == 201: print_log("Linked Task -> Note")
        else: print_log(f"Failed Link Task -> Note: {r.text if r else 'No response'}", False)

        # Task -> Tag
        r = make_request("POST", "/tasks/tags", json={"task_id": task_id, "tag_ids": [tag_id]}, headers=headers)
        if r and r.status_code == 200: print_log("Linked Task -> Tag")
        else: print_log(f"Failed Link Task -> Tag: {r.text if r else 'No response'}", False)

        # Note -> Tag
        r = make_request("POST", "/notes/tags", json={"note_id": note_id, "tag_ids": [tag_id]}, headers=headers)
        if r and r.status_code == 200: print_log("Linked Note -> Tag")
        else: print_log(f"Failed Link Note -> Tag: {r.text if r else 'No response'}", False)

        # Task -> Event
        r = make_request("POST", "/events/tasks", json={"event_id": event_id, "task_id": task_id}, headers=headers)
        if r and r.status_code == 201: print_log("Linked Event -> Task")
        else: print_log(f"Failed Link Event -> Task: {r.text if r else 'No response'}", False)
        
        # Event -> Note
        r = make_request("POST", "/events/notes", json={"event_id": event_id, "note_id": note_id}, headers=headers)
        if r and r.status_code == 201: print_log("Linked Event -> Note")
        else: print_log(f"Failed Link Event -> Note: {r.text if r else 'No response'}", False)

        # 7. Verification
        print("\n--- 🔍 Verification (Reads) ---")
        
        # Get Task (expect Note and Event)
        r = make_request("GET", f"/tasks/{task_id}", headers=headers)
        if r and r.status_code == 200:
            data = r.json()
            has_note = any(n['id'] == note_id for n in data.get('notes', []))
            has_event = any(e['id'] == event_id for e in data.get('events', []))
            if has_note and has_event: print_log("GET Task verified: Contains Note & Event")
            else: print_log(f"GET Task failed verification: Note={has_note}, Event={has_event}", False)
        else:
            print_log(f"GET Task failed: {r.text if r else 'No response'}", False)

        # Get Note (expect Task and Event)
        r = make_request("GET", f"/notes/{note_id}", headers=headers)
        if r and r.status_code == 200:
            data = r.json()
            has_task = any(t['id'] == task_id for t in data.get('tasks', []))
            has_event = any(e['id'] == event_id for e in data.get('events', []))
            if has_task and has_event: print_log("GET Note verified: Contains Task & Event")
            else: print_log(f"GET Note failed verification: Task={has_task}, Event={has_event}", False)
        else:
            print_log(f"GET Note failed: {r.text if r else 'No response'}", False)

        # Get Event (expect Task and Note)
        r = make_request("GET", f"/events/{event_id}", headers=headers)
        if r and r.status_code == 200:
            data = r.json()
            has_task = any(t['id'] == task_id for t in data.get('tasks', []))
            has_note = any(n['id'] == note_id for n in data.get('notes', []))
            if has_task and has_note: print_log("GET Event verified: Contains Task & Note")
            else: print_log(f"GET Event failed verification: Task={has_task}, Note={has_note}", False)
        else:
            print_log(f"GET Event failed: {r.text if r else 'No response'}", False)

        # 8. Cleanup
        print("\n--- 🧹 Cleanup ---")
        make_request("DELETE", f"/tasks/{task_id}", headers=headers)
        make_request("DELETE", f"/notes/{note_id}", headers=headers)
        make_request("DELETE", f"/events/{event_id}", headers=headers)
        print_log("Test entities deleted")

    finally:
        # Save Log
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(request_logs, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Request/Response Log saved to {LOG_FILE}")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
