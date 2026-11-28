<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { useMenuStore } from '~/stores/menu'
import { usePersian } from '~/composables/usePersian'

const menuStore = useMenuStore()
const { toPersianDigits } = usePersian()

const scrollerRef = ref<HTMLElement | null>(null)
const startBtnRef = ref<HTMLButtonElement | null>(null)
const endBtnRef = ref<HTMLButtonElement | null>(null)

const hasOverflow = ref(false)
const canScrollStart = ref(false)
const canScrollEnd = ref(false)

let resizeObserver: ResizeObserver | null = null

const allProductCount = computed(() => {
  return menuStore.menuCategories.reduce((sum, c) => sum + c.products.length, 0)
})

const prefersReducedMotion = (): boolean => {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

const getTabButtons = (): HTMLButtonElement[] => {
  const el = scrollerRef.value
  if (!el) return []
  return Array.from(el.querySelectorAll<HTMLButtonElement>('[role="tab"]'))
}

const updateScrollState = () => {
  const el = scrollerRef.value
  if (!el) return

  const tabs = getTabButtons()
  hasOverflow.value = el.scrollWidth > el.clientWidth + 2

  if (tabs.length === 0 || !hasOverflow.value) {
    canScrollStart.value = false
    canScrollEnd.value = false
    return
  }

  const containerRect = el.getBoundingClientRect()
  const firstRect = tabs[0]!.getBoundingClientRect()
  const lastRect = tabs[tabs.length - 1]!.getBoundingClientRect()

  const prevCanStart = canScrollStart.value
  const prevCanEnd = canScrollEnd.value

  canScrollStart.value = firstRect.right > containerRect.right + 2
  canScrollEnd.value = lastRect.left < containerRect.left - 2

  if (prevCanStart && !canScrollStart.value && document.activeElement === startBtnRef.value) {
    if (canScrollEnd.value) endBtnRef.value?.focus()
  } else if (prevCanEnd && !canScrollEnd.value && document.activeElement === endBtnRef.value) {
    if (canScrollStart.value) startBtnRef.value?.focus()
  }
}

const slideByDirection = (direction: 'start' | 'end') => {
  const el = scrollerRef.value
  if (!el) return
  const step = Math.max(220, Math.round(el.clientWidth * 0.65))
  el.scrollBy({
    left: direction === 'start' ? step : -step,
    behavior: prefersReducedMotion() ? 'auto' : 'smooth',
  })
}

const scrollSelectedIntoView = () => {
  const el = scrollerRef.value
  if (!el) return
  const activeTab = el.querySelector<HTMLButtonElement>('[role="tab"][aria-selected="true"]')
  if (!activeTab) return

  const containerRect = el.getBoundingClientRect()
  const tabRect = activeTab.getBoundingClientRect()
  const pad = 20
  const behavior: ScrollBehavior = prefersReducedMotion() ? 'auto' : 'smooth'

  if (tabRect.left < containerRect.left + pad) {
    el.scrollBy({ left: tabRect.left - containerRect.left - pad, behavior })
  } else if (tabRect.right > containerRect.right - pad) {
    el.scrollBy({ left: tabRect.right - containerRect.right + pad, behavior })
  }
}

const handleTabKeydown = (event: KeyboardEvent, index: number) => {
  const tabs = getTabButtons()
  if (tabs.length === 0) return

  let targetIndex: number | null = null
  if (event.key === 'ArrowLeft') {
    targetIndex = (index + 1) % tabs.length
  } else if (event.key === 'ArrowRight') {
    targetIndex = (index - 1 + tabs.length) % tabs.length
  } else if (event.key === 'Home') {
    targetIndex = 0
  } else if (event.key === 'End') {
    targetIndex = tabs.length - 1
  }

  if (targetIndex === null) return
  event.preventDefault()
  const targetTab = tabs[targetIndex]
  if (!targetTab) return
  targetTab.focus()

  const el = scrollerRef.value
  if (!el) return
  const containerRect = el.getBoundingClientRect()
  const tabRect = targetTab.getBoundingClientRect()
  if (tabRect.left < containerRect.left + 16) {
    el.scrollBy({ left: tabRect.left - containerRect.left - 16, behavior: 'auto' })
  } else if (tabRect.right > containerRect.right - 16) {
    el.scrollBy({ left: tabRect.right - containerRect.right + 16, behavior: 'auto' })
  }
}

watch(
  () => menuStore.topCategories.length,
  async () => {
    await nextTick()
    updateScrollState()
  }
)

watch(
  () => menuStore.selectedCategory,
  async () => {
    await nextTick()
    scrollSelectedIntoView()
    updateScrollState()
  }
)

onMounted(async () => {
  await nextTick()
  updateScrollState()
  if (scrollerRef.value && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => {
      updateScrollState()
    })
    resizeObserver.observe(scrollerRef.value)
  }
  window.addEventListener('resize', updateScrollState, { passive: true })
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  window.removeEventListener('resize', updateScrollState)
})
</script>

<template>
  <div class="w-full space-y-3">
    <div class="relative flex items-center gap-2">
      <button
        v-if="hasOverflow"
        ref="startBtnRef"
        type="button"
        :disabled="!canScrollStart"
        @click="slideByDirection('start')"
        aria-label="اسکرول دسته‌بندی‌ها به راست"
        class="category-arrow-btn touch-target flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-[var(--color-border-subtle)] bg-white text-[var(--color-brand-forest)] shadow-[var(--shadow-sm)] disabled:opacity-35 disabled:shadow-none"
      >
        <ChevronRight :size="18" aria-hidden="true" />
      </button>

      <div
        ref="scrollerRef"
        @scroll="updateScrollState"
        class="category-scroller flex min-w-0 flex-1 items-center gap-3 overflow-x-auto pb-2 pt-1 no-scrollbar"
        :class="{
          'has-fade-start': canScrollStart,
          'has-fade-end': canScrollEnd,
        }"
        role="tablist"
        aria-label="دسته‌بندی‌های اصلی منو"
      >
        <button
          type="button"
          role="tab"
          :aria-selected="menuStore.selectedCategory === 'all'"
          :tabindex="menuStore.selectedCategory === 'all' ? 0 : -1"
          @click="menuStore.setCategory('all')"
          @keydown="handleTabKeydown($event, 0)"
          class="category-tab touch-target group relative flex shrink-0 items-center gap-3 rounded-2xl border px-4 py-2.5 transition-[border-color,background-color,color,transform] duration-200 ease-[var(--ease-out)] active:scale-[0.97]"
          :class="
            menuStore.selectedCategory === 'all'
              ? 'border-[var(--color-brand-forest)] bg-[var(--color-brand-forest)] text-white shadow-sm'
              : 'border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] text-[var(--color-text-primary)] hover:border-[var(--color-brand-forest)] hover:bg-[var(--color-surface-ivory)]'
          "
        >
          <div
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-colors"
            :class="menuStore.selectedCategory === 'all' ? 'bg-white' : 'bg-white/80 group-hover:bg-white'"
          >
            <img src="/svg/food.svg" alt="" width="24" height="24" aria-hidden="true" class="h-6 w-6 object-contain" />
          </div>
          <div class="flex flex-col text-start">
            <span class="text-xs font-bold leading-tight">همه دسته‌ها</span>
            <span
              class="text-[11px] mt-0.5"
              :class="menuStore.selectedCategory === 'all' ? 'text-white/85 font-medium' : 'text-[var(--color-text-secondary)]'"
            >
              {{ toPersianDigits(allProductCount) }} آیتم
            </span>
          </div>
        </button>

        <button
          v-for="(cat, idx) in menuStore.topCategories"
          :key="cat.id"
          type="button"
          role="tab"
          :aria-selected="menuStore.selectedCategory === cat.slug"
          :tabindex="menuStore.selectedCategory === cat.slug ? 0 : -1"
          @click="menuStore.setCategory(cat.slug)"
          @keydown="handleTabKeydown($event, idx + 1)"
          class="category-tab touch-target group relative flex shrink-0 items-center gap-3 rounded-2xl border px-4 py-2.5 transition-[border-color,background-color,color,transform] duration-200 ease-[var(--ease-out)] active:scale-[0.97]"
          :class="
            menuStore.selectedCategory === cat.slug
              ? 'border-[var(--color-brand-forest)] bg-[var(--color-brand-forest)] text-white shadow-sm'
              : 'border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] text-[var(--color-text-primary)] hover:border-[var(--color-brand-forest)] hover:bg-[var(--color-surface-ivory)]'
          "
        >
          <div
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-colors"
            :class="menuStore.selectedCategory === cat.slug ? 'bg-white' : 'bg-white/80 group-hover:bg-white'"
          >
            <img
              :src="cat.image_url || '/svg/food.svg'"
              alt=""
              width="24"
              height="24"
              aria-hidden="true"
              class="h-6 w-6 object-contain"
            />
          </div>

          <div class="flex flex-col text-start">
            <span class="text-xs font-bold leading-tight">
              {{ cat.name }}
            </span>
            <span
              class="text-[11px] mt-0.5"
              :class="
                menuStore.selectedCategory === cat.slug
                  ? 'text-white/85 font-medium'
                  : 'text-[var(--color-text-secondary)]'
              "
            >
              {{ toPersianDigits(cat.products.length) }} آیتم
            </span>
          </div>
        </button>
      </div>

      <button
        v-if="hasOverflow"
        ref="endBtnRef"
        type="button"
        :disabled="!canScrollEnd"
        @click="slideByDirection('end')"
        aria-label="اسکرول دسته‌بندی‌ها به چپ"
        class="category-arrow-btn touch-target flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-[var(--color-border-subtle)] bg-white text-[var(--color-brand-forest)] shadow-[var(--shadow-sm)] disabled:opacity-35 disabled:shadow-none"
      >
        <ChevronLeft :size="18" aria-hidden="true" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.category-tab[aria-selected="true"]::after {
  content: "";
  position: absolute;
  inset-inline: 16px;
  inset-block-end: 0;
  border-block-end: 3px solid var(--color-accent-gold);
  border-radius: 9999px;
}
</style>
