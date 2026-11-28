<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { X, Plus, Minus, Clock, ExternalLink } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { useMenuStore } from '~/stores/menu'
import { useCartStore } from '~/stores/cart'
import { usePersian } from '~/composables/usePersian'
import { closeDialogSmoothly, useDialogLightDismiss } from '~/composables/useDialogControl'
import type { CartItemAddOn, ProductAddOnPublic } from '~/types'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const menuStore = useMenuStore()
const cartStore = useCartStore()
const { toPersianDigits, formatToman } = usePersian()

const dialogRef = ref<HTMLDialogElement | null>(null)
const quantity = ref(1)
const addonQuantities = ref<Record<number, number>>({})

const product = computed(() => menuStore.selectedProductForModal)

const requestClose = async () => {
  await closeDialogSmoothly(dialogRef.value)
  menuStore.closeProductModal()
}

useDialogLightDismiss(dialogRef, requestClose)

watch(
  () => menuStore.selectedProductForModal,
  (newVal) => {
    if (newVal) {
      quantity.value = 1
      const initialMap: Record<number, number> = {}
      for (const addon of newVal.addons) {
        initialMap[addon.addon_id] = addon.min_quantity > 0 ? addon.min_quantity : 0
      }
      addonQuantities.value = initialMap
      if (!dialogRef.value?.open) {
        dialogRef.value?.showModal()
      }
    } else if (dialogRef.value?.open) {
      dialogRef.value.close()
    }
  }
)

const maxProductQty = 99

const isAvailable = computed(() => {
  if (!product.value) return false
  return product.value.status === 'AVAILABLE'
})

const setAddonQty = (addon: ProductAddOnPublic, delta: number) => {
  const current = addonQuantities.value[addon.addon_id] ?? 0
  const next = Math.min(addon.max_quantity, Math.max(0, current + delta))
  addonQuantities.value = {
    ...addonQuantities.value,
    [addon.addon_id]: next,
  }
}

const selectedAddonsList = computed<CartItemAddOn[]>(() => {
  if (!product.value) return []
  return product.value.addons
    .map(addon => {
      const qty = addonQuantities.value[addon.addon_id] ?? 0
      return {
        addon_id: addon.addon_id,
        name: addon.name,
        price: addon.price,
        quantity: qty,
        min_quantity: addon.min_quantity,
        max_quantity: addon.max_quantity,
      }
    })
    .filter(a => a.quantity > 0)
})

const addonsTotal = computed(() => {
  return selectedAddonsList.value.reduce((sum, a) => sum + a.price * a.quantity, 0)
})

const totalPrice = computed(() => {
  if (!product.value) return 0
  return product.value.price * quantity.value + addonsTotal.value
})

const handleAddToCart = async () => {
  if (!product.value || !isAvailable.value) return

  cartStore.addItem(product.value, quantity.value, selectedAddonsList.value)

  toast.success(`${product.value.name} به سبد خرید اضافه شد`, {
    description: `${toPersianDigits(quantity.value)} عدد | ${formatToman(totalPrice.value)}`,
    action: {
      label: 'مشاهده سبد',
      onClick: () => cartStore.openCart(),
    },
  })

  await requestClose()
}
</script>

<template>
  <dialog
    ref="dialogRef"
    closedby="any"
    aria-labelledby="product-modal-title"
    @close="menuStore.closeProductModal"
    class="modal-top-layer fixed inset-0 m-auto z-50 w-[95%] max-w-2xl rounded-3xl border border-[var(--color-border-subtle)] bg-white p-0 shadow-[var(--shadow-lg)]"
  >
    <div v-if="product" class="flex max-h-[90dvh] flex-col overflow-hidden">
      <div class="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-[var(--color-border-subtle)] bg-white/95 px-6 backdrop-blur-xs">
        <div class="flex items-center gap-2">
          <span class="rounded-full bg-[var(--color-surface-cream)] px-3 py-1 text-xs font-bold text-[var(--color-brand-forest)]">
            {{ product.category.name }}
          </span>
          <span
            v-if="product.is_discounted"
            class="rounded-full bg-[var(--color-accent-gold-soft)] px-2.5 py-0.5 text-xs font-bold text-[var(--color-accent-gold-text)]"
          >
            {{ toPersianDigits(product.discount_percent) }}٪ تخفیف
          </span>
          <span
            v-if="!isAvailable"
            class="rounded-full bg-[var(--color-danger-bg)] px-2.5 py-0.5 text-xs font-bold text-[var(--color-danger)]"
          >
            ناموجود
          </span>
        </div>

        <div class="flex items-center gap-2">
          <NuxtLink
            :to="`/products/${product.slug}`"
            @click="requestClose"
            class="touch-target inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-semibold text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-cream)] hover:text-[var(--color-brand-forest)]"
          >
            <ExternalLink :size="14" aria-hidden="true" />
            <span>صفحه مجزا</span>
          </NuxtLink>

          <button
            type="button"
            @click="requestClose"
            class="touch-target flex h-10 w-10 items-center justify-center rounded-full text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-cream)] active:scale-[0.97] transition-[background-color,transform] duration-150 ease-[var(--ease-out)]"
            aria-label="بستن پنجره محصول"
          >
            <X :size="20" aria-hidden="true" />
          </button>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto overscroll-contain p-6 space-y-6">
        <div class="flex flex-col gap-6 sm:flex-row sm:items-start">
          <div class="relative flex h-52 w-full sm:w-52 shrink-0 items-center justify-center rounded-2xl bg-[var(--color-surface-cream)] p-4 overflow-hidden border border-[var(--color-border-subtle)]">
            <img
              :src="product.image_url || '/img/placeholder.webp'"
              :alt="product.name"
              width="176"
              height="176"
              class="h-44 w-44 rounded-full object-cover shadow-sm"
            />
          </div>

          <div class="flex-1 space-y-3">
            <h1
              id="product-modal-title"
              class="text-xl font-bold text-[var(--color-text-primary)]"
            >
              {{ product.name }}
            </h1>

            <div class="flex flex-wrap items-center gap-3 text-xs text-[var(--color-text-secondary)]">
              <div class="inline-flex items-center gap-1 font-semibold text-[var(--color-text-primary)]">
                <Clock :size="14" aria-hidden="true" class="text-[var(--color-brand-forest)]" />
                <span>{{ toPersianDigits(product.prep_time_minutes) }} دقیقه آماده‌سازی</span>
              </div>
            </div>

            <div class="flex items-baseline gap-2.5">
              <span class="text-lg font-extrabold text-[var(--color-brand-forest)]">
                {{ formatToman(product.price) }}
              </span>
              <span
                v-if="product.is_discounted && product.compare_at_price"
                class="text-xs text-[var(--color-text-muted)] line-through"
              >
                {{ formatToman(product.compare_at_price) }}
              </span>
            </div>

            <p class="text-xs sm:text-sm leading-relaxed text-[var(--color-text-secondary)]">
              {{ product.description }}
            </p>
          </div>
        </div>

        <div v-if="product.addons.length > 0" class="space-y-3">
          <div class="flex items-center justify-between">
            <h2 class="text-sm font-bold text-[var(--color-text-primary)]">
              افزودنی‌های اختیاری (مجموع این ردیف)
            </h2>
            <span class="text-[11px] text-[var(--color-text-secondary)]">
              بر اساس حداکثر مجاز هر محصول
            </span>
          </div>

          <div class="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
            <div
              v-for="addon in product.addons"
              :key="addon.addon_id"
              class="flex items-center justify-between gap-2 rounded-2xl border p-3 transition-colors"
              :class="
                (addonQuantities[addon.addon_id] ?? 0) > 0
                  ? 'border-[var(--color-brand-forest)] bg-[var(--color-surface-cream)]'
                  : 'border-[var(--color-border-subtle)] bg-white'
              "
            >
              <div class="min-w-0">
                <p class="text-xs font-bold text-[var(--color-text-primary)] truncate">
                  {{ addon.name }}
                </p>
                <p class="text-[11px] text-[var(--color-text-secondary)] mt-0.5">
                  +{{ formatToman(addon.price) }} (حداکثر {{ toPersianDigits(addon.max_quantity) }})
                </p>
              </div>

              <div class="flex items-center gap-1.5 rounded-full border border-[var(--color-border-subtle)] bg-white px-1.5 py-1 shrink-0">
                <button
                  type="button"
                  :disabled="(addonQuantities[addon.addon_id] ?? 0) <= 0"
                  @click="setAddonQty(addon, -1)"
                  class="touch-target flex h-8 w-8 items-center justify-center rounded-full text-[var(--color-text-primary)] hover:bg-[var(--color-surface-cream)] disabled:opacity-40"
                  :aria-label="`کاهش ${addon.name}`"
                >
                  <Minus :size="14" aria-hidden="true" />
                </button>
                <span class="w-6 text-center text-xs font-bold text-[var(--color-text-primary)]">
                  {{ toPersianDigits(addonQuantities[addon.addon_id] ?? 0) }}
                </span>
                <button
                  type="button"
                  :disabled="(addonQuantities[addon.addon_id] ?? 0) >= addon.max_quantity"
                  @click="setAddonQty(addon, 1)"
                  class="touch-target flex h-8 w-8 items-center justify-center rounded-full text-[var(--color-text-primary)] hover:bg-[var(--color-surface-cream)] disabled:opacity-40"
                  :aria-label="`افزایش ${addon.name}`"
                >
                  <Plus :size="14" aria-hidden="true" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="border-t border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] p-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-3 rounded-full border border-[var(--color-border-subtle)] bg-white px-3 py-1.5 shadow-xs">
          <button
            type="button"
            :disabled="!isAvailable || quantity <= 1"
            @click="quantity = Math.max(1, quantity - 1)"
            class="touch-target flex h-9 w-9 items-center justify-center rounded-full text-[var(--color-text-primary)] hover:bg-[var(--color-surface-cream)] disabled:opacity-40"
            aria-label="کاهش تعداد"
          >
            <Minus :size="16" aria-hidden="true" />
          </button>
          <span class="w-8 text-center text-sm font-bold text-[var(--color-text-primary)]">
            {{ toPersianDigits(quantity) }}
          </span>
          <button
            type="button"
            :disabled="!isAvailable || quantity >= maxProductQty"
            @click="quantity = Math.min(maxProductQty, quantity + 1)"
            class="touch-target flex h-9 w-9 items-center justify-center rounded-full text-[var(--color-text-primary)] hover:bg-[var(--color-surface-cream)] disabled:opacity-40"
            aria-label="افزایش تعداد"
          >
            <Plus :size="16" aria-hidden="true" />
          </button>
        </div>

        <GooeyButton
          variant="primary"
          size="md"
          :disabled="!isAvailable"
          class="flex-1 w-full sm:w-auto !justify-between"
          aria-label="افزودن به سبد خرید"
          @click="handleAddToCart"
        >
          <div class="flex items-center gap-2">
            <img
              src="/svg/cart.svg"
              alt=""
              width="20"
              height="20"
              aria-hidden="true"
              class="h-5 w-5 object-contain filter brightness-0 invert"
            />
            <span>{{ isAvailable ? 'افزودن به سبد خرید' : 'این محصول فعلاً ناموجود است' }}</span>
          </div>
          <span v-if="isAvailable" class="text-sm font-extrabold text-[var(--color-accent-gold-soft)]">
            {{ formatToman(totalPrice) }}
          </span>
        </GooeyButton>
      </div>
    </div>
  </dialog>
</template>
