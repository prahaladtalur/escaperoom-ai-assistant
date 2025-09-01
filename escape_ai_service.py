#!/usr/bin/env python3
"""
EscapeRoom AI Assistant - Background Service Version
Runs continuously in the background, always listening for voice commands
"""

import os
import pandas as pd
import speech_recognition as sr
import google.generativeai as genai
from dotenv import load_dotenv
import json
import re
import time
import threading
from datetime import datetime

class EscapeRoomAIService:
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
        self.running = True
        
        # Wake words to activate the assistant
        self.wake_words = ['escape room', 'puzzle help', 'ai assistant', 'help me']
    
    def log(self, message):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def load_puzzles(self):
        """Load puzzle data from CSV file"""
        try:
            df = pd.read_csv('puzzles.csv')
            self.log(f"Loaded {len(df)} puzzles from 4 rooms")
            return df
        except FileNotFoundError:
            raise FileNotFoundError("puzzles.csv not found. Please ensure the file exists.")
    
    def setup_microphone(self):
        """Calibrate microphone for ambient noise"""
        self.log("Calibrating microphone for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        self.log("Microphone ready!")
    
    def listen_continuously(self):
        """Continuously listen for wake words and commands"""
        self.log("Starting continuous listening mode...")
        self.log("Say 'escape room' or 'puzzle help' to activate, then describe your puzzle")
        
        while self.running:
            try:
                with self.microphone as source:
                    # Listen for wake word with shorter timeout
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                text = self.recognizer.recognize_google(audio).lower()
                
                # Check for wake words
                if any(wake_word in text for wake_word in self.wake_words):
                    self.log(f"Wake word detected: '{text}'")
                    self.handle_activated_session()
                
                # Check for shutdown command
                elif 'shutdown assistant' in text or 'stop service' in text:
                    self.log("Shutdown command received")
                    self.running = False
                    break
                    
            except sr.WaitTimeoutError:
                # Normal timeout, continue listening
                continue
            except sr.UnknownValueError:
                # Could not understand speech, continue listening
                continue
            except sr.RequestError as e:
                self.log(f"Speech recognition error: {e}")
                time.sleep(5)  # Wait before retrying
            except Exception as e:
                self.log(f"Unexpected error: {e}")
                time.sleep(5)
    
    def handle_activated_session(self):
        """Handle an activated session after wake word detection"""
        self.log("Assistant activated! Describe your puzzle problem...")
        
        try:
            # Listen for the actual query with longer timeout
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
            
            user_query = self.recognizer.recognize_google(audio)
            self.log(f"Query received: '{user_query}'")
            
            # Process the query
            self.process_query(user_query)
            
        except sr.WaitTimeoutError:
            self.log("No query received after activation")
        except sr.UnknownValueError:
            self.log("Could not understand the query")
        except Exception as e:
            self.log(f"Error processing activated session: {e}")
    
    def process_query(self, user_query):
        """Process the user query and provide hints"""
        self.log("Finding matching puzzle...")
        room, puzzle_name = self.match_puzzle_with_gemini(user_query)
        
        if not room or not puzzle_name:
            self.log("Could not match query to a puzzle")
            return
        
        result = self.get_puzzle_hints(room, puzzle_name)
        if result:
            puzzle_row, hints = result
            self.display_hints(puzzle_row, hints)
        else:
            self.log("Could not find puzzle in database")
    
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
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                return result.get('room'), result.get('puzzle_name')
            else:
                self.log("Could not parse Gemini response")
                return None, None
                
        except Exception as e:
            self.log(f"Error with Gemini API: {e}")
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
            self.log(f"Error retrieving hints: {e}")
            return None
    
    def display_hints(self, puzzle_row, hints):
        """Display puzzle information and hints"""
        self.log(f"PUZZLE FOUND: {puzzle_row['puzzle_name']} in {puzzle_row['room']}")
        for hint in hints:
            self.log(hint)
        if not hints:
            self.log("No hints available for this puzzle")
    
    def run(self):
        """Start the background service"""
        self.log("🎮 EscapeRoom AI Assistant Service Started!")
        self.log("Running in background mode - always listening...")
        self.log("Say 'shutdown assistant' to stop the service")
        
        try:
            self.listen_continuously()
        except KeyboardInterrupt:
            self.log("Service stopped by user")
        finally:
            self.log("EscapeRoom AI Assistant Service stopped")

if __name__ == "__main__":
    try:
        service = EscapeRoomAIService()
        service.run()
    except Exception as e:
        print(f"Failed to start EscapeRoom AI Service: {e}")