/**
 * app.js — AI Education Session Copilot frontend
 *
 * Architecture (see plan section 6 for the full reasoning):
 *   1. getDisplayMedia() captures the meeting TAB's audio (not the mic —
 *      in a virtual class, student voices come through speakers/output,
 *      not the instructor's mic). Requires Chrome/Edge; requires the
 *      instructor to run Zoom/Meet/Teams via its WEB client in another
 *      tab, then pick "Chrome Tab" + "Share tab audio" in the picker.
 *   2. AudioWorklet (pcm-worklet-processor.js) downsamples to 16kHz PCM
 *      s16le, since WhisperLiveKit's --pcm-input mode expects that format
 *      and browsers default to 44.1/48kHz.
 *   3. This app connects DIRECTLY to WhisperLiveKit's /asr WebSocket
 *      (Option A from the plan) and streams PCM frames to it.
 *   4. WhisperLiveKit sends FrontData objects back (confirmed from source:
 *      whisperlivekit/timed_objects.py at main). Each newly received
 *      committed line is forwarded to Stream Judge's endpoint for judgment.
 *
 * PROTOCOL — confirmed from WhisperLiveKit's source, not guessed:
 *
 *   On connect, server sends once:
 *     {"type": "config", "useAudioWorklet": true, "mode": "full"}
 *
 *   Data messages (serialized FrontData):
 *     {
 *       "status": "",
 *       "lines": [{"speaker": <int>, "text": <string>, "start": "H:MM:SS.cc", "end": "H:MM:SS.cc"}, ...],
 *       "buffer_transcription": "interim text...",
 *       "buffer_diarization": "",
 *       "buffer_translation": "",
 *       "remaining_time_transcription": 0.0,
 *       "remaining_time_diarization": 0.0
 *     }
 *     - "lines" holds committed/finalized segments.
 *     - "buffer_transcription" holds provisional (not yet finalized) text.
 *     - A line with speaker===-2 and text===null is a silence segment — skip it.
 *     - There is NO per-line confidence score in the FrontData format
 *       (confirmed in timed_objects.py — Segment.to_dict() omits it).
 *
 *   At the very end: {"type": "ready_to_stop"}
 */

const WHISPER_LIVEKIT_WS_URL = window.WHISPER_LIVEKIT_WS_URL || 'ws://localhost:8050/asr';
const STREAM_JUDGE_BASE_URL = window.STREAM_JUDGE_BASE_URL || 'http://localhost:8002';
const TARGET_SAMPLE_RATE = 16000;
const SILENCE_SPEAKER_ID = -2;

let sessionId = null;
let displayStream = null;
let audioContext = null;
let workletNode = null;
let whisperSocket = null;
let lastLineCount = 0;

const statusEl = () => document.getElementById('status');
const transcriptEl = () => document.getElementById('transcript');

function setStatus(text) {
  const el = statusEl();
  if (el) el.textContent = text;
}

function appendTranscriptLine(speaker, text) {
  const el = transcriptEl();
  if (!el) return;
  const line = document.createElement('div');
  line.className = 'transcript-line';
  line.textContent = `[speaker ${speaker}] ${text}`;
  el.appendChild(line);
  el.scrollTop = el.scrollHeight;
}

function updateInterimText(text) {
  const el = transcriptEl();
  if (!el) return;
  let interim = el.querySelector('.interim');
  if (!interim) {
    interim = document.createElement('div');
    interim.className = 'transcript-line interim';
    interim.style.color = '#888';
    interim.style.fontStyle = 'italic';
    el.appendChild(interim);
  }
  interim.textContent = text ? `… ${text}` : '';
}

async function forwardLineToStreamJudge(speaker, text) {
  try {
    await fetch(`${STREAM_JUDGE_BASE_URL}/session/${sessionId}/transcript-chunk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        text: text,
        speaker_id: String(speaker),
      }),
    });
  } catch (err) {
    console.warn('Failed to forward line to Stream Judge:', err);
  }
}

function handleWhisperLiveKitMessage(raw) {
  let msg;
  try {
    msg = JSON.parse(raw);
  } catch (e) {
    console.warn('Non-JSON message from WhisperLiveKit, ignoring:', raw);
    return;
  }

  // Config message — sent once on connect
  if (msg.type === 'config') {
    console.log('WhisperLiveKit config:', msg);
    if (!msg.useAudioWorklet) {
      console.warn('Server did not report useAudioWorklet=true — check --pcm-input is set.');
    }
    return;
  }

  // End-of-session signal
  if (msg.type === 'ready_to_stop') {
    setStatus('Session ended.');
    return;
  }

  // FrontData: broadcast on every transcription update
  const lines = msg.lines || [];
  const buffer = msg.buffer_transcription || '';

  // Lines that are new since last message
  if (lines.length > lastLineCount) {
    const newLines = lines.slice(lastLineCount);
    for (const line of newLines) {
      if (line.speaker === SILENCE_SPEAKER_ID || line.text === null) {
        continue;
      }
      appendTranscriptLine(line.speaker, line.text);
      forwardLineToStreamJudge(line.speaker, line.text);
    }
  }
  lastLineCount = lines.length;

  // Show interim (not-yet-committed) text
  updateInterimText(buffer);
}

function connectToWhisperLiveKit() {
  lastLineCount = 0;
  whisperSocket = new WebSocket(WHISPER_LIVEKIT_WS_URL);
  whisperSocket.binaryType = 'arraybuffer';

  whisperSocket.onopen = () => setStatus('Connected — listening...');

  whisperSocket.onmessage = (event) => handleWhisperLiveKitMessage(event.data);

  whisperSocket.onerror = (err) => {
    console.error('WhisperLiveKit WebSocket error:', err);
    setStatus('Connection error — check whisper-livekit is running.');
  };

  whisperSocket.onclose = () => setStatus('Disconnected.');
}

async function startCapture() {
  sessionId = document.getElementById('sessionIdInput')?.value || crypto.randomUUID();

  try {
    // video: true is required by getDisplayMedia() even though we only
    // want audio — the picker still needs a video surface to select from.
    displayStream = await navigator.mediaDevices.getDisplayMedia({
      video: true,
      audio: true,
    });
  } catch (err) {
    setStatus('Screen/tab share was cancelled or denied.');
    console.error(err);
    return;
  }

  const audioTracks = displayStream.getAudioTracks();
  if (audioTracks.length === 0) {
    setStatus('No audio track captured — did you check "Share tab audio"?');
    displayStream.getTracks().forEach((t) => t.stop());
    return;
  }

  audioContext = new AudioContext();
  await audioContext.audioWorklet.addModule('pcm-worklet-processor.js');

  const sourceNode = audioContext.createMediaStreamSource(displayStream);
  workletNode = new AudioWorkletNode(audioContext, 'pcm-worklet-processor', {
    processorOptions: { targetSampleRate: TARGET_SAMPLE_RATE },
  });

  workletNode.port.onmessage = (event) => {
    if (whisperSocket && whisperSocket.readyState === WebSocket.OPEN) {
      whisperSocket.send(event.data); // raw Int16 PCM ArrayBuffer, s16le
    }
  };

  sourceNode.connect(workletNode);

  connectToWhisperLiveKit();
  setStatus('Capturing tab audio...');

  audioTracks[0].addEventListener('ended', stopCapture);
}

function stopCapture() {
  if (whisperSocket) {
    // Send an empty byte buffer to signal end-of-audio so the server
    // flushes its pipeline and sends ready_to_stop.
    if (whisperSocket.readyState === WebSocket.OPEN) {
      whisperSocket.send(new ArrayBuffer(0));
    }
    whisperSocket.close();
    whisperSocket = null;
  }
  if (workletNode) {
    workletNode.disconnect();
    workletNode = null;
  }
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  if (displayStream) {
    displayStream.getTracks().forEach((t) => t.stop());
    displayStream = null;
  }
  lastLineCount = 0;
  setStatus('Stopped.');
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('startButton')?.addEventListener('click', startCapture);
  document.getElementById('stopButton')?.addEventListener('click', stopCapture);
});
