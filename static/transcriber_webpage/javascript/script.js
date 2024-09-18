let mediaRecorder;
let socket;
let isConnected = false; // New flag to track the connection status
let currentAudio = null; // Track the currently playing audio

// Function to make the POST request to Deepgram TTS API
async function getDeepgramTTS(text) {
    const url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en";
    const apiKey = "e2b10be16ef191908492b50e6deab126112a1d1f"; // Replace with your actual API key

    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Token ${apiKey}`,
            },
            body: JSON.stringify({ text: text }),
        });

        if (response.ok) {
            const blob = await response.blob(); // Get the audio content as a blob
            return URL.createObjectURL(blob); // Create a temporary URL for the audio
        } else {
            console.error("Deepgram API request failed:", response.status, response.statusText);
            return null;
        }
    } catch (error) {
        console.error("Error calling Deepgram API:", error);
        return null;
    }
}

// Function to play the audio, immediately stopping any current playback
function playAudio(audioUrl) {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0; // Reset playback position
    }

    currentAudio = new Audio(audioUrl);
    currentAudio.play();
  
    currentAudio.onended = () => {
        currentAudio = null;
    };
}

// Function to toggle connection and icon
function toggleConnection() {
    if (isConnected) {
        closeConnection();
    } else {
        askpermission();
    }
}

function updateMicIcon() {
    const micIcon = document.getElementById("mic-icon");
    if (isConnected) {
        micIcon.classList.remove("fa-microphone");
        micIcon.classList.add("fa-stop");
    } else {
        micIcon.classList.remove("fa-stop");
        micIcon.classList.add("fa-microphone");
    }
}

function updateChat(transcript, groqResponse) {
    const chatContainer = document.querySelector("#chat-container");

    chatContainer.innerHTML = '';

    const botMessage = document.createElement('p');
    botMessage.classList.add('yellow-text', 'italic', 'text-lg');
    botMessage.style.maxWidth = '600px';
    botMessage.textContent = groqResponse;

    const userMessage = document.createElement('p');
    userMessage.classList.add('text-gray-500', 'italic', 'mx-auto', 'text-lg');
    userMessage.style.maxWidth = '600px';
    userMessage.textContent = transcript;

    chatContainer.appendChild(botMessage);
    chatContainer.appendChild(userMessage);
}

const askpermission = () => {
    console.log("Starting connection");

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
    }

    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
    }

    navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
        if (!MediaRecorder.isTypeSupported("audio/webm")) {
            return alert("Browser not supported");
        }

        mediaRecorder = new MediaRecorder(stream, {
            mimeType: "audio/webm",
        });

        socket = new WebSocket(`ws://${window.location.host}/listen`);

        socket.onopen = () => {
            document.querySelector("#status").textContent = "Connected";
            isConnected = true;
            updateMicIcon();

            mediaRecorder.addEventListener("dataavailable", async (event) => {
                if (event.data.size > 0 && socket.readyState === WebSocket.OPEN) {
                    socket.send(event.data);
                }
            });

            mediaRecorder.start(250);
        };

        socket.onmessage = async (message) => {
            try {
                const received = JSON.parse(message.data);
                const transcript = received["transcript"];
                const groqResponse = received["groq_response"];

                if (groqResponse) {
                    updateChat(transcript, groqResponse);

                    const audioUrl = await getDeepgramTTS(groqResponse);
                    if (audioUrl) {
                        playAudio(audioUrl);
                    }
                }
            } catch (error) {
                console.error("Error parsing WebSocket message:", error);
            }
        };

        socket.onclose = () => {
            document.querySelector("#status").textContent = "Disconnected!! Click to connect again";
            isConnected = false;
            updateMicIcon();
        };

        socket.onerror = (error) => {
            console.log("WebSocket error", error);
        };
    });
};

const closeConnection = () => {
    try {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.close();
        }
    } catch (error) {
        console.log("WebSocket closing error");
    }

    try {
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
        }
    } catch (error) {
        console.log("MediaRecorder stopping error");
    }

    document.querySelector("#status").textContent = "Disconnected!! Click to connect again";
    isConnected = false;
    updateMicIcon();
};
