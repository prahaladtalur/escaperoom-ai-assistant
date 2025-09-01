from flask import Flask, request, jsonify, session, send_file
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import json, re, os
from openai import OpenAI
import tempfile
import uuid

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')
df = pd.read_csv('puzzles.csv')

# OpenAI client for TTS
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None

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
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1e1e1e;
            color: #e0e0e0;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .container { 
            width: 90%;
            max-width: 800px;
            height: 90vh;
            background: #2a2a2a;
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        
        .header { 
            padding: 20px;
            border-bottom: 1px solid #444;
            text-align: center;
        }
        
        .header h1 {
            color: #4a9eff;
            font-size: 24px;
            font-weight: 600;
        }
        
        .chat-area { 
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .message { 
            max-width: 75%;
            padding: 12px 16px;
            border-radius: 18px;
            font-size: 15px;
            line-height: 1.4;
        }
        
        .user-message { 
            background: #4a9eff;
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }
        
        .assistant-message { 
            background: #3a3a3a;
            color: #e0e0e0;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
        }
        
        .input-area { 
            padding: 20px;
            border-top: 1px solid #444;
            display: flex;
            gap: 12px;
            align-items: center;
        }
        
        #messageInput { 
            flex: 1;
            padding: 12px 16px;
            border: 1px solid #555;
            border-radius: 24px;
            background: #3a3a3a;
            color: #e0e0e0;
            font-size: 15px;
            outline: none;
        }
        
        #messageInput:focus {
            border-color: #4a9eff;
        }
        
        .btn { 
            padding: 12px 20px;
            border: none;
            border-radius: 20px;
            background: #4a9eff;
            color: white;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .btn:hover { 
            background: #357abd;
        }
        
        .btn-secondary {
            background: #555;
        }
        
        .btn-secondary:hover {
            background: #666;
        }
        
        .status {
            font-size: 12px;
            color: #888;
            text-align: center;
            margin-top: 8px;
        }
        
        .typing {
            opacity: 0.7;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>EscapeRoom Assistant</h1>
        </div>
        
        <div class="chat-area" id="chatArea">
            <div class="message assistant-message">
                Hi! I'm here to help you with escape room puzzles. Tell me what you're working on and I'll give you hints one at a time.
            </div>
        </div>
        
        <div class="input-area">
            <input type="text" id="messageInput" placeholder="Describe your puzzle..." />
            <button class="btn" onclick="sendMessage()">Send</button>
            <button class="btn btn-secondary" id="voiceBtn" onclick="toggleVoice()">Voice</button>
            <button class="btn btn-secondary" id="speakBtn" onclick="toggleSpeak()">🔊</button>
            <button class="btn btn-secondary" onclick="clearChat()">Clear</button>
        </div>
        <div class="status" id="status"></div>
    </div>

    <script>
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            addMessage(message, 'user');
            input.value = '';
            
            const typingDiv = addMessage('Thinking...', 'assistant typing');
            
            fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                typingDiv.remove();
                addMessage(data.response, 'assistant');
                if (speechEnabled && data.audio_id) {
                    playAudio(data.audio_id);
                } else if (speechEnabled) {
                    speakText(data.response);
                }
            })
            .catch(error => {
                typingDiv.remove();
                addMessage('Sorry, something went wrong. Try again.', 'assistant');
            });
        }
        
        function addMessage(text, sender) {
            const chatArea = document.getElementById('chatArea');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + sender.replace(' ', '-') + '-message';
            messageDiv.textContent = text;
            chatArea.appendChild(messageDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
            return messageDiv;
        }
        
        function clearChat() {
            fetch('/api/clear', { method: 'POST' });
            document.getElementById('chatArea').innerHTML = 
                '<div class="message assistant-message">Hi! I\\'m here to help you with escape room puzzles. Tell me what you\\'re working on and I\\'ll give you hints one at a time.</div>';
            synth.cancel();
        }
        
        let recognition;
        let isListening = false;
        let speechEnabled = true;
        let synth = window.speechSynthesis;
        
        if ('webkitSpeechRecognition' in window) {
            recognition = new webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';
            
            recognition.onstart = function() {
                isListening = true;
                document.getElementById('status').textContent = 'Listening...';
                document.getElementById('voiceBtn').textContent = 'Stop';
            };
            
            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                document.getElementById('messageInput').value = transcript;
                sendMessage();
            };
            
            recognition.onend = function() {
                isListening = false;
                document.getElementById('voiceBtn').textContent = 'Voice';
                document.getElementById('status').textContent = '';
            };
            
            recognition.onerror = function(event) {
                document.getElementById('status').textContent = 'Voice error - try again';
                isListening = false;
                document.getElementById('voiceBtn').textContent = 'Voice';
            };
        }
        
        function toggleVoice() {
            if (!recognition) {
                alert('Voice recognition not supported');
                return;
            }
            
            if (isListening) {
                recognition.stop();
            } else {
                recognition.start();
            }
        }
        
        function playAudio(audioId) {
            const audio = new Audio(`/api/audio/${audioId}`);
            audio.play().catch(e => console.log('Audio play failed:', e));
        }
        
        function speakText(text) {
            if ('speechSynthesis' in window) {
                synth.cancel();
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.rate = 0.9;
                utterance.pitch = 1.0;
                utterance.volume = 0.8;
                synth.speak(utterance);
            }
        }
        
        function toggleSpeak() {
            speechEnabled = !speechEnabled;
            const btn = document.getElementById('speakBtn');
            btn.textContent = speechEnabled ? '🔊' : '🔇';
            btn.title = speechEnabled ? 'Voice enabled' : 'Voice disabled';
            if (!speechEnabled) {
                synth.cancel();
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
    You are a helpful escape room assistant. Be conversational and friendly.
    
    Available puzzles: {json.dumps(puzzle_data)}
    
    Current puzzle: {session.get('current_puzzle')}
    Hints given: {session.get('hint_count', 0)}
    
    Recent conversation:
    {history}
    
    User: "{message}"
    
    If they mention a puzzle, give ONE relevant hint. If they ask for more help on the same puzzle, give the NEXT hint.
    Be helpful and encouraging.
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
                        
                        response_text = f"For the {row['puzzle_name']}: {hint}"
                        
                        if session['hint_count'] < len(hints):
                            response_text += " Need another hint? Just ask!"
                        else:
                            response_text += " That's all the hints I have for this one!"
                break
        
        conversation.append({'user': message, 'assistant': response_text})
        session['conversation'] = conversation[-10:]
        
        return jsonify({'response': response_text, 'audio_id': generate_audio(response_text)})
        
    except Exception as e:
        return jsonify({'response': 'Sorry, I had trouble with that. Can you try rephrasing?'})

def generate_audio(text):
    if not openai_client:
        return None
    
    try:
        audio_id = str(uuid.uuid4())
        response = openai_client.audio.speech.create(
            model="tts-1",
            voice="nova",  # Female voice, options: alloy, echo, fable, onyx, nova, shimmer
            input=text
        )
        
        audio_path = f"/tmp/audio_{audio_id}.mp3"
        response.stream_to_file(audio_path)
        return audio_id
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

@app.route('/api/audio/<audio_id>')
def get_audio(audio_id):
    audio_path = f"/tmp/audio_{audio_id}.mp3"
    if os.path.exists(audio_path):
        return send_file(audio_path, mimetype='audio/mpeg')
    return '', 404

@app.route('/api/clear', methods=['POST'])
def clear():
    session.clear()
    return jsonify({'status': 'cleared'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5009)