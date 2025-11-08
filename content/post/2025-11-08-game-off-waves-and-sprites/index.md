---
title: "DevLog: Adding Dynamic Waves and Animated Sprites to Grav Sync"
draft: false
tags:
  - game-dev
  - javascript
categories:
  - game-dev
comments: true
date: 2025-11-08
---

Over the past development cycle, I worked on two features for Grav Sync, these updates transformed the game from a static puzzle into a more dynamic and visually engaging experience.

Here's a detailed look at what was implemented and why.

## Branch 1: `random-wave` - Introducing Dynamic Challenge

### The Problem

The original game featured a fixed target wave that players needed to match. While functional, this meant that once players learned the solution, the game became repetitive. Every playthrough was essentially the same puzzle.

### The Solution: Randomized Target Frequencies

I implemented a system to randomize the target wave's frequency at the start of each round, making every attempt unique and challenging.

**Key Changes:**

1. **Random Frequency Generation**: Added `getRandomInt(10, 30)` function to generate target frequencies within a balanced range
2. **Dynamic Target Updates**: The target frequency now regenerates each time the target wave resets (when it reaches the player's orbital radius)
3. **UI Enhancement**: Added on-screen display of the current target frequency to give players clear feedback

**Implementation Details:**

```javascript
// Initialize with random frequency in setup()
targetWave.frequency = getRandomInt(10, 30);

// Regenerate on wave reset
if (targetWave.baseRadius === playerRadius) {
  if (sync > 0.8) {
    score++;
  }
  targetWave.frequency = getRandomInt(10, 30); // New random target
  targetWave.baseRadius = 380;
}
```

### Refining the Synchronization System

While implementing randomization, I also overhauled how synchronization is calculated. The original system treated frequency and amplitude equally, but through playtesting, it became clear that **frequency matching is far more critical** to achieving visual alignment.

**The New Weighted System:**

- **80% weight on frequency matching**: Ensures players prioritize getting the wave count correct
- **20% weight on amplitude matching**: Fine-tuning for perfect alignment
- **Phase ignored**: Simplified gameplay by removing phase as a factor, making the puzzle more approachable

**Technical Implementation:**

```javascript
function calculateSync() {
  // Frequency score: compare numeric values directly (ignoring phase)
  let freqRange = maxFrequency - minFrequency;
  let freqDiff = abs(targetWave.frequency - playerWave.frequency) / freqRange;
  let freqScore = 1 - freqDiff;

  // Amplitude score: compare amplitude values
  let ampRange = maxAmplitude - minAmplitude;
  let ampDiff = abs(targetWave.amplitude - playerWave.amplitude) / ampRange;
  let ampScore = 1 - ampDiff;

  // Combine with 80:20 weighting
  return freqScore * 0.8 + ampScore * 0.2;
}
```

This change made the game feel more intuitive, players could immediately see the impact of frequency adjustments while still needing to fine-tune amplitude for perfect scores.

### Impact

The `random-wave` branch transformed Grav Sync from a single-solution puzzle into a replayable game with procedural variation. Each round now presents a fresh challenge, and the weighted sync system provides clearer feedback about what matters most.

## Branch 2: `sprites` - Bringing Earth to Life

### The Vision

The original Earth was rendered as a simple static circle with basic ellipse shapes for continents. While functional, it lacked the polish and visual interest the game deserved. I wanted Earth to feel like a living, rotating planet at the center of the cosmic waves.

### Creating the Sprite System

**Step 1: Sprite Sheet Preparation**

I found a [94-frame sprite sheet](https://opengameart.org/content/rotating-pixel-art-earth) showing Earth rotating (attribution has been made into the repo):

- **Format**: 480×480 PNG
- **Layout**: 10×10 grid (10 frames per row for 9 rows, 4 frames in the final row)
- **Frame size**: 48×48 pixels per frame
- **Animation style**: Flat earth texture scrolling across a circular mask

**Step 2: Frame Data Mapping**

Created `animations/earth.json` to map all 94 frames with precise coordinates:

```json
{
  "frames": [
    {
      "name": "sprite-00",
      "position": { "x": 0, "y": 0, "w": 48, "h": 48 }
    }
    // ... 93 more frames
  ]
}
```

**Step 3: Building the Sprite Class**

Implemented a reusable `Sprite` class in `sprite.js`:

```javascript
class Sprite {
  constructor(animation, x, y, speed, scale = 1) {
    this.x = x;
    this.y = y;
    this.animation = animation; // Array of p5.Image objects
    this.w = this.animation[0].width;
    this.len = this.animation.length;
    this.speed = speed; // Animation speed (frames per draw call)
    this.scale = scale; // Scaling factor
    this.index = 0; // Current frame index
  }

  show() {
    let index = floor(this.index) % this.len;
    push();
    imageMode(CENTER);
    image(
      this.animation[index],
      this.x,
      this.y,
      this.w * this.scale,
      this.w * this.scale
    );
    pop();
  }

  animate() {
    this.index += this.speed; // Advance animation
  }
}
```

**Key Features:**

- **Flexible animation speed**: Random speed on initialization creates subtle variation
- **Scalable sprites**: Can match any target size (scaled to 96×96 to match original Earth diameter)
- **Center-based positioning**: Uses `imageMode(CENTER)` for intuitive placement
- **Error handling**: Validates animation array to prevent crashes

### Integration Challenges

**Challenge 1: Variable Scope Issues**

Initial implementation had bugs where the animation array wasn't properly declared:

```javascript
// Problem: 'animation' not declared
for (let i = 0; i < frames.length; i++) {
  animation.push(img); // ReferenceError
}
earth = new Sprite(animation, 0, i * 75, ...); // 'i' undefined here
```

**Solution:**

```javascript
function setup() {
  let animation = []; // Properly scoped
  // Load frames...
  earth = new Sprite(animation, earthX, earthY, random(0.1, 0.4), spriteScale);
}
```

**Challenge 2: Sprite Positioning**

Initially, sprites appeared in the top-left corner instead of centered. The issue was that p5.js's `image()` function defaults to corner-mode positioning.

**Solution**: Wrapped rendering in `push()`/`pop()` and set `imageMode(CENTER)` to ensure sprites draw from their center point.

**Challenge 3: Size Matching**

The original hand-drawn Earth had a diameter of 96px (radius 48), but the sprite frames were 48×48.

**Solution**: Calculate scale factor dynamically:

```javascript
let spriteScale = (earthRadius * 2) / 48; // 96 / 48 = 2.0
earth = new Sprite(animation, earthX, earthY, random(0.1, 0.4), spriteScale);
```

### The Result

![4.gif](https://github.com/basteez/basteez.github.io/blob/main/content/post/2025-11-08-game-off-waves-and-sprites/earth.gif?raw=true)

The sprite system brought immediate visual improvements:

- **Living planet**: Earth now rotates continuously, adding life to the scene
- **Variable speed**: Random animation speeds (0.1–0.4) create subtle uniqueness each game
- **Smooth animation**: 94 frames provide fluid rotation without obvious looping
- **Maintained aesthetics**: Scaled perfectly to match the original Earth size

### Code Quality Improvements

Added validation to prevent edge-case crashes:

```javascript
if (
  this.animation.length > 0 &&
  this.animation[0] &&
  typeof this.animation[0].width !== "undefined"
) {
  this.w = this.animation[0].width;
} else {
  this.w = 0;
  console.warn("Sprite: animation array is empty or invalid.");
}
```

Also fixed a stroke bleed issue where wave rendering affected subsequent draws:

```javascript
function drawWave(wave, currentTime) {
  // ... draw wave ...
  endShape(CLOSE);
  stroke("black"); // Reset stroke to prevent bleeding
}
```

## What's Next?

With these two branches merged, Grav Sync now has:

- Dynamic, randomized gameplay
- Polished visual presentation
- Intuitive sync feedback

Future improvements could include:

- **Audio integration**: Frequency-based soundscapes using p5.sound
- **Difficulty curves**: Progressive challenge scaling
- **Particle effects or shaders**: Visual feedback when sync is achieved

## Conclusion

These two updates made Grav Sync more engaging: random frequencies add replay value, and the animated Earth sprite improves the visual appeal. The game is now more fun to play than the original static version.

You can [check out the full code on GitHub](https://github.com/basteez/grav-sync), and I'd love to hear feedback from anyone who tries it out!
