"""Bounded, deterministic raw PCM sample conversion reference.

No WAV container parser, channel remix, dither, noise shaping or realtime promises.
The rules are explicit and deliberately narrower than all supported audio formats.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import struct

MAX_REFERENCE_FRAMES = 256
_FORMAT_BITS = {"u8": 8, "s16": 16, "s24": 24, "s32": 32, "f32": 32, "f64": 64}


@dataclass(frozen=True)
class PCMFormat:
    kind: str
    channels: int
    byte_order: str = "little"
    layout: str = "interleaved"
    valid_bits: int | None = None
    channel_labels: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if self.kind not in _FORMAT_BITS:
            raise ValueError("unknown raw PCM sample kind")
        if not isinstance(self.channels, int) or isinstance(self.channels, bool) or not 1 <= self.channels <= 8:
            raise ValueError("channels must be an integer 1..8")
        if self.byte_order not in ("little", "big"):
            raise ValueError("byte_order must be little or big")
        if self.layout not in ("interleaved", "planar"):
            raise ValueError("layout must be interleaved or planar")
        if self.kind.startswith("f"):
            if self.valid_bits is not None:
                raise ValueError("floating-point PCM has no valid_bits field in this oracle")
        else:
            bits = self.container_bits
            valid = bits if self.valid_bits is None else self.valid_bits
            if not isinstance(valid, int) or isinstance(valid, bool):
                raise ValueError("valid_bits must be an integer")
            if self.kind == "u8":
                if valid != 8:
                    raise ValueError("unsigned 8-bit PCM requires exactly 8 valid bits")
            elif not 2 <= valid <= bits:
                raise ValueError("signed PCM valid_bits must be between 2 and container width")
        if self.channel_labels is not None:
            labels = self.channel_labels
            if (not isinstance(labels, tuple) or len(labels) != self.channels
                    or any(not isinstance(v, str) or not v.strip() for v in labels)
                    or len(set(labels)) != len(labels)):
                raise ValueError("channel labels must be distinct nonempty strings matching channel count")

    @property
    def container_bits(self) -> int:
        return _FORMAT_BITS[self.kind]

    @property
    def precision_bits(self) -> int:
        return self.container_bits if self.valid_bits is None else self.valid_bits

    @property
    def bytes_per_sample(self) -> int:
        return self.container_bits // 8

    @property
    def bytes_per_frame(self) -> int:
        return self.channels * self.bytes_per_sample


def _layout_bytes(payload: bytes | list[bytes], fmt: PCMFormat) -> tuple[list[bytes], int]:
    if fmt.layout == "interleaved":
        if not isinstance(payload, (bytes, bytearray)):
            raise ValueError("interleaved payload must be one bytes object")
        if not len(payload) or len(payload) % fmt.bytes_per_frame:
            raise ValueError("interleaved length must be a nonzero whole number of frames")
        n = len(payload) // fmt.bytes_per_frame
        if n > MAX_REFERENCE_FRAMES:
            raise ValueError("reference frame limit exceeded")
        width = fmt.bytes_per_sample
        planes = [
            b"".join(payload[(i*fmt.channels+ch)*width:(i*fmt.channels+ch+1)*width]
                     for i in range(n))
            for ch in range(fmt.channels)
        ]
        return planes, n

    if not isinstance(payload, (list, tuple)) or len(payload) != fmt.channels:
        raise ValueError("planar payload must contain exactly one bytes plane per channel")
    if any(not isinstance(p, (bytes, bytearray)) for p in payload):
        raise ValueError("planar payload elements must be bytes")
    lengths = [len(p) for p in payload]
    if (not lengths[0] or any(size != lengths[0] for size in lengths)
            or lengths[0] % fmt.bytes_per_sample):
        raise ValueError("planar channels must have equal whole-sample nonzero lengths")
    n = lengths[0] // fmt.bytes_per_sample
    if n > MAX_REFERENCE_FRAMES:
        raise ValueError("reference frame limit exceeded")
    return [bytes(p) for p in payload], n


def decode_pcm(payload: bytes | list[bytes], fmt: PCMFormat) -> dict:
    """Decode raw interleaved/planar samples, not a RIFF/WAVE header or metadata."""
    if not isinstance(fmt, PCMFormat):
        raise ValueError("fmt must be PCMFormat")
    planes, frames = _layout_bytes(payload, fmt)
    width = fmt.bytes_per_sample
    precision = fmt.precision_bits
    pad_bits = fmt.container_bits - precision
    scale = float(1 << (precision - 1)) if fmt.kind != "u8" else 128.0
    out = []
    for plane in planes:
        samples = []
        for i in range(frames):
            raw = plane[i*width:(i+1)*width]
            if fmt.kind.startswith("f"):
                code = "f" if fmt.kind == "f32" else "d"
                value = struct.unpack(("<" if fmt.byte_order == "little" else ">") + code, raw)[0]
                if not math.isfinite(value):
                    raise ValueError("nonfinite floating-point PCM sample")
            else:
                signed = fmt.kind != "u8"
                code = int.from_bytes(raw, byteorder=fmt.byte_order, signed=signed)
                if pad_bits and (code & ((1 << pad_bits) - 1)):
                    raise ValueError("nonzero unused low bits in left-aligned PCM container")
                code >>= pad_bits
                if fmt.kind == "u8":
                    code -= 128
                value = code / scale
            samples.append(value)
        out.append(samples)
    return {
        "format": fmt.kind,
        "frames": frames,
        "channels": fmt.channels,
        "layout": fmt.layout,
        "channel_labels": fmt.channel_labels,
        "valid_bits": fmt.precision_bits if not fmt.kind.startswith("f") else None,
        "planar_samples": out,
        "normalization": "signed_2^(valid_bits-1)_or_unsigned8_center128" if not fmt.kind.startswith("f") else "native_ieee_float_no_clamp",
    }


def _numeric_sample(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("samples must be finite real numbers")
    try:
        x = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError("samples must fit a finite floating representation") from exc
    if not math.isfinite(x):
        raise ValueError("samples must be finite")
    return x


def encode_pcm(planar_samples: list[list[float]], fmt: PCMFormat,
               integer_overflow: str = "saturate") -> dict:
    """Encode normalized planar samples with deterministic ties-to-even rounding.

    Integer overflow options: saturate or error. No dither is applied.
    Floating formats preserve over-reference values where representable.
    """
    if not isinstance(fmt, PCMFormat):
        raise ValueError("fmt must be PCMFormat")
    if integer_overflow not in ("saturate", "error"):
        raise ValueError("integer_overflow must be saturate or error")
    if (not isinstance(planar_samples, (tuple, list))
            or len(planar_samples) != fmt.channels
            or any(not isinstance(channel, (tuple, list)) for channel in planar_samples)):
        raise ValueError("planar input must have exactly the declared channel count")
    frames = len(planar_samples[0])
    if not 1 <= frames <= MAX_REFERENCE_FRAMES or any(len(ch) != frames for ch in planar_samples):
        raise ValueError("channel lengths must match and be within reference limit")

    samples = [[_numeric_sample(x) for x in ch] for ch in planar_samples]
    bit_depth = fmt.precision_bits
    shift = fmt.container_bits - bit_depth
    scale = 1 << (bit_depth - 1)
    byte_planes = []
    saturated = [0] * fmt.channels
    float_underflow = [0] * fmt.channels
    beyond_ref = [sum(abs(x) > 1.0 for x in channel) for channel in samples]

    for ci, channel in enumerate(samples):
        output = bytearray()
        for x in channel:
            if fmt.kind.startswith("f"):
                code = "f" if fmt.kind == "f32" else "d"
                prefix = "<" if fmt.byte_order == "little" else ">"
                try:
                    raw = struct.pack(prefix + code, x)
                except (OverflowError, struct.error) as exc:
                    raise ValueError("floating PCM value is not representable") from exc
                represented = struct.unpack(prefix + code, raw)[0]
                if x != 0 and represented == 0:
                    float_underflow[ci] += 1
            else:
                # Positive 1.0 requires clipping under symmetric negative-power
                # normalization because +2^(B-1) has no signed PCM code.
                if x >= 1.0:
                    q = scale
                elif x < -1.0:
                    q = -scale - 1
                else:
                    q = round(x * scale)  # Python nearest/ties-to-even
                if q < -scale or q > scale - 1:
                    if integer_overflow == "error":
                        raise ValueError("integer quantization exceeds representable PCM range")
                    q = max(-scale, min(q, scale - 1))
                    saturated[ci] += 1
                stored = (q + 128) if fmt.kind == "u8" else (q << shift)
                raw = int(stored).to_bytes(fmt.bytes_per_sample, fmt.byte_order,
                                           signed=fmt.kind != "u8")
            output.extend(raw)
        byte_planes.append(bytes(output))

    if fmt.layout == "interleaved":
        width = fmt.bytes_per_sample
        payload = b"".join(
            byte_planes[ch][i*width:(i+1)*width]
            for i in range(frames) for ch in range(fmt.channels)
        )
    else:
        payload = byte_planes
    return {
        "payload": payload,
        "frames": frames,
        "saturated_samples_by_channel": saturated,
        "float_underflow_to_zero_by_channel": float_underflow,
        "over_reference_samples_by_channel": beyond_ref,
        "integer_rounding": "nearest_ties_to_even_without_dither",
        "integer_overflow": integer_overflow,
    }
