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
load_dotenv()


class TranscriptConsumer(AsyncWebsocketConsumer):
    dg_client = Deepgram(os.getenv("DEEPGRAM_API_KEY"))
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    start_time = 0
    previous_chats = []  # To store the full chat history during the session

    async def get_transcript(self, data: Dict) -> None:
        if "channel" in data:
            transcript = data["channel"]["alternatives"][0]["transcript"]
            accuracy = data["channel"]["alternatives"][0]["confidence"]
            audio_time = data["start"] + data["duration"]

            if transcript:
                latency = time.time() - audio_time - self.start_time

                # Pass the previous chats to the system prompt using f-string
                system_prompt = f"You are anya a personal journalist covering daily life events of your user. You have a youthful and cheery personality. Keep your responses as brief as possible . Don\\'t ask more than 1 question at a time. Don\\'t make much assumptions . \nread previous chats and respond according to that. Let the user speak if his words are not completed according to the previous chats. Say \\um hm\\ or confirm by asking a very small question that he or she is finished or not. if user words are not completed and wait for him or her to complete the chat \n. You must add a \\'•\\' symbol every 5 to 10 words at natural pauses where your response can be split for text to speech.\n\n\n\nPREVIOUS CHATS\n:\n{json.dumps(self.previous_chats, indent=2)}\n\n"

                # Send the transcript to Groq and get a response
                try:
                    chat_completion = self.groq_client.chat.completions.create(
                        messages=[
                            {
                                "role": "system",
                                "content": system_prompt,
                            },
                            {"role": "user", "content": transcript},
                        ],
                        model="llama-3.1-8b-instant",
                    )
                    groq_response = chat_completion.choices[0].message.content

                    # Append current chat to previous chats
                    self.previous_chats.append({
                        "user": transcript,
                        "groq": groq_response
                    })

                    response_data = {
                        "transcript": transcript,
                        "groq_response": groq_response,  # Groq's response
                        "accuracy": accuracy,
                        "latency": latency,
                    }
                    response_json = json.dumps(response_data)
                    await self.send(response_json)

                except Exception as e:
                    print(f"Error in Groq API request: {e}")

    async def save_chat_history(self):
        """Saves the entire chat session when the conversation ends."""
        user = self.scope['user']
        if user.is_authenticated:
            # Save the entire conversation as JSON in the database
            await sync_to_async(ChatHistory.objects.create)(
                user=user,
                transcript=json.dumps(self.previous_chats)  # Saving the full conversation as JSON
            )
        else:
            print("User is not authenticated. Cannot save chat history.")

    async def connect_to_deepgram(self):
        try:
            self.start_time = time.time()
            connection_start = time.time()
            self.socket = await self.dg_client.transcription.live(
                {"punctuate": True, "interim_results": False}
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
        await self.connect_to_deepgram()
        await self.accept()

    async def disconnect(self, close_code):
        # Save the entire chat history when the connection is closed
        await self.save_chat_history()
        await self.close()

    async def receive(self, bytes_data):
        self.socket.send(bytes_data)
