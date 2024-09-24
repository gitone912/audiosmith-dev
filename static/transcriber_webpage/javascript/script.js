let mediaRecorder;
let socket;
let isConnected = false; // New flag to track the connection status
let currentAudio = null; // Track the currently playing audio

let bars; // Global reference for bars to be controlled
let disconnectTimeout;
let spokenOnce = false;

// `${Math.random() * (0.1 - 0.1) + 0.1}s`;
// Initialize bars on window load
window.addEventListener("load", () => {
    bars = document.querySelectorAll(".bar");
    bars.forEach(item => {
        item.style.animationDuration = `${Math.random() * (0.7 - 0.2) + 0.2}s`; // Random animation duration
        item.style.animationPlayState = "paused"; // Pause animation initially
    });
});

// Function to control bar animation
function toggleBarAnimation(play) {
    if (!bars) return;

    bars.forEach(item => {
        item.style.animationPlayState = play ? "running" : "paused";
    });
}
// Function to make the POST request to Deepgram TTS API
async function getDeepgramTTS(text) {
    const url = "https://api.deepgram.com/v1/speak?model=aura-stella-en";
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
        toggleBarAnimation(false); // Stop bars when audio is stopped
    }

    currentAudio = new Audio(audioUrl);
    currentAudio.play();

    // Start the bar animation when audio starts
    toggleBarAnimation(true);

    currentAudio.onended = () => {
        currentAudio = null;
        toggleBarAnimation(false); // Stop bar animation when audio ends
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

    // Clear previous chat messages
    chatContainer.innerHTML = '';

    // Create user message element (show immediately when the user starts speaking)
    const userMessage = document.createElement('p');
    userMessage.classList.add('text-gray-500', 'italic', 'mx-auto', 'text-lg');
    userMessage.style.maxWidth = '600px';
    userMessage.textContent = transcript;

    // Append user message
    chatContainer.appendChild(userMessage);
    
    // Create bot message element (empty at first, for typing effect)
    const botMessage = document.createElement('p');
    botMessage.classList.add('yellow-text', 'italic', 'text-lg');
    botMessage.style.maxWidth = '600px';
    chatContainer.appendChild(botMessage);
    
    // Delay bot response to simulate typing after user finishes speaking
    setTimeout(() => {
        let i = 0;
        function typeText() {
            if (i < groqResponse.length) {
                botMessage.textContent += groqResponse.charAt(i);
                i++;
                setTimeout(typeText, 50); // Adjust typing speed here
            }
        }
        typeText();
    }, 50); // Optional delay before starting the bot's typing effect
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

        socket.onopen = async () => {
            document.querySelector("#status").textContent = "Connecting...";
            isConnected = true;
            updateMicIcon();
            clearTimeout(disconnectTimeout);
    
    // Hide the "disconnected" button if it's visible
    document.getElementById("disconnectedButton").classList.add("hidden");
            // Play the greeting message once the connection is established
            
        
            mediaRecorder.addEventListener("dataavailable", async (event) => {
                if (event.data.size > 0 && socket.readyState === WebSocket.OPEN) {
                    socket.send(event.data);
                }
            });
            if (initialGreeting) {
                const greetingAudioUrl = await getDeepgramTTS(initialGreeting);
                if (greetingAudioUrl) {
                    playAudio(greetingAudioUrl);
                    spokenOnce = true;
                    document.querySelector("#status").textContent = "Connected!! Click to disconnect";
                    document.querySelector("#buttonsup").textContent = "Connected!! Click to disconnect";
                }
            }
        
            mediaRecorder.start(250);
        };
        

        socket.onmessage = async (message) => {
            try {
                const received = JSON.parse(message.data);
                const transcript = received["transcript"];
                const groqResponse = received["groq_response"];

                if (groqResponse) {
                    

                    const audioUrl = await getDeepgramTTS(groqResponse);
                    if (audioUrl) {
                        playAudio(audioUrl);
                        updateChat(transcript, groqResponse);
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
            disconnectTimeout = setTimeout(() => {
                if (spokenOnce) {
                    document.getElementById("disconnectedButton").classList.remove("hidden");
                }
            }, 50);
            
            
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
    document.querySelector("#buttonsup").textContent = "Click to connect";
    isConnected = false;
    updateMicIcon();
};
