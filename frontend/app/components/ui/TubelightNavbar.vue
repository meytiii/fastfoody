<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue'
import type { Component } from 'vue'

export interface TubelightNavItem {
  name: string
  url: string
  icon?: Component
}

const props = withDefaults(
  defineProps<{
    items: TubelightNavItem[]
    modelValue?: string
    className?: string
    position?: 'floating-top' | 'floating-bottom' | 'static'
  }>(),
  {
    modelValue: '',
    className: '',
    position: 'static',
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'select', item: TubelightNavItem): void
}>()

const activeTab = ref(props.modelValue || (props.items.length > 0 ? props.items[0].name : ''))
const navContainerRef = ref<HTMLElement | null>(null)
const itemRefs = new Map<string, HTMLElement>()

const setItemRef = (el: any, name: string) => {
  if (el) {
    itemRefs.set(name, el as HTMLElement)
  } else {
    itemRefs.delete(name)
  }
}

const lampStyle = reactive({
  left: 0,
  top: 0,
  width: 0,
  height: 0,
  opacity: 0,
})
const lampReady = ref(false)

const updateLamp = () => {
  if (!navContainerRef.value || !activeTab.value) {
    lampStyle.opacity = 0
    return
  }
  const activeEl = itemRefs.get(activeTab.value)
  if (!activeEl) {
    lampStyle.opacity = 0
    return
  }

  const containerRect = navContainerRef.value.getBoundingClientRect()
  const elRect = activeEl.getBoundingClientRect()

  lampStyle.left = elRect.left - containerRect.left
  lampStyle.top = elRect.top - containerRect.top
  lampStyle.width = elRect.width
  lampStyle.height = elRect.height
  lampStyle.opacity = 1
  lampReady.value = true
}

const selectItem = (item: TubelightNavItem) => {
  activeTab.value = item.name
  emit('update:modelValue', item.name)
  emit('select', item)
  nextTick(() => updateLamp())
}

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal && newVal !== activeTab.value) {
      activeTab.value = newVal
      nextTick(() => updateLamp())
    }
  }
)

watch(
  () => props.items,
  () => {
    nextTick(() => updateLamp())
  },
  { deep: true }
)

onMounted(() => {
  nextTick(() => {
    updateLamp()
    window.addEventListener('resize', updateLamp, { passive: true })
    if (document.fonts) {
      document.fonts.ready.then(() => updateLamp())
    }
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', updateLamp)
})

defineExpose({
  updateLamp,
  selectItem,
})
</script>

<template>
  <div
    :class="[
      position === 'floating-top' && 'fixed top-0 sm:top-4 left-1/2 -translate-x-1/2 z-50 pt-3 sm:pt-0',
      position === 'floating-bottom' && 'fixed bottom-4 left-1/2 -translate-x-1/2 z-50',
      position === 'static' && 'relative inline-flex',
      className,
    ]"
  >
    <div
      ref="navContainerRef"
      class="relative flex items-center gap-1 sm:gap-2 rounded-full border border-[var(--color-border-subtle)] bg-white/92 px-2 py-1.5 shadow-[var(--shadow-md)] backdrop-blur-md"
      role="tablist"
      aria-label="ناوبری تیوپ‌لایت"
    >
      <!-- Sliding Lamp Highlight Indicator with Spring Timing -->
      <div
        v-if="lampReady"
        class="pointer-events-none absolute z-0 rounded-full transition-all duration-300 ease-[cubic-bezier(0.25,1,0.5,1)]"
        :style="{
          left: `${lampStyle.left}px`,
          top: `${lampStyle.top}px`,
          width: `${lampStyle.width}px`,
          height: `${lampStyle.height}px`,
          opacity: lampStyle.opacity,
        }"
        aria-hidden="true"
      >
        <!-- Pill background tint -->
        <div class="h-full w-full rounded-full bg-[var(--color-brand-forest)]/[0.08]" />

        <!-- Tubelight filament & ambient glow -->
        <div
          class="absolute -top-1.5 left-1/2 -translate-x-1/2 w-8 h-1 rounded-t-full bg-[var(--color-brand-forest)] shadow-[0_0_8px_rgba(24,58,45,0.45)]"
        >
          <!-- Wide diffuse glow -->
          <div class="absolute -top-2 -left-2 w-12 h-6 rounded-full bg-[var(--color-brand-forest)]/25 blur-md pointer-events-none" />
          <!-- Accent warm highlight -->
          <div class="absolute -top-1 left-0 w-8 h-6 rounded-full bg-[var(--color-accent-gold)]/30 blur-md pointer-events-none" />
          <!-- Core spark -->
          <div class="absolute top-0 left-2 w-4 h-4 rounded-full bg-[var(--color-brand-forest)]/40 blur-xs pointer-events-none" />
        </div>
      </div>

      <!-- Nav Items -->
      <button
        v-for="item in items"
        :key="item.name"
        :ref="(el) => setItemRef(el, item.name)"
        type="button"
        role="tab"
        :aria-selected="activeTab === item.name"
        @click="selectItem(item)"
        class="touch-target relative z-10 flex items-center justify-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition-colors duration-200 cursor-pointer select-none"
        :class="
          activeTab === item.name
            ? 'text-[var(--color-brand-forest)]'
            : 'text-[var(--color-text-secondary)] hover:text-[var(--color-brand-forest)] hover:bg-[var(--color-surface-cream)]/70'
        "
      >
        <component
          :is="item.icon"
          v-if="item.icon"
          :size="18"
          :stroke-width="2.25"
          class="shrink-0 transition-transform duration-200"
          :class="activeTab === item.name ? 'scale-105' : 'opacity-80'"
        />
        <span class="inline">{{ item.name }}</span>
      </button>
    </div>
  </div>
</template>

