import httpx
import os
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"
USERNAME = "admin"
PASSWORD = "Admin123456"

def run_test():
    with httpx.Client(base_url=BASE_URL, timeout=30.0, trust_env=False) as client:
        # 1. Login
        print("Logging in...")
        response = client.post("/auth/login", json={"username": USERNAME, "password": PASSWORD})
        if response.status_code != 200:
            print(f"Login failed: {response.status_code} {response.text}")
            return
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login successful.")

        # 2. Create Knowledge Base
        print("Creating Knowledge Base...")
        kb_data = {
            "name": "Test KB",
            "description": "Created by test script",
            "category": "test"
        }
        response = client.post("/knowledge-bases", json=kb_data, headers=headers)
        if response.status_code not in (200, 201):
            # Check if it fails, maybe it already exists?
             print(f"Create KB failed: {response.status_code} {response.text}")
             # Try to list and pick one
             print("Listing KBs...")
             response = client.get("/knowledge-bases", headers=headers)
             if response.status_code != 200:
                 print(f"List KBs failed: {response.status_code} {response.text}")
                 return
             kbs = response.json()["items"]
             if not kbs:
                 print("No KBs found and creation failed.")
                 return
             kb_id = kbs[0]["id"]
             print(f"Using existing KB: {kb_id}")
        else:
            kb_id = response.json()["id"]
            print(f"KB Created: {kb_id}")

        # 3. Upload Document
        print(f"Uploading document to KB {kb_id}...")
        
        # Create a dummy file
        with open("test_doc.txt", "w") as f:
            f.write("This is a test document content for RAG system.")
            
        try:
            with open("test_doc.txt", "rb") as f:
                files = {"file": ("test_doc.txt", f, "text/plain")}
                # Note: upload_document expects knowledge_base_id as query param
                response = client.post(
                    f"/documents/upload?knowledge_base_id={kb_id}",
                    files=files,
                    headers=headers
                )
                
            print(f"Upload status: {response.status_code}")
            print(f"Upload response: {response.text}")
            
        finally:
            if os.path.exists("test_doc.txt"):
                os.remove("test_doc.txt")

if __name__ == "__main__":
    run_test()
