import { onMounted, onUnmounted, type Ref } from 'vue'

let supportsDisplayTransitionCache: boolean | undefined

function canTransitionDisplay(): boolean {
  if (!import.meta.client) return false
  if (supportsDisplayTransitionCache !== undefined) return supportsDisplayTransitionCache
  if (!window.CSS?.supports?.('transition-behavior', 'allow-discrete') || !document.body) {
    return false
  }
  const probe = document.createElement('div')
  probe.style.cssText = 'transition: display 1s allow-discrete !important; display: block;'
  document.body.appendChild(probe)
  getComputedStyle(probe).display
  probe.style.display = 'none'
  supportsDisplayTransitionCache = getComputedStyle(probe).display === 'block'
  probe.remove()
  return supportsDisplayTransitionCache
}

function supportsTopLayerExit(): boolean {
  if (!import.meta.client) return false
  return Boolean(window.CSS?.supports?.('overlay', 'auto')) && canTransitionDisplay()
}

export async function closeDialogSmoothly(dialog: HTMLDialogElement | null): Promise<void> {
  if (!dialog || !dialog.open) return
  if (!supportsTopLayerExit()) {
    dialog.setAttribute('data-closing', '')
    const animations = dialog.getAnimations({ subtree: true })
    if (animations.length > 0) {
      await Promise.race([
        Promise.allSettled(animations.map(a => a.finished)),
        new Promise(resolve => setTimeout(resolve, 400)),
      ])
    }
    if (!dialog.hasAttribute('data-closing')) return
    dialog.removeAttribute('data-closing')
  }
  dialog.close()
}

export function useDialogLightDismiss(
  dialogRef: Ref<HTMLDialogElement | null>,
  onCloseRequest: () => void
) {
  let pressedOutside = false

  const isPointOutsideDialog = (e: PointerEvent, dialog: HTMLDialogElement): boolean => {
    const r = dialog.getBoundingClientRect()
    return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom
  }

  const handlePointerDown = (e: PointerEvent) => {
    const dialog = dialogRef.value
    if (!dialog || !dialog.open) return
    pressedOutside = isPointOutsideDialog(e, dialog)
  }

  const handlePointerUp = (e: PointerEvent) => {
    const dialog = dialogRef.value
    if (!dialog || !dialog.open) return
    if (!('closedBy' in HTMLDialogElement.prototype)) {
      if (pressedOutside && isPointOutsideDialog(e, dialog)) {
        onCloseRequest()
      }
    }
    pressedOutside = false
  }

  const handleCancel = (e: Event) => {
    e.preventDefault()
    onCloseRequest()
  }

  onMounted(() => {
    const dialog = dialogRef.value
    if (!dialog) return
    dialog.addEventListener('pointerdown', handlePointerDown)
    dialog.addEventListener('pointerup', handlePointerUp)
    dialog.addEventListener('cancel', handleCancel)
  })

  onUnmounted(() => {
    const dialog = dialogRef.value
    if (!dialog) return
    dialog.removeEventListener('pointerdown', handlePointerDown)
    dialog.removeEventListener('pointerup', handlePointerUp)
    dialog.removeEventListener('cancel', handleCancel)
  })
}
