import time
import json
import os
import requests
from bs4 import BeautifulSoup
from main import process_with_ai

PROCESSED_FILE = "processed_projects.json"

def load_processed_ids():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_processed_ids(processed_ids):
    with open(PROCESSED_FILE, "w") as f:
        json.dump(list(processed_ids), f)

def fetch_mostaql_projects():
    url = "https://mostaql.com/projects?category=development"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Connection Error: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        projects = []
        
        project_elements = soup.find_all("div", class_="project__row")
        
        for el in project_elements:
            title_tag = el.find("h2", class_="project__title")
            link_tag = title_tag.find("a") if title_tag else None
            
            if link_tag:
                title = link_tag.text.strip()
                link = link_tag["href"]
                project_id = link.split("/")[-1]
                
                projects.append({
                    "id": project_id,
                    "title": title,
                    "link": link
                })
                
        return projects
    except Exception as e:
        print(f"Fetch Error: {e}")
        return []

def run_poller():
    print("Project monitoring system started successfully...")
    processed_ids = load_processed_ids()
    
    while True:
        print("Checking for new projects...")
        projects = fetch_mostaql_projects()
        
        for project in projects:
            if project["id"] not in processed_ids:
                print(f"New project detected: {project['title']}")
                
                # استدعاء دالة الذكاء الاصطناعي لمعالجة المشروع وتوليد العرض
                process_with_ai(project)
                
                processed_ids.add(project["id"])
                save_processed_ids(processed_ids)
                
        time.sleep(300)

if __name__ == "__main__":
    run_poller()
