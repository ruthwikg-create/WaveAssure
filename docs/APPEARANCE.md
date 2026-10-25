# Appearance and motion controls (research UI)

In the top toolbar (including the isolated retrospective reviewer page):

- **Theme — System:** follows the browser/operating-system light/dark preference.
- **Theme — Light:** high-contrast pale cards and dark lettering.
- **Theme — Dark:** high-contrast dark panels and light lettering.
- **Motion on/off:** defaults to off and controls only brief hover/focus feedback. Card entrance effects, glowing status indicators, and ambient motion have been removed. Operating-system reduced-motion preference always overrides this setting.

Choices are stored only in your browser's local storage, under `waveassure.theme.v1` and `waveassure.motion.v1`. They are not sent to the backend, included in clinical evidence, or applied to waveform numerical values.

The waveform renderer uses different **static** high-contrast colors for ECG, PPG and ABP, but preserves all data and time coordinates. No ECG animation should be interpreted as real-time monitoring. When a theme changes, the current review selections are not reset.

Keyboard users can tab to the appearance selector and motion button. Appearance CSS uses `:focus-visible`, and the motion preference can be disabled explicitly. Please complete independent screen-reader and actual hospital user testing before any regulated use.

See [the interface design decisions](INTERFACE_CRAFT.md) for implementation details.
