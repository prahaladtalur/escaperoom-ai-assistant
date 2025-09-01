from flask import Flask, request, jsonify, session
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import json, re, os

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')
df = pd.read_csv('puzzles.csv')

app = Flask(__name__)
app.secret_key = 'escape_room_chat'

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
        .header { text-align: center; margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 15px; }
        .header h1 { font-size: 24px; margin-bottom: 5px; }
        .chat-container { height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; background: #f9f9f9; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user-message { background: #e3f2fd; text-align: right; }
        .assistant-message { background: #f1f8e9; }
        .input-section { display: flex; gap: 10px; }
        #messageInput { flex: 1; padding: 10px; border: 1px solid #ccc; font-size: 14px; }
        .btn { padding: 10px 15px; border: 1px solid #333; background: white; font-size: 14px; cursor: pointer; }
        .btn:hover { background: #eee; }
        .hint-box { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 10px 0; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>EscapeRoom Assistant</h1>
            <p>Chat with me about your puzzle problems!</p>
        </div>
        
        <div class="chat-container" id="chatContainer">
            <div class="message assistant-message">
                Hi! I'm here to help with your escape room puzzles. Tell me what you're stuck on!
            </div>
        </div>
        
        <div class="input-section">
            <input type="text" id="messageInput" placeholder="Type your message..." />
            <button class="btn" onclick="sendMessage()">Send</button>
            <button class="btn" onclick="clearChat()">Clear</button>
        </div>
    </div>

    <script>
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            addMessage(message, 'user');
            input.value = '';
            
            fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                addMessage(data.response, 'assistant');
            })
            .catch(error => {
                addMessage('Sorry, something went wrong!', 'assistant');
            });
        }
        
        function addMessage(text, sender) {
            const chatContainer = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + sender + '-message';
            messageDiv.textContent = text;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        function clearChat() {
            fetch('/api/clear', { method: 'POST' });
            document.getElementById('chatContainer').innerHTML = 
                '<div class="message assistant-message">Hi! I\\'m here to help with your escape room puzzles. Tell me what you\\'re stuck on!</div>';
        }
        
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
    '''

@app.route('/api/chat', methods=['POST'])
def chat():
    message = request.json.get('message', '')
    
    if 'conversation' not in session:
        session['conversation'] = []
    if 'puzzle_progress' not in session:
        session['puzzle_progress'] = {}
    
    conversation = session['conversation']
    
    # Get conversational response from Gemini
    puzzles = [f"Room: {r['room']}, Puzzle: {r['puzzle_name']}" for _, r in df.iterrows()]
    history = "\\n".join([f"User: {c['user']}\\nAssistant: {c['assistant']}" for c in conversation[-3:]])
    
    prompt = f"""
    You are a helpful escape room assistant. Available puzzles: {puzzles}
    
    Previous conversation: {history}
    
    User message: "{message}"
    
    If user asks about a specific puzzle, return JSON: {{"puzzle_match": true, "room": "exact name", "puzzle_name": "exact name", "response": "conversational response"}}
    If general chat, return JSON: {{"puzzle_match": false, "response": "conversational response"}}
    """
    
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'\\{.*\\}', response.text, re.DOTALL)
        
        if json_match:
            result = json.loads(json_match.group())
            
            if result.get('puzzle_match'):
                room = result.get('room')
                puzzle_name = result.get('puzzle_name')
                puzzle_key = f"{room}_{puzzle_name}"
                
                # Get next hint for this puzzle
                hint_count = session['puzzle_progress'].get(puzzle_key, 0)
                
                puzzle = df[(df['room'] == room) & (df['puzzle_name'] == puzzle_name)]
                if not puzzle.empty:
                    row = puzzle.iloc[0]
                    hints = [row.get(f'hint{i}') for i in range(1, 5) if pd.notna(row.get(f'hint{i}'))]
                    
                    if hint_count < len(hints):
                        hint = hints[hint_count]
                        session['puzzle_progress'][puzzle_key] = hint_count + 1
                        
                        response_text = f"Here's hint {hint_count + 1} for {puzzle_name}: {hint}"
                        
                        if hint_count + 1 < len(hints):
                            response_text += "\\n\\nNeed another hint? Just ask!"
                        else:
                            response_text += "\\n\\nThat's all the hints I have for this puzzle!"
                    else:
                        response_text = f"I've already given you all {len(hints)} hints for {puzzle_name}. Try working through them step by step!"
                else:
                    response_text = result.get('response', "I couldn't find that puzzle.")
            else:
                response_text = result.get('response', "I'm here to help with puzzles!")
        else:
            response_text = "I'm here to help with your escape room puzzles!"
        
        # Update conversation history
        conversation.append({'user': message, 'assistant': response_text})
        session['conversation'] = conversation[-10:]  # Keep last 10 exchanges
        
        return jsonify({'response': response_text})
        
    except Exception as e:
        return jsonify({'response': 'Sorry, I had trouble understanding that. Can you try rephrasing?'})

@app.route('/api/clear', methods=['POST'])
def clear():
    session['conversation'] = []
    session['puzzle_progress'] = {}
    return jsonify({'status': 'cleared'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5004)