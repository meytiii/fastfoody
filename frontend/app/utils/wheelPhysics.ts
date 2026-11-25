export interface SpinProfileConfig {
  edgeMarginRatio: number
  minRotations: number
  maxRotations: number
  easeInMs: readonly [number, number]
  cruiseMs: readonly [number, number]
  easeOutMs: readonly [number, number]
  settleMs: readonly [number, number]
  overshootDeg: readonly [number, number]
  reducedMotionMs: number
  pointerMaxDeflectionDeg: number
  pointerMinDeflectionRatio: number
  pointerSpringStiffness: number
  pointerSpringDamping: number
}

export const WHEEL_SPIN_CONFIG: SpinProfileConfig = {
  edgeMarginRatio: 0.14,
  minRotations: 5,
  maxRotations: 8,
  easeInMs: [700, 950],
  cruiseMs: [600, 950],
  easeOutMs: [3400, 4100],
  settleMs: [350, 460],
  overshootDeg: [1.4, 2.8],
  reducedMotionMs: 180,
  pointerMaxDeflectionDeg: 25,
  pointerMinDeflectionRatio: 0.42,
  pointerSpringStiffness: 420,
  pointerSpringDamping: 22,
}

export interface SpinPlan {
  winningIndex: number
  offsetRatio: number
  startRotation: number
  finalRotation: number
  overshootDeg: number
  peakRotation: number
  totalForwardDelta: number
  easeInMs: number
  cruiseMs: number
  easeOutMs: number
  settleMs: number
  totalDurationMs: number
  cruiseVelocityDegPerMs: number
  easeInDistance: number
  cruiseDistance: number
  easeOutDistance: number
}

export interface SpinFrameSample {
  rotationDeg: number
  velocityDegPerMs: number
  speedRatio: number
  finished: boolean
}

export function randomInRange(min: number, max: number): number {
  return min + Math.random() * (max - min)
}

export function easeInCubic(t: number): number {
  return t * t * t
}

export function easeOutQuart(t: number): number {
  const inv = 1 - t
  return 1 - inv * inv * inv * inv
}

export function easeSineInOut(t: number): number {
  return 0.5 * (1 - Math.cos(Math.PI * t))
}

export function pickSliceOffsetRatio(
  previousOffsetRatio: number | null,
  marginRatio: number = WHEEL_SPIN_CONFIG.edgeMarginRatio,
): number {
  const safeSpan = Math.max(0.05, 1 - 2 * marginRatio)
  let ratio = marginRatio + Math.random() * safeSpan

  if (previousOffsetRatio !== null && Math.abs(ratio - previousOffsetRatio) < 0.08) {
    ratio = marginRatio + ((ratio - marginRatio + safeSpan * 0.5) % safeSpan)
  }

  return ratio
}

export function resolveSliceIndexAtRotation(rotationDeg: number, sliceCount: number): number {
  if (sliceCount <= 0) return -1
  const step = 360 / sliceCount
  const pointerAngleOnWheel = ((-rotationDeg % 360) + 360) % 360
  return Math.floor(pointerAngleOnWheel / step) % sliceCount
}

export function createSpinPlan(
  startRotation: number,
  sliceCount: number,
  winningIndex: number,
  previousOffsetRatio: number | null,
  config: SpinProfileConfig = WHEEL_SPIN_CONFIG,
): SpinPlan {
  const step = 360 / sliceCount
  const offsetRatio = pickSliceOffsetRatio(previousOffsetRatio, config.edgeMarginRatio)
  const targetAngleInWheel = winningIndex * step + offsetRatio * step
  const desiredMod = (360 - (targetAngleInWheel % 360) + 360) % 360
  const currentMod = ((startRotation % 360) + 360) % 360
  const deltaMod = (desiredMod - currentMod + 360) % 360
  const fullRotations =
    config.minRotations +
    Math.floor(Math.random() * (config.maxRotations - config.minRotations + 1))
  const finalRotation = startRotation + fullRotations * 360 + deltaMod

  const maxSafeOvershoot = Math.max(0.5, step * config.edgeMarginRatio * 0.72)
  const overshootDeg = Math.min(
    randomInRange(config.overshootDeg[0], config.overshootDeg[1]),
    maxSafeOvershoot,
  )

  const easeInMs = randomInRange(config.easeInMs[0], config.easeInMs[1])
  const cruiseMs = randomInRange(config.cruiseMs[0], config.cruiseMs[1])
  const easeOutMs = randomInRange(config.easeOutMs[0], config.easeOutMs[1])
  const settleMs = randomInRange(config.settleMs[0], config.settleMs[1])

  const totalForwardDelta = finalRotation - startRotation + overshootDeg
  const effectiveTimeUnits = easeInMs / 3 + cruiseMs + easeOutMs / 4
  const cruiseVelocityDegPerMs = totalForwardDelta / effectiveTimeUnits

  const easeInDistance = (cruiseVelocityDegPerMs * easeInMs) / 3
  const cruiseDistance = cruiseVelocityDegPerMs * cruiseMs
  const easeOutDistance = (cruiseVelocityDegPerMs * easeOutMs) / 4

  return {
    winningIndex,
    offsetRatio,
    startRotation,
    finalRotation,
    overshootDeg,
    peakRotation: finalRotation + overshootDeg,
    totalForwardDelta,
    easeInMs,
    cruiseMs,
    easeOutMs,
    settleMs,
    totalDurationMs: easeInMs + cruiseMs + easeOutMs + settleMs,
    cruiseVelocityDegPerMs,
    easeInDistance,
    cruiseDistance,
    easeOutDistance,
  }
}

export function sampleSpinPlan(plan: SpinPlan, elapsedMs: number): SpinFrameSample {
  if (elapsedMs <= 0) {
    return {
      rotationDeg: plan.startRotation,
      velocityDegPerMs: 0,
      speedRatio: 0,
      finished: false,
    }
  }

  if (elapsedMs >= plan.totalDurationMs) {
    return {
      rotationDeg: plan.finalRotation,
      velocityDegPerMs: 0,
      speedRatio: 0,
      finished: true,
    }
  }

  const t1End = plan.easeInMs
  if (elapsedMs < t1End) {
    const u = elapsedMs / plan.easeInMs
    const rotationDeg = plan.startRotation + plan.easeInDistance * easeInCubic(u)
    const velocity = plan.cruiseVelocityDegPerMs * u * u
    return {
      rotationDeg,
      velocityDegPerMs: velocity,
      speedRatio: Math.min(1, velocity / plan.cruiseVelocityDegPerMs),
      finished: false,
    }
  }

  const t2End = t1End + plan.cruiseMs
  if (elapsedMs < t2End) {
    const u = (elapsedMs - t1End) / plan.cruiseMs
    const rotationDeg = plan.startRotation + plan.easeInDistance + plan.cruiseDistance * u
    return {
      rotationDeg,
      velocityDegPerMs: plan.cruiseVelocityDegPerMs,
      speedRatio: 1,
      finished: false,
    }
  }

  const t3End = t2End + plan.easeOutMs
  if (elapsedMs < t3End) {
    const u = (elapsedMs - t2End) / plan.easeOutMs
    const inv = 1 - u
    const rotationDeg =
      plan.startRotation +
      plan.easeInDistance +
      plan.cruiseDistance +
      plan.easeOutDistance * easeOutQuart(u)
    const velocity = plan.cruiseVelocityDegPerMs * inv * inv * inv
    return {
      rotationDeg,
      velocityDegPerMs: velocity,
      speedRatio: Math.min(1, Math.max(0, velocity / plan.cruiseVelocityDegPerMs)),
      finished: false,
    }
  }

  const u = (elapsedMs - t3End) / plan.settleMs
  const rotationDeg = plan.peakRotation - plan.overshootDeg * easeSineInOut(u)
  return {
    rotationDeg,
    velocityDegPerMs: 0,
    speedRatio: 0,
    finished: false,
  }
}

export interface PointerSpringState {
  angleDeg: number
  velocityDegPerSec: number
}

export function stepPointerSpring(
  state: PointerSpringState,
  deltaMs: number,
  config: SpinProfileConfig = WHEEL_SPIN_CONFIG,
): PointerSpringState {
  const clampedSec = Math.min(0.05, Math.max(0, deltaMs / 1000))
  if (clampedSec === 0) return state

  const fixedStep = 1 / 120
  let remaining = clampedSec
  let angle = state.angleDeg
  let velocity = state.velocityDegPerSec

  while (remaining > 0) {
    const dt = Math.min(fixedStep, remaining)
    const accel = -config.pointerSpringStiffness * angle - config.pointerSpringDamping * velocity
    velocity += accel * dt
    angle += velocity * dt
    remaining -= dt
  }

  if (Math.abs(angle) < 0.04 && Math.abs(velocity) < 0.2) {
    return { angleDeg: 0, velocityDegPerSec: 0 }
  }

  return { angleDeg: angle, velocityDegPerSec: velocity }
}

export function computePointerDeflection(
  speedRatio: number,
  config: SpinProfileConfig = WHEEL_SPIN_CONFIG,
): number {
  const slowBias = 1 - (1 - config.pointerMinDeflectionRatio) * Math.min(1, Math.max(0, speedRatio))
  return -config.pointerMaxDeflectionDeg * slowBias
}
