#!/usr/bin/env python3
"""
EscapeRoom Assistant
Voice-activated puzzle hint system
"""

import os
import pandas as pd
import speech_recognition as sr
import google.generativeai as genai
from dotenv import load_dotenv
import json
import re

class EscapeRoomAssistant:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        self.puzzles_df = self.load_puzzles()
        self.setup_microphone()
    
    def load_puzzles(self):
        """Load puzzle data from CSV file"""
        try:
            df = pd.read_csv('puzzles.csv')
            print(f"Loaded {len(df)} puzzles from 4 rooms")
            return df
        except FileNotFoundError:
            raise FileNotFoundError("puzzles.csv not found. Please ensure the file exists.")
    
    def setup_microphone(self):
        """Calibrate microphone for ambient noise"""
        print("Calibrating microphone for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        print("Microphone ready!")
    
    def listen_for_speech(self):
        """Capture and convert speech to text"""
        print("\nListening... (say 'quit' or 'exit' to stop)")
        
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=10)
            
            print("Processing speech...")
            text = self.recognizer.recognize_google(audio)
            print(f"You said: '{text}'")
            return text.lower()
            
        except sr.WaitTimeoutError:
            print("No speech detected. Try again.")
            return None
        except sr.UnknownValueError:
            print("Could not understand speech. Please try again.")
            return None
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
            return None
    
    def match_puzzle_with_gemini(self, user_query):
        """Use Gemini API to match user query to puzzle"""
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
        
        Use the exact room and puzzle_name text as they appear in the list.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                return result.get('room'), result.get('puzzle_name')
            else:
                print("Could not parse Gemini response")
                return None, None
                
        except Exception as e:
            print(f"Error with Gemini API: {e}")
            return None, None
    
    def get_puzzle_hints(self, room, puzzle_name):
        """Retrieve hints for the matched puzzle"""
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
                    hints.append(f"Hint {i}: {hint}")
            
            return puzzle_row, hints
            
        except Exception as e:
            print(f"Error retrieving hints: {e}")
            return None
    
    def display_hints(self, puzzle_row, hints):
        """Display puzzle information and hints"""
        print(f"\n{'='*60}")
        print(f"You're working on the {puzzle_row['puzzle_name']} in {puzzle_row['room']}.")
        print(f"{'='*60}")
        
        for hint in hints:
            print(hint)
        
        if not hints:
            print("No hints available for this puzzle.")
        
        print(f"{'='*60}")
    
    def run(self):
        """Main program loop"""
        print("EscapeRoom Assistant Started!")
        print("Say something like: 'I'm stuck on the mushroom puzzle in room 2'")
        print("Say 'quit' or 'exit' to stop.")
        
        while True:
            try:
                # Listen for user input
                user_input = self.listen_for_speech()
                
                if not user_input:
                    continue
                
                # Check for exit commands
                if user_input in ['quit', 'exit', 'stop']:
                    print("Goodbye! Good luck with your escape room!")
                    break
                
                # Match puzzle using Gemini
                print("Finding matching puzzle...")
                room, puzzle_name = self.match_puzzle_with_gemini(user_input)
                
                if not room or not puzzle_name:
                    print("Sorry, I couldn't match your query to a puzzle. Please try rephrasing.")
                    continue
                
                # Get and display hints
                result = self.get_puzzle_hints(room, puzzle_name)
                if result:
                    puzzle_row, hints = result
                    self.display_hints(puzzle_row, hints)
                else:
                    print("Sorry, I couldn't find that puzzle in the database.")
                
            except KeyboardInterrupt:
                print("\nGoodbye! Good luck with your escape room!")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                print("Please try again.")

if __name__ == "__main__":
    try:
        assistant = EscapeRoomAssistant()
        assistant.run()
    except Exception as e:
        print(f"Failed to start EscapeRoom Assistant: {e}")