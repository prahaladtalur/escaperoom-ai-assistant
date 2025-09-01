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
        .chat-container { height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; background: #f9f9f9; }
        .message { margin: 10px 0; padding: 10px; border-radius: 10px; max-width: 80%; }
        .user-message { background: #007bff; color: white; margin-left: auto; text-align: right; }
        .assistant-message { background: white; border: 1px solid #ddd; }
        .input-section { display: flex; gap: 10px; }
        #messageInput { flex: 1; padding: 10px; border: 1px solid #ccc; font-size: 14px; border-radius: 5px; }
        .btn { padding: 10px 15px; border: 1px solid #333; background: white; font-size: 14px; cursor: pointer; border-radius: 5px; }
        .btn:hover { background: #eee; }
        .typing { font-style: italic; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>EscapeRoom Assistant</h1>
            <p>Your friendly puzzle helper</p>
        </div>
        
        <div class="chat-container" id="chatContainer">
            <div class="message assistant-message">
                Hey there! I'm your escape room buddy. What puzzle are you working on? Tell me what's going on and I'll help you figure it out! 😊
            </div>
        </div>
        
        <div class="input-section">
            <input type="text" id="messageInput" placeholder="Tell me about your puzzle..." />
            <button class="btn" onclick="sendMessage()">Send</button>
            <button class="btn" id="voiceBtn" onclick="toggleVoice()">🎤 Voice</button>
            <button class="btn" onclick="clearChat()">New Chat</button>
        </div>
        <div id="voiceStatus" style="text-align: center; margin-top: 10px; font-size: 12px; color: #666;"></div>
    </div>

    <script>
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            addMessage(message, 'user');
            input.value = '';
            
            // Show typing indicator
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
            })
            .catch(error => {
                typingDiv.remove();
                addMessage('Oops, something went wrong! Try again?', 'assistant');
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
                '<div class="message assistant-message">Hey there! I\\'m your escape room buddy. What puzzle are you working on? Tell me what\\'s going on and I\\'ll help you figure it out! 😊</div>';
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
                document.getElementById('voiceStatus').textContent = 'Listening...';
                document.getElementById('voiceBtn').textContent = '🛑 Stop';
            };
            
            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                document.getElementById('messageInput').value = transcript;
                document.getElementById('voiceStatus').textContent = 'Heard: "' + transcript + '"';
                sendMessage();
            };
            
            recognition.onend = function() {
                isListening = false;
                document.getElementById('voiceBtn').textContent = '🎤 Voice';
                setTimeout(() => {
                    document.getElementById('voiceStatus').textContent = '';
                }, 2000);
            };
            
            recognition.onerror = function(event) {
                document.getElementById('voiceStatus').textContent = 'Voice error - try again';
                isListening = false;
                document.getElementById('voiceBtn').textContent = '🎤 Voice';
            };
        }
        
        function toggleVoice() {
            if (!recognition) {
                alert('Voice recognition not supported in this browser');
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
    
    # Build context for Gemini
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
    You are a friendly, conversational escape room assistant. Be natural, helpful, and engaging.
    
    Available puzzles: {json.dumps(puzzle_data)}
    
    Current puzzle context: {session.get('current_puzzle')}
    Hints given so far: {session.get('hint_count', 0)}
    
    Recent conversation:
    {history}
    
    User just said: "{message}"
    
    Instructions:
    - Be conversational and friendly, not robotic
    - If they mention a puzzle, identify it and give ONE relevant hint
    - If they ask for more help on same puzzle, give the NEXT hint
    - If they seem stuck, encourage them and offer the next hint
    - If they're chatting generally, chat back naturally
    - Keep responses concise but helpful
    
    Respond naturally as a helpful friend would.
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Try to detect if we're talking about a specific puzzle
        for _, row in df.iterrows():
            puzzle_name = row['puzzle_name'].lower()
            room_name = row['room'].lower()
            
            if any(word in message.lower() for word in puzzle_name.split()) or room_name in message.lower():
                puzzle_key = f"{row['room']}_{row['puzzle_name']}"
                
                if session.get('current_puzzle') != puzzle_key:
                    session['current_puzzle'] = puzzle_key
                    session['hint_count'] = 0
                
                # Get next hint if they're asking for help
                if any(word in message.lower() for word in ['help', 'hint', 'stuck', 'how', 'what']):
                    hints = [row.get(f'hint{i}') for i in range(1, 5) if pd.notna(row.get(f'hint{i}'))]
                    
                    if session['hint_count'] < len(hints):
                        hint = hints[session['hint_count']]
                        session['hint_count'] += 1
                        
                        response_text = f"Ah, the {row['puzzle_name']}! Here's what I'd try: {hint}"
                        
                        if session['hint_count'] < len(hints):
                            response_text += " Let me know if you need another hint!"
                        else:
                            response_text += " That's all the hints I have - you've got this!"
                break
        
        # Update conversation
        conversation.append({'user': message, 'assistant': response_text})
        session['conversation'] = conversation[-10:]
        
        return jsonify({'response': response_text})
        
    except Exception as e:
        return jsonify({'response': 'Sorry, I had a brain freeze there! What were you saying about the puzzle?'})

@app.route('/api/clear', methods=['POST'])
def clear():
    session.clear()
    return jsonify({'status': 'cleared'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5006)