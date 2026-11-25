class AudioProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.audioBuffer = []
    }
    process(inputs) {
        const input = inputs[0]
        if (input.length > 0) {
            const audioSamples = input[0]
            this.audioBuffer.push(...audioSamples)
            if (this.audioBuffer.length >= 1600) {
                // Even the microphone samples are Float32Array, we use "new Float32Array(this.audioBuffer)".
                // Because audioPacket is normal JavaScript array.
                // We use Float32Array to turn the collected samples into a typed array.
                const audioPacket = new Float32Array(this.audioBuffer)
                const pcmSamples = new Int16Array(audioPacket.length)
                for (let i=0; i < audioPacket.length; i++) {
                    const sample = Math.max(-1, Math.min(1, audioPacket[i]))
                    pcmSamples[i] = sample < 0 ? sample * 32768 : sample * 32767
                }
                this.port.postMessage(pcmSamples)
                this.audioBuffer = []
            }
        }
        return true
    }
}
registerProcessor("audio-processor", AudioProcessor)