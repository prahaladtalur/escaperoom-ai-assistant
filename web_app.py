#!/usr/bin/env python3
"""
EscapeRoom Assistant - Web Application
Web interface with voice recognition
"""

from flask import Flask, render_template, request, jsonify
import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import json
import re

app = Flask(__name__)

class EscapeRoomWeb:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.puzzles_df = self.load_puzzles()
    
    def load_puzzles(self):
        try:
            return pd.read_csv('puzzles.csv')
        except FileNotFoundError:
            raise FileNotFoundError("puzzles.csv not found")
    
    def match_puzzle_with_gemini(self, user_query):
        puzzle_list = []
        for _, row in self.puzzles_df.iterrows():
            puzzle_list.append(f"Room: {row['room']}, Puzzle: {row['puzzle_name']}")
        
        prompt = f"""
        Available puzzles:
        {chr(10).join(puzzle_list)}
        
        User query: "{user_query}"
        
        Match this user query to the closest puzzle from the list above. 
        Return ONLY a JSON object with exactly these fields:
        {{"room": "exact room name", "puzzle_name": "exact puzzle name"}}
        """
        
        try:
            response = self.model.generate_content(prompt)
            json_match = re.search(r'\{.*\}', response.text.strip(), re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get('room'), result.get('puzzle_name')
            return None, None
        except Exception as e:
            print(f"Gemini API error: {e}")
            return None, None
    
    def get_puzzle_hints(self, room, puzzle_name):
        try:
            puzzle = self.puzzles_df[
                (self.puzzles_df['room'] == room) & 
                (self.puzzles_df['puzzle_name'] == puzzle_name)
            ]
            
            if puzzle.empty:
                return None
            
            puzzle_row = puzzle.iloc[0]
            hints = []
            for i in range(1, 5):
                hint = puzzle_row.get(f'hint{i}')
                if pd.notna(hint) and hint.strip():
                    hints.append(hint)
            
            return {
                'room': puzzle_row['room'],
                'puzzle_name': puzzle_row['puzzle_name'],
                'description': puzzle_row.get('physical_description', ''),
                'hints': hints
            }
        except Exception:
            return None

assistant = EscapeRoomWeb()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def process_query():
    data = request.json
    user_query = data.get('query', '')
    
    if not user_query:
        return jsonify({'error': 'No query provided'})
    
    room, puzzle_name = assistant.match_puzzle_with_gemini(user_query)
    
    if not room or not puzzle_name:
        return jsonify({'error': 'Could not match query to a puzzle'})
    
    puzzle_info = assistant.get_puzzle_hints(room, puzzle_name)
    
    if not puzzle_info:
        return jsonify({'error': 'Puzzle not found in database'})
    
    return jsonify(puzzle_info)

@app.route('/api/puzzles')
def get_all_puzzles():
    puzzles = []
    for _, row in assistant.puzzles_df.iterrows():
        puzzles.append({
            'room': row['room'],
            'puzzle_name': row['puzzle_name'],
            'description': row.get('physical_description', '')
        })
    return jsonify(puzzles)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)