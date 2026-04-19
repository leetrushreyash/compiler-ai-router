import urllib.request
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# Basic CORS headers so the browser doesn't block the request from file:// index.html
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response

@app.route('/route', methods=['POST', 'OPTIONS'])
def route_code():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    data = request.json
    code = data.get('code', '')
    user_prompt = data.get('prompt', '')
    
    # System prompt gives the LLM the absolute rules of the platform
    system_prompt = """You are a strict routing agent. Your ONLY job is to output a single pure JSON object.
Do not reply with conversational text or markdown blocks.
The user may or may not provide code context. Always prioritize the 'User Prompt' to decide the target.

TARGET A (Deep AI Analytics & Python):
- Choose A if prompt mentions: "deep correlation analysis", "code smell correlation", "energy utilization", "neural symbolic", "carbon", or general "Python AI analysis".

TARGET B (Refactoring & Autofixing):
- Choose B if prompt mentions: "model selector", "auto-fixing", "refactoring", "fixing code", or general JavaScript/TS code without deep metrics.

TARGET C (C/C++ Security):
- Choose C if prompt mentions: "C/C++", "security audits", "memory leak", "buffer overflow", "pointers", or "vulnerability".

RETURN STRICTLY JSON IN THIS EXACT FORMAT:
{"target": "A", "reason": "User asked for deep correlation analysis."}
"""
    
    ollama_payload = {
        "model": "llama3.2",
        "prompt": f"User Prompt: {user_prompt}\nCode (Optional): {code}",
        "system": system_prompt,
        "stream": False,
        "format": "json"
    }
    
    try:
        req = urllib.request.Request('http://127.0.0.1:11434/api/generate', 
                                     data=json.dumps(ollama_payload).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            # The exact response inside the JSON
            decision_json = result['response'].strip()
            
            # Clean up potential markdown formatting from LLM
            if decision_json.startswith('```json'):
                decision_json = decision_json[7:]
            if decision_json.startswith('```'):
                decision_json = decision_json[3:]
            if decision_json.endswith('```'):
                decision_json = decision_json[:-3]
            decision_json = decision_json.strip()
            
            # Re-parse the inner JSON string returned by the LLM
            decision = json.loads(decision_json)
            return jsonify(decision)
            
    except Exception as e:
        print(f"Ollama Failure: {e}")
        # Return the actual error clearly without pretending it is Project B!
        return jsonify({"target": "ERROR", "reason": f"Routing failed! Details: {str(e)}", "error": True})

if __name__ == '__main__':
    print("Starting Local Ollama Routing Agent on Port 5000...")
    app.run(port=5000, debug=True)
