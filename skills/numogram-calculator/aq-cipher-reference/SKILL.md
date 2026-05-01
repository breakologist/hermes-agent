---
name: aq-cipher-reference
description: Correct AQ (Alphanumeric Qabbala) cipher values for computation and verification. Use when calculating AQ values, verifying dictionary entries, or building AQ tools.
---

# AQ Cipher — Base-36 Reference

## The Cipher

AQ uses **Base-36** values. NOT the standard English Qabalah (A=1..Z=26).

| Digits | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|--------|---|---|---|---|---|---|---|---|---|---|
| Value | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |

| Letters | A | B | C | D | E | F | G | H | I | J | K | L | M |
|---------|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Value | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 |

| Letters | N | O | P | Q | R | S | T | U | V | W | X | Y | Z |
|---------|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Value | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 | 33 | 34 | 35 |

## Python Implementation

```python
AQ_MAP = {}
for i in range(10):
    AQ_MAP[str(i)] = i
for i, c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    AQ_MAP[c] = i + 10
    AQ_MAP[c.lower()] = i + 10

def aq(s):
    return sum(AQ_MAP.get(c, 0) for c in s)
```

## Verification Values

| Word | AQ | DR | Zone |
|------|----|----|------|
| AL | 31 | 4 | |
| AQ | 36 | 9 | Plex |
| IAO | 52 | 7 | |
| KEK | 54 | 9 | Plex |
| LAMA | 63 | 9 | Plex |
| HECATE | 96 | 6 | |
| KEYS | 96 | 6 | |
| THREE | 101 | 2 | |
| LUCIFER | 137 | 2 | |
| ABRACADABRA | 151 | 7 | |
| HERMETIC | 153 | 9 | Plex |
| THE NUMOGRAM | 234 | 9 | Plex |
| THE CYBERNETIC CULTURE RESEARCH UNIT | 666 | 9 | Plex |
| DO WHAT THOU WILT SHALL BE THE WHOLE OF THE LAW | 777 | 3 | Warp |

## Common Mistakes

- **WRONG**: Standard A=1..Z=26 (gives AL=13 instead of 31)
- **RIGHT**: Base-36 A=10..Z=35
- Spaces and punctuation are ignored in the sum
- Digital root (mod 9) gives the Numogram zone

## Source

- [Qabbala 101 by Nick Land](http://qabbala101.com/)
- [AQQA calculator](https://alektryon.github.io/aqqa/)
- [ccru.cc](https://www.ccru.cc/) — 14 ciphers, 665K+ phrases
- [Gematria Research blog](https://gematriaresearch.blogspot.com/2023/02/the-wonders-magic-of-alphanumeric.html)
