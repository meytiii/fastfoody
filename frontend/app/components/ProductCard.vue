<script setup lang="ts">
import { computed } from 'vue'
import { Plus, Clock, AlertCircle } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import type { ProductSummaryPublic } from '~/types'
import { useMenuStore } from '~/stores/menu'
import { useCartStore } from '~/stores/cart'
import { usePersian } from '~/composables/usePersian'
import { storefrontApi } from '~/services/api'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const props = defineProps<{
  product: ProductSummaryPublic
}>()

const menuStore = useMenuStore()
const cartStore = useCartStore()
const { toPersianDigits, formatToman } = usePersian()

const isAvailable = computed(() => {
  return props.product.status === 'AVAILABLE' && props.product.is_in_stock
})

const hasDiscount = computed(() => {
  return (
    props.product.is_discounted &&
    props.product.compare_at_price !== null &&
    props.product.compare_at_price > props.product.price
  )
})

const isLowStock = computed(() => {
  return (
    isAvailable.value &&
    props.product.stock_quantity !== null &&
    props.product.stock_quantity <= 5
  )
})

const handleCardClick = () => {
  menuStore.openProductModal(props.product.slug)
}

const handleQuickAdd = async (e: MouseEvent) => {
  e.stopPropagation()
  if (!isAvailable.value) return

  try {
    const detail = await storefrontApi.catalog.getProductBySlug(props.product.slug)
    if (detail.addons.length > 0) {
      menuStore.selectedProductForModal = detail
      return
    }
    cartStore.addItem(detail, 1, [])
    toast.success(`${detail.name} به سبد خرید اضافه شد`, {
      action: {
        label: 'مشاهده سبد',
        onClick: () => cartStore.openCart(),
      },
    })
  } catch (err: any) {
    toast.error(err?.message || 'امکان افزودن محصول وجود ندارد')
  }
}
</script>

<template>
  <article
    class="group relative flex h-full flex-col justify-between rounded-2xl border border-[var(--color-border-subtle)] bg-white p-3.5 sm:p-4 shadow-[var(--shadow-sm)] transition-all duration-200"
    :class="
      isAvailable
        ? 'hover:-translate-y-0.5 hover:border-[var(--color-brand-forest)] hover:shadow-[var(--shadow-md)]'
        : 'opacity-80 bg-[var(--color-surface-cream)]/60'
    "
  >
    <div>
      <div class="relative mb-3 flex items-center justify-between gap-2 min-h-6">
        <span
          v-if="!isAvailable"
          class="rounded-full bg-[var(--color-danger-bg)] px-2.5 py-0.5 text-[11px] font-bold text-[var(--color-danger)]"
        >
          ناموجود
        </span>
        <span
          v-else-if="hasDiscount"
          class="rounded-full bg-[var(--color-accent-gold-soft)] px-2.5 py-0.5 text-[11px] font-bold text-[var(--color-accent-gold-text)]"
        >
          {{ toPersianDigits(product.discount_percent) }}٪ تخفیف
        </span>
        <span
          v-else
          class="text-[11px] text-[var(--color-text-secondary)] font-medium truncate"
        >
          {{ product.category.name }}
        </span>

        <span
          v-if="isLowStock"
          class="inline-flex items-center gap-1 rounded-full bg-[var(--color-warning-bg)] px-2 py-0.5 text-[10px] font-bold text-[var(--color-warning)] shrink-0"
        >
          <AlertCircle :size="11" aria-hidden="true" />
          <span>تنها {{ toPersianDigits(product.stock_quantity) }} عدد</span>
        </span>
      </div>

      <button
        type="button"
        @click="handleCardClick"
        class="w-full text-start focus-visible:outline-2 focus-visible:outline-[var(--color-brand-forest)] rounded-xl"
        :aria-label="`مشاهده جزئیات ${product.name}`"
      >
        <div
          class="relative mb-3.5 flex aspect-square w-full items-center justify-center overflow-hidden rounded-xl bg-[var(--color-surface-cream)] p-2"
        >
          <img
            :src="product.image_url || '/img/placeholder.webp'"
            :alt="product.name"
            width="300"
            height="300"
            loading="lazy"
            class="h-full w-full object-cover rounded-full shadow-xs transition-transform duration-300"
            :class="isAvailable ? 'group-hover:scale-105' : 'grayscale-[40%]'"
          />

          <div
            class="absolute bottom-2 inset-inline-end-2 flex items-center gap-1 rounded-full bg-white/95 px-2.5 py-0.5 text-[11px] font-semibold text-[var(--color-text-primary)] shadow-xs"
          >
            <Clock :size="12" aria-hidden="true" class="text-[var(--color-brand-forest)]" />
            <span>{{ toPersianDigits(product.prep_time_minutes) }} دقیقه</span>
          </div>
        </div>

        <h3
          class="text-sm sm:text-base font-bold text-[var(--color-text-primary)] transition-colors group-hover:text-[var(--color-brand-forest)] line-clamp-1"
        >
          {{ product.name }}
        </h3>
        <p class="mt-1 text-xs text-[var(--color-text-secondary)] line-clamp-2 leading-relaxed min-h-[2.4rem]">
          {{ product.description }}
        </p>
      </button>
    </div>

    <div class="mt-4 pt-3 border-t border-[var(--color-border-subtle)] flex items-center justify-between gap-2">
      <div class="flex flex-col min-w-0">
        <span
          v-if="hasDiscount && product.compare_at_price"
          class="text-[11px] text-[var(--color-text-muted)] line-through"
        >
          {{ formatToman(product.compare_at_price) }}
        </span>
        <span class="text-sm sm:text-base font-bold text-[var(--color-brand-forest)] truncate">
          {{ formatToman(product.price) }}
        </span>
      </div>

      <GooeyButton
        variant="secondary"
        size="sm"
        :disabled="!isAvailable"
        :aria-label="isAvailable ? `افزودن ${product.name} به سبد خرید` : `${product.name} ناموجود است`"
        class="h-10 px-3 text-xs shrink-0"
        @click="handleQuickAdd"
      >
        <Plus v-if="isAvailable" :size="14" aria-hidden="true" />
        <span>{{ isAvailable ? 'افزودن' : 'ناموجود' }}</span>
      </GooeyButton>
    </div>

    <div class="mt-2 flex items-center justify-end">
      <NuxtLink
        :to="`/products/${product.slug}`"
        class="text-[11px] font-semibold text-[var(--color-text-secondary)] hover:text-[var(--color-brand-forest)] hover:underline"
      >
        صفحه محصول
      </NuxtLink>
    </div>
  </article>
</template>
