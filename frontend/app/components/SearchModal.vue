<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search, X, Star, ArrowLeft } from 'lucide-vue-next'
import { useUiStore } from '~/stores/ui'
import { useMenuStore } from '~/stores/menu'
import { usePersian } from '~/composables/usePersian'
import type { Product } from '~/types'

const uiStore = useUiStore()
const menuStore = useMenuStore()
const { toPersianDigits, formatToman } = usePersian()

const searchInput = ref('')

const searchResults = computed(() => {
  const q = searchInput.value.trim().toLowerCase()
  if (!q) return []
  return menuStore.products.filter(p =>
    p.title.toLowerCase().includes(q) ||
    p.description.toLowerCase().includes(q) ||
    p.badges?.some(b => b.toLowerCase().includes(q))
  )
})

const handleSelect = (product: Product) => {
  uiStore.closeSearch()
  menuStore.openProductModal(product)
}
</script>

<template>
  <Transition
    enter-active-class="transition-opacity duration-200"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition-opacity duration-150"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="uiStore.isSearchOpen"
      class="fixed inset-0 z-50 flex items-start justify-center bg-[rgba(18,37,29,0.5)] p-4 sm:p-6 backdrop-blur-xs"
      @click.self="uiStore.closeSearch"
    >
      <div
        class="w-full max-w-xl rounded-3xl border border-[var(--color-border-subtle)] bg-white p-5 shadow-[var(--shadow-lg)] mt-12 sm:mt-20 overscroll-contain"
        role="dialog"
        aria-label="جستجوی منوی غذا"
      >
        <!-- Search Input Bar -->
        <div class="relative flex items-center">
          <Search :size="20" class="absolute inset-inline-start-3.5 text-[var(--color-text-muted)]" />
          <input
            v-model="searchInput"
            type="search"
            autofocus
            placeholder="جستجوی برگر، پیتزا، پاستا یا سالاد..."
            class="w-full rounded-2xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)]/70 py-3 ps-11 pe-10 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-brand-forest)] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-forest)]/10"
          />
          <button
            type="button"
            @click="uiStore.closeSearch"
            class="touch-target absolute inset-inline-end-1 flex h-8 w-8 items-center justify-center rounded-full text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
            aria-label="بستن"
          >
            <X :size="18" />
          </button>
        </div>

        <!-- Search Results List -->
        <div class="mt-4 max-h-[350px] overflow-y-auto space-y-2">
          <div v-if="searchInput.trim() && searchResults.length === 0" class="py-8 text-center text-xs text-[var(--color-text-secondary)]">
            موردی مطابق با جستجوی شما یافت نشد.
          </div>

          <button
            v-for="dish in searchResults"
            :key="dish.id"
            type="button"
            @click="handleSelect(dish)"
            class="touch-target flex w-full items-center justify-between rounded-xl p-2.5 transition-colors hover:bg-[var(--color-surface-cream)] text-start"
          >
            <div class="flex items-center gap-3">
              <img
                :src="dish.image"
                :alt="dish.title"
                class="h-12 w-12 rounded-xl object-cover bg-white"
              />
              <div>
                <h4 class="text-xs sm:text-sm font-bold text-[var(--color-text-primary)]">
                  {{ dish.title }}
                </h4>
                <div class="flex items-center gap-2 text-[11px] text-[var(--color-text-secondary)] mt-0.5">
                  <span class="flex items-center gap-0.5 font-bold text-[var(--color-accent-gold-hover)]">
                    <Star :size="11" class="fill-[var(--color-accent-gold)]" />
                    {{ toPersianDigits(dish.rating) }}
                  </span>
                  <span>•</span>
                  <span>{{ formatToman(dish.price) }}</span>
                </div>
              </div>
            </div>

            <ArrowLeft :size="16" class="text-[var(--color-text-muted)] icon-directional" />
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

