/**
 * pcm-worklet-processor.js
 *
 * Runs in the browser's dedicated audio rendering thread (not the main
 * thread) via AudioWorklet. Receives Float32 audio samples at whatever
 * native sample rate the browser's AudioContext is running (typically
 * 44.1kHz or 48kHz — this varies by browser and is NOT something you can
 * rely on being 16kHz), downsamples to 16kHz, converts to 16-bit signed
 * PCM (s16le), and posts the resulting ArrayBuffer back to the main thread.
 *
 * This is required because WhisperLiveKit's --pcm-input mode expects raw
 * PCM s16le at ~16kHz — see plan section 6.
 */

class PCMWorkletProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    this.inputSampleRate = sampleRate; // global provided by AudioWorkletGlobalScope
    this.targetSampleRate = (options.processorOptions && options.processorOptions.targetSampleRate) || 16000;
    this.resampleRatio = this.inputSampleRate / this.targetSampleRate;
    this._fractionalIndex = 0;
  }

  /**
   * Simple linear-interpolation downsampler. Not the highest-quality
   * resampling algorithm available, but correct, dependency-free, and
   * fast enough to run per-audio-block in real time — appropriate for a
   * hackathon MVP. Revisit only if transcription quality suffers.
   */
  _downsample(inputChannelData) {
    const outputLength = Math.floor(inputChannelData.length / this.resampleRatio);
    const output = new Float32Array(outputLength);

    let inputIndex = this._fractionalIndex;
    for (let i = 0; i < outputLength; i++) {
      const idx = Math.floor(inputIndex);
      const frac = inputIndex - idx;
      const sample1 = inputChannelData[idx] || 0;
      const sample2 = inputChannelData[idx + 1] || sample1;
      output[i] = sample1 + (sample2 - sample1) * frac;
      inputIndex += this.resampleRatio;
    }
    this._fractionalIndex = inputIndex - Math.floor(inputIndex / inputChannelData.length) * inputChannelData.length;

    return output;
  }

  _floatToInt16PCM(floatSamples) {
    const int16 = new Int16Array(floatSamples.length);
    for (let i = 0; i < floatSamples.length; i++) {
      const clamped = Math.max(-1, Math.min(1, floatSamples[i]));
      int16[i] = clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff;
    }
    return int16;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || input.length === 0) {
      return true; // keep processor alive even if no input yet
    }

    const channelData = input[0]; // mono — downmix isn't needed since
    // getDisplayMedia tab audio typically arrives as a single usable channel
    // for speech; revisit if multi-channel handling proves necessary.
    if (!channelData || channelData.length === 0) {
      return true;
    }

    const downsampled = this._downsample(channelData);
    const pcm16 = this._floatToInt16PCM(downsampled);

    this.port.postMessage(pcm16.buffer, [pcm16.buffer]);

    return true; // returning false would stop the processor
  }
}

registerProcessor('pcm-worklet-processor', PCMWorkletProcessor);
