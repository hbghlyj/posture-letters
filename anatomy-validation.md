# Posture Master — Anatomical Consistency Audit

**Tolerance:** ±5%  
**Baseline:** revised A forward-fold pose  
**Result:** 1 passed; 25 flagged  
**Policy:** diagnostic only; exact 1782 pose construction takes priority where the two goals conflict.

## Baseline measurements

| Element | Baseline units |
|---|---:|
| Thigh | 300.9 |
| Calf | 304.8 |
| Whole leg | 605.7 |
| Upper arm | 155.0 |
| Forearm | 177.5 |
| Whole arm | 332.5 |
| Pelvis-to-shoulder torso/spine | 512.1 |
| Head diameter | 110.0 |

Measurements use source centerlines, not outline bounding boxes. No hidden foreshortening exemptions are applied.

## A–Z summary

| Glyph | Status | Limb totals | Torso | Head | Primary finding |
|---|---|---|---:|---:|---|
| A | **PASS** | L 606.9, L 604.5, A 325.0, A 340.0 | 512.1 | 110.0 | Within tolerance |
| B | **FAIL** | A 184.6, A 200.2, A 270.9, A 393.8 | 350.3 | 110.0 | limb 1 (arm) total 184.6 is -44.5% from 332.5 |
| C | **FAIL** | A 334.4, A 324.7, A 385.6, A 317.8 | 371.5 | 110.0 | limb 2 forearm 163.5 is -7.9% from 177.5 |
| D | **FAIL** | L 663.7, A 327.4, A 293.0 | 524.1 | 110.0 | expected 4 measurable limbs; found 3 |
| E | **FAIL** | A 410.2, A 286.6, A 425.0, A 390.0 | 580.0 | 110.0 | limb 1 (arm) total 410.2 is +23.4% from 332.5 |
| F | **FAIL** | A 410.6, A 289.0, A 240.6, A 240.6 | 380.0 | 110.0 | limb 1 (arm) total 410.6 is +23.5% from 332.5 |
| G | **FAIL** | L 721.6, A 412.0, L 429.6, A 308.8 | 423.6 | 96.0 | limb 1 (leg) total 721.6 is +19.1% from 605.7 |
| H | **FAIL** | A 195.6, A 390.2, A 390.0, A 195.6, A 390.2, A 390.0 | 206.2, 206.2 | 110.0, 110.0 | expected 4 measurable limbs; found 6 |
| I | **FAIL** | A 290.4, A 290.4, A 340.1, A 340.1 | 290.0 | 110.0 | limb 1 (arm) total 290.4 is -12.7% from 332.5 |
| J | **FAIL** | A 266.5, A 84.0, A 282.4 | 898.4 | 110.0 | expected 4 measurable limbs; found 3 |
| K | **FAIL** | A 349.7, A 256.8, A 266.2, A 387.1 | 320.1 | 110.0 | limb 1 (arm) total 349.7 is +5.2% from 332.5 |
| L | **FAIL** | A 380.0, A 340.0, A 305.0, A 270.7 | 472.3 | 110.0 | limb 1 (arm) total 380.0 is +14.3% from 332.5 |
| M | **FAIL** | L 640.0, L 640.0 | — | 70.0 | expected 4 measurable limbs; found 2 |
| N | **FAIL** | L 1243.0, A 70.7, A 318.7 | 510.6 | 110.0 | expected 4 measurable limbs; found 3 |
| O | **FAIL** | L 696.2, L 696.2 | — | 124.0 | expected 4 measurable limbs; found 2 |
| P | **FAIL** | A 324.6, A 283.1, A 240.2, A 240.5 | 395.0 | 110.0 | limb 1 has 4 skeletal segments; expected upper/lower pair |
| Q | **FAIL** | L 720.4, L 720.4, A 182.2 | — | 124.0 | expected 4 measurable limbs; found 3 |
| R | **FAIL** | L 853.8, L 478.4, A 240.5 | 395.0 | 110.0 | expected 4 measurable limbs; found 3 |
| S | **FAIL** | A 363.8, A 317.7, L 517.9, A 114.4 | 423.2 | 110.0 | limb 1 (arm) total 363.8 is +9.4% from 332.5 |
| T | **FAIL** | A 258.2, A 258.2, A 345.0, A 345.0 | 235.0 | 110.0 | limb 1 (arm) total 258.2 is -22.4% from 332.5 |
| U | **FAIL** | L 721.2, L 721.2, L 617.7, L 617.7 | 100.0 | 110.0 | limb 1 (leg) total 721.2 is +19.1% from 605.7 |
| V | **FAIL** | L 516.6, L 516.6, A 338.9, A 338.9 | 120.0 | 110.0 | limb 1 (leg) total 516.6 is -14.7% from 605.7 |
| W | **FAIL** | A 339.4, A 339.4, L 1155.4, L 1155.4 | 135.0 | 110.0 | limb 1 upper arm 184.4 is +19.0% from 155.0 |
| X | **FAIL** | A 363.2, A 363.2, A 371.4, A 371.4 | 80.0 | 110.0 | limb 1 (arm) total 363.2 is +9.2% from 332.5 |
| Y | **FAIL** | A 231.1, A 231.1, A 380.4, A 380.4 | 210.0 | 110.0 | limb 1 (arm) total 231.1 is -30.5% from 332.5 |
| Z | **FAIL** | A 415.5, L 445.3, A 377.8 | 614.8 | 110.0 | expected 4 measurable limbs; found 3 |

## Detailed flags

### B
- limb 1 (arm) total 184.6 is -44.5% from 332.5
- limb 1 upper arm 91.2 is -41.1% from 155.0
- limb 1 forearm 93.3 is -47.4% from 177.5
- limb 2 (arm) total 200.2 is -39.8% from 332.5
- limb 2 upper arm 116.7 is -24.7% from 155.0
- limb 2 forearm 83.5 is -53.0% from 177.5
- limb 3 (arm) total 270.9 is -18.5% from 332.5
- limb 3 upper arm 135.6 is -12.5% from 155.0
- limb 3 forearm 135.2 is -23.8% from 177.5
- limb 4 (arm) total 393.8 is +18.4% from 332.5
- limb 4 upper arm 200.8 is +29.6% from 155.0
- limb 4 forearm 193.0 is +8.7% from 177.5
- torso 350.3 is -31.6% from 512.1
- nearest-baseline classification gives 4 arm(s) and 0 leg(s)

### C
- limb 2 forearm 163.5 is -7.9% from 177.5
- limb 3 (arm) total 385.6 is +16.0% from 332.5
- limb 3 upper arm 145.3 is -6.2% from 155.0
- limb 3 forearm 240.2 is +35.3% from 177.5
- limb 4 upper arm 127.8 is -17.6% from 155.0
- limb 4 forearm 190.1 is +7.1% from 177.5
- torso 371.5 is -27.5% from 512.1
- nearest-baseline classification gives 4 arm(s) and 0 leg(s)

### D
- expected 4 measurable limbs; found 3
- limb 1 (leg) total 663.7 is +9.6% from 605.7
- limb 1 has 4 skeletal segments; expected upper/lower pair
- limb 2 has 3 skeletal segments; expected upper/lower pair
- limb 3 (arm) total 293.0 is -11.9% from 332.5
- limb 3 has 3 skeletal segments; expected upper/lower pair

### E
- limb 1 (arm) total 410.2 is +23.4% from 332.5
- limb 1 upper arm 210.2 is +35.6% from 155.0
- limb 1 forearm 200.0 is +12.7% from 177.5
- limb 2 (arm) total 286.6 is -13.8% from 332.5
- limb 2 forearm 125.0 is -29.6% from 177.5
- limb 3 (arm) total 425.0 is +27.8% from 332.5
- limb 3 upper arm 210.0 is +35.5% from 155.0
- limb 3 forearm 215.0 is +21.1% from 177.5
- limb 4 (arm) total 390.0 is +17.3% from 332.5
- limb 4 upper arm 195.0 is +25.8% from 155.0
- limb 4 forearm 195.0 is +9.9% from 177.5
- torso 580.0 is +13.3% from 512.1
- nearest-baseline classification gives 4 arm(s) and 0 leg(s)

### F
- limb 1 (arm) total 410.6 is +23.5% from 332.5
- limb 1 upper arm 200.6 is +29.4% from 155.0
- limb 1 forearm 210.0 is +18.3% from 177.5
- limb 2 (arm) total 289.0 is -13.1% from 332.5
- limb 2 upper arm 144.0 is -7.1% from 155.0
- limb 2 forearm 145.0 is -18.3% from 177.5
- limb 3 (arm) total 240.5 is -27.7% from 332.5
- limb 3 upper arm 130.1 is -16.1% from 155.0
- limb 3 forearm 110.5 is -37.8% from 177.5
- limb 4 (arm) total 240.5 is -27.7% from 332.5
- limb 4 upper arm 130.1 is -16.1% from 155.0
- limb 4 forearm 110.5 is -37.8% from 177.5
- torso 380.0 is -25.8% from 512.1
- nearest-baseline classification gives 4 arm(s) and 0 leg(s)

### G
- limb 1 (leg) total 721.6 is +19.1% from 605.7
- limb 1 has 5 skeletal segments; expected upper/lower pair
- limb 2 (arm) total 412.0 is +23.9% from 332.5
- limb 2 has 3 skeletal segments; expected upper/lower pair
- limb 3 (leg) total 429.6 is -29.1% from 605.7
- limb 3 has 3 skeletal segments; expected upper/lower pair
- limb 4 (arm) total 308.8 is -7.1% from 332.5
- limb 4 forearm 155.7 is -12.3% from 177.5
- torso 423.6 is -17.3% from 512.1
- head 96.0 is -12.7% from 110.0

### H
- expected 4 measurable limbs; found 6
- expected 1 measurable torso; found 2
- expected 1 head; found 2
- limb 1 (arm) total 195.6 is -41.2% from 332.5
- limb 1 has 3 skeletal segments; expected upper/lower pair
- limb 2 (arm) total 390.2 is +17.3% from 332.5
- limb 2 upper arm 195.1 is +25.9% from 155.0
- limb 2 forearm 195.0 is +9.9% from 177.5
- limb 3 (arm) total 390.0 is +17.3% from 332.5
- limb 3 upper arm 195.0 is +25.8% from 155.0
- limb 3 forearm 195.0 is +9.9% from 177.5
- limb 4 (arm) total 195.6 is -41.2% from 332.5
- limb 4 has 3 skeletal segments; expected upper/lower pair
- limb 5 (arm) total 390.2 is +17.3% from 332.5
- limb 5 upper arm 195.1 is +25.9% from 155.0
- limb 5 forearm 195.0 is +9.9% from 177.5
- limb 6 (arm) total 390.0 is +17.3% from 332.5
- limb 6 upper arm 195.0 is +25.8% from 155.0
- limb 6 forearm 195.0 is +9.9% from 177.5
- torso 206.2 is -59.7% from 512.1
- torso 206.2 is -59.7% from 512.1

### I
- limb 1 (arm) total 290.4 is -12.7% from 332.5
- limb 1 upper arm 145.3 is -6.2% from 155.0
- limb 1 forearm 145.0 is -18.3% from 177.5
- limb 2 (arm) total 290.4 is -12.7% from 332.5
- limb 2 upper arm 145.3 is -6.2% from 155.0
- limb 2 forearm 145.0 is -18.3% from 177.5
- limb 3 upper arm 170.1 is +9.7% from 155.0
- limb 4 upper arm 170.1 is +9.7% from 155.0
- torso 290.0 is -43.4% from 512.1
- nearest-baseline classification gives 4 arm(s) and 0 leg(s)

### J
- expected 4 measurable limbs; found 3
- limb 1 (arm) total 266.5 is -19.9% from 332.5
- limb 1 upper arm 136.5 is -12.0% from 155.0
- limb 1 forearm 130.0 is -26.8% from 177.5
- limb 2 (arm) total 84.0 is -74.8% from 332.5
- limb 2 upper arm 41.2 is -73.4% from 155.0
- limb 2 forearm 42.7 is -75.9% from 177.5
- limb 3 (arm) total 282.4 is -15.1% from 332.5
- limb 3 upper arm 134.6 is -13.1% from 155.0
- limb 3 forearm 147.7 is -16.8% from 177.5
- torso 898.4 is +75.4% from 512.1

### K
- limb 1 (arm) total 349.7 is +5.2% from 332.5
- limb 1 has 4 skeletal segments; expected upper/lower pair
- limb 2 (arm) total 256.8 is -22.8% from 332.5
- limb 2 upper arm 140.8 is -9.2% from 155.0
- limb 2 forearm 116.0 is -34.7% from 177.5
- limb 3 (arm) total 266.2 is -19.9% from 332.5
- limb 3 upper arm 145.8 is -6.0% from 155.0
- limb 3 forearm 120.4 is -32.2% from 177.5
- limb 4 (arm) total 387.0 is +16.4% from 332.5
- limb 4 upper arm 180.3 is +16.4% from 155.0
- limb 4 forearm 206.7 is +16.5% from 177.5
- torso 320.1 is -37.5% from 512.1
- nearest-baseline classification gives 4 arm(s) and 0 leg(s)

### L
- limb 1 (arm) total 380.0 is +14.3% from 332.5
- limb 1 upper arm 190.0 is +22.6% from 155.0
- limb 1 forearm 190.0 is +7.0% from 177.5
- limb 2 upper arm 170.0 is +9.7% from 155.0
- limb 3 (arm) total 305.0 is -8.3% from 332.5
- limb 3 upper arm 177.6 is +14.6% from 155.0
- limb 3 forearm 127.5 is -28.2% from 177.5
- limb 4 (arm) total 270.7 is -18.6% from 332.5
- limb 4 forearm 117.7 is -33.7% from 177.5
- torso 472.3 is -7.8% from 512.1
- nearest-baseline classification gives 4 arm(s) and 0 leg(s)

### M
- expected 4 measurable limbs; found 2
- expected 1 measurable torso; found 0
- contains 2 unclassified composite body path(s): 433.0, 433.0
- limb 1 (leg) total 640.0 is +5.7% from 605.7
- limb 1 has 1 skeletal segments; expected upper/lower pair
- limb 2 (leg) total 640.0 is +5.7% from 605.7
- limb 2 has 1 skeletal segments; expected upper/lower pair
- head 70.0 is -36.4% from 110.0

### N
- expected 4 measurable limbs; found 3
- limb 1 (leg) total 1243.0 is +105.2% from 605.7
- limb 1 has 4 skeletal segments; expected upper/lower pair
- limb 2 (arm) total 70.7 is -78.7% from 332.5
- limb 2 upper arm 40.3 is -74.0% from 155.0
- limb 2 forearm 30.4 is -82.9% from 177.5
- limb 3 has 3 skeletal segments; expected upper/lower pair

### O
- expected 4 measurable limbs; found 2
- expected 1 measurable torso; found 0
- limb 1 (leg) total 696.2 is +14.9% from 605.7
- limb 1 has 5 skeletal segments; expected upper/lower pair
- limb 2 (leg) total 696.2 is +14.9% from 605.7
- limb 2 has 5 skeletal segments; expected upper/lower pair
- head 124.0 is +12.7% from 110.0

### P
- limb 1 has 4 skeletal segments; expected upper/lower pair
- limb 2 (arm) total 283.1 is -14.9% from 332.5
- limb 2 has 3 skeletal segments; expected upper/lower pair
- limb 3 (arm) total 240.2 is -27.8% from 332.5
- limb 3 upper arm 125.1 is -19.3% from 155.0
- limb 3 forearm 115.1 is -35.2% from 177.5
- limb 4 (arm) total 240.5 is -27.7% from 332.5
- limb 4 upper arm 125.1 is -19.3% from 155.0
- limb 4 forearm 115.4 is -35.0% from 177.5
- torso 395.0 is -22.9% from 512.1
- nearest-baseline classification gives 4 arm(s) and 0 leg(s)

### Q
- expected 4 measurable limbs; found 3
- expected 1 measurable torso; found 0
- limb 1 (leg) total 720.4 is +18.9% from 605.7
- limb 1 has 5 skeletal segments; expected upper/lower pair
- limb 2 (leg) total 720.4 is +18.9% from 605.7
- limb 2 has 5 skeletal segments; expected upper/lower pair
- limb 3 (arm) total 182.2 is -45.2% from 332.5
- limb 3 has 4 skeletal segments; expected upper/lower pair
- head 124.0 is +12.7% from 110.0

### R
- expected 4 measurable limbs; found 3
- limb 1 (leg) total 853.8 is +40.9% from 605.7
- limb 1 has 4 skeletal segments; expected upper/lower pair
- limb 2 (leg) total 478.4 is -21.0% from 605.7
- limb 2 thigh 178.9 is -40.6% from 300.9
- limb 3 (arm) total 240.5 is -27.7% from 332.5
- limb 3 upper arm 130.4 is -15.9% from 155.0
- limb 3 forearm 110.1 is -38.0% from 177.5
- torso 395.0 is -22.9% from 512.1

### S
- limb 1 (arm) total 363.8 is +9.4% from 332.5
- limb 1 forearm 205.0 is +15.5% from 177.5
- limb 3 (leg) total 517.9 is -14.5% from 605.7
- limb 3 has 4 skeletal segments; expected upper/lower pair
- limb 4 (arm) total 114.4 is -65.6% from 332.5
- limb 4 upper arm 65.2 is -57.9% from 155.0
- limb 4 forearm 49.2 is -72.3% from 177.5
- torso 423.2 is -17.4% from 512.1
- nearest-baseline classification gives 3 arm(s) and 1 leg(s)

### T
- limb 1 (arm) total 258.2 is -22.4% from 332.5
- limb 1 upper arm 143.2 is -7.6% from 155.0
- limb 1 forearm 115.0 is -35.2% from 177.5
- limb 2 (arm) total 258.2 is -22.4% from 332.5
- limb 2 upper arm 143.2 is -7.6% from 155.0
- limb 2 forearm 115.0 is -35.2% from 177.5
- limb 3 upper arm 172.0 is +11.0% from 155.0
- limb 4 upper arm 172.0 is +11.0% from 155.0
- torso 235.0 is -54.1% from 512.1
- nearest-baseline classification gives 4 arm(s) and 0 leg(s)

### U
- limb 1 (leg) total 721.2 is +19.1% from 605.7
- limb 1 has 3 skeletal segments; expected upper/lower pair
- limb 2 (leg) total 721.2 is +19.1% from 605.7
- limb 2 has 3 skeletal segments; expected upper/lower pair
- limb 3 has 3 skeletal segments; expected upper/lower pair
- limb 4 has 3 skeletal segments; expected upper/lower pair
- torso 100.0 is -80.5% from 512.1
- nearest-baseline classification gives 0 arm(s) and 4 leg(s)

### V
- limb 1 (leg) total 516.6 is -14.7% from 605.7
- limb 1 thigh 243.8 is -19.0% from 300.9
- limb 1 calf 272.8 is -10.5% from 304.8
- limb 2 (leg) total 516.6 is -14.7% from 605.7
- limb 2 thigh 243.8 is -19.0% from 300.9
- limb 2 calf 272.8 is -10.5% from 304.8
- limb 3 upper arm 174.4 is +12.5% from 155.0
- limb 3 forearm 164.5 is -7.3% from 177.5
- limb 4 upper arm 174.4 is +12.5% from 155.0
- limb 4 forearm 164.5 is -7.3% from 177.5
- torso 120.0 is -76.6% from 512.1

### W
- limb 1 upper arm 184.4 is +19.0% from 155.0
- limb 1 forearm 155.0 is -12.7% from 177.5
- limb 2 upper arm 184.4 is +19.0% from 155.0
- limb 2 forearm 155.0 is -12.7% from 177.5
- limb 3 (leg) total 1155.4 is +90.7% from 605.7
- limb 3 thigh 425.4 is +41.4% from 300.9
- limb 3 calf 730.0 is +139.5% from 304.8
- limb 4 (leg) total 1155.4 is +90.7% from 605.7
- limb 4 thigh 425.4 is +41.4% from 300.9
- limb 4 calf 730.0 is +139.5% from 304.8
- torso 135.0 is -73.6% from 512.1

### X
- limb 1 (arm) total 363.2 is +9.2% from 332.5
- limb 1 upper arm 182.6 is +17.8% from 155.0
- limb 2 (arm) total 363.2 is +9.2% from 332.5
- limb 2 upper arm 182.6 is +17.8% from 155.0
- limb 3 (arm) total 371.4 is +11.7% from 332.5
- limb 3 upper arm 172.2 is +11.1% from 155.0
- limb 3 forearm 199.1 is +12.2% from 177.5
- limb 4 (arm) total 371.4 is +11.7% from 332.5
- limb 4 upper arm 172.2 is +11.1% from 155.0
- limb 4 forearm 199.1 is +12.2% from 177.5
- torso 80.0 is -84.4% from 512.1
- nearest-baseline classification gives 4 arm(s) and 0 leg(s)

### Y
- limb 1 (arm) total 231.1 is -30.5% from 332.5
- limb 1 upper arm 118.0 is -23.9% from 155.0
- limb 1 forearm 113.1 is -36.3% from 177.5
- limb 2 (arm) total 231.1 is -30.5% from 332.5
- limb 2 upper arm 118.0 is -23.9% from 155.0
- limb 2 forearm 113.1 is -36.3% from 177.5
- limb 3 (arm) total 380.4 is +14.4% from 332.5
- limb 3 upper arm 190.1 is +22.6% from 155.0
- limb 3 forearm 190.3 is +7.2% from 177.5
- limb 4 (arm) total 380.4 is +14.4% from 332.5
- limb 4 upper arm 190.1 is +22.6% from 155.0
- limb 4 forearm 190.3 is +7.2% from 177.5
- torso 210.0 is -59.0% from 512.1
- nearest-baseline classification gives 4 arm(s) and 0 leg(s)

### Z
- expected 4 measurable limbs; found 3
- limb 1 (arm) total 415.5 is +25.0% from 332.5
- limb 1 upper arm 205.0 is +32.3% from 155.0
- limb 1 forearm 210.5 is +18.6% from 177.5
- limb 2 (leg) total 445.3 is -26.5% from 605.7
- limb 2 thigh 195.3 is -35.1% from 300.9
- limb 2 calf 250.0 is -18.0% from 304.8
- limb 3 (arm) total 377.8 is +13.6% from 332.5
- limb 3 upper arm 162.8 is +5.0% from 155.0
- limb 3 forearm 215.0 is +21.1% from 177.5
- torso 614.8 is +20.0% from 512.1

## Enforcement note

For diagnostic CI, `python validate_anatomy.py --strict` exits non-zero while any glyph is outside tolerance. It is not the release gate for the historically faithful build: composite surreal constructions are intentionally not auto-exempted or normalized.
