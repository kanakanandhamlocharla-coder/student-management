class AudioProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.targetSampleRate = 16000;
        this.audioBuffer = [];
    }

    downsampleTo16k(samples, inputRate) {
        if (inputRate === this.targetSampleRate) {
            return samples;
        }
        const ratio = inputRate / this.targetSampleRate;
        const outputLength = Math.floor(samples.length / ratio);
        const result = new Float32Array(outputLength);
        for (let i = 0; i < outputLength; i++) {
            const srcIndex = i * ratio;
            const low = Math.floor(srcIndex);
            const high = Math.min(low + 1, samples.length - 1);
            const frac = srcIndex - low;
            result[i] = samples[low] * (1 - frac) + samples[high] * frac;
        }
        return result;
    }

    process(inputs) {
        const input = inputs[0];
        if (input && input.length > 0 && input[0].length > 0) {
            // `sampleRate` is provided by AudioWorkletGlobalScope
            const resampled = this.downsampleTo16k(input[0], sampleRate);
            for (let i = 0; i < resampled.length; i++) {
                this.audioBuffer.push(resampled[i]);
            }

            if (this.audioBuffer.length >= 1600) {
                const pcmSamples = new Int16Array(this.audioBuffer.length);
                for (let i = 0; i < this.audioBuffer.length; i++) {
                    const sample = Math.max(-1, Math.min(1, this.audioBuffer[i]));
                    pcmSamples[i] = sample < 0 ? sample * 32768 : sample * 32767;
                }
                this.port.postMessage(pcmSamples, [pcmSamples.buffer]);
                this.audioBuffer = [];
            }
        }
        return true;
    }
}
registerProcessor("audio-processor", AudioProcessor);