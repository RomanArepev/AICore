from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)

# Add CORS support
CORS(app, resources={r"/query": {"origins": "http://79.132.143.108:5000"}})

@app.route('/', methods=['GET', 'POST'])
def index():
    response_text = ""
    if request.method == 'POST':
        user_input = request.form.get('user_input')
        if user_input:
            # Send the input to the specified endpoint
            response = requests.post('http://79.132.143.108:8000/query', json={'text': user_input})
            if response.ok:
                response_data = response.json()
                # Assuming the response contains a key 'answer' for the answer text
                response_text = response_data.get('answer', 'No answer received')
            else:
                response_text = 'Error: Unable to get a response from the server.'
    return render_template('index.html', response_text=response_text)

@app.route('/query', methods=['POST'])
def query():
    # Your existing logic here
    return jsonify({'answer': 'Your response here'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 