let mediaRecorder;
let socket;
let stopwatchInterval;
let remainingTime = 90;
let totalAccuracy = 0;
let countdownInterval;
let totalLatency = 0;
let transcriptCount = 0;

// Queue to handle audio playbacks
let audioQueue = [];
let currentAudio = null;

// Start the stopwatch countdown
const startStopwatch = () => {
  countdownInterval = setInterval(() => {
    remainingTime -= 1;
    if (remainingTime >= 0) {
      updateStopwatch();
    } else {
      closeConnection();
    }
  }, 1000);
};

// Update the stopwatch display
const updateStopwatch = () => {
  const minutes = Math.floor(remainingTime / 60);
  const seconds = remainingTime % 60;
  document.querySelector("#stopwatch").textContent = `${minutes}:${
    seconds < 10 ? "0" : ""
  }${seconds}`;
};

const stopStopwatch = () => {
  clearInterval(countdownInterval);
};

const resetStopwatch = () => {
  remainingTime = 90;
  updateStopwatch();
};

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
      console.error(
        "Deepgram API request failed:",
        response.status,
        response.statusText
      );
      return null;
    }
  } catch (error) {
    console.error("Error calling Deepgram API:", error);
    return null;
  }
}

// Function to manage audio playback
function playAudioQueue(audioUrl) {
  // Add the new audio URL to the queue
  audioQueue.push(audioUrl);
  
  // If no audio is currently playing, play the next one in the queue
  if (!currentAudio) {
    playNextAudio();
  }
}

function playNextAudio() {
  // If there's audio in the queue
  if (audioQueue.length > 0) {
    const nextAudioUrl = audioQueue.shift(); // Get the next audio URL
    currentAudio = new Audio(nextAudioUrl); // Create a new Audio object

    currentAudio.play(); // Play the audio

    // When the current audio finishes, play the next one
    currentAudio.onended = () => {
      currentAudio = null;
      playNextAudio();
    };

    // If interrupted (a new audio is added), stop the current audio and play the new one
    currentAudio.onplay = () => {
      if (audioQueue.length > 0) {
        currentAudio.pause(); // Stop the current audio
        currentAudio = null;
        playNextAudio(); // Play the next audio in the queue
      }
    };
  }
}

const askpermission = () => {
  console.log("Yeah we started");

  // Close the existing WebSocket connection if it exists
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.close();
  }

  // Stop the existing MediaRecorder if it exists
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
  }

  navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
    if (!MediaRecorder.isTypeSupported("audio/webm"))
      return alert("Browser not supported");

    mediaRecorder = new MediaRecorder(stream, {
      mimeType: "audio/webm",
    });

    socket = new WebSocket(`ws://${window.location.host}/listen`);
    console.log(window.location.host);

    socket.onopen = () => {
      document.querySelector("#status").textContent = "Connected";
      startStopwatch();

      mediaRecorder.addEventListener("dataavailable", async (event) => {
        if (event.data.size > 0 && socket.readyState === WebSocket.OPEN) {
          socket.send(event.data);
        }
      });

      mediaRecorder.start(250);

      setTimeout(() => {
        closeConnection();
      }, 90000); // 90 seconds
    };

    socket.onmessage = async (message) => {
      try {
        const received = JSON.parse(message.data);
        console.log("Received Data:", received);

        if (received) {
          const accuracy = received["accuracy"];
          const latency = received["latency"];
          const transcript = received["transcript"];
          const groqResponse = received["groq_response"];

          // Update the page with the received transcript and Groq response
          document.querySelector("#transcript").value += " " + transcript;
          if (groqResponse) {
            document.querySelector("#bot").value += " " + groqResponse;

            // Call Deepgram TTS and play the response
            const audioUrl = await getDeepgramTTS(groqResponse);
            if (audioUrl) {
              playAudioQueue(audioUrl); // Use the queue system for audio playback
            }
          }

          // Update accuracy and latency values
          document.querySelector("#accuracy").textContent = accuracy.toFixed(2);
          document.querySelector("#latency").textContent = latency.toFixed(2);

          // Calculate and update average accuracy and latency
          totalAccuracy += accuracy;
          totalLatency += latency;
          transcriptCount++;

          const averageAccuracy = (totalAccuracy / transcriptCount).toFixed(2);
          const averageLatency = (totalLatency / transcriptCount).toFixed(2);

          document.querySelector("#averageAccuracy").textContent =
            averageAccuracy;
          document.querySelector("#averageLatency").textContent =
            averageLatency;
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };

    socket.onclose = () => {
      console.log({ event: "onclose" });
      stopStopwatch();
    };

    socket.onerror = (error) => {
      console.log({ event: "onerror", error });
    };
  });
};

const clearTranscript = () => {
  document.querySelector("#transcript").value = "";
  document.querySelector("#accuracy").textContent = "0";
  document.querySelector("#latency").textContent = "0";
};

const closeConnection = () => {
  // Close the existing WebSocket connection if it exists
  try {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.close();
    }
  } catch {
    console.log("group_discard_Error");
  }
  // Stop the existing MediaRecorder if it exists
  try {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
    }
  } catch (error) {
    console.log("MediaREcording Error");
  }

  document.querySelector("#stopwatch").textContent = `${1}:${3}${0}`;
  resetStopwatch();
  document.querySelector("#status").textContent =
    "Disconnected!! ,Press Record to transcribe again";
  document.querySelector("#accuracy").textContent = "0";
  document.querySelector("#latency").textContent = "0";
};
