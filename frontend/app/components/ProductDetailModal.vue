<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  X,
  Plus,
  Minus,
  Clock,
  Flame,
  Star,
  Check,
  ShoppingBag,
} from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { useMenuStore } from '~/stores/menu'
import { useCartStore } from '~/stores/cart'
import { usePersian } from '~/composables/usePersian'
import type { ProductModifier, ProductSize } from '~/types'

const menuStore = useMenuStore()
const cartStore = useCartStore()
const { toPersianDigits, formatToman } = usePersian()

const dialogRef = ref<HTMLDialogElement | null>(null)
const quantity = ref(1)
const selectedSize = ref<ProductSize | undefined>(undefined)
const selectedAddons = ref<ProductModifier[]>([])
const specialInstructions = ref('')

const product = computed(() => menuStore.selectedProductForModal)

// Watch open/close state of modal
watch(
  () => menuStore.selectedProductForModal,
  (newVal) => {
    if (newVal) {
      quantity.value = 1
      selectedSize.value = newVal.sizes?.[0]
      selectedAddons.value = []
      specialInstructions.value = ''
      dialogRef.value?.showModal()
    } else {
      dialogRef.value?.close()
    }
  }
)

const toggleAddon = (addon: ProductModifier) => {
  const index = selectedAddons.value.findIndex(a => a.id === addon.id)
  if (index > -1) {
    selectedAddons.value.splice(index, 1)
  } else {
    selectedAddons.value.push(addon)
  }
}

const isAddonSelected = (addonId: string) => {
  return selectedAddons.value.some(a => a.id === addonId)
}

// Live calculation of item unit and total price
const unitPrice = computed(() => {
  if (!product.value) return 0
  const base = product.value.price
  const sizeOffset = selectedSize.value?.priceOffset || 0
  const addonsTotal = selectedAddons.value.reduce((sum, a) => sum + a.price, 0)
  return base + sizeOffset + addonsTotal
})

const totalPrice = computed(() => {
  return unitPrice.value * quantity.value
})

const handleAddToCart = () => {
  if (!product.value) return

  cartStore.addItem(product.value, quantity.value, {
    size: selectedSize.value,
    addons: selectedAddons.value,
    specialInstructions: specialInstructions.value,
  })

  toast.success(`${product.value.title} به سبد خرید اضافه شد`, {
    description: `${toPersianDigits(quantity.value)} عدد - ${formatToman(totalPrice.value)}`,
    action: {
      label: 'مشاهده سبد',
      onClick: () => cartStore.openCart(),
    },
  })

  menuStore.closeProductModal()
}

const handleBackdropClick = (e: MouseEvent) => {
  if (e.target === dialogRef.value) {
    menuStore.closeProductModal()
  }
}
</script>

<template>
  <dialog
    ref="dialogRef"
    @click="handleBackdropClick"
    @close="menuStore.closeProductModal"
    aria-labelledby="product-modal-title"
    class="fixed inset-0 m-auto z-50 w-[95%] max-w-2xl rounded-3xl border border-[var(--color-border-subtle)] bg-white p-0 shadow-[var(--shadow-lg)] backdrop:bg-[rgba(18,37,29,0.55)] backdrop:backdrop-blur-xs overscroll-contain transition-all"
  >
    <div v-if="product" class="flex max-h-[90vh] flex-col overflow-hidden">
      <!-- Modal Header Bar -->
      <div
        class="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-[var(--color-border-subtle)] bg-white/95 px-6 backdrop-blur-xs"
      >
        <div class="flex items-center gap-2">
          <span
            v-for="badge in product.badges"
            :key="badge"
            class="rounded-full bg-[var(--color-accent-gold-soft)] px-2.5 py-0.5 text-[11px] font-semibold text-[var(--color-accent-gold-hover)]"
          >
            {{ badge }}
          </span>
        </div>

        <button
          type="button"
          @click="menuStore.closeProductModal"
          class="touch-target flex h-10 w-10 items-center justify-center rounded-full text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-cream)] active:scale-95"
          aria-label="بستن پنجره"
        >
          <X :size="20" />
        </button>
      </div>

      <!-- Modal Body (Scrollable) -->
      <div class="flex-1 overflow-y-auto p-6 space-y-6">
        <!-- Visual & Info Split -->
        <div class="flex flex-col gap-6 sm:flex-row sm:items-start">
          <div
            class="relative flex h-52 w-full sm:w-52 shrink-0 items-center justify-center rounded-2xl bg-[var(--color-surface-cream)] p-4 overflow-hidden border border-[var(--color-border-subtle)]"
          >
            <img
              :src="product.image"
              :alt="product.title"
              class="h-44 w-44 rounded-full object-cover shadow-sm transition-transform hover:scale-105 duration-300"
            />
          </div>

          <div class="flex-1 space-y-2.5">
            <h2
              id="product-modal-title"
              class="text-xl font-bold text-[var(--color-text-primary)]"
            >
              {{ product.title }}
            </h2>

            <!-- Rating & Stats -->
            <div class="flex items-center gap-3 text-xs text-[var(--color-text-secondary)]">
              <div class="flex items-center gap-1 font-semibold text-[var(--color-text-primary)]">
                <Star :size="14" class="fill-[var(--color-accent-gold)] text-[var(--color-accent-gold)]" />
                <span>{{ toPersianDigits(product.rating) }}</span>
                <span class="text-[var(--color-text-muted)]">
                  ({{ toPersianDigits(product.reviewsCount) }} نظر)
                </span>
              </div>
              <span class="text-[var(--color-border-subtle)]">|</span>
              <div class="flex items-center gap-1">
                <Clock :size="14" class="text-[var(--color-brand-forest)]" />
                <span>{{ toPersianDigits(product.prepTimeMinutes) }} دقیقه آماده‌سازی</span>
              </div>
              <span v-if="product.calories" class="text-[var(--color-border-subtle)]">|</span>
              <div v-if="product.calories" class="flex items-center gap-1">
                <Flame :size="14" class="text-[var(--color-accent-gold)]" />
                <span>{{ toPersianDigits(product.calories) }} کالری</span>
              </div>
            </div>

            <p class="text-xs leading-relaxed text-[var(--color-text-secondary)]">
              {{ product.description }}
            </p>
          </div>
        </div>

        <!-- Portion / Size Option -->
        <div v-if="product.sizes && product.sizes.length > 0" class="space-y-3">
          <label class="block text-xs font-bold text-[var(--color-text-primary)]">
            انتخاب اندازه / حجم سرو
          </label>
          <div class="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
            <button
              v-for="size in product.sizes"
              :key="size.id"
              type="button"
              @click="selectedSize = size"
              class="flex items-center justify-between rounded-xl border p-3.5 text-xs font-medium transition-all"
              :class="
                selectedSize?.id === size.id
                  ? 'border-[var(--color-brand-forest)] bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)] ring-2 ring-[var(--color-brand-forest)]/20 font-bold'
                  : 'border-[var(--color-border-subtle)] bg-white text-[var(--color-text-primary)] hover:border-[var(--color-brand-forest)]'
              "
            >
              <span>{{ size.name }}</span>
              <span v-if="size.priceOffset > 0" class="text-[11px] text-[var(--color-text-secondary)]">
                +{{ formatToman(size.priceOffset) }}
              </span>
              <span v-else class="text-[11px] text-[var(--color-text-muted)]">
                قیمت پایه
              </span>
            </button>
          </div>
        </div>

        <!-- Add-ons Selection -->
        <div v-if="product.addons && product.addons.length > 0" class="space-y-3">
          <label class="block text-xs font-bold text-[var(--color-text-primary)]">
            مخلفات و افزودنی‌های دلخواه
          </label>
          <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
            <button
              v-for="addon in product.addons"
              :key="addon.id"
              type="button"
              @click="toggleAddon(addon)"
              class="flex items-center justify-between rounded-xl border p-3 text-xs font-medium transition-all"
              :class="
                isAddonSelected(addon.id)
                  ? 'border-[var(--color-brand-forest)] bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)]'
                  : 'border-[var(--color-border-subtle)] bg-white text-[var(--color-text-primary)] hover:border-[var(--color-border-focus)]'
              "
            >
              <div class="flex items-center gap-2">
                <div
                  class="flex h-4.5 w-4.5 items-center justify-center rounded-md border"
                  :class="
                    isAddonSelected(addon.id)
                      ? 'border-[var(--color-brand-forest)] bg-[var(--color-brand-forest)] text-white'
                      : 'border-[var(--color-border-subtle)] bg-white'
                  "
                >
                  <Check v-if="isAddonSelected(addon.id)" :size="12" />
                </div>
                <span>{{ addon.name }}</span>
              </div>
              <span class="text-[11px] text-[var(--color-text-secondary)]">
                +{{ formatToman(addon.price) }}
              </span>
            </button>
          </div>
        </div>

        <!-- Special Instructions Textarea -->
        <div class="space-y-2">
          <label for="instructions" class="block text-xs font-bold text-[var(--color-text-primary)]">
            توضیحات یا یادداشت ویژه برای سرآشپز (اختیاری)
          </label>
          <textarea
            id="instructions"
            v-model="specialInstructions"
            rows="2"
            maxlength="200"
            placeholder="مثال: بدون پیاز، سس جداگانه در ظرف کوچک ارسال شود..."
            class="w-full rounded-xl border border-[var(--color-border-subtle)] bg-white p-3 text-xs text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-brand-forest)] focus:ring-2 focus:ring-[var(--color-brand-forest)]/10 focus:outline-none transition-all"
          />
        </div>
      </div>

      <!-- Sticky Footer Action -->
      <div
        class="border-t border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] p-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4"
      >
        <!-- Stepper -->
        <div
          class="flex items-center gap-3 rounded-full border border-[var(--color-border-subtle)] bg-white px-3 py-1.5 shadow-xs"
        >
          <button
            type="button"
            @click="quantity = Math.max(1, quantity - 1)"
            class="touch-target flex h-8 w-8 items-center justify-center rounded-full text-[var(--color-text-primary)] hover:bg-[var(--color-surface-cream)] active:scale-90"
            aria-label="کاهش"
          >
            <Minus :size="16" />
          </button>
          <span class="w-8 text-center text-sm font-bold text-[var(--color-text-primary)]">
            {{ toPersianDigits(quantity) }}
          </span>
          <button
            type="button"
            @click="quantity++"
            class="touch-target flex h-8 w-8 items-center justify-center rounded-full text-[var(--color-text-primary)] hover:bg-[var(--color-surface-cream)] active:scale-90"
            aria-label="افزایش"
          >
            <Plus :size="16" />
          </button>
        </div>

        <!-- Add to cart CTA -->
        <button
          type="button"
          @click="handleAddToCart"
          class="touch-target flex flex-1 w-full sm:w-auto items-center justify-between rounded-full bg-[var(--color-brand-forest)] px-6 py-3 text-sm font-bold text-white shadow-sm transition-all hover:bg-[var(--color-brand-forest-light)] active:scale-98"
        >
          <div class="flex items-center gap-2">
            <ShoppingBag :size="18" />
            <span>افزودن به سبد خرید</span>
          </div>
          <span class="text-sm font-extrabold text-[var(--color-accent-gold-soft)]">
            {{ formatToman(totalPrice) }}
          </span>
        </button>
      </div>
    </div>
  </dialog>
</template>

