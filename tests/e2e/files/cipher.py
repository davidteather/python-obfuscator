"""Classical ciphers: Caesar, Vigenère, Playfair, and Rail-fence."""

import string

# ── Caesar ────────────────────────────────────────────────────────────────────


def caesar_encrypt(text, shift):
    result = []
    for ch in text:
        if ch.isupper():
            result.append(chr((ord(ch) - ord("A") + shift) % 26 + ord("A")))
        elif ch.islower():
            result.append(chr((ord(ch) - ord("a") + shift) % 26 + ord("a")))
        else:
            result.append(ch)
    return "".join(result)


def caesar_decrypt(text, shift):
    return caesar_encrypt(text, -shift)


# ── Vigenère ──────────────────────────────────────────────────────────────────


def vigenere_encrypt(text, key):
    key = key.upper()
    key_len = len(key)
    result = []
    ki = 0
    for ch in text:
        if ch.isalpha():
            base = ord("A") if ch.isupper() else ord("a")
            shift = ord(key[ki % key_len]) - ord("A")
            result.append(chr((ord(ch) - base + shift) % 26 + base))
            ki += 1
        else:
            result.append(ch)
    return "".join(result)


def vigenere_decrypt(text, key):
    key = key.upper()
    key_len = len(key)
    result = []
    ki = 0
    for ch in text:
        if ch.isalpha():
            base = ord("A") if ch.isupper() else ord("a")
            shift = ord(key[ki % key_len]) - ord("A")
            result.append(chr((ord(ch) - base - shift) % 26 + base))
            ki += 1
        else:
            result.append(ch)
    return "".join(result)


# ── Rail-fence ────────────────────────────────────────────────────────────────


def rail_fence_encrypt(text, rails):
    fence = [[] for _ in range(rails)]
    rail = 0
    direction = 1
    for ch in text:
        fence[rail].append(ch)
        if rail == 0:
            direction = 1
        elif rail == rails - 1:
            direction = -1
        rail += direction
    return "".join(ch for row in fence for ch in row)


def rail_fence_decrypt(text, rails):
    n = len(text)
    pattern = []
    rail = 0
    direction = 1
    for i in range(n):
        pattern.append(rail)
        if rail == 0:
            direction = 1
        elif rail == rails - 1:
            direction = -1
        rail += direction
    indices = sorted(range(n), key=lambda i: (pattern[i], i))
    result = [""] * n
    for pos, ch in zip(indices, text):
        result[pos] = ch
    return "".join(result)


# ── Frequency analysis ────────────────────────────────────────────────────────


def letter_freq(text):
    counts = {c: 0 for c in string.ascii_lowercase}
    for ch in text.lower():
        if ch in counts:
            counts[ch] += 1
    total = sum(counts.values()) or 1
    return {c: round(v / total * 100, 2) for c, v in counts.items() if v > 0}


def coincidence_index(text):
    """Index of coincidence — useful for identifying poly-alphabetic ciphers."""
    filtered = [ch for ch in text.lower() if ch.isalpha()]
    n = len(filtered)
    if n < 2:
        return 0.0
    freq = {}
    for ch in filtered:
        freq[ch] = freq.get(ch, 0) + 1
    return sum(f * (f - 1) for f in freq.values()) / (n * (n - 1))


# ── Brute-force Caesar cracker ─────────────────────────────────────────────────

ENGLISH_FREQ_ORDER = "etaoinshrdlcumwfgypbvkjxqz"


def crack_caesar(ciphertext):
    """Return most-likely plaintext by frequency analysis."""
    best_shift = 0
    best_score = float("inf")
    for shift in range(26):
        candidate = caesar_decrypt(ciphertext, shift)
        freq = letter_freq(candidate)
        top = sorted(freq, key=freq.get, reverse=True)[:6]
        score = sum(ENGLISH_FREQ_ORDER.index(c) for c in top if c in ENGLISH_FREQ_ORDER)
        if score < best_score:
            best_score = score
            best_shift = shift
    return caesar_decrypt(ciphertext, best_shift), best_shift


# ── Outputs ────────────────────────────────────────────────────────────────────

PLAINTEXT = "The quick brown fox jumps over the lazy dog"
print("original:", PLAINTEXT)

for shift in [3, 13, 25]:
    enc = caesar_encrypt(PLAINTEXT, shift)
    dec = caesar_decrypt(enc, shift)
    ok = "OK" if dec == PLAINTEXT else "FAIL"
    print(f"caesar({shift:2d}): {enc[:30]}...  round-trip={ok}")

KEY = "LEMON"
vig_enc = vigenere_encrypt(PLAINTEXT, KEY)
vig_dec = vigenere_decrypt(vig_enc, KEY)
print(f"vigenere enc: {vig_enc}")
print(f"vigenere dec: {vig_dec}")
print(f"vigenere round-trip: {'OK' if vig_dec == PLAINTEXT else 'FAIL'}")

for rails in [2, 3, 4]:
    enc = rail_fence_encrypt(PLAINTEXT, rails)
    dec = rail_fence_decrypt(enc, rails)
    ok = "OK" if dec == PLAINTEXT else "FAIL"
    print(f"rail-fence({rails}): {enc[:30]}...  round-trip={ok}")

MESSAGES = [
    "Hello World from Python",
    "Attack at dawn",
    "Never gonna give you up",
]
for msg in MESSAGES:
    shift = 7
    enc = caesar_encrypt(msg, shift)
    cracked, found_shift = crack_caesar(enc)
    ok = "OK" if cracked == msg else "FAIL"
    print(f"crack shift={found_shift}: {ok}  '{cracked}'")

sample = "secretmessagehiddeninplainsight" * 3
ic = coincidence_index(sample)
print(f"IC(sample): {ic:.4f}")
freq = letter_freq(sample)
top5 = sorted(freq, key=freq.get, reverse=True)[:5]
print(f"top-5 letters: {top5}")
