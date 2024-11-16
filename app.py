from flask import Flask, render_template, request, jsonify
import requests
import os
import time

app = Flask(__name__)

ASSEMBLY_API_KEY = "af150f4d9e84484b94eb7ed32e711e88"
API_URL = "https://api.assemblyai.com/v2/transcript"
UPLOAD_URL = "https://api.assemblyai.com/v2/upload"

# Route for the homepage
@app.route('/aitranscriptor')
def index():
    return render_template('index.html')

# Route to handle file upload and transcription
@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio_file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['audio_file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    upload_folder = os.path.join(os.getcwd(), 'uploads')

    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    file_path = os.path.join(upload_folder, file.filename)

    try:
        # Save the file
        file.save(file_path)

        # Step 1: Upload the file to AssemblyAI
        headers = {
            'authorization': ASSEMBLY_API_KEY
        }
        with open(file_path, 'rb') as f:
            response = requests.post(UPLOAD_URL, headers=headers, files={'file': f})

        if response.status_code != 200:
            return jsonify({"error": f"Error uploading file: {response.text}"}), 500

        audio_url = response.json()['upload_url']

        # Step 2: Request transcription
        transcript_request = {
            'audio_url': audio_url
        }
        transcript_response = requests.post(API_URL, headers=headers, json=transcript_request)

        if transcript_response.status_code != 200:
            return jsonify({"error": f"Error requesting transcription: {transcript_response.text}"}), 500

        transcript_id = transcript_response.json()['id']

        # Step 3: Poll the transcription status
        while True:
            status_response = requests.get(f"{API_URL}/{transcript_id}", headers=headers)
            status_data = status_response.json()

            if status_data['status'] == 'completed':
                return jsonify({"transcription": status_data['text']}), 200
            elif status_data['status'] == 'failed':
                return jsonify({"error": "Transcription failed"}), 500

            time.sleep(5)  # Poll every 5 seconds

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
