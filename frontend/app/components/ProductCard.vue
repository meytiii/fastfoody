<script setup lang="ts">
import { computed } from 'vue'
import { Plus, Star, Clock, Flame } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import type { Product } from '~/types'
import { useMenuStore } from '~/stores/menu'
import { useCartStore } from '~/stores/cart'
import { usePersian } from '~/composables/usePersian'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const props = defineProps<{
  product: Product
}>()

const menuStore = useMenuStore()
const cartStore = useCartStore()
const { toPersianDigits, formatToman } = usePersian()

const hasDiscount = computed(() => {
  return props.product.originalPrice && props.product.originalPrice > props.product.price
})

const handleCardClick = () => {
  menuStore.openProductModal(props.product)
}

const handleQuickAdd = (e: MouseEvent) => {
  e.stopPropagation()
  // If product has multiple sizes or addons, opening the modal is better for choice
  if ((props.product.sizes && props.product.sizes.length > 1) || (props.product.addons && props.product.addons.length > 0)) {
    menuStore.openProductModal(props.product)
    return
  }

  cartStore.addItem(props.product, 1)
  toast.success(`${props.product.title} به سبد افزوده شد`, {
    action: {
      label: 'مشاهده سبد',
      onClick: () => cartStore.openCart(),
    },
  })
}
</script>

<template>
  <article
    @click="handleCardClick"
    class="group relative flex h-full cursor-pointer flex-col justify-between rounded-2xl border border-[var(--color-border-subtle)] bg-white p-3.5 sm:p-4 shadow-[var(--shadow-sm)] transition-all duration-200 hover:-translate-y-1 hover:border-[var(--color-brand-forest)] hover:shadow-[var(--shadow-md)]"
  >
    <!-- Top Tags & Badges -->
    <div>
      <div class="relative mb-3 flex items-center justify-between">
        <span
          v-if="product.badges && product.badges.length > 0"
          class="rounded-full bg-[var(--color-accent-gold-soft)] px-2.5 py-0.5 text-[10px] sm:text-[11px] font-semibold text-[var(--color-accent-gold-hover)]"
        >
          {{ product.badges[0] }}
        </span>
        <span v-else class="text-[11px] text-[var(--color-text-muted)] font-medium">
          غذای تازه
        </span>

        <!-- Rating Pill -->
        <div
          class="flex items-center gap-1 rounded-full bg-[var(--color-surface-cream)] px-2 py-0.5 text-[11px] font-bold text-[var(--color-text-primary)]"
        >
          <Star :size="12" class="fill-[var(--color-accent-gold)] text-[var(--color-accent-gold)]" />
          <span>{{ toPersianDigits(product.rating) }}</span>
        </div>
      </div>

      <!-- Dish Image with Hover Zoom -->
      <div
        class="relative mb-3.5 flex aspect-square w-full items-center justify-center overflow-hidden rounded-xl bg-[var(--color-surface-cream)] p-2"
      >
        <img
          :src="product.image"
          :alt="product.title"
          loading="lazy"
          class="h-full w-full object-cover rounded-full shadow-xs transition-transform duration-300 group-hover:scale-105"
        />

        <!-- Preparation Time Pill -->
        <div
          class="absolute bottom-2 inset-inline-end-2 flex items-center gap-1 rounded-full bg-white/90 px-2 py-0.5 text-[10px] font-medium text-[var(--color-text-secondary)] backdrop-blur-xs shadow-xs"
        >
          <Clock :size="11" class="text-[var(--color-brand-forest)]" />
          <span>{{ toPersianDigits(product.prepTimeMinutes) }} دقیقه</span>
        </div>
      </div>

      <!-- Title & Excerpt -->
      <h3
        class="text-sm sm:text-base font-bold text-[var(--color-text-primary)] transition-colors group-hover:text-[var(--color-brand-forest)] line-clamp-1"
      >
        {{ product.title }}
      </h3>
      <p class="mt-1 text-xs text-[var(--color-text-secondary)] line-clamp-2 leading-relaxed">
        {{ product.description }}
      </p>
    </div>

    <!-- Bottom Pricing and CTA -->
    <div class="mt-4 pt-3 border-t border-[var(--color-border-subtle)] flex items-center justify-between">
      <div class="flex flex-col">
        <span
          v-if="hasDiscount"
          class="text-[11px] text-[var(--color-text-muted)] line-through"
        >
          {{ formatToman(product.originalPrice) }}
        </span>
        <span class="text-sm sm:text-base font-bold text-[var(--color-brand-forest)]">
          {{ formatToman(product.price) }}
        </span>
      </div>

      <!-- Quick Add Button -->
      <GooeyButton
        variant="secondary"
        size="sm"
        aria-label="افزودن به سبد خرید"
        class="h-9 px-3 text-xs"
        @click="handleQuickAdd"
      >
        <Plus :size="14" class="transition-transform group-hover:rotate-90" />
        <span class="hidden sm:inline">افزودن</span>
      </GooeyButton>
    </div>
  </article>
</template>

