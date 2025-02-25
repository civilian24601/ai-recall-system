# /mnt/f/projects/ai-recall-system/code_base/api_structure.py

import requests
from flask import Flask, request
from flask_restful import Resource, Api
from flask_cors import CORS
from network_utils import detect_api_url  # <-- Now we can import the same logic if we want

app = Flask(__name__)
CORS(app)
api = Api(app)

class APIHandler(Resource):
    """Handles API requests and connects to AI processing."""

    def post(self):
        """
        Process user input and send it to the local LM Studio for a response.

        Expected JSON Input:
        {
            "prompt": "User prompt here..."
        }
        """
        data = request.get_json()
        user_prompt = data.get("prompt", "")

        deepseek_response = self.query_deepseek(user_prompt)
        return {"status": "success", "response": deepseek_response}

    def query_deepseek(self, prompt):
        """
        Send user input to LM Studio using the same environment detection as agent_manager.

        Args:
            prompt (str): The user query or instruction.

        Returns:
            str: AI response text or an error message.
        """
        # Use the unified environment detection
        api_url = detect_api_url(default_url="http://10.5.0.2:1234/v1/chat/completions")
        # If you prefer the user to set that IP, you could pass it as a param or use an env var

        try:
            response = requests.post(
                api_url,
                json={
                    "model": "deepseek-coder-33b-instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.7
                }
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"Error {response.status_code}: AI response not available."
        except requests.exceptions.RequestException as e:
            return f"Error communicating with LM Studio: {e}"

api.add_resource(APIHandler, "/api/task")

if __name__ == "__main__":
    # This is typically used for manual testing or for a separate QA flow
    # in case you want to expose a simple Flask endpoint to test the local model
    app.run(debug=True, host="0.0.0.0", port=5000)
