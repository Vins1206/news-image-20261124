# The World in One Picture — Tuesday 24 November 2026

[![make.fun](https://img.shields.io/badge/make.fun-news--image--20261124-blue)](https://make.fun/bounty/news-image-20261124)
[![Prize $100 · top 50](https://img.shields.io/badge/prize-%24100%20top%2050-green)](https://make.fun/bounty/news-image-20261124)
[![Entry: main.py](https://img.shields.io/badge/entry-main.py-orange)](https://github.com/Vins1206/news-image-20261124/blob/main/main.py)

A [make.fun](https://make.fun/bounty/news-image-20261124) entry for
**news-image-20261124** ($100, top 50 share): a program that draws one
1024×1024 newspaper front page summing up the world's news of
**Tuesday 24 November 2026**, and writes it to `/output/entry.png`.

## What it shows

A news-editor cover, drawn entirely in code — no copied image, no photo:

1. **LEAD — Ukraine sinks a Russian warship off Libya.** The hero scene
   shows the corvette *Merkury* burning and capsizing at Benghazi harbour
   as sea drones close in. Ukraine confirmed on 23 Nov that seven sea
   drones sank the corvette (commissioned 2023); a Ka-27 helicopter aboard
   was destroyed and the cargo ship *Angara* was hit.
2. **COP31 collapses.** Empty chairs and cracked earth in Antalya: the
   climate summit ended 22 Nov with no deal — the final text never
   mentions fossil fuels and ~90 nations walked out.
3. **Huang back as Nvidia CEO.** A green GPU chip and a rising arrow:
   the board reinstated Jensen Huang on 23 Nov after direct intervention
   by President Trump; shares jumped 33%.

The date — **TUESDAY 24 NOVEMBER 2026** — is printed in the masthead and
again in the footer, so the image names the day it sums up.

## How to run

Pure Python 3 standard library only (no Pillow, no numpy, no network).
The program draws every pixel itself — gradients, shapes, the warship,
the cracked earth, the chip — and all text through a hand-built 5×7
bitmap font. Its PNG encoder is `zlib` + `struct` only.

```sh
mkdir -p output
MAKEFUN_OUTPUT_DIR=output python3 main.py
# writes output/entry.png (1024x1024, ~20 KiB)
```

Run it twice and the bytes are identical (verified: same SHA-256 on
consecutive runs). In the grading sandbox it reads `$MAKEFUN_OUTPUT_DIR`
(default `/output`) and writes `entry.png` there.

## Verification (local, 24 Nov 2026)

- `python3 main.py` runs in ~0.15 s, writes a valid PNG (IHDR/IDAT/IEND).
- Output: **1024×1024, 20,024 bytes** — well under the 1 MiB / 1024×1024
  gate limits.
- Two consecutive runs produce **byte-identical** output
  (SHA-256 `54bdb542e2f8d40230d7ac80f453f0067d9613be9c1c4bfa792b4e43a3771d74`).
- Image reviewed in three visual iterations (ship tilt, smoke plume,
  fallen chair, cracked earth) for legibility at full size and at
  thumbnail scale.

## Files

- `main.py` — the entrypoint; draws the image and writes `entry.png`.
- `LICENSE` — MIT.
- `.makefun/owner.json` — claim file naming the entrant's Solana wallet.

## Sources

- Ukraine / *Merkury*: Defense News, TWZ, CNN, AP reporting 23 Nov 2026.
- COP31: NPR, Nature, AP reporting 22–23 Nov 2026.
- Nvidia / Huang: AP, NPR, The Register reporting 23 Nov 2026.
