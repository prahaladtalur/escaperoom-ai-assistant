from flask import Flask, request, jsonify
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import json, re, os

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')
df = pd.read_csv('puzzles.csv')

app = Flask(__name__)

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>EscapeRoom Assistant</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f0f0f0; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; border: 1px solid #ccc; }
        .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 15px; }
        .header h1 { font-size: 24px; margin-bottom: 5px; }
        .header p { font-size: 14px; color: #666; }
        .input-section { background: #f9f9f9; border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; }
        #queryInput { width: 100%; padding: 10px; border: 1px solid #ccc; font-size: 14px; margin-bottom: 10px; }
        .btn { padding: 10px 15px; border: 1px solid #333; background: white; font-size: 14px; cursor: pointer; margin-right: 10px; }
        .btn:hover { background: #eee; }
        .results { background: #f9f9f9; border: 1px solid #ddd; padding: 20px; display: none; }
        .puzzle-info h2 { color: #333; margin-bottom: 10px; font-size: 18px; }
        .puzzle-description { background: #eee; padding: 10px; margin-bottom: 15px; font-style: italic; border-left: 3px solid #333; }
        .hints { list-style: none; padding: 0; }
        .hints li { background: white; margin: 10px 0; padding: 15px; border: 1px solid #ddd; border-left: 4px solid #666; font-size: 16px; }
        .error { background: #ffe6e6; border: 1px solid #ff9999; color: #cc0000; padding: 10px; margin: 10px 0; }
        .loading { text-align: center; padding: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>EscapeRoom Assistant</h1>
            <p>Puzzle solving helper</p>
        </div>
        
        <div class="input-section">
            <input type="text" id="queryInput" placeholder="Describe your puzzle problem (e.g. stuck on mushroom puzzle in room 2)" />
            <button class="btn" onclick="submitQuery()">Get Hints</button>
            <button class="btn" onclick="clearResults()">Clear</button>
        </div>
        
        <div class="results" id="results"></div>
    </div>

    <script>
        function submitQuery() {
            const query = document.getElementById('queryInput').value.trim();
            if (!query) return;
            
            const resultsDiv = document.getElementById('results');
            resultsDiv.style.display = 'block';
            resultsDiv.innerHTML = '<div class="loading"><p>Finding your puzzle...</p></div>';
            
            fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    resultsDiv.innerHTML = '<div class="error">' + data.error + '</div>';
                } else {
                    displayResults(data);
                }
            })
            .catch(error => {
                resultsDiv.innerHTML = '<div class="error">Connection error: ' + error.message + '</div>';
            });
        }
        
        function displayResults(data) {
            const hintsHtml = data.hints.map(hint => 
                '<li>' + hint + '</li>'
            ).join('');
            
            document.getElementById('results').innerHTML = 
                '<div class="puzzle-info">' +
                '<h2>' + data.puzzle_name + '</h2>' +
                '<p><strong>Location:</strong> ' + data.room + '</p>' +
                (data.description ? '<div class="puzzle-description">' + data.description + '</div>' : '') +
                '<h3>Hints:</h3>' +
                '<ul class="hints">' + hintsHtml + '</ul>' +
                '</div>';
        }
        
        function clearResults() {
            document.getElementById('results').style.display = 'none';
            document.getElementById('queryInput').value = '';
        }
        
        document.getElementById('queryInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                submitQuery();
            }
        });
    </script>
</body>
</html>
    '''

@app.route('/api/query', methods=['POST'])
def query():
    q = request.json.get('query', '')
    puzzles = [f"Room: {r['room']}, Puzzle: {r['puzzle_name']}" for _, r in df.iterrows()]
    
    response = model.generate_content(f"Match '{q}' to: {puzzles}. Return JSON: {{\"room\": \"name\", \"puzzle_name\": \"name\"}}")
    match = re.search(r'\{.*\}', response.text)
    if match:
        result = json.loads(match.group())
        room, name = result.get('room'), result.get('puzzle_name')
        
        puzzle = df[(df['room'] == room) & (df['puzzle_name'] == name)]
        if not puzzle.empty:
            row = puzzle.iloc[0]
            hints = [row.get(f'hint{i}') for i in range(1, 5) if pd.notna(row.get(f'hint{i}'))]
            return jsonify({
                'room': room,
                'puzzle_name': name,
                'description': row.get('physical_description', ''),
                'hints': hints
            })
    
    return jsonify({'error': 'No puzzle found'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5003)