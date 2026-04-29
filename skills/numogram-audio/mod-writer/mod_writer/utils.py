"""
Sample generation and note utilities.
"""

def generate_square_wave(duration_secs: float = 0.1, freq: float = 440.0,
                         sample_rate: int = 8363, amplitude: float = 0.5) -> bytes:
    """
    Generate 8-bit signed PCM square wave.
    Protracker sample rate ~8363 Hz. amplitude 0–1.
    Returns raw bytes (little-endian 16-bit signed, but .mod uses 8-bit offset-binary)
    """
    n_samples = int(duration_secs * sample_rate)
    period = sample_rate / freq
    samples = []
    for i in range(n_samples):
        # Square wave: +1 for first half of period, -1 for second
        phase = (i % period) / period
        val = 1.0 if phase < 0.5 else -1.0
        samples.append(val * amplitude)
    
    # Convert to 8-bit signed (0-255, 128=zero)
    pcm8 = bytes([int(128 + 127 * s) for s in samples])
    return pcm8

def generate_triangle_wave(duration_secs: float = 0.1, freq: float = 440.0,
                            sample_rate: int = 8363, amplitude: float = 0.5) -> bytes:
    n_samples = int(duration_secs * sample_rate)
    period = sample_rate / freq
    samples = []
    for i in range(n_samples):
        phase = (i % period) / period
        # Triangle: 0..1..0..-1..0 shape going from 0 to 1 to 0 to -1 to 0
        if phase < 0.25:
            val = phase * 4        # 0 -> 1
        elif phase < 0.75:
            val = 1 - (phase - 0.25) * 4  # 1 -> -1
        else:
            val = -1 + (phase - 0.75) * 4 # -1 -> 0
        samples.append(val * amplitude)
    return bytes([int(128 + 127 * s) for s in samples])

def generate_noise(duration_secs: float = 0.1, sample_rate: int = 8363,
                   amplitude: float = 0.5) -> bytes:
    import random
    n_samples = int(duration_secs * sample_rate)
    samples = [random.uniform(-1, 1) * amplitude for _ in range(n_samples)]
    return bytes([int(128 + 127 * s) for s in samples])
