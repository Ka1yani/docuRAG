import requests
import json
import time

API_URL = "http://localhost:8000"

QUESTIONS = [
    "What is the main topic of the document?",
    "Who is the author or target audience?",
    "When was this document created or published?",
    "What are the key findings or conclusions?",
    "Are there any specific dates mentioned?",
    "What methodology or approach was used?",
    "List the major components or phases described.",
    "What are the primary challenges discussed?",
    "Are there any solutions or recommendations provided?",
    "How does the document define the problem?",
    "What are the prerequisites or requirements listed?",
    "Is there a mention of budget or cost?",
    "Who are the key stakeholders involved?",
    "What are the future goals or next steps?",
    "Describe the initial conditions or background context.",
    "What metrics or indicators are used to measure success?",
    "Are there any legal or compliance issues raised?",
    "What geographical regions or locations are mentioned?",
    "What is the most frequently cited statistic?",
    "What unexpected or random topic is discussed in the text that isn't really relevant?"
]

def test_ask():
    print(f"Testing {len(QUESTIONS)} questions against the API...")
    for idx, question in enumerate(QUESTIONS):
        print(f"\n--- Question {idx + 1} ---")
        print(f"Q: {question}")
        
        try:
            response = requests.post(f"{API_URL}/ask", json={"query": question}, timeout=120)
            if response.status_code == 200:
                data = response.json()
                print(f"A: {data.get('final_answer')}")
                
                citations = data.get('citations', [])
                if citations:
                    cites = [f"[{c['file_name']}, p.{c['page_number']}]" for c in citations]
                    print(f"Citations: {', '.join(cites)}")
                else:
                    print("Citations: None found")
            else:
                print(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Request failed: {e}")
            
        time.sleep(1) # Be nice to the LLM backend

if __name__ == "__main__":
    test_ask()
