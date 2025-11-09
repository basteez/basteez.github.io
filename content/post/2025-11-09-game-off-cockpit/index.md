---
title: "Adding Interactive Cockpit Controls to Grav-Sync"
draft: false
tags:
  - game-dev
  - javascript
categories:
  - game-dev
comments: true
date: 2025-11-09
---

Today I implemented a major visual upgrade to my GitHub Game Off 2025 project, **Grav-Sync**, by adding an interactive cockpit interface with animated control knobs. This enhancement significantly improves the game's visual feedback and makes the controls more intuitive and engaging.

## What Changed

### Animated Control Knobs

The main feature I added today is a fully functional cockpit interface with two animated control knobs:

- **Red Knob** (controlled by A/D keys): Adjusts wave frequency
- **Blue Knob** (controlled by W/S keys): Adjusts wave amplitude

Each knob has a 2-frame animation that advances whenever the player presses the corresponding control keys, providing immediate visual feedback for player input.

### New Sprite System Method

To support the knobs, I extended the `Sprite` class with a new `nextFrame()` method that allows manual frame advancement. This is different from the existing automatic animation used by the Earth sprite, which continuously cycles through frames. The knobs only animate when the player provides input, making them feel more responsive and connected to the controls.

```javascript
// Advance animation by one frame (useful for manual control)
nextFrame() {
  this.index = (this.index + 1) % this.len;
}
```

### Input Handler Integration

I updated the `InputHandler` class to trigger knob animations alongside the existing player wave adjustments. Now when you press W/S or A/D keys, not only does your wave change, but the corresponding knob visibly rotates, providing clear visual feedback:

```javascript
w: {
  pressed: keyIsDown(87) || keyIsDown(119),
  action: () => {
    this.player.increaseAmplitude();
    blueKnob.nextFrame();
  },
}
```

### Cockpit Rendering

I created a new `drawCockpit()` method in the `Game` class that handles the rendering of the cockpit base image and positions both knobs correctly relative to it. The cockpit is positioned near the bottom of the screen, and the knobs are placed at appropriate positions using a local coordinate system:

- The cockpit base is rendered first
- Both knobs are positioned relative to the cockpit using `push()`/`pop()` transformations
- Each knob maintains its current animation frame and scale

### UI Repositioning

To accommodate the new cockpit interface, I repositioned the UI elements:

- Moved amplitude and frequency displays to be adjacent to their respective knobs
- Centered the sync percentage and score displays on the cockpit
- Removed some redundant labels to keep the interface clean
- Adjusted the Earth sprite position slightly upward to leave room for the cockpit

### Configuration Adjustments

I made a small but important change to the configuration: the Earth sprite's Y position was adjusted upward by 80 pixels (`config.earthY = config.screenHeight / 2 - 80`) to better center the visible play area above the cockpit.

## Technical Implementation

The implementation involved several files:

1. **animations/knob.json** - Animation configuration defining two frames for the knob rotation
2. **sprites/** - Added three new images: `cockpit.png`, `red-knob.png`, and `blue-knob.png`
3. **sketch.js** - Preloaded new assets and initialized knob sprites
4. **game.js** - Implemented `drawCockpit()` method for rendering
5. **input.js** - Integrated knob animations with key press handlers
6. **sprite.js** - Added `nextFrame()` method for manual animation control
7. **ui.js** - Repositioned UI text elements
8. **config.js** - Adjusted Earth position

## Code Organization

After implementing the cockpit feature, I also performed a minor refactoring to better organize global variables in `sketch.js`, grouping related variables together for improved code readability.

## Results

![result.gif](https://github.com/basteez/basteez.github.io/blob/main/content/post/2025-11-09-game-off-cockpit/result.gif?raw=true)

The cockpit addition makes the game feel more polished and immersive. Players now have:

- **Visual feedback** - See exactly when their inputs are registered
- **Clearer controls** - The knobs make it obvious what W/S and A/D keys control
- **Better aesthetics** - The cockpit theme reinforces the space/orbital mechanics concept
- **Improved layout** - UI elements are better organized around the cockpit

This change represents a significant step forward in the game's visual design and user experience. The cockpit not only looks good but also serves a functional purpose by making the controls more intuitive and providing immediate visual feedback for player actions.

## What's Next

With the cockpit in place, the game is starting to feel more complete. Future improvements might include:

- Adding sound effects for knob rotation
- Adding a main manu

You can [check out the full code on GitHub](https://github.com/basteez/grav-sync), and I'd love to hear feedback from anyone who tries it out!
