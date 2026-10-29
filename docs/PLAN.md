# Spectrum Visualiser — Plan (Conceive + Design)

29 Oct 2026 · Joe

## Status

Skeleton code in place (headers + build files, no implementation). Hardware is known and both previous-student blogs are read; the plan below is built on what they actually did and didn't do. Live version of this plan: https://claude.ai/artifact/BAJq52LbSn5nmyxJky5Ten (this file is the repo copy).

| Part | What we have | What it means for the design |
| --- | --- | --- |
| Board | Freenove ESP32-S3-WROOM (same as the hourglass) | Not the classic ESP32 Aidan used: no I2S-ADC mode, his pins (GPIO 34/23/18/5/27) don't map across. Unplug the camera ribbon to free GPIO 4–18. |
| Input | MAX9814 electret mic module | Built-in automatic gain control (AGC); output sits on a 1.25 V bias with about 2 V peak-to-peak max. Nobody on the project has used it yet: Aidan's never arrived. |
| Display | 4-in-1 MAX7219 module, 32 × 8 (photo) | 32 columns, 8 rows — same as Aidan's |
| Other | Push button(s), resistors/caps from the kit; lab function generator (confirmed) | Electrical test path is available |

**Course repo not available** (github.com/caseyov/spectrumVisualiser is private), so the firmware is rebuilt from scratch in **ESP-IDF v6**, using Aidan's and Casey's blogs as the reference. The proposal and CDIO report are still Canvas-only.

**Carried over from the hourglass:** decision log, "tune from recorded data" (serial log → Python → charts), crediting example code in file headers, ESP32-S3 pin notes.

## What the brief is really marking

The brief rewards a system you can explain and prove, not the fanciest one. Every demo point needs a piece of evidence behind it, so plan the evidence now.

| Demo point in the brief | Where it lives in the write-up | Evidence that answers it |
| --- | --- | --- |
| Demonstrate with suitable input signals | Operate | Test-signal set (tones, sweeps, two-tone, noise, silence, music, speech) |
| Explain how the stages work together | Design | Block diagram + one paragraph per stage |
| Show how performance was tested | Implement / Operate | Test table with measured results, logs, photos, video |
| Useful operating range and limits | Conceive (target) → Operate (measured) | Frequency-response sweep; noise floor; clipping level |
| One significant decision or improvement | Design + decision log | Before/after measurement (e.g. linear vs log bands) |
| A failure mode or misleading behaviour | Design (risks) → Operate | Aliasing demo: tone above Nyquist shows up as a false low peak |
| Usability, inclusion, ethics, security, sustainability | Conceive | Short section, tied to concrete design choices |
| What you'd investigate next | Reflection | Ranked list from test results |

## What's been done before

The previous prototypes proved the pipeline works on a signal generator, but none used a microphone, none measured accuracy in numbers, and all mapped frequencies linearly. Those three gaps are where our work goes.

| Prototype | Input | Sampling / FFT | Mapping | Testing | Limits they found |
| --- | --- | --- | --- | --- | --- |
| Zhexi Zhang (via Casey's blog) | DC-biased, level-adjusted input + low-pass filter | Continuous ADC ~24 kHz (Nyquist 12 kHz) | Linear | 0–20 kHz sweep, broadband audio | Foldback above 12 kHz: high tones shown at low positions. Analogue filter reduced it, but distortion remained near the top. |
| Aidan Gan | Signal generator → 220 Ω + 22 nF → GPIO 34 (mic and jack never arrived) | analogRead() set to 60 kHz only reached ~12 kHz → switched to I2S-ADC + DMA, ~96 kHz, N = 512 (187.5 Hz per bin) | Linear, 4 ranges on a button: 0–6 / 12 / 18 / 24 kHz | Tones checked by eye ("near the centre") | ADC noise, simple input filter, low resolution of 8 × 32; mirrored peaks at high frequency (aliasing) |
| Shajeeb / HAZI-TECH | Line-in into Uno A0 | ~38.5 kHz, 64 samples (~600 Hz per bin) | 32 linear columns | Online tone generator, photos | Hand-tuned scaling; bass crammed into 1–2 columns |
| ShillehTek ESP32 + I2S mic | Digital I2S mic | 44.1 kHz, 1024 samples | 32 columns, low bands share bins | — | Calls itself a visual display, not an analyser; MAX7219 logic level vs 3.3 V |

What this tells us:

- **Measure the real sample rate first.** Aidan's ADC ran at a fifth of the rate he set. On the S3 the fast path is the ADC continuous (DMA) driver on ADC1; ESP-IDF says ADC2 DMA is no longer supported. Check the S3's maximum rate in `soc_caps.h` — don't assume 96 kHz carries over.
- **Aliasing is the known failure mode** in both prototypes. We should reproduce it on purpose, then show our fix with numbers.
- **Aidan's 0–6 kHz range puts 0–187 Hz in one column** — all bass and most of a male voice's pitch. That's the clearest thing to improve.

## Conceive — writing outline

Proposed product: an **"honest" sound-spectrum display for a teaching lab** that listens through a microphone. It should look good with music, but its main job is that a student can play a tone at it and trust which column lights up — and the display says so when it can't be trusted. (Alternative framing: a music visualiser where looks beat accuracy. Pick one as a team and say why.)

**1. Purpose statement** (2–3 sentences): what it does, for whom, and the one thing it must get right.

**2. Users and stakeholders**

| Stakeholder | What they need | Design consequence |
| --- | --- | --- |
| Students in a lab | Peaks in the right place; obvious when it's silent, overloaded or out of range | Status row, log mapping, tone-finder mode |
| Demonstrators | Repeatable demo, quick to set up | Known test signals, electrical test input as well as the mic |
| People in the room | Not recorded | Audio stays in RAM, no storage, no wireless, visible "listening" state |
| Our team / assessors | Evidence and explainable choices | Serial logging, decision log |
| Future teams | Can repair, adapt, reuse | All settings in one config block, documented wiring, public repo |

**3. Requirements with targets** (proposed — confirm after first tests)

| ID | Requirement | Proposed target | How it's checked |
| --- | --- | --- | --- |
| R1 | Useful range | ~100 Hz – 8 kHz through the mic (voice + most instruments) | Electrical sweep, then acoustic sweep |
| R2 | Frequency accuracy | A pure tone lights the correct column (±1) across R1 | Tone at each column's centre and edges |
| R3 | Responsiveness | Sound → LEDs under ~100 ms | Slow-mo phone video of a clap |
| R4 | Refresh | ≥ 20 frames/s | Frame time logged |
| R5 | Quiet room | ≤ 1 lit pixel per column | Silence test |
| R6 | Out-of-range honesty | Tones above the range never appear as false low peaks | Aliasing test (Zhexi's and Aidan's failure mode) |
| R7 | Loudness | Bar height rises with level; the AGC's squashing is measured and stated | Stepped-level test |
| R8 | Control | One button changes mode/range; choice survives a reset | Function test |

**4. Success criteria** — R1–R6 met; the music demo looks right; every limit (range, AGC, resolution, aliasing) is measured and stated, not hidden.

**5. Wider considerations** (one short paragraph each, tied to a design choice)

- **Privacy** (now central — the main input is a mic): audio is processed in memory and thrown away each frame; nothing stored or transmitted; no Wi-Fi/Bluetooth enabled; a button to stop listening, with a clear display state.
- **Inclusion**: single-colour display, so no colour coding to miss; adjustable brightness; no fast full-screen flashing (photosensitivity); useful to deaf or hard-of-hearing users as a sound-awareness display.
- **Security**: only relevant if wireless is added; leaving it off is itself a decision to log.
- **Sustainability**: low default brightness, standard parts, modular wiring, documented so the kit gets reused next year.

**6. Key risks** (detail in Design): S3 ADC speed and noise, aliasing, AGC making loudness misleading, too few FFT bins for bass, room/speaker colouring acoustic tests, MAX7219 3.3 V logic margin.

## Design — writing outline

Write one short block per pipeline stage: **options considered → choice → why → evidence.** Starred choices are proposals to test, not decisions yet.

**Two input paths, on purpose.** An *electrical* path (signal generator → conditioning → ADC) tests the ADC and FFT with exact frequencies. An *acoustic* path (phone tone app → speaker → MAX9814 → ADC) tests the real product. A difference between the two is the mic, speaker and room — something to measure, not hide.

| Stage | Options | Proposed choice | Why / evidence |
| --- | --- | --- | --- |
| Mic setup | MAX9814 gain 40 / 50 / 60 dB (Gain pin); attack/release ratio (A/R pin) | ★ Power at 3.3 V; start at 40 dB, try 50/60 | Output ~0.25–2.25 V fits the ADC; lower gain clips less. Log raw samples at each setting. |
| Conditioning | Mic straight to ADC (it's already biased); RC low-pass; electrical path = coupling cap + bias divider + RC | ★ Mic direct to an ADC1 pin; electrical path with an RC sized for *our* sample rate | Aidan's 220 Ω + 22 nF cuts off at ~33 kHz — fine at 96 kHz, too high to stop aliasing at ~40 kHz |
| Sampling | analogRead() loop (Aidan: only ~12 kHz real); ADC continuous/DMA | ★ Continuous/DMA on ADC1, ~40 kHz if the S3 allows | Count samples per second; check `soc_caps.h` limit |
| Processing | Raw FFT; + DC removal; + Hann window; dB magnitude | ★ DC removal + Hann + FFT, N = 1024 | Mic bias must be removed; window cuts leakage — show a tone with and without |
| Mapping | Linear (all previous prototypes); pure log; hybrid | ★ Hybrid: one FFT bin per column at the bottom, log-spaced above | Pure log needs bins narrower than we have (below) |
| Range modes | Aidan's 4 linear ranges; decimated "bass/voice" mode | ★ Full mode + a bass/voice mode made by filtering and keeping every 4th sample | Finer bins where music lives; two-tone test proves it |
| Scaling | Fixed constant; dB with measured noise floor; auto-gain | ★ dB with a noise floor measured in a quiet room | The MAX9814 already has AGC — adding software auto-gain would double-squash loudness |
| Smoothing | None; fast-rise slow-fall; peak-hold | ★ Fast rise, slow fall + peak dots | Tune from video |
| Display | 32 × 8 MAX7219 at 5 V | ★ Low default brightness | 3.3 V logic vs 3.5 V spec: test pattern first, buffer (74HCT125) if glitchy |
| Controls | One or two buttons | ★ Button 1 cycles modes (saved in flash); button 2 stops listening | Function test |
| Framework | Arduino-ESP32 core (arduino-cli, like Aidan); ESP-IDF v6 | ★ ESP-IDF v6 (decided 29/10) | Previous code unavailable, so there's nothing to stay close to; IDF gives direct access to the continuous ADC driver and FreeRTOS tasks, and is already set up from the hourglass |

**Proposed pins** (Freenove ESP32-S3, camera unplugged — confirm at bring-up): MAX9814 OUT → GPIO 1 (ADC1); MAX7219 DIN / CLK / CS → GPIO 11 / 12 / 10; button(s) → GPIO 14 (and 21) to GND with pull-ups. Avoid GPIO 2 (on-board LED), 0/3/45/46 (strapping), 35–37 (PSRAM).

**Numbers for the write-up** (check against measurements):

- Bin width = sample rate ÷ N. Aidan: 96 000 / 512 = 187.5 Hz. Ours at 40 kHz, N = 1024: ~39 Hz, with 25.6 ms of audio per frame.
- Bass/voice mode: keep every 4th sample → 10 kHz effective, Nyquist 5 kHz. N = 512 gives ~19.5 Hz bins from 51 ms of audio; N = 1024 gives ~9.8 Hz but 102 ms — finer bins cost responsiveness (R3). A real trade-off to show.
- 32 log columns from 100 Hz to 8 kHz are ~0.2 octave each, i.e. each band is ~15 % of its centre frequency. At 39 Hz bins that's narrower than one bin below roughly 260 Hz — so the bottom few columns get one bin each, and log spacing takes over above.
- Latency ≈ frame length + FFT time + display write; log each part.

**Software structure** (no code yet): sample → process → map → draw as separate functions; all tunable numbers in one config block; sampling + FFT on one core, display + buttons on the other; a serial debug stream of band values every frame for Python plots.

**Risks and mitigations**

| Risk | Effect | Mitigation |
| --- | --- | --- |
| S3 ADC slower or noisier than assumed | Range shrinks; noisy floor | Measure rate and floor before anything else |
| Aliasing (seen by Zhexi and Aidan) | High tone shown as a false low peak | Sample well above display range; RC sized for our rate; digital filter before decimating |
| MAX9814 AGC | Bar height isn't true loudness | Measure the compression curve; state it; don't add software AGC |
| Too few bins at low end | Bass columns jumpy or empty | Hybrid mapping; decimated bass mode |
| Phone speaker can't play bass | Acoustic tests look worse than the device is | Electrical path for low tones; note the speaker limit |
| Mic clipping on loud sounds | Fake harmonics | Clip pixel; lower gain setting |
| MAX7219 logic margin | Random pixels | Test pattern at bring-up; HCT buffer |

## Bits on top of the examples

Build the **core** first, then **one flagship**, then stretch goals if time allows. Each item is something the previous prototypes didn't do, and each produces its own before/after evidence.

| Tier | Addition | Over what's been done | Evidence it produces |
| --- | --- | --- | --- |
| Core | **Port to ESP32-S3 + first working mic path** (MAX9814) | Aidan's mic never arrived; nobody has run this on an S3 | Raw-sample plots, measured sample rate, gain-setting comparison |
| Core | **Measured accuracy, not "near the centre"** — serial logging + Python | Previous tests were by eye | Hz-in vs column table with error, frequency-response plot, noise floor, latency |
| Core | **Hybrid log mapping** | All prototypes linear; Aidan's 0–6 kHz range puts 0–187 Hz in one column | Same music linear vs hybrid, side-by-side video; tone-per-column test |
| Core | **"Can I trust it?" status row** — pixels for silence, clipping, energy above the display range, listening on/off | Answers the brief's "how would a user know it's working?" | Each test triggers the right pixel |
| Flagship | **Tone-finder mode** — shows the strongest frequency as scrolling digits (e.g. "440") with its column highlighted | Turns accuracy into something a student can see | Input Hz vs shown Hz, with error, across the range |
| Stretch | Decimated bass/voice mode | Aidan's ranges kept 187.5 Hz bins everywhere | Two-tone resolution test, both modes |
| Stretch | Aliasing demo — Zhexi's foldback reproduced, then fixed | Turns the known failure into evidence | Tone above Nyquist, filter on/off |
| Stretch | AGC compression measured and shown | Explains why loud and quiet music look similar | Stepped-level curve per gain setting |
| Stretch | Accessibility: brightness, bars vs dots, slow "calm" decay | Inclusion point with something real behind it | Quick check with a few classmates |

## Test plan

Each test runs on the electrical path (signal generator) and, where it makes sense, the acoustic path (phone tone app → speaker → mic, fixed distance, quiet room). Log band values over serial every time; keep a photo or short video too.

| Test | Path | Method | Pass (requirement) |
| --- | --- | --- | --- |
| Real sample rate | — | Count samples per second; time 1000 frames | Within a few % of the set value |
| Mic output check | Acoustic | Log raw samples: quiet, speech, loud clap; at 40/50/60 dB gain | Centred near 1.25 V; note where it clips |
| Frequency response | Both | Sweep 50 Hz – 20 kHz at fixed level; log peak column and height | Fall-off points stated for each path (R1) |
| Column accuracy | Electrical | Tone at each column's centre and both edges | Correct column ±1 (R2) |
| Tone-finder accuracy | Both | Known tones; shown Hz vs set Hz | Error table; within one bin |
| Two-tone resolution | Electrical | Two tones, move apart until two peaks appear; both modes | Matches bin-width calc |
| Leakage | Electrical | Pure tone, window on vs off | Fewer neighbouring columns lit with window |
| Quiet room / noise floor | Acoustic | Mic in a quiet room; then input shorted | ≤ 1 pixel per column (R5) |
| Loudness / AGC | Both | Same tone, volume in steps | Curve of bar height vs level; AGC squashing stated (R7) |
| Aliasing | Electrical | Tone above Nyquist, filter on/off | No false low peak with filter (R6) |
| Latency | Acoustic | Slow-mo video of a clap | Under ~100 ms (R3) |
| Frame rate | — | Log frame time | ≥ 20 fps (R4) |
| Real audio | Acoustic | Several music genres, speech, sudden changes | Notes + video |
| Buttons / modes | — | Every mode, power-cycle, stop-listening | Correct mode, survives reset (R8) |
| Power (optional) | — | USB meter, low vs high brightness | Values for the sustainability point |

## Six-session plan

Session 1–2 rebuild Aidan's approach on our hardware as a measured baseline; every "bit on top" is then judged against that baseline.

| Session | CDIO focus | Goals | Done when | Evidence to upload |
| --- | --- | --- | --- | --- |
| 1 | Conceive | Read blogs; ESP-IDF project skeleton; check kit; matrix test pattern; log raw mic samples; agree product + R1–R8 | Matrix lights; mic signal seen in serial log | Photos, raw-sample plot, requirements table |
| 2 | Design | Block diagram; pins; continuous ADC at a measured rate; baseline = Aidan's method (linear, N = 512) rebuilt from his blog on the S3 | Tone moves across the display; real rate known | Diagram, calcs, baseline plots, decision log |
| 3 | Implement | Core: DC removal + window, hybrid mapping, dB scale, noise floor, serial logging | Tone lands in the right column | Linear vs hybrid video; accuracy table v1 |
| 4 | Implement | Status row; smoothing + peak dots; button modes; start tone-finder | Core features working | Function tests, video |
| 5 | Operate | Full test plan on both paths; aliasing demo; AGC curve; finish tone-finder | Test table filled | Plots, test table, failure-mode video |
| 6 | Operate / Improve | Fix the top issue; demo script; rehearse; "what next" list | Demo rehearsed | Final video, reflections citing evidence |

**Suggested split for three:** A — mic, conditioning, sampling (ADC rate, aliasing); B — FFT, mapping, scaling, modes; C — display, buttons, logging + Python plots, integration.

**Per-session reflection prompts:** what I did; one decision and its evidence; what surprised us; what I'd change; next step.

## Open questions

- [x] Is a lab signal generator available for the electrical path? **Yes** (Joe, 29/10)
- [ ] Is there a 3.5 mm jack in the box, or mic only?
- [x] Product framing: teaching-lab instrument or music visualiser? **Teaching-lab, accuracy first** (Joe, 29/10)
- [ ] Which flagship: tone-finder, or something the team prefers?
- [ ] Team split and who writes which part of the report

## Decision log (seed)

| Date | Decision | Alternatives considered | Reason / evidence |
| --- | --- | --- | --- |
| 29/10 | Teaching-lab framing (accuracy over looks) — confirmed by Joe | Music-first visualiser | Brief rewards evidence and known limits |
| 29/10 | Two input paths: electrical for exact tests, mic for the product — lab function generator confirmed available | Mic only; generator only (Aidan) | Separates ADC/FFT errors from mic/speaker/room effects |
| 29/10 | Hybrid log mapping — *proposed* | Linear (all previous prototypes); pure log | Pure log needs finer bins than we have at the bottom |
| 29/10 | No software auto-gain — *proposed* | Software AGC | MAX9814 already has AGC; doubling it hides loudness |
| 29/10 | Write firmware from scratch in ESP-IDF v6 | Adapt course repo code (Arduino-ESP32) | Repo is private and couldn't be obtained; IDF gives direct control of the S3's continuous ADC; toolchain already working from the hourglass |
| 29/10 | MAX7219 driver: SPI mode 0, no DMA, one CS-low transaction per row register for the whole chain, 1 MHz to start | Bit-banged GPIO; DMA; one chip at a time | Datasheet timing (clocked on rising edge, latched on CS rising edge); ≤ 16 bytes per transfer so DMA adds nothing; writing all chips per transaction keeps them in step. Clock raised only after the soak test is clean |
| 29/10 | Find orientation by sweeping all 16 `frame_orient_t` combinations on the matrix, plus three raw-bit photos | Guess, edit, reflash until right | One flash gives the answer and a photo record; the mapping logic is unit-tested on the laptop first |
| 29/10 | Status-row layout in `frame_draw_status` is provisional (top-right pixels) — superseded below | — | Real layout is a session-4 design decision; placeholder lets code build |
| 29/10 | ADC: continuous (DMA) driver on ADC1, rate counted in the driver's frame-done interrupt; overflow counter added to `adc_sampler.h` | `adc_oneshot` in a loop (Aidan's `analogRead` only reached ~12 kHz of 60 kHz); counting samples as they are read | Hardware-clocked sampling; counting in the interrupt measures what the ADC produced, independent of the reader. Overflows make gaps in audio visible instead of silent |
| 29/10 | ADC attenuation 12 dB (~0–3.1 V range) | 6 dB (~0–1.75 V, finer steps) | MAX9814 swings 0.25–2.25 V; 6 dB would clip the top of loud signals. Check against STATS min/max in bring-up 02 |
| 29/10 | ADC buffer drops old data when full (`flush_pool`) — *corrected at review: the driver discards the whole ~100 ms pool, not just the oldest chunk* | Stall until read | A late frame is worse than a dropped one for latency (R3); the overflow count shows when it happens, and the frame being read then has a gap |
| 29/10 | Requested rate 40 kHz (S3 allows 611–83 333 Hz, `soc_caps.h`); bring-up 02 sweeps 20–83.3 kHz | Go straight to max rate | 40 kHz gives Nyquist 20 kHz above the 8 kHz display range and 39 Hz bins at N = 1024; the sweep shows where the S3 stops keeping up. All Hz maths use a separate `APP_SAMPLE_RATE_ACTUAL_HZ` set from the measured value |
| 29/10 | Serial console at 921600 baud | 115200 default | FRAME lines are ~9 KB/s at 39 frames/s, close to 115200's ~11.5 KB/s limit; RAW frames are ~5 KB each |
| 29/10 | Hybrid log mapping algorithm: column by column, split the remaining range into equal ratios for the columns left, round to whole bins, minimum one bin | Fixed log edges then merge empty columns; pure log | Never leaves an empty column, no duplicated bins, log spacing appears automatically once bands get wider than a bin (100–8000 Hz at 39 Hz bins: 9 single-bin columns, then log). Column table printed by `test_band_map` |
| 29/10 | Column value = loudest bin in the column (max) | Average or sum of bins | A pure tone shows full height wherever it lands; average would make wide top columns look quieter than narrow bottom ones |
| 29/10 | DC bin (bin 0) never used | Include it | It holds the mic's 1.25 V bias, not sound |
| 29/10 | Bar height truncates (row lights only when fully reached) | Round to nearest | Noise just above the floor lights nothing (R5, quiet room) |
| 29/10 | Bar ballistics: fast rise, slow fall (20 rows/s), peak dot held 0.5 s then falls 6 rows/s — *starting values* | No smoothing; symmetric smoothing | Fast rise keeps latency low (R3); slow fall stops flicker. Values to tune from video |
| 29/10 | Tone finder: loudest bin + parabolic interpolation on dB values | Loudest bin only (±20 Hz error at 39 Hz bins); zero-padding / longer FFT | Sub-bin accuracy at almost no cost: synthetic sines 150 Hz–7.8 kHz within 1 Hz on the laptop. Real accuracy to be measured |
| 29/10 | Spectrum output in dBFS (0 dB = sine filling the 12-bit range), window gain corrected | Raw FFT magnitude units | Every level in logs/plots has a physical meaning; a tone reads the same with window on/off, so the leakage test compares only leakage |
| 29/10 | DC removal by subtracting each frame's mean | Fixed bias constant; high-pass filter | Bias drifts with temperature/supply; frame mean tracks it with no tuning. Small cost: very low bass can shift the mean slightly |
| 29/10 | Bass/voice mode: 63-tap windowed-sinc low-pass (Blackman, cut-off 80 % of new Nyquist) before keeping every 4th sample; N = 512 after decimation (51 ms) | Decimate without filter; N = 1024 (102 ms, finer bins) | Without the filter, 5–20 kHz content would fold into the bass columns (the aliasing failure mode, in software). N = 512 keeps latency near the R3 target; 19.5 Hz bins are still 2× finer than full mode |
| 29/10 | Linear baseline mode uses the same N (1024) and range (100–8000 Hz) as full mode — **changed from plan** (plan said Aidan-style N = 512) | Rebuild Aidan exactly (N = 512, his ranges) | Changing only the mapping makes the linear vs hybrid comparison one variable at a time. Aidan's exact setup can still be shown by changing two config values — confirmed by Joe |
| 29/10 | Buttons polled every 10 ms with a 30 ms time-based debounce; event reported on release, long press ≥ 800 ms | GPIO interrupts; counting identical reads | Polling is simple, can't be swamped by contact bounce, and 10 ms is far below human reaction time. Reporting on release lets one button do short and long actions |
| 29/10 | NVS saves mode and brightness only, written only when they change | Save every setting; save periodically | R8 needs the mode to survive a reset; flash has limited write cycles |
| 29/10 | Device always starts **listening** at power-up (listening state not saved) — confirmed by Joe | Remember the last state; start not listening | It's a display, so it should work when switched on; the status pixel shows it is listening, and the button stops capture fully (ADC off, buffer flushed). Privacy section should say this |
| 29/10 | Debug stream: one FRAME line per analysed frame (dB to 1 decimal), TONE line only when a tone is found, RATE once a second; `APP_DEBUG_EVERY_N_FRAMES` to thin it out | Binary format; human-readable logs only | Text CSV-style lines can be read in the monitor and parsed by Python with no extra tools; 0.1 dB is far finer than one display row (4 dB) |
| 29/10 | Audio frames back to back, no overlap (N = 1024 at 40 kHz = 25.6 ms → ~39 frames/s) | 50 % overlap (78 frames/s, double the FFT work) | Already above R4 (≥ 20 fps) and the display refreshes at 40 fps; overlap only adds work. Revisit if latency (R3) is too high |
| 29/10 | Status flags: SILENT = frame RMS below `APP_SILENCE_RMS`; CLIPPING = any raw sample within `APP_CLIP_MARGIN` of 0 or 4095; ABOVE_RANGE = strongest bin above the displayed range is louder than `APP_TONE_MIN_DB` and within 6 dB of the loudest column | Single "bad signal" light; ABOVE_RANGE on any energy above range | Each flag answers one "can I trust it?" question; ABOVE_RANGE only fires when the out-of-range sound is comparable to what's shown, so harmonics of normal sounds don't trigger it. It can't see tones above Nyquist (they've already folded back) — that's the analogue filter's job (R6) |
| 29/10 | Tone finder searches every bin from 50 Hz up to Nyquist, not just the displayed range | Only the displayed range | A teaching tool should say "12 000 Hz" rather than show nothing or a wrong column; `tone_col` = −1 marks it as off the display |
| 29/10 | Mode change rebuilds spectrum + band map inside the audio task; bad config falls back to full mode | Rebuild from the input task | Keeps ownership rule (only audio_task touches spectrum/band_map); no locking needed |
| 29/10 | `process_us` measures FFT + mapping only, not serial printing | Include printing | It's the processing part of the latency budget; printing (~3 ms per FRAME line at 921600 baud) is a debug cost, not part of the product |
| 29/10 | Display refreshes on its own 25 ms timer (40 fps), using the newest audio frame | Redraw only when a frame arrives | Bars keep falling smoothly between frames; the display never waits on audio, and old frames are skipped rather than queued (latency) |
| 29/10 | Status area: top two rows of columns 28–31; while any flag is set that area is blanked first, then column 31 = silent, 30 = clipping, 29 = above range, 28 = not listening | Reserve a whole row (bars only 7 high); blink the pixels | Keeps all 8 rows for bars; columns 28–31 are 5.5–8 kHz, which rarely reach full height; blanking means a status pixel can't be read as a bar top. No blinking (photosensitivity) |
| 29/10 | Tone-finder screen: "440Hz" centred in rows 1–5, updated 4×/s, one pixel in the bottom row under the column that tone lights in full mode | Scrolling text; updating every frame | Up to "20000Hz" fits in 32 px so nothing needs to scroll; updating every frame flickers too fast to read; the marker links the number to the spectrum view |
| 29/10 | Bars reset (not left to fall) on mode change and when listening stops | Let them decay | Old-mode bars in a new mode would be misleading; "not listening" should look clearly empty at once |
| 29/10 | Peak dot drawn only when above the bar | Always draw | A dot inside a lit bar is invisible anyway |
| 29/10 | DISPLAY line once a second: refresh rate, frame age (end of capture → written to LEDs, avg/max), SPI write time | Measure latency only with video | Gives the electronic part of the latency budget in numbers; the clap video then checks the total (R3) |
| 29/10 | Debug lines built in a buffer and printed in one call | Several printf calls per line | Two tasks on two cores print; split calls could interleave mid-line and break the Python parser |
| 29/10 | Buttons: MODE short = next mode (full → bass/voice → tone finder → linear), MODE long = next brightness step (0, 2, 5, 9, 15); LISTEN any press = stop/start listening | Separate brightness button; brightness in fine steps | Two buttons cover everything (R8); five brightness steps are easy to cycle and include 0 (lowest power) and 15 (bright room) |
| 29/10 | `input_task_start()` now takes the loaded settings (header change) | Input task loads settings itself | main already loads them once; passing them in means the first button press steps from the real saved state, and NVS is read in one place |
| 29/10 | Firmware prints its key settings at boot (rate, N, window, range, floor, dB/row, SPI clock) | Rely on notes | Every evidence log then records the configuration it was made with, so results can be compared after values change |
| 29/10 | Firmware runs with no buttons wired (pull-ups hold the pins high) | — | Session-B tests can start before buttons are wired; the saved/default mode is used |
| 29/10 | Analysis tools in plain Python (numpy + matplotlib), one script per test, reading raw monitor logs; tables printed as Markdown | Spreadsheet by hand; pandas; Jupyter notebooks | Same log → same numbers every time (repeatable evidence); Markdown tables paste straight into the report; scripts live in the repo next to the firmware they measure |
| 29/10 | Tone accuracy uses the **median** shown Hz over a log (first 0.5 s skipped), plus the 5–95 % spread | Mean; a single reading | Median ignores the odd glitch frame; the spread shows how steady the reading is, which matters to a student reading the digits |
| 29/10 | Suggested noise floor = loudest column's 95th-percentile level in a quiet room + 1 dB | Average level; by eye | R5 allows ≤ 1 lit pixel per column, so the floor must sit above nearly all quiet frames in the worst column (e.g. mains hum), not the average one |
| 29/10 | `plot_raw.py` spectrum uses the same dBFS reference as the firmware; volts axis approximate (3.1 V / 4095, uncalibrated) | ADC calibration API | Levels compare directly with FRAME logs; exact volts aren't needed for any requirement, only bias and clipping in counts |
| 29/10 | **Code review fixes (before first hardware run):** | | |
| 29/10 | Tone finder only interpolates when both neighbour bins are inside the searched range; offset clamped to ±½ bin | Interpolate whenever k > 0 | A loud DC/rumble bin just below the search range could drag the estimate below it (found in review; new test fails on the old code) |
| 29/10 | Display blanks if no audio frame arrives for 500 ms | Keep showing the last frame | An "honest display" must not freeze on old data if the audio side stops |
| 29/10 | Main firmware re-sends MAX7219 control registers every second (`max7219_resync`, header change); bring-up 01 does not | Never re-send; buffer chip only | 3.3 V logic is below spec, so a glitch could leave the display in shutdown/test/wrong scan limit until reset. Bring-up 01 leaves glitches visible so they can still be counted; resync is a mitigation, the 74HCT125 buffer is the fix |
| 29/10 | Display task stack 4 KB → 6 KB, input task 3 KB → 4 KB | Measure first | Float printf and NVS writes are stack-hungry; RAM is plentiful, a stack overflow on demo day isn't |
| 29/10 | Audio task waits 10 ms after an ADC read error; firmware logs column edges (Hz) at boot and on every mode change | — | No busy-loop if the ADC fails; the column table for R2 tests uses the real measured sample rate |
| 29/10 | Electrical input circuit: low-pass capacitor 2.2 nF, not 15 nF (f_c ≈ 12 kHz) | 15 nF (first draft) | Review caught that the bias divider's 5 kΩ adds to the 1 kΩ series resistor: 15 nF would have cut off at ≈ 1.8 kHz |
| | | | |

## Sources

- Mini-Challenge 2 brief (Al-Nuaimy / van Zalinge, Oct 2026)
- Aidan Gan — Spectrum Visualiser project blog: https://aidangan.blogspot.com/2026/06/spectrum-visualiser-project-week-1-this.html
- Casey Overkleeft — Spectrum Visualiser research and preparation (summary of Zhexi Zhang's report): https://labinaboxcaseyov.blogspot.com/2026/06/day-1-spectrum-visualiser-research-and.html
- Course repo: github.com/caseyov/spectrumVisualiser — private, not available; firmware rebuilt from scratch
- Espressif — ESP32-S3 ADC continuous mode driver (ESP-IDF v6.0): https://docs.espressif.com/projects/esp-idf/en/v6.0/esp32s3/api-reference/peripherals/adc/adc_continuous.html
- Adafruit — MAX9814 AGC electret mic amplifier guide: https://learn.adafruit.com/adafruit-agc-electret-microphone-amplifier-max9814
- Shajeeb — Arduino 32-band visualizer: https://github.com/shajeebtm/Arduino-audio-spectrum-visualizer-analyzer
- HAZI-TECH 32-band: https://github.com/HAZI-TECH/32-Band-LED-Audio-Spectrum-Analyzer
- ShillehTek ESP32 + I2S mic: https://shillehtek.com/blogs/news/esp32-inmp441-max7219-sound-reactive-led-matrix
- Still to read: Original Project Proposal, Lab-in-a-Box CDIO Development Report (Canvas)
