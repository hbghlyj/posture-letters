# Posture Master — Anatomical Consistency Audit

**Tolerance:** ±5%  
**Baseline:** revised A forward-fold pose  
**Result:** 1 passed; 25 flagged  
**Policy:** diagnostic only; exact 1782 pose construction takes priority where the two goals conflict.

## Baseline measurements

| Element | Baseline units |
|---|---:|
| Thigh | 153.7 |
| Calf | 145.6 |
| Whole leg | 299.2 |
| Upper arm | 112.7 |
| Forearm | 85.1 |
| Whole arm | 197.8 |
| Pelvis-to-shoulder torso/spine | 162.8 |
| Head diameter | 110.0 |

Measurements use source centerlines, not outline bounding boxes. No hidden foreshortening exemptions are applied.

## A–Z summary

| Glyph | Status | Limb totals | Torso | Head | Primary finding |
|---|---|---|---:|---:|---|
| A | **PASS** | A 202.8, A 192.8, L 302.7, L 295.8, A 202.8, A 192.8, L 302.7, L 295.8 | 162.8, 162.8 | 110.0, 110.0 | Within tolerance |
| B | **FAIL** | A 184.6, A 200.2, L 270.9, L 393.8 | 350.3 | 110.0 | limb 1 (arm) total 184.6 is -6.7% from 197.8 |
| C | **FAIL** | L 334.4, L 324.7, L 385.6, L 317.8 | 371.5 | 110.0 | limb 1 (leg) total 334.4 is +11.8% from 299.2 |
| D | **FAIL** | L 603.3, L 604.5, L 635.2 | 288.0 | 110.0 | expected 4 measurable limbs; found 3 |
| E | **FAIL** | L 410.2, L 286.6, L 425.0, L 390.0 | 580.0 | 110.0 | limb 1 (leg) total 410.2 is +37.1% from 299.2 |
| F | **FAIL** | L 410.6, L 289.0, L 370.2, L 370.2 | 250.0 | 110.0 | limb 1 (leg) total 410.6 is +37.2% from 299.2 |
| G | **FAIL** | L 721.6, L 412.0, L 429.6, L 308.8 | 423.6 | 96.0 | limb 1 (leg) total 721.6 is +141.2% from 299.2 |
| H | **FAIL** | A 235.0, L 390.2, L 390.0, A 235.0, L 390.2, L 390.0 | 206.2, 206.2 | 110.0, 110.0 | expected 8 measurable limbs; found 6 |
| I | **FAIL** | L 274.4, L 274.4, L 400.1, L 400.1 | 225.0 | 110.0 | limb 1 (leg) total 274.4 is -8.3% from 299.2 |
| J | **FAIL** | L 272.1, L 272.1, L 363.6, L 258.9 | 430.0 | 110.0 | limb 1 (leg) total 272.1 is -9.0% from 299.2 |
| K | **FAIL** | L 349.7, L 256.8, L 266.2, L 387.1 | 320.1 | 110.0 | limb 1 (leg) total 349.7 is +16.9% from 299.2 |
| L | **FAIL** | L 339.3, L 339.3, L 515.0, L 515.0 | 280.0 | 110.0 | limb 1 (leg) total 339.3 is +13.4% from 299.2 |
| M | **FAIL** | L 508.0, L 508.0, L 993.0, L 987.4 | 535.6 | 110.0 | limb 1 (leg) total 508.0 is +69.8% from 299.2 |
| N | **FAIL** | L 498.0, L 498.0, L 658.0, L 679.7 | 508.5 | 110.0 | limb 1 (leg) total 498.0 is +66.4% from 299.2 |
| O | **FAIL** | L 696.2, L 696.2 | — | 124.0 | expected 4 measurable limbs; found 2 |
| P | **FAIL** | L 324.6, L 283.1, L 369.1, L 369.2 | 265.0 | 110.0 | limb 1 (leg) total 324.6 is +8.5% from 299.2 |
| Q | **FAIL** | L 720.4, L 720.4, A 182.2 | — | 124.0 | expected 4 measurable limbs; found 3 |
| R | **FAIL** | A 193.1, L 241.8, L 551.5, L 370.2 | 265.0 | 110.0 | limb 1 upper arm 97.7 is -13.3% from 112.7 |
| S | **FAIL** | L 363.8, L 317.7, L 517.9, A 114.4 | 423.2 | 110.0 | limb 1 (leg) total 363.8 is +21.6% from 299.2 |
| T | **FAIL** | L 258.2, L 258.2, L 345.0, L 345.0 | 235.0 | 110.0 | limb 1 (leg) total 258.2 is -13.7% from 299.2 |
| U | **FAIL** | L 721.2, L 721.2, L 617.7, L 617.7 | 100.0 | 110.0 | limb 1 (leg) total 721.2 is +141.0% from 299.2 |
| V | **FAIL** | L 516.6, L 516.6, L 338.9, L 338.9 | 120.0 | 110.0 | limb 1 (leg) total 516.6 is +72.7% from 299.2 |
| W | **FAIL** | L 339.4, L 339.4, L 1155.4, L 1155.4 | 135.0 | 110.0 | limb 1 (leg) total 339.4 is +13.4% from 299.2 |
| X | **FAIL** | L 363.2, L 363.2, L 371.4, L 371.4 | 80.0 | 110.0 | limb 1 (leg) total 363.2 is +21.4% from 299.2 |
| Y | **FAIL** | A 231.1, A 231.1, L 380.4, L 380.4 | 210.0 | 110.0 | limb 1 (arm) total 231.1 is +16.8% from 197.8 |
| Z | **FAIL** | L 415.5, L 445.3, L 377.8 | 614.8 | 110.0 | expected 4 measurable limbs; found 3 |

## Detailed flags

### B
- limb 1 (arm) total 184.6 is -6.7% from 197.8
- limb 1 upper arm 91.2 is -19.0% from 112.7
- limb 1 forearm 93.3 is +9.6% from 85.1
- limb 3 (leg) total 270.9 is -9.5% from 299.2
- limb 3 thigh 135.6 is -11.7% from 153.7
- limb 3 calf 135.2 is -7.1% from 145.6
- limb 4 (leg) total 393.8 is +31.6% from 299.2
- limb 4 thigh 200.8 is +30.7% from 153.7
- limb 4 calf 193.0 is +32.6% from 145.6
- torso 350.3 is +115.1% from 162.8

### C
- limb 1 (leg) total 334.4 is +11.8% from 299.2
- limb 1 thigh 162.2 is +5.6% from 153.7
- limb 1 calf 172.2 is +18.3% from 145.6
- limb 2 (leg) total 324.7 is +8.5% from 299.2
- limb 2 calf 163.5 is +12.3% from 145.6
- limb 3 (leg) total 385.6 is +28.9% from 299.2
- limb 3 thigh 145.3 is -5.4% from 153.7
- limb 3 calf 240.2 is +65.0% from 145.6
- limb 4 (leg) total 317.8 is +6.2% from 299.2
- limb 4 thigh 127.8 is -16.8% from 153.7
- limb 4 calf 190.1 is +30.6% from 145.6
- torso 371.5 is +128.2% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### D
- expected 4 measurable limbs; found 3
- limb 1 (leg) total 603.3 is +101.6% from 299.2
- limb 1 thigh 242.5 is +57.8% from 153.7
- limb 1 calf 360.8 is +147.9% from 145.6
- limb 2 (leg) total 604.5 is +102.0% from 299.2
- limb 2 thigh 243.7 is +58.6% from 153.7
- limb 2 calf 360.8 is +147.9% from 145.6
- limb 3 (leg) total 635.2 is +112.3% from 299.2
- limb 3 has 4 skeletal segments; expected upper/lower pair
- torso 288.0 is +76.9% from 162.8

### E
- limb 1 (leg) total 410.2 is +37.1% from 299.2
- limb 1 thigh 210.2 is +36.8% from 153.7
- limb 1 calf 200.0 is +37.4% from 145.6
- limb 2 thigh 161.6 is +5.1% from 153.7
- limb 2 calf 125.0 is -14.1% from 145.6
- limb 3 (leg) total 425.0 is +42.0% from 299.2
- limb 3 thigh 210.0 is +36.7% from 153.7
- limb 3 calf 215.0 is +47.7% from 145.6
- limb 4 (leg) total 390.0 is +30.3% from 299.2
- limb 4 thigh 195.0 is +26.9% from 153.7
- limb 4 calf 195.0 is +34.0% from 145.6
- torso 580.0 is +256.2% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### F
- limb 1 (leg) total 410.6 is +37.2% from 299.2
- limb 1 thigh 200.6 is +30.5% from 153.7
- limb 1 calf 210.0 is +44.3% from 145.6
- limb 2 thigh 144.0 is -6.3% from 153.7
- limb 3 (leg) total 370.2 is +23.7% from 299.2
- limb 3 thigh 187.1 is +21.8% from 153.7
- limb 3 calf 183.1 is +25.8% from 145.6
- limb 4 (leg) total 370.2 is +23.7% from 299.2
- limb 4 thigh 187.1 is +21.8% from 153.7
- limb 4 calf 183.1 is +25.8% from 145.6
- torso 250.0 is +53.6% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### G
- limb 1 (leg) total 721.6 is +141.2% from 299.2
- limb 1 has 5 skeletal segments; expected upper/lower pair
- limb 2 (leg) total 412.0 is +37.7% from 299.2
- limb 2 has 3 skeletal segments; expected upper/lower pair
- limb 3 (leg) total 429.6 is +43.6% from 299.2
- limb 3 has 3 skeletal segments; expected upper/lower pair
- limb 4 calf 155.7 is +7.0% from 145.6
- torso 423.6 is +160.2% from 162.8
- head 96.0 is -12.7% from 110.0
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### H
- expected 8 measurable limbs; found 6
- limb 1 (arm) total 235.0 is +18.8% from 197.8
- limb 1 upper arm 107.0 is -5.0% from 112.7
- limb 1 forearm 128.0 is +50.3% from 85.1
- limb 2 (leg) total 390.2 is +30.4% from 299.2
- limb 2 thigh 195.1 is +27.0% from 153.7
- limb 2 calf 195.0 is +34.0% from 145.6
- limb 3 (leg) total 390.0 is +30.3% from 299.2
- limb 3 thigh 195.0 is +26.9% from 153.7
- limb 3 calf 195.0 is +34.0% from 145.6
- limb 4 (arm) total 235.0 is +18.8% from 197.8
- limb 4 upper arm 107.0 is -5.0% from 112.7
- limb 4 forearm 128.0 is +50.3% from 85.1
- limb 5 (leg) total 390.2 is +30.4% from 299.2
- limb 5 thigh 195.1 is +27.0% from 153.7
- limb 5 calf 195.0 is +34.0% from 145.6
- limb 6 (leg) total 390.0 is +30.3% from 299.2
- limb 6 thigh 195.0 is +26.9% from 153.7
- limb 6 calf 195.0 is +34.0% from 145.6
- torso 206.2 is +26.6% from 162.8
- torso 206.2 is +26.6% from 162.8

### I
- limb 1 (leg) total 274.4 is -8.3% from 299.2
- limb 1 thigh 138.4 is -10.0% from 153.7
- limb 1 calf 136.0 is -6.6% from 145.6
- limb 2 (leg) total 274.4 is -8.3% from 299.2
- limb 2 thigh 138.4 is -10.0% from 153.7
- limb 2 calf 136.0 is -6.6% from 145.6
- limb 3 (leg) total 400.1 is +33.7% from 299.2
- limb 3 thigh 200.1 is +30.2% from 153.7
- limb 3 calf 200.1 is +37.4% from 145.6
- limb 4 (leg) total 400.1 is +33.7% from 299.2
- limb 4 thigh 200.1 is +30.2% from 153.7
- limb 4 calf 200.1 is +37.4% from 145.6
- torso 225.0 is +38.2% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### J
- limb 1 (leg) total 272.1 is -9.0% from 299.2
- limb 1 thigh 142.1 is -7.5% from 153.7
- limb 1 calf 130.0 is -10.7% from 145.6
- limb 2 (leg) total 272.1 is -9.0% from 299.2
- limb 2 thigh 142.1 is -7.5% from 153.7
- limb 2 calf 130.0 is -10.7% from 145.6
- limb 3 (leg) total 363.6 is +21.5% from 299.2
- limb 3 thigh 194.0 is +26.3% from 153.7
- limb 3 calf 169.6 is +16.5% from 145.6
- limb 4 (leg) total 258.9 is -13.5% from 299.2
- limb 4 thigh 119.6 is -22.1% from 153.7
- torso 430.0 is +164.1% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### K
- limb 1 (leg) total 349.7 is +16.9% from 299.2
- limb 1 has 4 skeletal segments; expected upper/lower pair
- limb 2 (leg) total 256.8 is -14.2% from 299.2
- limb 2 thigh 140.8 is -8.4% from 153.7
- limb 2 calf 116.0 is -20.3% from 145.6
- limb 3 (leg) total 266.2 is -11.0% from 299.2
- limb 3 thigh 145.8 is -5.1% from 153.7
- limb 3 calf 120.4 is -17.3% from 145.6
- limb 4 (leg) total 387.0 is +29.4% from 299.2
- limb 4 thigh 180.3 is +17.4% from 153.7
- limb 4 calf 206.7 is +42.0% from 145.6
- torso 320.1 is +96.6% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### L
- limb 1 (leg) total 339.3 is +13.4% from 299.2
- limb 1 thigh 188.9 is +22.9% from 153.7
- limb 2 (leg) total 339.3 is +13.4% from 299.2
- limb 2 thigh 188.9 is +22.9% from 153.7
- limb 3 (leg) total 515.0 is +72.1% from 299.2
- limb 3 thigh 265.0 is +72.5% from 153.7
- limb 3 calf 250.0 is +71.8% from 145.6
- limb 4 (leg) total 515.0 is +72.1% from 299.2
- limb 4 thigh 265.0 is +72.5% from 153.7
- limb 4 calf 250.0 is +71.8% from 145.6
- torso 280.0 is +72.0% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### M
- limb 1 (leg) total 508.0 is +69.8% from 299.2
- limb 1 thigh 254.0 is +65.3% from 153.7
- limb 1 calf 254.0 is +74.5% from 145.6
- limb 2 (leg) total 508.0 is +69.8% from 299.2
- limb 2 thigh 254.0 is +65.3% from 153.7
- limb 2 calf 254.0 is +74.5% from 145.6
- limb 3 (leg) total 993.0 is +231.9% from 299.2
- limb 3 thigh 495.4 is +222.4% from 153.7
- limb 3 calf 497.5 is +241.8% from 145.6
- limb 4 (leg) total 987.4 is +230.0% from 299.2
- limb 4 thigh 489.8 is +218.8% from 153.7
- limb 4 calf 497.5 is +241.8% from 145.6
- torso 535.6 is +229.0% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### N
- limb 1 (leg) total 498.0 is +66.4% from 299.2
- limb 1 thigh 250.0 is +62.7% from 153.7
- limb 1 calf 248.0 is +70.4% from 145.6
- limb 2 (leg) total 498.0 is +66.4% from 299.2
- limb 2 thigh 250.0 is +62.7% from 153.7
- limb 2 calf 248.0 is +70.4% from 145.6
- limb 3 (leg) total 658.0 is +119.9% from 299.2
- limb 3 thigh 95.7 is -37.7% from 153.7
- limb 3 calf 562.3 is +286.3% from 145.6
- limb 4 (leg) total 679.7 is +127.2% from 299.2
- limb 4 thigh 110.9 is -27.8% from 153.7
- limb 4 calf 568.8 is +290.8% from 145.6
- torso 508.5 is +212.3% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### O
- expected 4 measurable limbs; found 2
- expected 1 measurable torso(s); found 0
- limb 1 (leg) total 696.2 is +132.7% from 299.2
- limb 1 has 5 skeletal segments; expected upper/lower pair
- limb 2 (leg) total 696.2 is +132.7% from 299.2
- limb 2 has 5 skeletal segments; expected upper/lower pair
- head 124.0 is +12.7% from 110.0

### P
- limb 1 (leg) total 324.6 is +8.5% from 299.2
- limb 1 has 4 skeletal segments; expected upper/lower pair
- limb 2 (leg) total 283.1 is -5.4% from 299.2
- limb 2 has 3 skeletal segments; expected upper/lower pair
- limb 3 (leg) total 369.1 is +23.4% from 299.2
- limb 3 thigh 185.1 is +20.4% from 153.7
- limb 3 calf 184.1 is +26.5% from 145.6
- limb 4 (leg) total 369.2 is +23.4% from 299.2
- limb 4 thigh 185.1 is +20.5% from 153.7
- limb 4 calf 184.1 is +26.5% from 145.6
- torso 265.0 is +62.8% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### Q
- expected 4 measurable limbs; found 3
- expected 1 measurable torso(s); found 0
- limb 1 (leg) total 720.4 is +140.7% from 299.2
- limb 1 has 5 skeletal segments; expected upper/lower pair
- limb 2 (leg) total 720.4 is +140.7% from 299.2
- limb 2 has 5 skeletal segments; expected upper/lower pair
- limb 3 (arm) total 182.2 is -7.9% from 197.8
- limb 3 has 4 skeletal segments; expected upper/lower pair
- head 124.0 is +12.7% from 110.0

### R
- limb 1 upper arm 97.7 is -13.3% from 112.7
- limb 1 forearm 95.5 is +12.1% from 85.1
- limb 2 (leg) total 241.8 is -19.2% from 299.2
- limb 2 thigh 115.7 is -24.7% from 153.7
- limb 2 calf 126.1 is -13.4% from 145.6
- limb 3 (leg) total 551.5 is +84.3% from 299.2
- limb 3 thigh 246.1 is +60.2% from 153.7
- limb 3 calf 305.4 is +109.8% from 145.6
- limb 4 (leg) total 370.2 is +23.7% from 299.2
- limb 4 thigh 185.1 is +20.5% from 153.7
- limb 4 calf 185.1 is +27.2% from 145.6
- torso 265.0 is +62.8% from 162.8
- nearest-baseline classification gives 1 arm(s) and 3 leg(s)

### S
- limb 1 (leg) total 363.8 is +21.6% from 299.2
- limb 1 calf 205.0 is +40.8% from 145.6
- limb 2 (leg) total 317.7 is +6.2% from 299.2
- limb 2 calf 170.0 is +16.8% from 145.6
- limb 3 (leg) total 517.9 is +73.1% from 299.2
- limb 3 has 4 skeletal segments; expected upper/lower pair
- limb 4 (arm) total 114.4 is -42.2% from 197.8
- limb 4 upper arm 65.2 is -42.1% from 112.7
- limb 4 forearm 49.2 is -42.2% from 85.1
- torso 423.2 is +159.9% from 162.8
- nearest-baseline classification gives 1 arm(s) and 3 leg(s)

### T
- limb 1 (leg) total 258.2 is -13.7% from 299.2
- limb 1 thigh 143.2 is -6.8% from 153.7
- limb 1 calf 115.0 is -21.0% from 145.6
- limb 2 (leg) total 258.2 is -13.7% from 299.2
- limb 2 thigh 143.2 is -6.8% from 153.7
- limb 2 calf 115.0 is -21.0% from 145.6
- limb 3 (leg) total 345.0 is +15.3% from 299.2
- limb 3 thigh 172.0 is +11.9% from 153.7
- limb 3 calf 173.0 is +18.9% from 145.6
- limb 4 (leg) total 345.0 is +15.3% from 299.2
- limb 4 thigh 172.0 is +11.9% from 153.7
- limb 4 calf 173.0 is +18.9% from 145.6
- torso 235.0 is +44.3% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### U
- limb 1 (leg) total 721.2 is +141.0% from 299.2
- limb 1 has 3 skeletal segments; expected upper/lower pair
- limb 2 (leg) total 721.2 is +141.0% from 299.2
- limb 2 has 3 skeletal segments; expected upper/lower pair
- limb 3 (leg) total 617.7 is +106.4% from 299.2
- limb 3 has 3 skeletal segments; expected upper/lower pair
- limb 4 (leg) total 617.7 is +106.4% from 299.2
- limb 4 has 3 skeletal segments; expected upper/lower pair
- torso 100.0 is -38.6% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### V
- limb 1 (leg) total 516.6 is +72.7% from 299.2
- limb 1 thigh 243.8 is +58.7% from 153.7
- limb 1 calf 272.8 is +87.4% from 145.6
- limb 2 (leg) total 516.6 is +72.7% from 299.2
- limb 2 thigh 243.8 is +58.7% from 153.7
- limb 2 calf 272.8 is +87.4% from 145.6
- limb 3 (leg) total 338.9 is +13.3% from 299.2
- limb 3 thigh 174.4 is +13.5% from 153.7
- limb 3 calf 164.5 is +13.0% from 145.6
- limb 4 (leg) total 338.9 is +13.3% from 299.2
- limb 4 thigh 174.4 is +13.5% from 153.7
- limb 4 calf 164.5 is +13.0% from 145.6
- torso 120.0 is -26.3% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### W
- limb 1 (leg) total 339.4 is +13.4% from 299.2
- limb 1 thigh 184.4 is +20.0% from 153.7
- limb 1 calf 155.0 is +6.5% from 145.6
- limb 2 (leg) total 339.4 is +13.4% from 299.2
- limb 2 thigh 184.4 is +20.0% from 153.7
- limb 2 calf 155.0 is +6.5% from 145.6
- limb 3 (leg) total 1155.4 is +286.1% from 299.2
- limb 3 thigh 425.4 is +176.9% from 153.7
- limb 3 calf 730.0 is +401.5% from 145.6
- limb 4 (leg) total 1155.4 is +286.1% from 299.2
- limb 4 thigh 425.4 is +176.9% from 153.7
- limb 4 calf 730.0 is +401.5% from 145.6
- torso 135.0 is -17.1% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### X
- limb 1 (leg) total 363.2 is +21.4% from 299.2
- limb 1 thigh 182.6 is +18.8% from 153.7
- limb 1 calf 180.6 is +24.1% from 145.6
- limb 2 (leg) total 363.2 is +21.4% from 299.2
- limb 2 thigh 182.6 is +18.8% from 153.7
- limb 2 calf 180.6 is +24.1% from 145.6
- limb 3 (leg) total 371.4 is +24.1% from 299.2
- limb 3 thigh 172.2 is +12.1% from 153.7
- limb 3 calf 199.1 is +36.8% from 145.6
- limb 4 (leg) total 371.4 is +24.1% from 299.2
- limb 4 thigh 172.2 is +12.1% from 153.7
- limb 4 calf 199.1 is +36.8% from 145.6
- torso 80.0 is -50.9% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### Y
- limb 1 (arm) total 231.1 is +16.8% from 197.8
- limb 1 forearm 113.1 is +32.8% from 85.1
- limb 2 (arm) total 231.1 is +16.8% from 197.8
- limb 2 forearm 113.1 is +32.8% from 85.1
- limb 3 (leg) total 380.4 is +27.1% from 299.2
- limb 3 thigh 190.1 is +23.7% from 153.7
- limb 3 calf 190.3 is +30.7% from 145.6
- limb 4 (leg) total 380.4 is +27.1% from 299.2
- limb 4 thigh 190.1 is +23.7% from 153.7
- limb 4 calf 190.3 is +30.7% from 145.6
- torso 210.0 is +29.0% from 162.8

### Z
- expected 4 measurable limbs; found 3
- limb 1 (leg) total 415.5 is +38.9% from 299.2
- limb 1 thigh 205.0 is +33.4% from 153.7
- limb 1 calf 210.5 is +44.6% from 145.6
- limb 2 (leg) total 445.3 is +48.8% from 299.2
- limb 2 thigh 195.3 is +27.1% from 153.7
- limb 2 calf 250.0 is +71.8% from 145.6
- limb 3 (leg) total 377.8 is +26.3% from 299.2
- limb 3 thigh 162.8 is +5.9% from 153.7
- limb 3 calf 215.0 is +47.7% from 145.6
- torso 614.8 is +277.6% from 162.8

## Enforcement note

For diagnostic CI, `python validate_anatomy.py --strict` exits non-zero while any glyph is outside tolerance. It is not the release gate for the historically faithful build: composite surreal constructions are intentionally not auto-exempted or normalized.
