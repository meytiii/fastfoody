<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as THREE from 'three'
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js'

interface VerletPoint {
  p: THREE.Vector3
  q: THREE.Vector3
  w: number
}

interface NimbuMirchiOptions {
  container: HTMLDivElement
  canvas: HTMLCanvasElement
  anchorY?: () => number
  anchorX?: () => number
  active?: () => boolean
  shadows?: boolean
  breeze?: boolean
}

const props = withDefaults(
  defineProps<{
    class?: string
    anchorY?: () => number
    anchorX?: () => number
    active?: () => boolean
    shadows?: boolean
    breeze?: boolean
  }>(),
  {
    class: '',
    shadows: true,
    breeze: true,
    anchorY: () => 0,
    anchorX: () => 0,
    active: () => true,
  }
)

const containerRef = ref<HTMLDivElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
let charmInstance: { dispose(): void } | null = null

function createNimbuMirchiEngine(opts: NimbuMirchiOptions): { dispose(): void } {
  const {
    container,
    canvas,
    anchorY = () => 0,
    anchorX = () => 0,
    active = () => true,
    shadows = true,
    breeze = true,
  } = opts

  const { Vector3, Quaternion } = THREE
  const smooth = THREE.MathUtils.smoothstep
  const disposables: any[] = []
  const track = <T>(x: T): T => {
    disposables.push(x)
    return x
  }

  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true })
  renderer.setClearColor(0, 0)
  renderer.toneMapping = THREE.NeutralToneMapping
  renderer.shadowMap.enabled = shadows
  renderer.shadowMap.type = THREE.VSMShadowMap

  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100)
  camera.position.set(0, 0, 10)
  const BASE_H = 2 * camera.position.z * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2))
  let VIEW_H = BASE_H

  const resize = () => {
    const w = Math.max(container.clientWidth || 300, 240)
    const h = Math.max(container.clientHeight || 400, 320)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
    renderer.setSize(w, h, false)
    camera.aspect = Math.max(0.1, w / Math.max(h, 1))
    camera.zoom = Math.max(0.1, Math.min(1, Math.sqrt(camera.aspect / 0.9)))
    VIEW_H = BASE_H / Math.max(0.1, camera.zoom)
    camera.updateProjectionMatrix()
  }
  resize()
  const resizer = new ResizeObserver(resize)
  resizer.observe(container)

  const pmrem = new THREE.PMREMGenerator(renderer)
  const envTex = pmrem.fromScene(new RoomEnvironment(), 0.04).texture
  scene.environment = envTex
  scene.environmentIntensity = 0.85
  pmrem.dispose()

  const key = new THREE.DirectionalLight(0xfff1e0, 1.6)
  key.position.set(-3, 4, 5)
  key.castShadow = shadows
  key.shadow.mapSize.set(1024, 1024)
  key.shadow.radius = 10
  key.shadow.blurSamples = 16
  key.shadow.bias = -0.0005
  Object.assign(key.shadow.camera, { left: -6, right: 6, top: 6, bottom: -6, near: 1, far: 20 })
  const rim = new THREE.DirectionalLight(0xffe3b5, 2.4)
  rim.position.set(2.5, 3, -6)
  scene.add(key, rim)

  const wall = new THREE.Mesh(
    track(new THREE.PlaneGeometry(60, 60)),
    track(new THREE.ShadowMaterial({ color: 0x143527, opacity: 0.28 }))
  )
  wall.position.z = -1.6
  wall.receiveShadow = true
  if (shadows) scene.add(wall)

  function canvasTexture(
    w: number,
    h: number,
    draw: (ctx: CanvasRenderingContext2D, w: number, h: number) => void,
    repeat?: [number, number]
  ) {
    const c = document.createElement('canvas')
    c.width = w
    c.height = h
    const ctx = c.getContext('2d')
    if (ctx) draw(ctx, w, h)
    const t = track(new THREE.CanvasTexture(c))
    if (repeat) {
      t.wrapS = t.wrapT = THREE.RepeatWrapping
      t.repeat.set(repeat[0], repeat[1])
    }
    return t
  }

  const peelColor = canvasTexture(512, 256, (ctx, w, h) => {
    const g = ctx.createLinearGradient(0, 0, 0, h)
    g.addColorStop(0, '#a9b02a')
    g.addColorStop(0.16, '#e2cf35')
    g.addColorStop(0.5, '#f3d838')
    g.addColorStop(0.84, '#e2cf35')
    g.addColorStop(1, '#a9b02a')
    ctx.fillStyle = g
    ctx.fillRect(0, 0, w, h)
    for (let i = 0; i < 2600; i++) {
      ctx.fillStyle = Math.random() < 0.5 ? 'rgba(255,240,140,.35)' : 'rgba(170,140,20,.25)'
      ctx.beginPath()
      ctx.arc(Math.random() * w, Math.random() * h, 0.6 + Math.random() * 1.4, 0, Math.PI * 2)
      ctx.fill()
    }
  })
  peelColor.colorSpace = THREE.SRGBColorSpace

  const peelBump = canvasTexture(512, 256, (ctx, w, h) => {
    ctx.fillStyle = '#808080'
    ctx.fillRect(0, 0, w, h)
    for (let i = 0; i < 4200; i++) {
      const x = Math.random() * w
      const y = Math.random() * h
      const r = 1 + Math.random() * 2.4
      const g = ctx.createRadialGradient(x, y, 0, x, y, r)
      g.addColorStop(0, 'rgba(30,30,30,.6)')
      g.addColorStop(1, 'rgba(128,128,128,0)')
      ctx.fillStyle = g
      ctx.fillRect(x - r, y - r, r * 2, r * 2)
    }
  })

  const chiliBump = canvasTexture(256, 256, (ctx, w, h) => {
    ctx.fillStyle = '#808080'
    ctx.fillRect(0, 0, w, h)
    for (let i = 0; i < 120; i++) {
      ctx.strokeStyle = `rgba(${Math.random() < 0.5 ? '60,60,60' : '200,200,200'},.25)`
      ctx.lineWidth = 0.5 + Math.random() * 1.5
      const x = Math.random() * w
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.bezierCurveTo(x + 6, h * 0.3, x - 6, h * 0.7, x + 3, h)
      ctx.stroke()
    }
  }, [2, 1])

  const CHILI_GREENS = [0x2c7a1c, 0x37881f, 0x25691a, 0x3b8f24, 0x2f7f1d, 0x2a7019]
  const chiliMats = CHILI_GREENS.map(c =>
    track(
      new THREE.MeshPhysicalMaterial({
        color: c,
        roughness: 0.3,
        clearcoat: 1,
        clearcoatRoughness: 0.1,
        bumpMap: chiliBump,
        bumpScale: 0.6,
        sheen: 0.3,
        sheenColor: new THREE.Color(0x9fdc6a),
      })
    )
  )
  const calyxMat = track(new THREE.MeshStandardMaterial({ color: 0x4d6e1d, roughness: 0.8, envMapIntensity: 0.5 }))
  const stemMat = track(new THREE.MeshStandardMaterial({ color: 0x6b7f2a, roughness: 0.85, envMapIntensity: 0.5 }))
  const threadMat = track(new THREE.MeshStandardMaterial({ color: 0xf1e9d6, roughness: 0.95 }))
  const lemonMat = track(
    new THREE.MeshPhysicalMaterial({
      map: peelColor,
      roughness: 0.42,
      clearcoat: 0.5,
      clearcoatRoughness: 0.3,
      bumpMap: peelBump,
      bumpScale: 1.4,
    })
  )

  function chiliGeometry(len: number, r: number, curl: number, sway: number) {
    const pts: THREE.Vector2[] = []
    const N = 36
    for (let i = 0; i <= N; i++) {
      const t = i / N
      const body = Math.pow(Math.sin(Math.min(t / 0.86, 1) * Math.PI / 2), 0.68) * (1 - 0.1 * t)
      const shoulder = 1 + 0.1 * smooth(t, 0.7, 0.92)
      pts.push(new THREE.Vector2(Math.max(r * body * shoulder, 0.003), t * len))
    }
    pts.push(new THREE.Vector2(r * 0.8, len + 0.02), new THREE.Vector2(r * 0.42, len + 0.04), new THREE.Vector2(0.001, len + 0.045))
    const g = new THREE.LatheGeometry(pts, 28)
    const pos = g.attributes.position!
    for (let i = 0; i < pos.count; i++) {
      let x = pos.getX(i)
      let z = pos.getZ(i)
      const y = pos.getY(i)
      const t = Math.min(y / len, 1)
      const ang = Math.atan2(z, x)
      const lobe = 1 + 0.07 * Math.cos(3 * ang + t * 2.5) * smooth(t, 0.08, 0.45)
      const wrinkle = 1 + 0.02 * Math.sin(t * 34 + ang * 2)
      x *= lobe * wrinkle
      z *= lobe * wrinkle
      const f = 1 - t
      x += curl * f * f * f
      z += sway * Math.sin(f * Math.PI) * f
      pos.setX(i, x)
      pos.setZ(i, z)
    }
    g.translate(0, -len, 0)
    g.computeVertexNormals()
    return track(g)
  }

  function calyxGeometry(r: number) {
    const g = new THREE.CylinderGeometry(r * 0.5, r * 1.1, 0.07, 40, 2)
    const pos = g.attributes.position!
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i)
      const y = pos.getY(i)
      const z = pos.getZ(i)
      const ang = Math.atan2(z, x)
      const low = y < 0 ? 1 : 0.35
      const k = 1 + 0.24 * Math.cos(5 * ang) * low
      pos.setXYZ(i, x * k, y - 0.045 * Math.max(0, Math.cos(5 * ang)) * low, z * k)
    }
    g.translate(0, 0.02, 0)
    g.computeVertexNormals()
    return track(g)
  }

  function stemGeometry(bend: number) {
    const c = new THREE.QuadraticBezierCurve3(new Vector3(0, 0.04, 0), new Vector3(0.02, 0.15, 0), new Vector3(-bend, 0.22, 0.02))
    return track(new THREE.TubeGeometry(c, 12, 0.024, 8, false))
  }

  function lemonGeometry(R: number) {
    const g = new THREE.SphereGeometry(R, 72, 54)
    const pos = g.attributes.position!
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i)
      const y = pos.getY(i)
      const z = pos.getZ(i)
      const u = y / R
      const a = Math.abs(u)
      const tip = Math.sign(u) * R * 0.26 * Math.pow(Math.max(0, a - 0.62) / 0.38, 3)
      const pinch = 1 - 0.12 * smooth(a, 0.55, 1)
      pos.setXYZ(i, x * pinch, y * 1.12 + tip, z * pinch)
    }
    g.computeVertexNormals()
    return track(g)
  }

  const CHILI_COUNT = 6
  const CHILI_GAP = 0.26
  const LEMON_R = 0.6
  const rand = (i: number, k: number) => {
    const s = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453
    return s - Math.floor(s)
  }

  const mesh = <T extends THREE.BufferGeometry, M extends THREE.Material>(geo: T, mat: M) => {
    const m = new THREE.Mesh(geo, mat)
    m.castShadow = shadows
    return m
  }

  const chiliGroup = new THREE.Group()
  for (let i = 0; i < CHILI_COUNT; i++) {
    const len = 1.0 + rand(i, 1) * 0.3
    const r = 0.135 + rand(i, 2) * 0.03
    const chili = new THREE.Group()
    chili.add(mesh(chiliGeometry(len, r, 0.25 + rand(i, 3) * 0.25, (rand(i, 4) - 0.5) * 0.18), chiliMats[i % chiliMats.length]!))
    chili.add(mesh(calyxGeometry(r), calyxMat))
    chili.add(mesh(stemGeometry(0.04 + rand(i, 5) * 0.06), stemMat))
    chili.rotation.z = Math.PI / 2 - 0.62 - (rand(i, 6) - 0.5) * 0.35
    chili.position.x = 0.05
    const pivot = new THREE.Group()
    pivot.position.y = -0.12 - i * CHILI_GAP
    pivot.rotation.y = i * 2.35 + rand(i, 7) * 0.4
    pivot.add(chili)
    chiliGroup.add(pivot)
  }

  const CHILI = 0.12 + (CHILI_COUNT - 1) * CHILI_GAP + 0.14
  const core = (len: number) => mesh(track(new THREE.CylinderGeometry(0.02, 0.02, len, 6).translate(0, -len / 2, 0)), threadMat)
  const chiliThread = core(CHILI)
  chiliGroup.add(chiliThread)

  const lemonGroup = new THREE.Group()
  const LEMON_GAP = 0.1
  const lemon = mesh(lemonGeometry(LEMON_R), lemonMat)
  lemon.position.y = -LEMON_GAP - LEMON_R * 1.38
  lemon.rotation.y = 0.6
  lemonGroup.add(lemon, core(LEMON_GAP + 0.1))
  const LEMON = LEMON_GAP + LEMON_R * 2.76

  const charm = new THREE.Group()
  charm.add(chiliGroup, lemonGroup)
  scene.add(charm)

  const SEG = 0.3
  const GRAVITY = -40
  const STEP = 1 / 120
  const DAMPING = 0.985
  const MAX_SPEED = 0.05
  const STRETCH_MAX = 3.5
  const ROPE = 4 * SEG
  let stretch = 1
  let recoil = 0
  const MAX_BEND = THREE.MathUtils.degToRad(35)

  const anchorPoint = () => {
    const h = Math.max(container.clientHeight || 400, 320)
    const w = Math.max(container.clientWidth || 300, 240)
    const rawX = typeof anchorX === 'function' ? anchorX() : 0
    const customX = typeof rawX === 'function' ? (rawX as any)() : (typeof rawX === 'number' ? rawX : 0)
    const safeX = Number.isFinite(customX) ? customX : 0
    const rawY = typeof anchorY === 'function' ? anchorY() : 0
    const customY = typeof rawY === 'function' ? (rawY as any)() : (typeof rawY === 'number' ? rawY : 0)
    const safeY = Number.isFinite(customY) ? customY : 0
    const ax = safeX ? (safeX / w - 0.5) * (VIEW_H * camera.aspect) : 0
    return new Vector3(ax, VIEW_H / 2 - (safeY / h) * VIEW_H + 0.1, 0)
  }

  const point = (y: number, mass: number): VerletPoint => {
    const p = new Vector3(0, y, 0)
    return { p, q: p.clone(), w: mass ? 1 / mass : 0 }
  }

  const y0 = anchorPoint().y
  const pts: VerletPoint[] = [0, 1, 2, 3, 4].map(i => point(y0 - i * SEG, i ? (i < 4 ? 1 : 1.5) : 0))
  pts.push(point(y0 - 4 * SEG - CHILI, 1), point(y0 - 4 * SEG - CHILI - LEMON, 1.5))
  const top = pts[4]!
  const joint = pts[5]!
  const bottom = pts[6]!

  const links: [VerletPoint, VerletPoint, number, number][] = [
    ...pts.slice(0, 4).map((a, i) => [a, pts[i + 1]!, 0, SEG] as [VerletPoint, VerletPoint, number, number]),
    [top, joint, CHILI, CHILI],
    [joint, bottom, LEMON, LEMON],
    [top, bottom, Math.sqrt(CHILI ** 2 + LEMON ** 2 + 2 * CHILI * LEMON * Math.cos(MAX_BEND)), Infinity],
  ]

  const knotEnd = new Vector3()
  const curve = new THREE.CatmullRomCurve3([...pts.slice(0, 5).map(p => p.p), knotEnd], false, 'chordal')
  const plies = [0, 1, 2].map(() => {
    const m = mesh(new THREE.BufferGeometry(), threadMat)
    scene.add(m)
    return m
  })
  const SAMPLES = 64
  const PLY_OFFSET = 0.022
  const PLY_R = 0.024
  const TWIST = 0.3

  const raycaster = new THREE.Raycaster()
  const ndc = new THREE.Vector2()
  const plane = new THREE.Plane(new Vector3(0, 0, 1), 0)
  const target = new Vector3()
  const cursor = new Vector3()
  const lastCursor = new Vector3()
  const push = new Vector3()
  let hasCursor = false
  let grab: { pt: VerletPoint; offset: THREE.Vector3; w: number; reach: number } | null = null
  let justDragged = false

  const aim = (x: number, y: number) => {
    const r = container.getBoundingClientRect()
    ndc.set(((x - r.left) / r.width) * 2 - 1, -((y - r.top) / r.height) * 2 + 1)
    raycaster.setFromCamera(ndc, camera)
  }

  const hit = (x: number, y: number) => {
    aim(x, y)
    return raycaster.intersectObject(charm, true)[0]
  }

  const onDown = (e: PointerEvent) => {
    const found = hit(e.clientX, e.clientY)
    if (!found) return
    e.preventDefault()
    let pick = top
    if (joint.p.distanceTo(found.point) < pick.p.distanceTo(found.point)) {
      pick = joint
    }
    if (bottom.p.distanceTo(found.point) < pick.p.distanceTo(found.point)) {
      pick = bottom
    }
    plane.constant = -pick.p.z
    raycaster.ray.intersectPlane(plane, target)
    const reach = 4 * SEG + (pick === top ? 0 : CHILI) + (pick === bottom ? LEMON : 0)
    grab = { pt: pick, offset: pick.p.clone().sub(target), w: pick.w, reach }
    pick.w = 0
    container.setPointerCapture?.(e.pointerId)
    container.style.cursor = 'grabbing'
  }

  const onMove = (e: PointerEvent) => {
    aim(e.clientX, e.clientY)
    if (grab) {
      raycaster.ray.intersectPlane(plane, target)
      return
    }
    plane.constant = 0
    if (raycaster.ray.intersectPlane(plane, cursor)) {
      if (hasCursor) push.add(cursor.clone().sub(lastCursor).clampLength(0, 0.4))
      lastCursor.copy(cursor)
      hasCursor = true
    }
    container.style.cursor = raycaster.intersectObject(charm, true).length ? 'grab' : ''
  }

  const onUp = () => {
    if (!grab) return
    grab.pt.w = grab.w
    grab = null
    justDragged = true
    container.style.cursor = ''
    if (stretch > 1.05) recoil = 0.8
  }

  const onLeave = () => {
    hasCursor = false
  }

  const onClick = (e: MouseEvent) => {
    if (justDragged) {
      e.preventDefault()
      e.stopPropagation()
    }
    justDragged = false
  }

  const onTouch = (e: TouchEvent) => {
    const firstTouch = e.touches[0]
    if (firstTouch && hit(firstTouch.clientX, firstTouch.clientY)) {
      e.preventDefault()
    }
  }

  container.addEventListener('pointerdown', onDown)
  container.addEventListener('pointermove', onMove)
  container.addEventListener('pointerup', onUp)
  container.addEventListener('pointercancel', onUp)
  container.addEventListener('pointerleave', onLeave)
  container.addEventListener('click', onClick, true)
  container.addEventListener('touchstart', onTouch, { passive: false })

  let twist = 0
  let spin = 0
  let clock = 0

  function step() {
    clock += STEP
    const wind = breeze ? (Math.sin(clock * 0.6) * 0.6 + Math.sin(clock * 1.7 + 1) * 0.3) * 1.6 : 0
    recoil = Math.max(0, recoil - STEP)
    if (!grab) stretch = 1 + (stretch - 1) * 0.9
    const cap = recoil || stretch > 1.02 ? 0.2 : MAX_SPEED
    for (const pt of pts) {
      if (!pt.w) continue
      const v = pt.p.clone().sub(pt.q).multiplyScalar(DAMPING).clampLength(0, cap)
      pt.q.copy(pt.p)
      pt.p.add(v)
      pt.p.y += GRAVITY * STEP * STEP
      pt.p.x += wind * STEP * STEP
      pt.p.z *= 0.98
    }
    if (push.lengthSq() > 1e-8) {
      for (const pt of pts) {
        if (!pt.w) continue
        const d = pt.p.distanceTo(cursor)
        if (d < 0.9) pt.p.addScaledVector(push, 0.06 * (1 - d / 0.9))
      }
      push.multiplyScalar(0.8)
    }
    if (grab) {
      const goal = target.clone().add(grab.offset)
      const fromAnchor = goal.clone().sub(pts[0]!.p)
      const rigid = grab.reach - ROPE
      stretch = Math.min(Math.max((fromAnchor.length() - rigid) / ROPE, 1), STRETCH_MAX)
      const reach = rigid + ROPE * stretch
      if (fromAnchor.length() > reach) goal.copy(pts[0]!.p).add(fromAnchor.setLength(reach))
      grab.pt.q.copy(grab.pt.p)
      grab.pt.p.lerp(goal, 0.35)
    }
    const sw = top.w + bottom.w
    if (sw) {
      const straight = joint.p.clone().sub(top.p).setLength(LEMON).add(joint.p).sub(bottom.p).multiplyScalar(8e-4 / sw)
      bottom.p.addScaledVector(straight, bottom.w)
      top.p.addScaledVector(straight, -top.w)
    }
    for (let n = 0; n < 30; n++) {
      for (const [a, b, min, max] of links) {
        const ws = a.w + b.w
        if (!ws) continue
        const top_ = max === SEG ? SEG * stretch : max
        const d = b.p.clone().sub(a.p)
        const dist = d.length() || 1e-6
        const len = Math.min(Math.max(dist, min), top_)
        if (len === dist) continue
        d.multiplyScalar((dist - len) / dist / ws)
        a.p.addScaledVector(d, a.w)
        b.p.addScaledVector(d, -b.w)
      }
    }
    if (!grab) spin += (bottom.p.x - bottom.q.x) * 0.12
    spin = (spin - twist * 0.01) * 0.93
    twist += spin
  }

  const DOWN = new Vector3(0, -1, 0)
  const UP = new Vector3(0, 1, 0)
  const qa = new Quaternion()
  const qb = new Quaternion()

  function sync() {
    chiliGroup.position.copy(top.p)
    chiliThread.scale.y = Math.max(1, top.p.distanceTo(joint.p) / CHILI)
    chiliGroup.quaternion.setFromUnitVectors(DOWN, joint.p.clone().sub(top.p).normalize()).multiply(qa.setFromAxisAngle(UP, twist))
    lemonGroup.position.copy(joint.p)
    lemonGroup.quaternion.setFromUnitVectors(DOWN, bottom.p.clone().sub(joint.p).normalize()).multiply(qb.setFromAxisAngle(UP, twist * 0.9))
    knotEnd.copy(joint.p).sub(top.p).setLength(0.08).add(top.p)
    curve.updateArcLengths()
    const centre = curve.getSpacedPoints(SAMPLES)
    const { normals, binormals } = curve.computeFrenetFrames(SAMPLES, false)
    const length = curve.getLength()
    plies.forEach((ply, k) => {
      const path = centre.map((c, i) => {
        const a = (2 * Math.PI * length * (1 - i / SAMPLES)) / TWIST + (k * 2 * Math.PI) / 3 + twist
        const n = normals[i] || new Vector3(1, 0, 0)
        const b = binormals[i] || new Vector3(0, 0, 1)
        return c.clone().addScaledVector(n, Math.cos(a) * PLY_OFFSET).addScaledVector(b, Math.sin(a) * PLY_OFFSET)
      })
      ply.geometry.dispose()
      ply.geometry = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(path), SAMPLES, PLY_R, 5)
    })
  }

  let sway = 0
  let last = performance.now()
  let acc = 0
  sync()
  renderer.setAnimationLoop((now: number) => {
    const dt = Math.min(now - last, 50) / 1000
    last = now
    if (!active()) return
    acc += dt
    const steps = Math.floor(acc / STEP)
    acc -= steps * STEP
    const p0 = pts[0]!
    const from = p0.p.clone()
    const to = anchorPoint()
    sway += (Math.max(-0.6, Math.min(0.6, (to.y - from.y) * 4)) - sway) * Math.min(1, dt * 5)
    to.x = to.x + sway
    for (let i = 1; i <= steps; i++) {
      p0.p.lerpVectors(from, to, i / steps)
      step()
    }
    sync()
    renderer.render(scene, camera)
  })

  return {
    dispose() {
      renderer.setAnimationLoop(null)
      resizer.disconnect()
      container.removeEventListener('pointerdown', onDown)
      container.removeEventListener('pointermove', onMove)
      container.removeEventListener('pointerup', onUp)
      container.removeEventListener('pointercancel', onUp)
      container.removeEventListener('pointerleave', onLeave)
      container.removeEventListener('click', onClick, true)
      container.removeEventListener('touchstart', onTouch)
      plies.forEach(p => p.geometry.dispose())
      disposables.forEach(d => d.dispose())
      envTex.dispose()
      renderer.dispose()
    },
  }
}

onMounted(async () => {
  await nextTick()
  if (!containerRef.value || !canvasRef.value) return
  charmInstance = createNimbuMirchiEngine({
    container: containerRef.value,
    canvas: canvasRef.value,
    anchorY: props.anchorY,
    anchorX: props.anchorX,
    active: props.active,
    shadows: props.shadows,
    breeze: props.breeze,
  })
})

onUnmounted(() => {
  if (charmInstance) {
    charmInstance.dispose()
    charmInstance = null
  }
})
</script>

<template>
  <div
    ref="containerRef"
    class="relative touch-pan-y overflow-hidden select-none"
    :class="props.class"
  >
    <canvas
      ref="canvasRef"
      aria-hidden="true"
      class="pointer-events-none absolute inset-0 size-full"
    />
    <div
      v-if="$slots.default"
      class="pointer-events-none relative size-full [&_a]:pointer-events-auto [&_button]:pointer-events-auto"
    >
      <slot />
    </div>
  </div>
</template>
