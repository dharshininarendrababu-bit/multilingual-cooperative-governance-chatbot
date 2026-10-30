let mediaRecorder;
let audioChunks = [];

micBtn.addEventListener("click", async () => {
    if (mediaRecorder && mediaRecorder.state === "recording") {
        // Stop recording
        mediaRecorder.stop();
        recordingStatus.style.display = "none";
        micBtn.classList.remove("btn-danger");
        micBtn.classList.add("btn-outline-secondary");
        return;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
            const formData = new FormData();
            formData.append("audio", audioBlob, "voice.wav");
            formData.append("language", languageSelect.value);

            recordingStatus.innerText = "Transcribing with Sarvam AI...";
            recordingStatus.style.display = "inline";

            try {
                const res = await fetch("/api/transcribe", {
                    method: "POST",
                    body: formData
                });
                const data = await res.json();
                if (data.transcript) {
                    userInput.value = data.transcript;
                    sendMessage();
                } else {
                    alert("Voice transcription failed: " + (data.error || ""));
                }
            } catch (err) {
                console.error(err);
            } finally {
                recordingStatus.style.display = "none";
            }
        };

        mediaRecorder.start();
        recordingStatus.innerText = "🔴 Listening via Sarvam STT... Click mic again to stop";
        recordingStatus.style.display = "inline";
        micBtn.classList.remove("btn-outline-secondary");
        micBtn.classList.add("btn-danger");

    } catch (err) {
        alert("Microphone permission denied or not supported.");
    }
});
