<script setup lang="ts">
import { ref, watch } from 'vue'
import { Search, X, ArrowLeft, Sparkles } from 'lucide-vue-next'
import { useUiStore } from '~/stores/ui'
import { useMenuStore } from '~/stores/menu'
import { usePersian } from '~/composables/usePersian'
import { closeDialogSmoothly, useDialogLightDismiss } from '~/composables/useDialogControl'
import type { ProductSuggestionPublic } from '~/types'

const uiStore = useUiStore()
const menuStore = useMenuStore()
const { formatToman, toPersianDigits } = usePersian()

const dialogRef = ref<HTMLDialogElement | null>(null)
const searchInput = ref('')
let debounceTimer: ReturnType<typeof setTimeout> | null = null

const requestClose = async () => {
  await closeDialogSmoothly(dialogRef.value)
  uiStore.closeSearch()
}

useDialogLightDismiss(dialogRef, requestClose)

watch(
  () => uiStore.isSearchOpen,
  (isOpen) => {
    if (isOpen) {
      dialogRef.value?.showModal()
    } else if (dialogRef.value?.open) {
      dialogRef.value.close()
    }
  }
)

watch(searchInput, (val) => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    menuStore.fetchSuggestions(val)
  }, 180)
})

const handleSelectSuggestion = async (dish: ProductSuggestionPublic) => {
  await requestClose()
  await menuStore.openProductModal(dish.slug)
}

const applyCorrection = (corrected: string) => {
  searchInput.value = corrected
  menuStore.fetchSuggestions(corrected)
}

const submitFullSearch = async () => {
  const q = searchInput.value.trim()
  await requestClose()
  menuStore.searchQuery = q
  menuStore.offset = 0
  await navigateTo({ path: '/menu', query: q ? { q } : undefined })
  await menuStore.searchProducts()
}
</script>

<template>
  <dialog
    ref="dialogRef"
    closedby="any"
    aria-labelledby="search-modal-title"
    @close="uiStore.closeSearch"
    class="modal-top-layer fixed inset-0 mx-auto mt-12 sm:mt-20 z-50 w-[94%] max-w-xl rounded-3xl border border-[var(--color-border-subtle)] bg-white p-5 shadow-[var(--shadow-lg)]"
  >
    <div class="flex items-center justify-between mb-3">
      <h1 id="search-modal-title" class="text-sm font-bold text-[var(--color-brand-forest)]">
        جستجو در منوی فست‌فودی
      </h1>
      <button
        type="button"
        @click="requestClose"
        class="touch-target flex h-9 w-9 items-center justify-center rounded-full text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-cream)]"
        aria-label="بستن جستجو"
      >
        <X :size="18" aria-hidden="true" />
      </button>
    </div>

    <div role="search">
      <form @submit.prevent="submitFullSearch" class="relative flex items-center">
        <Search :size="18" aria-hidden="true" class="absolute inset-inline-start-3.5 text-[var(--color-text-muted)]" />
        <label for="global-search-input" class="visually-hidden">عبارت جستجو</label>
        <input
          id="global-search-input"
          v-model="searchInput"
          type="search"
          name="q"
          autofocus
          enterkeyhint="search"
          autocorrect="off"
          autocapitalize="none"
          spellcheck="false"
          placeholder="جستجوی برگر، پیتزا، همبرگر، چیکن..."
          class="h-12 w-full rounded-2xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)]/70 ps-11 pe-24 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-brand-forest)] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-forest)]/10"
        />
        <button
          type="submit"
          class="absolute inset-inline-end-1.5 rounded-xl bg-[var(--color-brand-forest)] px-3.5 py-2 text-xs font-bold text-white hover:bg-[var(--color-brand-forest-light)]"
        >
          جستجو
        </button>
      </form>
    </div>

    <div
      v-if="menuStore.didYouMean"
      class="mt-3 flex items-center gap-2 rounded-xl border border-[var(--color-accent-gold)]/40 bg-[var(--color-accent-gold-soft)] px-3.5 py-2 text-xs text-[var(--color-text-primary)]"
    >
      <Sparkles :size="14" aria-hidden="true" class="text-[var(--color-accent-gold-text)] shrink-0" />
      <span>آیا منظورتان</span>
      <button
        type="button"
        @click="applyCorrection(menuStore.didYouMean)"
        class="font-bold text-[var(--color-brand-forest)] underline"
      >
        «{{ menuStore.didYouMean }}»
      </button>
      <span>بود؟</span>
    </div>

    <div class="mt-4 max-h-[360px] overflow-y-auto space-y-1.5">
      <div v-if="menuStore.suggestionsLoading" class="py-8 text-center text-xs text-[var(--color-text-secondary)]">
        در حال جستجو...
      </div>

      <div
        v-else-if="searchInput.trim() && menuStore.suggestions.length === 0"
        class="py-8 text-center space-y-2"
      >
        <p class="text-xs text-[var(--color-text-secondary)]">
          محصولی با این عبارت پیدا نشد.
        </p>
        <button
          type="button"
          @click="submitFullSearch"
          class="text-xs font-bold text-[var(--color-brand-forest)] hover:underline"
        >
          مشاهده همه فیلترها در صفحه منو
        </button>
      </div>

      <button
        v-for="dish in menuStore.suggestions"
        :key="dish.id"
        type="button"
        @click="handleSelectSuggestion(dish)"
        class="touch-target flex w-full items-center justify-between rounded-xl p-2.5 transition-colors hover:bg-[var(--color-surface-cream)] text-start"
      >
        <div class="flex items-center gap-3 min-w-0">
          <img
            :src="dish.image_url || '/img/placeholder.webp'"
            :alt="dish.name"
            width="48"
            height="48"
            class="h-12 w-12 rounded-xl object-cover bg-white shrink-0"
          />
          <div class="min-w-0">
            <h2 class="text-xs sm:text-sm font-bold text-[var(--color-text-primary)] truncate">
              {{ dish.name }}
            </h2>
            <div class="flex flex-wrap items-center gap-2 text-[11px] text-[var(--color-text-secondary)] mt-0.5">
              <span class="font-bold text-[var(--color-brand-forest)]">
                {{ formatToman(dish.price) }}
              </span>
              <span
                v-if="dish.discount_percent > 0"
                class="rounded-full bg-[var(--color-accent-gold-soft)] px-2 py-0.5 text-[10px] font-bold text-[var(--color-accent-gold-text)]"
              >
                {{ toPersianDigits(dish.discount_percent) }}٪ تخفیف
              </span>
              <span
                v-if="dish.status !== 'AVAILABLE'"
                class="rounded-full bg-[var(--color-danger-bg)] px-2 py-0.5 text-[10px] font-bold text-[var(--color-danger)]"
              >
                ناموجود
              </span>
            </div>
          </div>
        </div>

        <ArrowLeft :size="16" aria-hidden="true" class="text-[var(--color-text-muted)] icon-directional shrink-0" />
      </button>
    </div>
  </dialog>
</template>
