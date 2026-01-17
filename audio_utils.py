import io
import numpy as np
import struct
import tempfile
import os
import subprocess
from logger import get_logger

logger = get_logger(__name__)

# 常量定义
DEFAULT_SAMPLE_RATE = 16000

def pcm_to_wav(pcm_data: np.ndarray, sample_rate: int = DEFAULT_SAMPLE_RATE) -> bytes:
    """Convert PCM data to WAV format with proper header"""
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = len(pcm_data) * 2
    total_size = 36 + data_size
    
    wav_header = struct.pack('<4sI4s', b'RIFF', total_size, b'WAVE')
    fmt_chunk = struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample)
    data_chunk_header = struct.pack('<4sI', b'data', data_size)
    
    wav_data = wav_header + fmt_chunk + data_chunk_header + pcm_data.tobytes()
    return wav_data

def convert_audio_format(
    audio_data: np.ndarray,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    target_format: str = "wav"
) -> bytes:
    """Convert numpy array audio data to specified format"""
    buffer = io.BytesIO()
    
    with io.BytesIO() as wav_file:
        # Write WAV header
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = len(audio_data) * 2
        total_size = 36 + data_size
        
        wav_header = struct.pack('<4sI4s', b'RIFF', total_size, b'WAVE')
        fmt_chunk = struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample)
        data_chunk_header = struct.pack('<4sI', b'data', data_size)
        
        wav_file.write(wav_header)
        wav_file.write(fmt_chunk)
        wav_file.write(data_chunk_header)
        wav_file.write(audio_data.tobytes())
        
        buffer.write(wav_file.getvalue())
    
    buffer.seek(0)
    return buffer.read()

def convert_mp3_to_pcm(mp3_data: bytes, target_sample_rate: int = DEFAULT_SAMPLE_RATE) -> np.ndarray:
    """Convert MP3 audio data to PCM numpy array"""
    try:
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as mp3_file:
            mp3_file.write(mp3_data)
            mp3_file.flush()
            mp3_path = mp3_file.name

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
            wav_path = wav_file.name

        try:
            subprocess.run([
                'ffmpeg', '-y',
                '-i', mp3_path,
                '-ar', str(target_sample_rate),
                '-ac', '1',
                '-f', 'wav',
                wav_path
            ], check=True, capture_output=True)

            with open(wav_path, 'rb') as f:
                wav_data = f.read()

            if len(wav_data) < 44:
                raise ValueError("Invalid WAV file: too small")

            header = wav_data[:44]
            if not header.startswith(b'RIFF') or b'WAVE' not in header:
                raise ValueError("Invalid WAV file: missing RIFF/WAVE header")

            audio_data = wav_data[44:]
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

            return audio_array

        finally:
            if os.path.exists(mp3_path):
                os.unlink(mp3_path)
            if os.path.exists(wav_path):
                os.unlink(wav_path)

    except Exception as e:
        logger.error(f"Audio conversion error: {e}")
        return np.array([], dtype=np.int16)

def compress_audio(audio_data: np.ndarray, compression_level: int = 1) -> bytes:
    """Compress audio data for efficient transmission"""
    try:
        import zlib
        
        # Convert to raw PCM data first
        pcm_data = audio_data.tobytes()
        
        # Use zlib compression
        compressed_data = zlib.compress(pcm_data, level=compression_level)
        
        # Add header with original length for decompression
        header = struct.pack('<I', len(pcm_data))
        
        return header + compressed_data
    except Exception as e:
        logger.error(f"Audio compression error: {e}")
        return audio_data.tobytes()

def decompress_audio(compressed_data: bytes) -> np.ndarray:
    """Decompress audio data"""
    try:
        # Check if it's a compressed format (starts with 4-byte header)
        if len(compressed_data) > 4:
            try:
                import zlib
                
                # Extract header to get original length
                original_length = struct.unpack('<I', compressed_data[:4])[0]
                
                # Decompress the data
                decompressed_data = zlib.decompress(compressed_data[4:])
                
                # Verify decompression success
                if len(decompressed_data) == original_length:
                    return np.frombuffer(decompressed_data, dtype=np.int16)
            except:
                # If decompression fails, fall back to other formats
                pass
        
        # Check if it's a WAV file
        if compressed_data.startswith(b'RIFF') and b'WAVE' in compressed_data[:12]:
            # Extract PCM data from WAV
            audio_data = compressed_data[44:]  # Skip WAV header
            return np.frombuffer(audio_data, dtype=np.int16)
        else:
            # Assume it's raw PCM data
            return np.frombuffer(compressed_data, dtype=np.int16)
    except Exception as e:
        logger.error(f"Audio decompression error: {e}")
        return np.array([], dtype=np.int16)

def calculate_audio_energy(audio_data: np.ndarray) -> float:
    """Calculate energy of audio data"""
    try:
        energy = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
        return energy / 32768.0  # Normalize to 0-1
    except Exception as e:
        logger.error(f"Error calculating audio energy: {e}")
        return 0.0

def detect_silence(audio_data: np.ndarray, threshold: float = 0.02) -> bool:
    """Detect if audio data is silent"""
    energy = calculate_audio_energy(audio_data)
    return energy < threshold
