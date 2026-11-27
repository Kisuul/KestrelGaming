---
name: audio-test-signals
description: Design and verify digital audio stimuli with exact sample support. Use for coherent or off-bin tones, impulse timing, multitone headroom, seeded noise, logarithmic sweeps, or phase continuity across blocks.
---

# Audio test signals

1. **Choose the stimulus.** Use a tone for scale or leakage,
   an impulse for timing, a mixture for interacting tones,
   or a sweep for broadband response. Use the shared bank
   for short fixtures and seeded noise.
   [Signal selection](references/TEST_SIGNALS_CONTRACT.md#choose-the-stimulus)
2. **Declare the sample clock.** Record the epoch, active
   span, exact rate, phase, channel order, guards, and units.
   Render each block against the original phase anchor.
   [Support and phase](references/TEST_SIGNALS_CONTRACT.md#support-and-phase)
3. **Budget level and bandwidth.** Check the declared peak
   bound and measure sample peak and RMS. Set sweep limits,
   retain response-tail samples, and verify usable excitation.
   [Multitone levels](references/TEST_SIGNALS_CONTRACT.md#multitone-levels) ·
   [Logarithmic sweeps](references/TEST_SIGNALS_CONTRACT.md#logarithmic-sweeps)
4. **Verify the realized signal.** Compare a large-origin
   block replay, a phase-dependent Nyquist tone, and a
   complete known-filter response with their expected values.
   [Offline reference](scripts/reference_test_signals.py) ·
   [Fixtures](../../tests/fixtures/AUDIO_TEST_SIGNALS_GOLDENS.md)
