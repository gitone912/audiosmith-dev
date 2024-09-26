from channels.generic.websocket import AsyncWebsocketConsumer
from dotenv import load_dotenv
from deepgram import Deepgram
from typing import Dict
import os
import json
import time
from groq import Groq
from django.contrib.auth import get_user_model
from .models import ChatHistory, Profile
from asgiref.sync import sync_to_async
import asyncio  # Import asyncio for the timing feature

load_dotenv()


class TranscriptConsumer(AsyncWebsocketConsumer):
    dg_client = Deepgram(os.getenv("DEEPGRAM_API_KEY"))
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    start_time = 0
    previous_chats = []  # To store the full chat history during the session
    transcript_buffer = ""  # Buffer to hold concatenated transcripts
    last_transcript_time = 0  # Time when the last transcript was received

    async def get_transcript(self, data: Dict) -> None:
        """Receive transcripts from Deepgram and append to buffer."""
        if "channel" in data:
            transcript = data["channel"]["alternatives"][0]["transcript"]

            if transcript:
                self.transcript_buffer += (
                    transcript + " "
                )  # Append the received transcript to the buffer
                self.last_transcript_time = (
                    time.time()
                )  # Update last transcript time to current time

    async def check_for_transcripts(self):
        """Continuously checks every 2 seconds if transcripts are still being received."""
        while True:
            await asyncio.sleep(2)  # Wait for 2 seconds before checking again
            current_time = time.time()

            # If more than 2 seconds have passed since the last transcript, send the final transcript
            if self.transcript_buffer and current_time - self.last_transcript_time >= 3:
                await self.send_final_transcript()
                self.transcript_buffer = (
                    ""  # Reset the buffer after sending the transcript
                )
            elif self.transcript_buffer and current_time - self.last_transcript_time >= 2.5:
                response_data = {
                    "transcript": 'processing...',
                    "groq_response": '...',
                    "accuracy": None,  # We are not tracking accuracy for multiple transcripts
                    "latency": None,
                }
                response_json = json.dumps(response_data)
                await self.send(response_json)  # Send the final response over WebSocket
            elif self.transcript_buffer and current_time - self.last_transcript_time >= 2:
                response_data = {
                    "transcript": 'listening...',
                    "groq_response": '...',
                    "accuracy": None,  # We are not tracking accuracy for multiple transcripts
                    "latency": None,
                }
                response_json = json.dumps(response_data)
                await self.send(response_json)  # Send the final response over WebSocket

    async def send_final_transcript(self):
        """Send the final concatenated transcript to Groq after a 2-second pause."""
        if not self.transcript_buffer.strip():  # If the buffer is empty, return
            return

        # Prepare the system prompt using the previous chat history
        system_prompt = f"You are Stella a personal journalist covering daily life events of your user. You have a youthful and cheery personality. Keep your responses as brief as possible. Initiate the conversation first. Don't ask more than 1 question at a time. Don't make many assumptions. Read previous chats and respond accordingly. Let the user speak if their words are not completed according to the previous chats. Act as a natural human. you can add '...' symbol for natural pauses where your response can be split for text to speech. you can use some human fillers as well.\nPREVIOUS CHATS:\n{json.dumps(self.previous_chats, indent=2)}\n"

        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {"role": "user", "content": self.transcript_buffer.strip()},
                ],
                model="llama-3.1-70b-versatile",
            )
            groq_response = chat_completion.choices[0].message.content

            # Append the current chat to the previous chat history
            self.previous_chats.append(
                {"user": self.transcript_buffer.strip(), "groq": groq_response}
            )

            # Prepare response data
            response_data = {
                "transcript": self.transcript_buffer.strip(),
                "groq_response": groq_response,
                "accuracy": None,  # We are not tracking accuracy for multiple transcripts
                "latency": time.time() - self.last_transcript_time,
            }
            response_json = json.dumps(response_data)
            await self.send(response_json)  # Send the final response over WebSocket

        except Exception as e:
            print(f"Error in Groq API request: {e}")

    async def save_chat_history(self):
        """Saves the entire chat session when the conversation ends."""
        user = self.scope["user"]
        if user.is_authenticated:
            # Save the entire conversation as JSON in the database
            await sync_to_async(ChatHistory.objects.create)(
                user=user,
                transcript=json.dumps(
                    self.previous_chats
                ),  # Save the full conversation as JSON
            )
        else:
            print("User is not authenticated. Cannot save chat history.")

    async def connect_to_deepgram(self):
        """Connect to the Deepgram API for live transcription."""
        try:
            self.start_time = time.time()
            connection_start = time.time()
            self.socket = await self.dg_client.transcription.live(
                {"punctuate": True, "interim_results": False,"model":"nova-2"}
            )
            connection_end = time.time()
            connection_time = connection_end - connection_start
            print("Startime:", self.start_time, "connection time:", connection_time)
            self.start_time = self.start_time + connection_time
            print("Update start time", self.start_time)
            self.socket.registerHandler(
                self.socket.event.CLOSE,
                lambda c: print(f"Connection closed with code {c}."),
            )
            self.socket.registerHandler(
                self.socket.event.TRANSCRIPT_RECEIVED, self.get_transcript
            )

        except Exception as e:
            raise Exception(f"Could not open socket: {e}")

    async def connect(self):
        """WebSocket connection established."""
        self.previous_chats = []
        await self.connect_to_deepgram()
        await self.accept()
        # Start a background task to check for transcripts every 2 seconds
        asyncio.create_task(self.check_for_transcripts())

    async def disconnect(self, close_code):
        """When WebSocket connection is closed, save the chat history."""
        await self.save_chat_history()
        await self.close()
       #reset the previous chat after closing
        self.previous_chats = []

    async def receive(self, bytes_data):
        """Send audio data to Deepgram for transcription."""
        self.socket.send(bytes_data)
