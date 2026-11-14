<script setup lang="ts">
import { useMenuStore } from '~/stores/menu'
import { usePersian } from '~/composables/usePersian'

const menuStore = useMenuStore()
const { toPersianDigits } = usePersian()
</script>

<template>
  <div class="w-full">
    
    <div
      class="flex items-center gap-3 overflow-x-auto pb-2 pt-1 no-scrollbar scroll-smooth"
      role="tablist"
      aria-label="دسته‌بندی‌های منو"
    >
      <button
        v-for="cat in menuStore.categories"
        :key="cat.id"
        type="button"
        role="tab"
        :aria-selected="menuStore.selectedCategory === cat.id"
        @click="menuStore.setCategory(cat.id)"
        class="touch-target group flex shrink-0 items-center gap-3 rounded-2xl border px-4 py-2.5 transition-all duration-200 active:scale-95"
        :class="
          menuStore.selectedCategory === cat.id
            ? 'border-[var(--color-brand-forest)] bg-[var(--color-brand-forest)] text-white shadow-sm'
            : 'border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] text-[var(--color-text-primary)] hover:border-[var(--color-brand-forest)] hover:bg-[var(--color-surface-ivory)]'
        "
      >
        
        <div
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-colors"
          :class="
            menuStore.selectedCategory === cat.id
              ? 'bg-white text-[var(--color-brand-forest)]'
              : 'bg-white/80 group-hover:bg-white text-[var(--color-brand-forest)]'
          "
        >
          <img
            :src="cat.icon"
            :alt="cat.title"
            class="h-5 w-5 object-contain"
          />
        </div>

        
        <div class="flex flex-col text-start">
          <span class="text-xs font-bold leading-tight">
            {{ cat.title }}
          </span>
          <span
            class="text-[10px] mt-0.5"
            :class="
              menuStore.selectedCategory === cat.id
                ? 'text-white/80 font-medium'
                : 'text-[var(--color-text-secondary)]'
            "
          >
            {{ toPersianDigits(cat.itemCount) }} آیتم
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

