<script setup lang="ts">
import { computed } from 'vue'
import { useMenuStore } from '~/stores/menu'
import { usePersian } from '~/composables/usePersian'

const menuStore = useMenuStore()
const { toPersianDigits } = usePersian()

const allProductCount = computed(() => {
  return menuStore.menuCategories.reduce((sum, c) => sum + c.products.length, 0)
})
</script>

<template>
  <div class="w-full">
    <div
      class="grid grid-cols-2 gap-2.5 sm:grid-cols-3 sm:gap-3 md:grid-cols-4 lg:grid-cols-5"
      role="group"
      aria-label="دسته‌بندی‌های اصلی منو"
    >
      <button
        type="button"
        :aria-pressed="menuStore.selectedCategory === 'all'"
        @click="menuStore.setCategory('all')"
        class="category-pill touch-target group relative flex min-w-0 items-center gap-2.5 sm:gap-3 rounded-2xl border px-3 py-2.5 sm:px-4"
        :class="
          menuStore.selectedCategory === 'all'
            ? 'border-[var(--color-brand-forest)] bg-[var(--color-brand-forest)] text-white shadow-[var(--shadow-sm)]'
            : 'border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] text-[var(--color-text-primary)]'
        "
      >
        <div
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-colors duration-200"
          :class="menuStore.selectedCategory === 'all' ? 'bg-white' : 'bg-white/85'"
        >
          <img src="/svg/food.svg" alt="" width="24" height="24" aria-hidden="true" class="h-6 w-6 object-contain" />
        </div>
        <div class="flex min-w-0 flex-col text-start">
          <span class="text-xs font-bold leading-snug">همه دسته‌ها</span>
          <span
            class="mt-0.5 text-[11px]"
            :class="menuStore.selectedCategory === 'all' ? 'text-white/85 font-medium' : 'text-[var(--color-text-secondary)]'"
          >
            {{ toPersianDigits(allProductCount) }} آیتم
          </span>
        </div>
      </button>

      <button
        v-for="cat in menuStore.topCategories"
        :key="cat.id"
        type="button"
        :aria-pressed="menuStore.selectedCategory === cat.slug"
        @click="menuStore.setCategory(cat.slug)"
        class="category-pill touch-target group relative flex min-w-0 items-center gap-2.5 sm:gap-3 rounded-2xl border px-3 py-2.5 sm:px-4"
        :class="
          menuStore.selectedCategory === cat.slug
            ? 'border-[var(--color-brand-forest)] bg-[var(--color-brand-forest)] text-white shadow-[var(--shadow-sm)]'
            : 'border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] text-[var(--color-text-primary)]'
        "
      >
        <div
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-colors duration-200"
          :class="menuStore.selectedCategory === cat.slug ? 'bg-white' : 'bg-white/85'"
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

        <div class="flex min-w-0 flex-col text-start">
          <span class="text-xs font-bold leading-snug">
            {{ cat.name }}
          </span>
          <span
            class="mt-0.5 text-[11px]"
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
  </div>
</template>

<style scoped>
.category-pill {
  transition:
    transform 150ms var(--ease-out),
    background-color 180ms ease,
    border-color 180ms ease,
    color 180ms ease,
    box-shadow 180ms ease;
}

@media (hover: hover) and (pointer: fine) {
  .category-pill[aria-pressed="false"]:hover {
    border-color: var(--color-brand-forest);
    background-color: var(--color-surface-ivory);
  }
  .category-pill[aria-pressed="false"]:hover > div:first-child {
    background-color: #FFFFFF;
  }
}

.category-pill:active {
  transform: scale(0.97);
}

.category-pill[aria-pressed="true"]::after {
  content: "";
  position: absolute;
  inset-inline: 16px;
  inset-block-end: 0;
  border-block-end: 3px solid var(--color-accent-gold);
  border-radius: 9999px;
}

@media (prefers-reduced-motion: reduce) {
  .category-pill {
    transition-duration: 120ms;
  }
  .category-pill:active {
    transform: none;
  }
}
</style>
