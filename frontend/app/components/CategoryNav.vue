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
  <div class="w-full space-y-3">
    <div
      class="flex items-center gap-3 overflow-x-auto pb-2 pt-1 no-scrollbar scroll-smooth"
      role="tablist"
      aria-label="دسته‌بندی‌های اصلی منو"
    >
      <button
        type="button"
        role="tab"
        :aria-selected="menuStore.selectedCategory === 'all'"
        @click="menuStore.setCategory('all')"
        class="touch-target group flex shrink-0 items-center gap-3 rounded-2xl border px-4 py-2.5 transition-colors duration-200 active:scale-95"
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
          <img src="/svg/food.svg" alt="" width="20" height="20" aria-hidden="true" class="h-5 w-5 object-contain" />
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
        v-for="cat in menuStore.topCategories"
        :key="cat.id"
        type="button"
        role="tab"
        :aria-selected="menuStore.selectedCategory === cat.slug"
        @click="menuStore.setCategory(cat.slug)"
        class="touch-target group flex shrink-0 items-center gap-3 rounded-2xl border px-4 py-2.5 transition-colors duration-200 active:scale-95"
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
            :alt="cat.name"
            width="20"
            height="20"
            class="h-5 w-5 object-contain"
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
</style>
