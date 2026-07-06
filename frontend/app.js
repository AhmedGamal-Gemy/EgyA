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
 *      (Option A from the plan), using mode=diff.
 *   4. WhisperLiveKit sends transcription results back over that same
 *      connection. Each newly-committed line is forwarded to Stream
 *      Judge's endpoint for judgment.
 *
 * PROTOCOL — confirmed from WhisperLiveKit's official docs/API.md
 * (not guessed — see plan section 6 for the citation), summarized here:
 *
 *   On connect, server sends once:
 *     {"type": "config", "useAudioWorklet": true, "mode": "diff"}
 *
 *   With ?mode=diff (used here instead of the default "full" mode,
 *   because it gives new_lines explicitly instead of resending the
 *   entire line list on every update):
 *     First message: {"type": "snapshot", "seq": 1, "lines": [...], ...}
 *     Then:          {"type": "diff", "seq": N, "new_lines": [...],
 *                      "lines_pruned": <int, optional>, ...}
 *
 *   Each line: {"speaker": <int>, "text": <string|null>, "start": ..., "end": ...}
 *     speaker === -2 with text === null means a silence segment — skip it.
 *
 *   At the very end: {"type": "ready_to_stop"}
 *
 * IMPORTANT CORRECTION vs an earlier draft of this file: WhisperLiveKit's
 * protocol does NOT include a per-line confidence score — this is
 * confirmed, not an oversight (its own Deepgram-compatible mode docs
 * explicitly say confidence is "not available"). The plan's original
 * "skip judgment below ASR confidence threshold" safeguard can't be
 * built as originally designed. Instead, uncertainty is now handled
 * entirely by the Judge LLM's own three-way verdict (correct/incorrect/
 * uncertain) in check_answer_correctness — see plan section 6 for the
 * updated reasoning.
 */

const WHISPER_LIVEKIT_WS_URL = window.WHISPER_LIVEKIT_WS_URL || 'ws://localhost:8000/asr?mode=diff';
const STREAM_JUDGE_BASE_URL = window.STREAM_JUDGE_BASE_URL || 'http://localhost:8002';
const TARGET_SAMPLE_RATE = 16000;
const SILENCE_SPEAKER_ID = -2;

let sessionId = null;
let displayStream = null;
let audioContext = null;
let workletNode = null;
let whisperSocket = null;
let localLines = []; // client-side reconstruction of committed lines, per the diff protocol

const statusEl = () => document.getElementById('status');
const transcriptEl = () => document.getElementById('transcript');

function setStatus(text) {
  const el = statusEl();
  if (el) el.textContent = text;
}

function appendTranscriptLine(line) {
  const el = transcriptEl();
  if (!el) return;
  const div = document.createElement('div');
  div.className = 'transcript-line';
  div.textContent = `[speaker ${line.speaker}] ${line.text}`;
  el.appendChild(div);
  el.scrollTop = el.scrollHeight;
}

async function forwardLineToStreamJudge(line) {
  try {
    await fetch(`${STREAM_JUDGE_BASE_URL}/session/${sessionId}/transcript-chunk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        text: line.text,
        speaker_id: String(line.speaker), // Stream Judge's schema uses string speaker_id; see plan section 6a
      }),
    });
  } catch (err) {
    // Non-fatal: don't let a Stream Judge hiccup break live transcription
    // display. Log and continue — this is a hackathon MVP, not a system
    // that needs guaranteed delivery.
    console.warn('Failed to forward line to Stream Judge:', err);
  }
}

/**
 * Handles one incoming WebSocket message per WhisperLiveKit's documented
 * diff-mode protocol. Mutates localLines in place and forwards any newly
 * committed (non-silence) lines to Stream Judge.
 */
function handleWhisperLiveKitMessage(raw) {
  let msg;
  try {
    msg = JSON.parse(raw);
  } catch (e) {
    console.warn('Non-JSON message from WhisperLiveKit, ignoring:', raw);
    return;
  }

  if (msg.type === 'config') {
    console.log('WhisperLiveKit config:', msg);
    if (!msg.useAudioWorklet) {
      console.warn('Server did NOT report useAudioWorklet=true — check --pcm-input is set (plan section 5b).');
    }
    return;
  }

  if (msg.type === 'ready_to_stop') {
    setStatus('Session ended.');
    return;
  }

  let newLines = [];

  if (msg.type === 'snapshot') {
    localLines = msg.lines || [];
    newLines = localLines; // treat all initial lines as "new" for forwarding purposes
  } else if (msg.type === 'diff') {
    const pruned = msg.lines_pruned || 0;
    if (pruned > 0) {
      localLines.splice(0, pruned);
    }
    newLines = msg.new_lines || [];
    localLines = localLines.concat(newLines);
    // Sanity check per the plan's documented client-reconstruction algorithm —
    // a mismatch means the client fell out of sync and should reconnect.
    if (typeof msg.n_lines === 'number' && localLines.length !== msg.n_lines) {
      console.warn(`Line count out of sync (local=${localLines.length}, server n_lines=${msg.n_lines}) — consider reconnecting.`);
    }
  } else {
    // Unexpected message shape — log it rather than silently ignoring,
    // since this is exactly the kind of thing that should be caught on
    // Day 1 if the real server behaves differently than documented.
    console.warn('Unrecognized message shape from WhisperLiveKit:', msg);
    return;
  }

  for (const line of newLines) {
    if (line.speaker === SILENCE_SPEAKER_ID || line.text === null) {
      continue; // silence segment, nothing to transcribe or judge
    }
    appendTranscriptLine(line);
    forwardLineToStreamJudge(line);
  }
}

function connectToWhisperLiveKit() {
  localLines = [];
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
  // Deliberately NOT connecting workletNode to audioContext.destination —
  // doing so would play the captured audio back out loud, which is not
  // wanted here (we only want to process it, not echo it back).

  connectToWhisperLiveKit();
  setStatus('Capturing tab audio...');

  // If the instructor stops sharing via the browser's own UI, clean up.
  audioTracks[0].addEventListener('ended', stopCapture);
}

function stopCapture() {
  if (whisperSocket) {
    // Signal end-of-audio per the documented protocol so the server
    // flushes remaining audio and sends ready_to_stop, rather than just
    // dropping the connection abruptly.
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
  setStatus('Stopped.');
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('startButton')?.addEventListener('click', startCapture);
  document.getElementById('stopButton')?.addEventListener('click', stopCapture);
});
