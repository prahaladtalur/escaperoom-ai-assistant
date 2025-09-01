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
    <title>The Escape Chamber</title>
    <style>
        body { 
            font-family: 'Courier New', monospace; 
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            margin: 0; padding: 20px; color: #e0e0e0;
            min-height: 100vh;
        }
        .container { 
            max-width: 700px; margin: 0 auto; 
            background: rgba(0,0,0,0.8); 
            padding: 25px; 
            border: 2px solid #444;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(255,215,0,0.3);
        }
        .header { 
            text-align: center; margin-bottom: 25px; 
            border-bottom: 2px solid #ffd700; 
            padding-bottom: 20px; 
        }
        .header h1 {
            color: #ffd700;
            font-size: 28px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
            margin-bottom: 5px;
        }
        .header p {
            color: #ccc;
            font-size: 14px;
            font-style: italic;
        }
        .chat-container { 
            height: 450px; overflow-y: auto; 
            border: 2px solid #444; 
            padding: 20px; margin-bottom: 20px; 
            background: rgba(0,0,0,0.6);
            border-radius: 8px;
        }
        .message { 
            margin: 15px 0; padding: 12px 15px; 
            border-radius: 8px; max-width: 85%; 
            font-size: 14px; line-height: 1.4;
        }
        .user-message { 
            background: linear-gradient(135deg, #8B4513, #A0522D); 
            color: white; margin-left: auto; text-align: right;
            border: 1px solid #CD853F;
        }
        .assistant-message { 
            background: linear-gradient(135deg, #2F4F4F, #708090); 
            color: #e0e0e0;
            border: 1px solid #696969;
        }
        .input-section { 
            display: flex; gap: 12px; 
            background: rgba(0,0,0,0.4);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #444;
        }
        #messageInput { 
            flex: 1; padding: 12px; 
            border: 2px solid #444; 
            font-size: 14px; border-radius: 6px;
            background: rgba(0,0,0,0.7);
            color: #e0e0e0;
            font-family: 'Courier New', monospace;
        }
        #messageInput:focus {
            outline: none;
            border-color: #ffd700;
            box-shadow: 0 0 5px rgba(255,215,0,0.5);
        }
        .btn { 
            padding: 12px 18px; 
            border: 2px solid #ffd700; 
            background: rgba(255,215,0,0.1); 
            color: #ffd700;
            font-size: 14px; cursor: pointer; 
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .btn:hover { 
            background: rgba(255,215,0,0.2);
            box-shadow: 0 0 10px rgba(255,215,0,0.4);
        }
        .typing { font-style: italic; color: #999; }
        #voiceStatus {
            text-align: center; 
            margin-top: 10px; 
            font-size: 12px; 
            color: #ffd700;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>THE ESCAPE CHAMBER</h1>
            <p>Your guide through the mysteries</p>
        </div>
        
        <div class="chat-container" id="chatContainer">
            <div class="message assistant-message">
                Welcome, puzzle solver. I am your guide through these mysterious chambers. Which enigma has captured your attention? Describe your predicament and I shall illuminate the path forward.
            </div>
        </div>
        
        <div class="input-section">
            <input type="text" id="messageInput" placeholder="Describe your puzzle dilemma..." />
            <button class="btn" onclick="sendMessage()">SEND</button>
            <button class="btn" id="voiceBtn" onclick="toggleVoice()">VOICE</button>
            <button class="btn" onclick="clearChat()">RESET</button>
        </div>
        <div id="voiceStatus"></div>
    </div>

    <script>
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            addMessage(message, 'user');
            input.value = '';
            
            const typingDiv = addMessage('Consulting the ancient texts...', 'assistant typing');
            
            fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                typingDiv.remove();
                addMessage(data.response, 'assistant');
            })
            .catch(error => {
                typingDiv.remove();
                addMessage('The connection to the spirit realm has been severed. Try again.', 'assistant');
            });
        }
        
        function addMessage(text, sender) {
            const chatContainer = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + sender.replace(' ', '-') + '-message';
            messageDiv.textContent = text;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            return messageDiv;
        }
        
        function clearChat() {
            fetch('/api/clear', { method: 'POST' });
            document.getElementById('chatContainer').innerHTML = 
                '<div class="message assistant-message">Welcome, puzzle solver. I am your guide through these mysterious chambers. Which enigma has captured your attention?</div>';
        }
        
        let recognition;
        let isListening = false;
        
        if ('webkitSpeechRecognition' in window) {
            recognition = new webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';
            
            recognition.onstart = function() {
                isListening = true;
                document.getElementById('voiceStatus').textContent = 'The chamber listens...';
                document.getElementById('voiceBtn').textContent = 'STOP';
            };
            
            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                document.getElementById('messageInput').value = transcript;
                document.getElementById('voiceStatus').textContent = 'Voice captured: "' + transcript + '"';
                sendMessage();
            };
            
            recognition.onend = function() {
                isListening = false;
                document.getElementById('voiceBtn').textContent = 'VOICE';
                setTimeout(() => {
                    document.getElementById('voiceStatus').textContent = '';
                }, 3000);
            };
            
            recognition.onerror = function(event) {
                document.getElementById('voiceStatus').textContent = 'The spirits could not hear you clearly';
                isListening = false;
                document.getElementById('voiceBtn').textContent = 'VOICE';
            };
        }
        
        function toggleVoice() {
            if (!recognition) {
                alert('Voice recognition not supported in this realm');
                return;
            }
            
            if (isListening) {
                recognition.stop();
            } else {
                recognition.start();
            }
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
    if 'current_puzzle' not in session:
        session['current_puzzle'] = None
    if 'hint_count' not in session:
        session['hint_count'] = 0
    
    conversation = session['conversation']
    
    puzzle_data = []
    for _, row in df.iterrows():
        hints = [row.get(f'hint{i}') for i in range(1, 5) if pd.notna(row.get(f'hint{i}'))]
        puzzle_data.append({
            'room': row['room'],
            'name': row['puzzle_name'],
            'description': row.get('physical_description', ''),
            'hints': hints
        })
    
    history = "\\n".join([f"User: {c['user']}\\nYou: {c['assistant']}" for c in conversation[-5:]])
    
    prompt = f"""
    You are a mysterious, wise escape room guide. Speak in an atmospheric, slightly mystical tone.
    
    Available puzzles: {json.dumps(puzzle_data)}
    
    Current puzzle context: {session.get('current_puzzle')}
    Hints given so far: {session.get('hint_count', 0)}
    
    Recent conversation:
    {history}
    
    User just said: "{message}"
    
    Instructions:
    - Speak like a mysterious guide in an escape room
    - If they mention a puzzle, identify it and give ONE relevant hint
    - If they ask for more help on same puzzle, give the NEXT hint
    - Use atmospheric language but stay helpful
    - Keep responses concise but engaging
    
    Respond as their mystical guide.
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        for _, row in df.iterrows():
            puzzle_name = row['puzzle_name'].lower()
            room_name = row['room'].lower()
            
            if any(word in message.lower() for word in puzzle_name.split()) or room_name in message.lower():
                puzzle_key = f"{row['room']}_{row['puzzle_name']}"
                
                if session.get('current_puzzle') != puzzle_key:
                    session['current_puzzle'] = puzzle_key
                    session['hint_count'] = 0
                
                if any(word in message.lower() for word in ['help', 'hint', 'stuck', 'how', 'what']):
                    hints = [row.get(f'hint{i}') for i in range(1, 5) if pd.notna(row.get(f'hint{i}'))]
                    
                    if session['hint_count'] < len(hints):
                        hint = hints[session['hint_count']]
                        session['hint_count'] += 1
                        
                        response_text = f"Ah, the {row['puzzle_name']} calls to you. Listen carefully: {hint}"
                        
                        if session['hint_count'] < len(hints):
                            response_text += " Should you require further guidance, speak again."
                        else:
                            response_text += " That is all the wisdom I can bestow upon this mystery."
                break
        
        conversation.append({'user': message, 'assistant': response_text})
        session['conversation'] = conversation[-10:]
        
        return jsonify({'response': response_text})
        
    except Exception as e:
        return jsonify({'response': 'The mystical energies are disturbed. Speak your query once more.'})

@app.route('/api/clear', methods=['POST'])
def clear():
    session.clear()
    return jsonify({'status': 'cleared'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5007)