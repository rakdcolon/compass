/**
 * Compass Voice Module
 * Handles audio capture (microphone → PCM 16kHz) and playback (PCM → speakers).
 * Bridges browser audio ↔ Nova 2 Sonic via WebSocket.
 */

const Voice = (() => {
  let ws = null;
  let mediaStream = null;
  let audioContext = null;
  let mediaRecorder = null;
  let isRecording = false;
  let waveformAnimationId = null;
  let analyser = null;

  const SAMPLE_RATE = 16000;
  const CHUNK_INTERVAL_MS = 100; // Send audio chunks every 100ms

  /**
   * Initialize a WebSocket connection to the Nova Sonic voice endpoint.
   * @param {string} sessionId
   * @param {string} language
   */
  async function connect(sessionId, language = 'en') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/voice/${sessionId}?language=${language}`;

    return new Promise((resolve, reject) => {
      ws = new WebSocket(wsUrl);
      ws.binaryType = 'arraybuffer';

      ws.onopen = () => {
        console.log('[Voice] WebSocket connected');
        resolve(ws);
      };

      ws.onerror = (err) => {
        console.error('[Voice] WebSocket error:', err);
        reject(err);
      };

      ws.onmessage = (event) => {
        if (event.data instanceof ArrayBuffer) {
          // Binary audio data from Nova Sonic
          playAudioChunk(event.data);
        } else {
          try {
            const msg = JSON.parse(event.data);
            handleVoiceEvent(msg);
          } catch (e) {
            console.warn('[Voice] Could not parse message:', event.data);
          }
        }
      };

      ws.onclose = () => {
        console.log('[Voice] WebSocket closed');
        stopRecording();
      };
    });
  }

  /**
   * Handle JSON events from the voice WebSocket.
   */
  function handleVoiceEvent(msg) {
    switch (msg.type) {
      case 'transcript':
        // User's speech transcription
        document.getElementById('transcript-display').textContent = `You: "${msg.text}"`;
        break;

      case 'response_text':
        // Nova Sonic's text response
        App.addMessage('assistant', msg.text, { isVoice: true });
        break;

      case 'done':
        // Nova Sonic finished responding
        setVoiceStatus('listening', 'Listening...');
        break;

      case 'error':
        App.showToast(msg.message || 'Voice error', 'error');
        stopRecording();
        break;

      case 'audio_meta':
        // Metadata about incoming audio
        break;

      case 'pong':
        // Keepalive response
        break;
    }
  }

  /**
   * Start recording from the microphone.
   * Captures audio, resamples to PCM 16kHz, and streams to Nova Sonic.
   */
  async function startRecording() {
    if (isRecording) return;

    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: SAMPLE_RATE,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });

      audioContext = new AudioContext({ sampleRate: SAMPLE_RATE });
      const source = audioContext.createMediaStreamSource(mediaStream);

      // Analyser for waveform visualization
      analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);

      // Use ScriptProcessor for audio capture (works across browsers)
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      source.connect(processor);
      processor.connect(audioContext.destination);

      processor.onaudioprocess = (e) => {
        if (!isRecording || !ws || ws.readyState !== WebSocket.OPEN) return;

        const inputData = e.inputBuffer.getChannelData(0);
        const pcmData = floatToPCM16(inputData);
        ws.send(pcmData.buffer);
      };

      isRecording = true;
      startWaveformAnimation();
      setVoiceStatus('recording', 'Recording... (speak now)');
      updateMicButton(true);

    } catch (err) {
      console.error('[Voice] Microphone access error:', err);
      App.showToast('Could not access microphone. Please check permissions.', 'error');
    }
  }

  /**
   * Stop recording and signal end to Nova Sonic.
   */
  function stopRecording() {
    if (!isRecording) return;
    isRecording = false;

    // Signal end of audio to Nova Sonic
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'stop' }));
    }

    // Stop media tracks
    if (mediaStream) {
      mediaStream.getTracks().forEach(t => t.stop());
      mediaStream = null;
    }

    if (audioContext) {
      audioContext.close().catch(() => {});
      audioContext = null;
    }

    stopWaveformAnimation();
    setVoiceStatus('idle', 'Click microphone to speak');
    updateMicButton(false);
  }

  /**
   * Toggle recording on/off.
   */
  async function toggleRecording() {
    if (isRecording) {
      stopRecording();
    } else {
      // Ensure WebSocket is connected
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        try {
          setVoiceStatus('connecting', 'Connecting...');
          await connect(App.getSessionId(), App.getLanguage());
        } catch (err) {
          App.showToast('Could not connect to voice service', 'error');
          return;
        }
      }
      await startRecording();
    }
  }

  /**
   * Play a PCM audio chunk received from Nova Sonic.
   * @param {ArrayBuffer} buffer - Raw PCM 16kHz mono 16-bit audio
   */
  function playAudioChunk(buffer) {
    if (!audioContext || audioContext.state === 'closed') {
      audioContext = new AudioContext({ sampleRate: SAMPLE_RATE });
    }

    const int16Array = new Int16Array(buffer);
    const float32Array = new Float32Array(int16Array.length);

    // Convert PCM 16-bit to float32
    for (let i = 0; i < int16Array.length; i++) {
      float32Array[i] = int16Array[i] / 32768.0;
    }

    const audioBuffer = audioContext.createBuffer(1, float32Array.length, SAMPLE_RATE);
    audioBuffer.copyToChannel(float32Array, 0);

    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);
    source.start();
  }

  /**
   * Convert Float32 audio to PCM 16-bit Int16Array.
   * @param {Float32Array} float32Array
   * @returns {Int16Array}
   */
  function floatToPCM16(float32Array) {
    const pcm = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return pcm;
  }

  /**
   * Animate the waveform canvas based on microphone input.
   */
  function startWaveformAnimation() {
    const canvas = document.getElementById('waveform-canvas');
    if (!canvas || !analyser) return;

    const ctx = canvas.getContext('2d');
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function draw() {
      waveformAnimationId = requestAnimationFrame(draw);
      analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = 'rgba(255,255,255,0.03)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const barWidth = (canvas.width / bufferLength) * 2.5;
      let barX = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height;
        const gradient = ctx.createLinearGradient(0, canvas.height - barHeight, 0, canvas.height);
        gradient.addColorStop(0, '#38bdf8');
        gradient.addColorStop(1, '#0ea5e9');
        ctx.fillStyle = gradient;
        ctx.fillRect(barX, canvas.height - barHeight, barWidth, barHeight);
        barX += barWidth + 1;
      }
    }

    draw();
  }

  function stopWaveformAnimation() {
    if (waveformAnimationId) {
      cancelAnimationFrame(waveformAnimationId);
      waveformAnimationId = null;
    }

    const canvas = document.getElementById('waveform-canvas');
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  function setVoiceStatus(state, text) {
    const dot = document.getElementById('voice-status-dot');
    const label = document.getElementById('voice-status-text');
    if (!dot || !label) return;

    label.textContent = text;
    dot.className = 'w-3 h-3 rounded-full';
    if (state === 'recording') {
      dot.className += ' bg-red-500 animate-pulse';
    } else if (state === 'connecting') {
      dot.className += ' bg-yellow-400 animate-pulse';
    } else {
      dot.className += ' bg-slate-500';
    }
  }

  function updateMicButton(active) {
    const btns = ['btn-mic-chat', 'btn-voice-bar'];
    btns.forEach(id => {
      const btn = document.getElementById(id);
      if (!btn) return;
      if (active) {
        btn.classList.add('bg-red-600');
        btn.classList.remove('bg-blue-600');
      } else {
        btn.classList.remove('bg-red-600');
        btn.classList.add('bg-blue-600');
      }
    });
  }

  function disconnect() {
    stopRecording();
    if (ws) {
      ws.close();
      ws = null;
    }
  }

  return { connect, startRecording, stopRecording, toggleRecording, disconnect };
})();
