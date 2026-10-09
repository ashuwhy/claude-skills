/**
 * MOTION
 *
 * The rule this file encodes: motion responds to touch, never to arrival.
 *
 * Content does not fade, slide or stagger into place. It is simply there.
 * The only things that move are things the user is currently touching, and
 * the two quiz states where motion carries meaning colour alone cannot.
 *
 * Everything here is near-critically damped. Overshoot reads as toy-like;
 * a spring that settles cleanly reads as physical.
 */

import { Easing, ReduceMotion } from 'react-native-reanimated';

/**
 * Press response. Damped hard enough that release has no visible wobble.
 * Stiff and light so it tracks the finger rather than trailing it.
 */
export const SPRING = {
  damping: 26,
  stiffness: 340,
  mass: 0.55,
  reduceMotion: ReduceMotion.System,
} as const;

/** Opacity, width and colour tweens. Quick, no character of its own. */
export const TIMING = {
  duration: 200,
  easing: Easing.bezier(0.33, 0, 0.2, 1),
  reduceMotion: ReduceMotion.System,
} as const;

export const DURATION = {
  fast: 140,
  base: 200,
  slow: 320,
} as const;

/**
 * How far a surface sinks under a finger.
 *
 * 0.98 is deliberately shallow. Anything deeper turns a tap into an event,
 * and the whole point is that it should feel like the surface acknowledged
 * you rather than performed for you.
 */
export const PRESS_SCALE = 0.98;
