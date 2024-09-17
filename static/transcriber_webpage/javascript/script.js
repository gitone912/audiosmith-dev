let mediaRecorder;
let socket;
let totalAccuracy = 0;
let totalLatency = 0;
let transcriptCount = 0;
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

// Function to play the audio, immediately stopping any current playback
function playAudio(audioUrl) {
  // Stop current audio if it is playing
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0; // Reset playback position
  }

  // Create new audio and play it
  currentAudio = new Audio(audioUrl);
  currentAudio.play();
  
  // Clear currentAudio when playback finishes
  currentAudio.onended = () => {
    currentAudio = null;
  };
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

            // Call Deepgram TTS and play the response immediately
            const audioUrl = await getDeepgramTTS(groqResponse);
            if (audioUrl) {
              playAudio(audioUrl); // Immediately play the new audio
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

          document.querySelector("#averageAccuracy").textContent = averageAccuracy;
          document.querySelector("#averageLatency").textContent = averageLatency;
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };

    socket.onclose = () => {
      console.log({ event: "onclose" });
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
    console.log("MediaRecording Error");
  }

  document.querySelector("#status").textContent =
    "Disconnected!! ,Press Record to transcribe again";
  document.querySelector("#accuracy").textContent = "0";
  document.querySelector("#latency").textContent = "0";
};
