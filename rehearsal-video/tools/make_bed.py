"""Synthesises the music + sound design bed for the film (original, no samples).

Every cue time mirrors a constant in index.html, so sound lands on motion.
Run:  python3 tools/make_bed.py   ->  assets/bed.wav
"""
import wave
import numpy as np

SR = 48000
DUR = 27.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(11)
L = np.zeros(N)
R = np.zeros(N)


def add(sig, at, pan=0.0, gain=1.0):
    i = int(at * SR)
    if i >= N:
        return
    sig = sig[: N - i] * gain
    L[i : i + len(sig)] += sig * np.sqrt(0.5 * (1 - pan))
    R[i : i + len(sig)] += sig * np.sqrt(0.5 * (1 + pan))


def env_ad(n, a, d):
    x = np.arange(n) / SR
    return np.minimum(x / max(a, 1e-4), 1.0) * np.exp(-np.maximum(x - a, 0) / d)


def smooth(x0, x1, tt):
    u = np.clip((tt - x0) / (x1 - x0), 0, 1)
    return u * u * (3 - 2 * u)


def lowpass(x, fc):
    # one-pole, fc may be an array
    a = 1 - np.exp(-2 * np.pi * np.asarray(fc, dtype=float) / SR)
    a = np.broadcast_to(a, x.shape)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def noise(n):
    return rng.standard_normal(n)


def whoosh(dur, f0, f1, peak=0.55):
    n = int(dur * SR)
    x = np.arange(n) / n
    env = np.exp(-((x - peak) ** 2) / 0.045) * np.sin(np.pi * x) ** 0.5
    fc = f0 * (f1 / f0) ** x
    y = lowpass(noise(n), fc)
    y = y - lowpass(y, fc * 0.25)
    return y * env


# ---------------- pad ----------------
A2, E3, A3, C4, Cs4, E4, B4, Cs5 = 110.0, 164.81, 220.0, 261.63, 277.18, 329.63, 493.88, 554.37


def voice(f, level, lfo, phase):
    v = np.zeros(N)
    for det, ph in ((-0.0035, 0.0), (0.0, 1.3), (0.004, 2.1)):
        v += np.sin(2 * np.pi * f * (1 + det) * t + ph + phase)
    v += 0.18 * np.sin(2 * np.pi * 2 * f * t + phase)
    return v / 3.2 * level * (0.8 + 0.2 * np.sin(2 * np.pi * lfo * t + phase))


intro = smooth(0.0, 1.4, t)
dark = smooth(3.0, 4.6, t) * (1 - smooth(10.0, 11.4, t))  # snooze + scroll
warm = smooth(11.2, 14.0, t)  # showing up
build = smooth(15.0, 20.0, t)
drop = 1 - 0.55 * smooth(20.1, 20.6, t) * (1 - smooth(22.3, 23.4, t))
final = smooth(23.3, 23.5, t)
outro = 1 - smooth(25.6, 27.0, t)

pad = np.zeros(N)
pad += voice(A2, 0.55, 0.11, 0.0) * intro
pad += voice(E3, 0.40, 0.07, 1.0) * intro
pad += voice(A3, 0.30, 0.09, 2.0) * intro * (0.6 + 0.4 * warm)
pad += voice(C4, 0.26, 0.13, 0.5) * dark
pad += voice(Cs4, 0.30, 0.10, 0.7) * warm
pad += voice(E4, 0.24, 0.08, 1.9) * np.maximum(warm * 0.5, build)
pad += voice(B4, 0.16, 0.12, 2.6) * np.maximum(build, final)
pad += voice(Cs5, 0.12, 0.15, 0.2) * final
pad *= (0.75 + 0.45 * build) * drop * outro
padL = pad * (0.9 + 0.1 * np.sin(2 * np.pi * 0.05 * t))
padR = pad * (0.9 - 0.1 * np.sin(2 * np.pi * 0.05 * t))
L += padL * 0.34
R += padR * 0.34

# ---------------- heartbeat pulse ----------------
def thump(f, d=0.22, drop_=0.5):
    n = int(0.6 * SR)
    x = np.arange(n) / SR
    ph = 2 * np.pi * f * (x + (drop_ * d) * (1 - np.exp(-x / d)))
    return np.sin(ph) * env_ad(n, 0.004, d)


for k, bt in enumerate(np.arange(3.4, 14.6, 1.1)):
    add(thump(52), bt, 0, 0.16)
    add(thump(52), bt + 0.22, 0, 0.09)

# ---------------- transits ----------------
add(whoosh(1.4, 300, 2600), 2.15, -0.2, 0.30)
add(whoosh(1.2, 2400, 320), 6.3, 0.2, 0.28)
add(whoosh(1.05, 400, 2400), 10.0, -0.2, 0.28)
add(whoosh(1.5, 3200, 180, 0.45), 14.55, 0.0, 0.42)

# ---------------- alarm (3.55 - 4.44) ----------------
for k in range(6):
    n = int(0.07 * SR)
    x = np.arange(n) / SR
    bip = (np.sin(2 * np.pi * 1975 * x) + 0.4 * np.sin(2 * np.pi * 3950 * x)) * np.sin(np.pi * np.arange(n) / n) ** 0.6
    add(bip, 3.56 + k * 0.145, 0.15, 0.05)

# ---------------- snooze taps ----------------
for tp, f in zip((4.46, 5.02, 5.56), (150, 128, 108)):
    add(thump(f, 0.11, 0.8), tp, 0, 0.55)
    add(lowpass(noise(int(0.03 * SR)), 2500) * env_ad(int(0.03 * SR), 0.001, 0.008), tp, 0, 0.5)

# ---------------- feed flicks ----------------
for fl, g in ((7.66, 0.2), (8.16, 0.2), (8.98, 0.3), (9.42, 0.3)):
    add(whoosh(0.28, 1800, 5200, 0.3), fl - 0.04, 0.25, g)
add(whoosh(0.95, 1500, 6000, 0.7), 9.8, 0.25, 0.24)

# ---------------- stairs: ascending plucks ----------------
def pluck(f, d=0.6):
    n = int(2.2 * SR)
    x = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * x) + 0.35 * np.sin(2 * np.pi * 2 * f * x) * np.exp(-x / 0.12) + 0.12 * np.sin(2 * np.pi * 3 * f * x) * np.exp(-x / 0.06)
    return y * env_ad(n, 0.004, d)


for land, f, pan in zip((11.70, 12.28, 12.80, 13.30, 13.78), (220.0, 277.18, 329.63, 440.0, 554.37), (-0.3, -0.15, 0, 0.15, 0.3)):
    add(pluck(f), land, pan, 0.22)
    add(thump(70, 0.07, 0.6), land, 0, 0.18)
for f, g in ((659.26, 0.12), (880.0, 0.09), (1108.73, 0.05)):
    add(pluck(f, 1.0), 13.88, 0.1, g)

# ---------------- days: one tick per day as the dot passes ----------------
LIT = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1]
for i, lit in enumerate(LIT):
    p = (i + 0.5) / 28
    at = 15.3 + ((p - 0.75 + 1) % 1) * 1.9
    n = int(0.12 * SR)
    x = np.arange(n) / SR
    if lit:
        add(np.sin(2 * np.pi * (1760 if i % 2 else 2217.46) * x) * env_ad(n, 0.002, 0.03), at, np.sin(p * 2 * np.pi) * 0.5, 0.07)
    else:
        add(np.sin(2 * np.pi * 330 * x) * env_ad(n, 0.002, 0.02), at, np.sin(p * 2 * np.pi) * 0.5, 0.05)

# ---------------- laps: a whir each time the dot passes the top ----------------
V0, V1, ACC_D = 1 / 1.9, 3.0, 2.1
ACC = (V1 - V0) / ACC_D
dAcc = V0 * ACC_D + 0.5 * ACC * ACC_D**2
pA = 1.75 + dAcc
DEC_D = 2 * (7 - pA) / V1
tt = np.arange(17.2, 17.2 + ACC_D + DEC_D, 1 / 2000)
tau = tt - 17.2
pp = np.where(
    tau <= ACC_D,
    1.75 + V0 * tau + 0.5 * ACC * tau**2,
    pA + (7 - pA) * (1 - (1 - np.clip((tau - ACC_D) / DEC_D, 0, 1)) ** 2),
)
cross = tt[1:][np.floor(pp[1:]) > np.floor(pp[:-1])]
for k, c in enumerate(cross):
    add(whoosh(0.3, 500 + 250 * k, 2200 + 500 * k, 0.5), c - 0.15, 0, 0.16 + 0.03 * k)
    add(thump(60 + 6 * k, 0.09, 0.6), c, 0, 0.2)
# riser under the acceleration
n = int((ACC_D + 0.3) * SR)
x = np.arange(n) / n
ris = np.sin(2 * np.pi * np.cumsum(110 * 2 ** (x * 2.0)) / SR) * x**2.2 * (1 - smooth(0.9, 1.0, x))
add(ris, 17.2, 0, 0.12)
add(lowpass(noise(n), 500 + 5000 * x**2) * x**2.5 * (1 - smooth(0.9, 1.0, x)), 17.2, 0, 0.10)
add(thump(48, 0.5, 0.4), 17.2 + ACC_D + DEC_D - 0.05, 0, 0.5)  # settle

# ---------------- the strike + the turn ----------------
add(whoosh(0.4, 900, 7000, 0.45), 21.9, 0.0, 0.5)
n = int(0.95 * SR)
x = np.arange(n) / n
glide = np.sin(2 * np.pi * np.cumsum(220 * 2 ** (x * 1.0)) / SR) * np.sin(np.pi * x) ** 1.5
add(glide, 22.4, 0, 0.09)
add(whoosh(0.95, 300, 3000, 0.75), 22.42, 0, 0.3)

# ---------------- final: the point lands ----------------
HIT = 23.42
add(thump(55, 1.2, 0.5), HIT, 0, 0.9)
add(lowpass(noise(int(0.5 * SR)), 900) * env_ad(int(0.5 * SR), 0.002, 0.09), HIT, 0, 0.5)
for f, g, pan in ((440.0, 0.20, -0.2), (554.37, 0.16, 0.2), (659.26, 0.16, -0.1), (987.77, 0.10, 0.3), (1318.5, 0.05, -0.3)):
    add(pluck(f, 1.7), HIT + 0.01, pan, g)

# ---------------- reverb + master ----------------
ir_n = int(2.4 * SR)
ir_t = np.arange(ir_n) / SR
def reverb(x, seed):
    r = np.random.default_rng(seed)
    ir = r.standard_normal(ir_n) * np.exp(-ir_t / 0.55)
    ir[: int(0.012 * SR)] = 0
    ir = lowpass(ir, 3800)
    m = len(x) + ir_n
    f = 1 << (m - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, f) * np.fft.rfft(ir, f), f)[: len(x)]
    return y / np.sqrt(np.sum(ir**2))


wetL, wetR = reverb(L, 1), reverb(R, 2)
L = L + 0.42 * wetL
R = R + 0.42 * wetR
fade = np.minimum(1, t / 0.4) * (1 - smooth(26.3, 27.0, t))
L *= fade
R *= fade
peak = max(np.abs(L).max(), np.abs(R).max())
g = 10 ** (-3 / 20) / peak
out = np.stack([np.tanh(L * g * 1.1), np.tanh(R * g * 1.1)], axis=1)
pcm = (out * 32767 * 0.92).astype("<i2")
with wave.open("assets/bed.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("lap crossings:", np.round(cross, 2), "settle", round(17.2 + ACC_D + DEC_D, 2))
