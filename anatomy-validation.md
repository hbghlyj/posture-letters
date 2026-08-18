# Posture Master — Anatomical Consistency Audit

**Tolerance:** ±5%  
**Baseline:** revised A forward-fold pose  
**Result:** 1 passed; 25 flagged  
**Policy:** diagnostic only; exact 1782 pose construction takes priority where the two goals conflict.

## Baseline measurements

| Element | Baseline units |
|---|---:|
| Thigh | 151.8 |
| Calf | 143.5 |
| Whole leg | 295.2 |
| Upper arm | 112.7 |
| Forearm | 85.1 |
| Whole arm | 197.8 |
| Pelvis-to-shoulder torso/spine | 162.8 |
| Head diameter | 110.0 |

Measurements use source centerlines, not outline bounding boxes. No hidden foreshortening exemptions are applied.

## A–Z summary

| Glyph | Status | Limb totals | Torso | Head | Primary finding |
|---|---|---|---:|---:|---|
| A | **PASS** | A 202.8, A 192.8, L 296.0, L 294.5, A 202.8, A 192.8, L 296.0, L 294.5 | 162.8, 162.8 | 110.0, 110.0 | Within tolerance |
| B | **FAIL** | L 471.4, L 394.1, L 516.7 | 238.0 | 110.0 | expected 4 measurable limbs; found 3 |
| C | **FAIL** | L 340.1, L 333.5, L 385.6, L 317.8 | 371.5 | 110.0 | limb 1 (leg) total 340.1 is +15.2% from 295.2 |
| D | **FAIL** | L 573.0, L 574.2, L 600.0 | 288.0 | 110.0 | expected 4 measurable limbs; found 3 |
| E | **FAIL** | L 469.2, L 381.5, L 558.3, L 574.2 | 292.0 | 110.0 | limb 1 (leg) total 469.2 is +58.9% from 295.2 |
| F | **FAIL** | L 406.0, L 306.0, L 368.1, L 368.1 | 256.0 | 110.0 | limb 1 (leg) total 406.0 is +37.5% from 295.2 |
| G | **FAIL** | L 335.2, L 302.8, L 576.0, L 616.8 | 587.9 | 110.0 | limb 1 (leg) total 335.2 is +13.5% from 295.2 |
| H | **FAIL** | A 208.0, L 390.2, L 390.0, A 208.0, L 390.2, L 390.0 | 206.2, 206.2 | 110.0, 110.0 | expected 8 measurable limbs; found 6 |
| I | **FAIL** | L 274.4, L 274.4, L 400.1, L 400.1 | 225.0 | 110.0 | limb 1 (leg) total 274.4 is -7.1% from 295.2 |
| J | **FAIL** | L 250.3, L 250.3, L 462.1, L 507.9 | 332.0 | 110.0 | limb 1 (leg) total 250.3 is -15.2% from 295.2 |
| K | **FAIL** | L 294.0, L 290.0, L 308.3, L 338.0 | 92.1 | 110.0 | limb 2 thigh 143.0 is -5.8% from 151.8 |
| L | **FAIL** | A 216.3, A 216.3, L 619.4, L 589.9 | 242.0 | 110.0 | limb 1 (arm) total 216.3 is +9.3% from 197.8 |
| M | **FAIL** | L 508.0, L 508.0, L 993.0, L 987.4 | 535.6 | 110.0 | limb 1 (leg) total 508.0 is +72.1% from 295.2 |
| N | **FAIL** | L 572.2, L 572.2, L 454.4, L 454.4 | 555.4 | 110.0 | limb 1 (leg) total 572.2 is +93.8% from 295.2 |
| O | **FAIL** | L 514.8, L 507.1, L 461.1, L 467.7 | 607.1 | 108.0 | limb 1 (leg) total 514.8 is +74.4% from 295.2 |
| P | **FAIL** | L 542.7, L 394.1, L 394.1 | 238.0 | 110.0 | expected 4 measurable limbs; found 3 |
| Q | **FAIL** | L 720.4, L 720.4, A 164.5 | — | 124.0 | expected 4 measurable limbs; found 3 |
| R | **FAIL** | L 542.7, L 394.1, L 509.6 | 238.0 | 110.0 | expected 4 measurable limbs; found 3 |
| S | **FAIL** | L 474.6, L 473.0, A 154.8, A 142.4 | 307.2 | 110.0 | limb 1 (leg) total 474.5 is +60.7% from 295.2 |
| T | **FAIL** | L 242.0, L 242.0, L 340.0, L 340.0 | 244.0 | 110.0 | limb 1 (leg) total 242.0 is -18.0% from 295.2 |
| U | **FAIL** | L 396.2, L 360.1, L 364.3, L 364.3 | 574.4 | 110.0 | limb 1 (leg) total 396.2 is +34.2% from 295.2 |
| V | **FAIL** | L 516.6, L 516.6, L 338.9, L 338.9 | 120.0 | 116.0 | limb 1 (leg) total 516.6 is +75.0% from 295.2 |
| W | **FAIL** | L 382.3, L 382.3, L 1071.3, L 1071.3 | 170.0 | 110.0 | limb 1 (leg) total 382.3 is +29.5% from 295.2 |
| X | **FAIL** | L 363.2, L 363.2, L 371.4, L 371.4 | 80.0 | 110.0 | limb 1 (leg) total 363.2 is +23.0% from 295.2 |
| Y | **FAIL** | L 368.1, L 368.1, L 295.5, L 295.5 | 180.0 | 110.0 | limb 1 (leg) total 368.2 is +24.7% from 295.2 |
| Z | **FAIL** | L 400.0, L 382.0, L 428.6, L 426.5 | 613.6 | 110.0 | limb 1 (leg) total 400.0 is +35.5% from 295.2 |

## Detailed flags

### B
- expected 4 measurable limbs; found 3
- limb 1 (leg) total 471.4 is +59.7% from 295.2
- limb 1 has 5 skeletal segments; expected upper/lower pair
- limb 2 (leg) total 394.1 is +33.5% from 295.2
- limb 2 thigh 198.0 is +30.5% from 151.8
- limb 2 calf 196.0 is +36.7% from 143.5
- limb 3 (leg) total 516.7 is +75.0% from 295.2
- limb 3 thigh 256.3 is +68.9% from 151.8
- limb 3 calf 260.4 is +81.5% from 143.5
- torso 238.0 is +46.2% from 162.8

### C
- limb 1 (leg) total 340.1 is +15.2% from 295.2
- limb 1 thigh 164.8 is +8.6% from 151.8
- limb 1 calf 175.3 is +22.2% from 143.5
- limb 2 (leg) total 333.5 is +13.0% from 295.2
- limb 2 thigh 162.6 is +7.1% from 151.8
- limb 2 calf 170.9 is +19.1% from 143.5
- limb 3 (leg) total 385.6 is +30.6% from 295.2
- limb 3 calf 240.2 is +67.5% from 143.5
- limb 4 (leg) total 317.8 is +7.7% from 295.2
- limb 4 thigh 127.8 is -15.8% from 151.8
- limb 4 calf 190.1 is +32.5% from 143.5
- torso 371.5 is +128.2% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### D
- expected 4 measurable limbs; found 3
- limb 1 (leg) total 573.0 is +94.1% from 295.2
- limb 1 thigh 242.5 is +59.8% from 151.8
- limb 1 calf 330.5 is +130.4% from 143.5
- limb 2 (leg) total 574.2 is +94.5% from 295.2
- limb 2 thigh 243.7 is +60.6% from 151.8
- limb 2 calf 330.5 is +130.4% from 143.5
- limb 3 (leg) total 600.0 is +103.2% from 295.2
- limb 3 has 4 skeletal segments; expected upper/lower pair
- torso 288.0 is +76.9% from 162.8

### E
- limb 1 (leg) total 469.2 is +58.9% from 295.2
- limb 1 has 3 skeletal segments; expected upper/lower pair
- limb 2 (leg) total 381.5 is +29.2% from 295.2
- limb 2 thigh 179.4 is +18.2% from 151.8
- limb 2 calf 202.1 is +40.9% from 143.5
- limb 3 (leg) total 558.3 is +89.1% from 295.2
- limb 3 thigh 188.0 is +23.9% from 151.8
- limb 3 calf 370.3 is +158.1% from 143.5
- limb 4 (leg) total 574.3 is +94.5% from 295.2
- limb 4 thigh 188.0 is +23.9% from 151.8
- limb 4 calf 386.3 is +169.3% from 143.5
- torso 292.0 is +79.3% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### F
- limb 1 (leg) total 406.0 is +37.5% from 295.2
- limb 1 thigh 178.0 is +17.3% from 151.8
- limb 1 calf 228.0 is +58.9% from 143.5
- limb 2 thigh 178.0 is +17.3% from 151.8
- limb 2 calf 128.0 is -10.8% from 143.5
- limb 3 (leg) total 368.1 is +24.7% from 295.2
- limb 3 thigh 186.0 is +22.6% from 151.8
- limb 3 calf 182.0 is +26.9% from 143.5
- limb 4 (leg) total 368.1 is +24.7% from 295.2
- limb 4 thigh 186.0 is +22.6% from 151.8
- limb 4 calf 182.0 is +26.9% from 143.5
- torso 256.0 is +57.2% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### G
- limb 1 (leg) total 335.2 is +13.5% from 295.2
- limb 1 thigh 163.5 is +7.7% from 151.8
- limb 1 calf 171.6 is +19.6% from 143.5
- limb 2 thigh 124.0 is -18.3% from 151.8
- limb 2 calf 178.8 is +24.6% from 143.5
- limb 3 (leg) total 576.1 is +95.1% from 295.2
- limb 3 thigh 317.0 is +108.9% from 151.8
- limb 3 calf 259.1 is +80.6% from 143.5
- limb 4 (leg) total 616.8 is +108.9% from 295.2
- limb 4 thigh 334.7 is +120.6% from 151.8
- limb 4 calf 282.1 is +96.6% from 143.5
- torso 587.9 is +261.1% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### H
- expected 8 measurable limbs; found 6
- limb 1 (arm) total 208.0 is +5.1% from 197.8
- limb 1 upper arm 104.0 is -7.7% from 112.7
- limb 1 forearm 104.0 is +22.2% from 85.1
- limb 2 (leg) total 390.2 is +32.2% from 295.2
- limb 2 thigh 195.1 is +28.6% from 151.8
- limb 2 calf 195.0 is +36.0% from 143.5
- limb 3 (leg) total 390.0 is +32.1% from 295.2
- limb 3 thigh 195.0 is +28.5% from 151.8
- limb 3 calf 195.0 is +35.9% from 143.5
- limb 4 (arm) total 208.0 is +5.1% from 197.8
- limb 4 upper arm 104.0 is -7.7% from 112.7
- limb 4 forearm 104.0 is +22.2% from 85.1
- limb 5 (leg) total 390.2 is +32.2% from 295.2
- limb 5 thigh 195.1 is +28.6% from 151.8
- limb 5 calf 195.0 is +36.0% from 143.5
- limb 6 (leg) total 390.0 is +32.1% from 295.2
- limb 6 thigh 195.0 is +28.5% from 151.8
- limb 6 calf 195.0 is +35.9% from 143.5
- torso 206.2 is +26.6% from 162.8
- torso 206.2 is +26.6% from 162.8

### I
- limb 1 (leg) total 274.4 is -7.1% from 295.2
- limb 1 thigh 138.4 is -8.8% from 151.8
- limb 1 calf 136.0 is -5.2% from 143.5
- limb 2 (leg) total 274.4 is -7.1% from 295.2
- limb 2 thigh 138.4 is -8.8% from 151.8
- limb 2 calf 136.0 is -5.2% from 143.5
- limb 3 (leg) total 400.1 is +35.5% from 295.2
- limb 3 thigh 200.1 is +31.8% from 151.8
- limb 3 calf 200.1 is +39.5% from 143.5
- limb 4 (leg) total 400.1 is +35.5% from 295.2
- limb 4 thigh 200.1 is +31.8% from 151.8
- limb 4 calf 200.1 is +39.5% from 143.5
- torso 225.0 is +38.2% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### J
- limb 1 (leg) total 250.3 is -15.2% from 295.2
- limb 1 thigh 130.2 is -14.2% from 151.8
- limb 1 calf 120.0 is -16.3% from 143.5
- limb 2 (leg) total 250.3 is -15.2% from 295.2
- limb 2 thigh 130.2 is -14.2% from 151.8
- limb 2 calf 120.0 is -16.3% from 143.5
- limb 3 (leg) total 462.1 is +56.5% from 295.2
- limb 3 has 3 skeletal segments; expected upper/lower pair
- limb 4 (leg) total 507.8 is +72.0% from 295.2
- limb 4 has 3 skeletal segments; expected upper/lower pair
- torso 332.0 is +103.9% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### K
- limb 2 thigh 143.0 is -5.8% from 151.8
- limb 3 calf 154.2 is +7.5% from 143.5
- limb 4 (leg) total 338.0 is +14.5% from 295.2
- limb 4 thigh 164.0 is +8.1% from 151.8
- limb 4 calf 174.0 is +21.3% from 143.5
- torso 92.1 is -43.4% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### L
- limb 1 (arm) total 216.3 is +9.3% from 197.8
- limb 1 forearm 108.0 is +26.9% from 85.1
- limb 2 (arm) total 216.3 is +9.3% from 197.8
- limb 2 forearm 108.0 is +26.9% from 85.1
- limb 3 (leg) total 619.4 is +109.8% from 295.2
- limb 3 has 3 skeletal segments; expected upper/lower pair
- limb 4 (leg) total 589.9 is +99.8% from 295.2
- limb 4 has 3 skeletal segments; expected upper/lower pair
- torso 242.0 is +48.6% from 162.8

### M
- limb 1 (leg) total 508.0 is +72.1% from 295.2
- limb 1 thigh 254.0 is +67.4% from 151.8
- limb 1 calf 254.0 is +77.1% from 143.5
- limb 2 (leg) total 508.0 is +72.1% from 295.2
- limb 2 thigh 254.0 is +67.4% from 151.8
- limb 2 calf 254.0 is +77.1% from 143.5
- limb 3 (leg) total 993.0 is +236.3% from 295.2
- limb 3 thigh 495.4 is +226.4% from 151.8
- limb 3 calf 497.5 is +246.8% from 143.5
- limb 4 (leg) total 987.4 is +234.4% from 295.2
- limb 4 thigh 489.8 is +222.7% from 151.8
- limb 4 calf 497.5 is +246.8% from 143.5
- torso 535.6 is +229.0% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### N
- limb 1 (leg) total 572.2 is +93.8% from 295.2
- limb 1 thigh 266.2 is +75.4% from 151.8
- limb 1 calf 306.0 is +113.3% from 143.5
- limb 2 (leg) total 572.2 is +93.8% from 295.2
- limb 2 thigh 266.2 is +75.4% from 151.8
- limb 2 calf 306.0 is +113.3% from 143.5
- limb 3 (leg) total 454.4 is +53.9% from 295.2
- limb 3 thigh 182.4 is +20.2% from 151.8
- limb 3 calf 272.0 is +89.6% from 143.5
- limb 4 (leg) total 454.4 is +53.9% from 295.2
- limb 4 thigh 182.4 is +20.2% from 151.8
- limb 4 calf 272.0 is +89.6% from 143.5
- torso 555.4 is +241.1% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### O
- limb 1 (leg) total 514.8 is +74.4% from 295.2
- limb 1 thigh 215.5 is +42.0% from 151.8
- limb 1 calf 299.3 is +108.6% from 143.5
- limb 2 (leg) total 507.1 is +71.8% from 295.2
- limb 2 thigh 207.9 is +37.0% from 151.8
- limb 2 calf 299.3 is +108.6% from 143.5
- limb 3 (leg) total 461.1 is +56.2% from 295.2
- limb 3 thigh 177.9 is +17.2% from 151.8
- limb 3 calf 283.2 is +97.4% from 143.5
- limb 4 (leg) total 467.7 is +58.4% from 295.2
- limb 4 thigh 184.5 is +21.5% from 151.8
- limb 4 calf 283.2 is +97.4% from 143.5
- torso 607.1 is +272.9% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### P
- expected 4 measurable limbs; found 3
- limb 1 (leg) total 542.7 is +83.8% from 295.2
- limb 1 has 5 skeletal segments; expected upper/lower pair
- limb 2 (leg) total 394.1 is +33.5% from 295.2
- limb 2 thigh 198.1 is +30.5% from 151.8
- limb 2 calf 196.0 is +36.7% from 143.5
- limb 3 (leg) total 394.1 is +33.5% from 295.2
- limb 3 thigh 198.0 is +30.5% from 151.8
- limb 3 calf 196.0 is +36.7% from 143.5
- torso 238.0 is +46.2% from 162.8

### Q
- expected 4 measurable limbs; found 3
- expected 1 measurable torso(s); found 0
- limb 1 (leg) total 720.4 is +144.0% from 295.2
- limb 1 has 5 skeletal segments; expected upper/lower pair
- limb 2 (leg) total 720.4 is +144.0% from 295.2
- limb 2 has 5 skeletal segments; expected upper/lower pair
- limb 3 (arm) total 164.5 is -16.9% from 197.8
- limb 3 has 4 skeletal segments; expected upper/lower pair
- head 124.0 is +12.7% from 110.0

### R
- expected 4 measurable limbs; found 3
- limb 1 (leg) total 542.7 is +83.8% from 295.2
- limb 1 has 5 skeletal segments; expected upper/lower pair
- limb 2 (leg) total 394.1 is +33.5% from 295.2
- limb 2 thigh 198.1 is +30.5% from 151.8
- limb 2 calf 196.0 is +36.7% from 143.5
- limb 3 (leg) total 509.6 is +72.6% from 295.2
- limb 3 thigh 240.8 is +58.7% from 151.8
- limb 3 calf 268.8 is +87.4% from 143.5
- torso 238.0 is +46.2% from 162.8

### S
- limb 1 (leg) total 474.5 is +60.7% from 295.2
- limb 1 thigh 225.6 is +48.6% from 151.8
- limb 1 calf 248.9 is +73.5% from 143.5
- limb 2 (leg) total 473.0 is +60.2% from 295.2
- limb 2 thigh 227.0 is +49.6% from 151.8
- limb 2 calf 246.0 is +71.5% from 143.5
- limb 3 (arm) total 154.8 is -21.8% from 197.8
- limb 3 upper arm 73.8 is -34.5% from 112.7
- limb 4 (arm) total 142.4 is -28.0% from 197.8
- limb 4 upper arm 60.0 is -46.8% from 112.7
- torso 307.2 is +88.7% from 162.8

### T
- limb 1 (leg) total 242.0 is -18.0% from 295.2
- limb 1 thigh 124.0 is -18.3% from 151.8
- limb 1 calf 118.0 is -17.7% from 143.5
- limb 2 (leg) total 242.0 is -18.0% from 295.2
- limb 2 thigh 124.0 is -18.3% from 151.8
- limb 2 calf 118.0 is -17.7% from 143.5
- limb 3 (leg) total 340.0 is +15.2% from 295.2
- limb 3 thigh 172.0 is +13.3% from 151.8
- limb 3 calf 168.0 is +17.1% from 143.5
- limb 4 (leg) total 340.0 is +15.2% from 295.2
- limb 4 thigh 172.0 is +13.3% from 151.8
- limb 4 calf 168.0 is +17.1% from 143.5
- torso 244.0 is +49.9% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### U
- limb 1 (leg) total 396.2 is +34.2% from 295.2
- limb 1 thigh 176.2 is +16.1% from 151.8
- limb 1 calf 220.0 is +53.4% from 143.5
- limb 2 (leg) total 360.1 is +22.0% from 295.2
- limb 2 thigh 176.1 is +16.1% from 151.8
- limb 2 calf 184.0 is +28.3% from 143.5
- limb 3 (leg) total 364.3 is +23.4% from 295.2
- limb 3 thigh 170.3 is +12.2% from 151.8
- limb 3 calf 194.0 is +35.2% from 143.5
- limb 4 (leg) total 364.3 is +23.4% from 295.2
- limb 4 thigh 170.3 is +12.2% from 151.8
- limb 4 calf 194.0 is +35.2% from 143.5
- torso 574.4 is +252.8% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### V
- limb 1 (leg) total 516.6 is +75.0% from 295.2
- limb 1 thigh 243.8 is +60.6% from 151.8
- limb 1 calf 272.8 is +90.2% from 143.5
- limb 2 (leg) total 516.6 is +75.0% from 295.2
- limb 2 thigh 243.8 is +60.6% from 151.8
- limb 2 calf 272.8 is +90.2% from 143.5
- limb 3 (leg) total 338.9 is +14.8% from 295.2
- limb 3 thigh 174.4 is +14.9% from 151.8
- limb 3 calf 164.5 is +14.7% from 143.5
- limb 4 (leg) total 338.9 is +14.8% from 295.2
- limb 4 thigh 174.4 is +14.9% from 151.8
- limb 4 calf 164.5 is +14.7% from 143.5
- torso 120.0 is -26.3% from 162.8
- head 116.0 is +5.5% from 110.0
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### W
- limb 1 (leg) total 382.3 is +29.5% from 295.2
- limb 1 thigh 202.4 is +33.4% from 151.8
- limb 1 calf 179.9 is +25.4% from 143.5
- limb 2 (leg) total 382.3 is +29.5% from 295.2
- limb 2 thigh 202.4 is +33.4% from 151.8
- limb 2 calf 179.9 is +25.4% from 143.5
- limb 3 (leg) total 1071.3 is +262.9% from 295.2
- limb 3 thigh 460.6 is +203.5% from 151.8
- limb 3 calf 610.7 is +325.8% from 143.5
- limb 4 (leg) total 1071.3 is +262.9% from 295.2
- limb 4 thigh 460.6 is +203.5% from 151.8
- limb 4 calf 610.7 is +325.8% from 143.5
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### X
- limb 1 (leg) total 363.2 is +23.0% from 295.2
- limb 1 thigh 182.6 is +20.3% from 151.8
- limb 1 calf 180.6 is +25.9% from 143.5
- limb 2 (leg) total 363.2 is +23.0% from 295.2
- limb 2 thigh 182.6 is +20.3% from 151.8
- limb 2 calf 180.6 is +25.9% from 143.5
- limb 3 (leg) total 371.4 is +25.8% from 295.2
- limb 3 thigh 172.2 is +13.5% from 151.8
- limb 3 calf 199.1 is +38.8% from 143.5
- limb 4 (leg) total 371.4 is +25.8% from 295.2
- limb 4 thigh 172.2 is +13.5% from 151.8
- limb 4 calf 199.1 is +38.8% from 143.5
- torso 80.0 is -50.9% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### Y
- limb 1 (leg) total 368.2 is +24.7% from 295.2
- limb 1 thigh 190.4 is +25.5% from 151.8
- limb 1 calf 177.7 is +23.9% from 143.5
- limb 2 (leg) total 368.2 is +24.7% from 295.2
- limb 2 thigh 190.4 is +25.5% from 151.8
- limb 2 calf 177.7 is +23.9% from 143.5
- limb 3 thigh 93.7 is -38.2% from 151.8
- limb 3 calf 201.8 is +40.7% from 143.5
- limb 4 thigh 93.7 is -38.2% from 151.8
- limb 4 calf 201.8 is +40.7% from 143.5
- torso 180.0 is +10.6% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### Z
- limb 1 (leg) total 400.0 is +35.5% from 295.2
- limb 1 has 1 skeletal segments; expected upper/lower pair
- limb 2 (leg) total 382.0 is +29.4% from 295.2
- limb 2 has 1 skeletal segments; expected upper/lower pair
- limb 3 (leg) total 428.5 is +45.2% from 295.2
- limb 3 has 3 skeletal segments; expected upper/lower pair
- limb 4 (leg) total 426.5 is +44.5% from 295.2
- limb 4 has 3 skeletal segments; expected upper/lower pair
- torso 613.6 is +276.9% from 162.8
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

## Enforcement note

For diagnostic CI, `python validate_anatomy.py --strict` exits non-zero while any glyph is outside tolerance. It is not the release gate for the historically faithful build: composite surreal constructions are intentionally not auto-exempted or normalized.
