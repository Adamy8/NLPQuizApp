import json
import os
from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class OpenAIQuizGenerator:
    def __init__ (self, api_key = None):
        self.api_key = api_key
    
    def generate_quiz(self, topic, num_questions = 5):
        system_prompt = ("You are an expert quiz generator. Create well-formed, educational quiz questions, that test knowledge but are also interesting. ")

        user_prompt = (f""" Gerneate a multiple-choice quiz with {num_questions} questions about {topic}.
        For each question:
        - make the question clear and concise
        - provide 4 answer choices (A, B, C, D)
        - make sure exactly one answer is correct
        - make the distractions plausible but clearly incorrect
        - indicate which option is correct
        
        format your response as valid JSON following this exact structure:
        {
            "title": "Quiz title related to topic",
            "questions": [
                {
                    "question": "Questions text",
                    "options": [
                        "Option A",
                        "Option B",
                        "Option C",
                        "Option D"
                    ],
                    "correct_index": 0 // 0-based index of the correct answer
                },
                // More questions...
            ]
        }""")
        return self.call_openai_api(system_prompt, user_prompt)

    def call_openai_api(self, system_prompt, user_prompt):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,   # creativity level
        }

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers = headers,
                json = data
            )
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                return self._parse_quiz_json(content)
            else:
                error_message = f"API Error: {response.status_code} - {response.text}"
                print(error_message)
                return {"error": error_message}
        
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            return {"error": str(e)}

    def _parse_quiz_json(self, content):
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[1].strip()
            elif "```" in content:
                json_str = content.split("```")[1].strip()
            else:
                json_str = content
            
            quiz_data = json.loads(json_str)
            return quiz_data
        except Expection as e:
            print(f"Error parsing JSON: {str(e)}")
            print(f"Raw content: {content}")
            return {"error": "Failed to parse JSON response from OpenAI"}

@app.route('/api/generate_quiz', methods=['POST'])
def generate_quiz():
    data = request.json
    topic = data.get('topic')
    num_questions = data.get('num_questions', 5)

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    quiz_generator = OpenAIQuizGenerator(api_key=OPENAI_API_KEY)

    result = quiz_generator.generate_quiz(topic, num_questions)

    if "error" in result:
        return jsonify({"error": result["error"]}), 500

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
