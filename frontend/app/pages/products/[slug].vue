<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ArrowRight, Plus, Minus, Clock } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { storefrontApi } from '~/services/api'
import { useCartStore } from '~/stores/cart'
import { usePersian } from '~/composables/usePersian'
import type { CartItemAddOn, ProductAddOnPublic, ProductDetailPublic } from '~/types'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const route = useRoute()
const cartStore = useCartStore()
const { toPersianDigits, formatToman } = usePersian()

const product = ref<ProductDetailPublic | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const quantity = ref(1)
const addonQuantities = ref<Record<number, number>>({})

const loadProduct = async () => {
  loading.value = true
  error.value = null
  try {
    const slug = String(route.params.slug || '')
    const data = await storefrontApi.catalog.getProductBySlug(slug)
    product.value = data
    const map: Record<number, number> = {}
    for (const addon of data.addons) {
      map[addon.addon_id] = addon.min_quantity > 0 ? addon.min_quantity : 0
    }
    addonQuantities.value = map
  } catch (err: any) {
    error.value = err?.message || 'محصول مورد نظر یافت نشد.'
  } finally {
    loading.value = false
  }
}

onMounted(loadProduct)

const maxQty = 99

const isAvailable = computed(() => {
  return Boolean(product.value && product.value.status === 'AVAILABLE')
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
    .map(addon => ({
      addon_id: addon.addon_id,
      name: addon.name,
      price: addon.price,
      quantity: addonQuantities.value[addon.addon_id] ?? 0,
      min_quantity: addon.min_quantity,
      max_quantity: addon.max_quantity,
    }))
    .filter(a => a.quantity > 0)
})

const addonsTotal = computed(() => {
  return selectedAddonsList.value.reduce((sum, a) => sum + a.price * a.quantity, 0)
})

const totalPrice = computed(() => {
  if (!product.value) return 0
  return product.value.price * quantity.value + addonsTotal.value
})

const handleAddToCart = () => {
  if (!product.value || !isAvailable.value) return
  cartStore.addItem(product.value, quantity.value, selectedAddonsList.value)
  toast.success(`${product.value.name} به سبد خرید اضافه شد`, {
    action: {
      label: 'مشاهده سبد',
      onClick: () => cartStore.openCart(),
    },
  })
}

useHead(() => ({
  title: product.value ? `${product.value.name} | فست‌فودی` : 'جزئیات محصول | فست‌فودی',
}))
</script>

<template>
  <main class="min-h-screen py-8 sm:py-14 bg-[var(--color-surface-cream)]/40">
    <div class="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 space-y-6">
      <div class="flex items-center justify-between gap-4">
        <NuxtLink
          to="/menu"
          class="inline-flex items-center gap-2 text-xs font-bold text-[var(--color-text-secondary)] hover:text-[var(--color-brand-forest)]"
        >
          <ArrowRight :size="15" aria-hidden="true" class="icon-directional" />
          <span>بازگشت به منو</span>
        </NuxtLink>

        <NuxtLink
          v-if="product"
          :to="`/menu?category=${product.category.slug}`"
          class="rounded-full border border-[var(--color-border-subtle)] bg-white px-3.5 py-1.5 text-xs font-bold text-[var(--color-brand-forest)] hover:border-[var(--color-brand-forest)]"
        >
          دسته: {{ product.category.name }}
        </NuxtLink>
      </div>

      <div
        v-if="loading"
        class="h-96 rounded-3xl border border-[var(--color-border-subtle)] bg-white animate-pulse"
        aria-busy="true"
      />

      <div
        v-else-if="error || !product"
        class="rounded-3xl border border-[var(--color-danger)]/30 bg-[var(--color-danger-bg)] p-10 text-center space-y-4"
      >
        <h1 class="text-lg font-bold text-[var(--color-danger)]">
          {{ error || 'محصول یافت نشد' }}
        </h1>
        <NuxtLink
          to="/menu"
          class="touch-target inline-flex items-center justify-center rounded-full bg-[var(--color-brand-forest)] px-6 py-2.5 text-xs font-bold text-white"
        >
          بازگشت به منوی غذاها
        </NuxtLink>
      </div>

      <article
        v-else
        class="rounded-3xl border border-[var(--color-border-subtle)] bg-white p-6 sm:p-10 shadow-[var(--shadow-md)] space-y-8"
      >
        <div class="grid grid-cols-1 gap-8 md:grid-cols-12 items-start">
          <div class="md:col-span-5 flex items-center justify-center rounded-2xl bg-[var(--color-surface-cream)] p-6 border border-[var(--color-border-subtle)]">
            <img
              :src="product.image_url || '/img/placeholder.webp'"
              :alt="product.name"
              width="320"
              height="320"
              class="aspect-square w-full max-w-[300px] rounded-full object-cover shadow-sm"
            />
          </div>

          <div class="md:col-span-7 space-y-5">
            <div class="flex flex-wrap items-center gap-2">
              <span
                v-if="!isAvailable"
                class="rounded-full bg-[var(--color-danger-bg)] px-3 py-1 text-xs font-bold text-[var(--color-danger)]"
              >
                ناموجود
              </span>
              <span
                v-if="product.is_discounted"
                class="rounded-full bg-[var(--color-accent-gold-soft)] px-3 py-1 text-xs font-bold text-[var(--color-accent-gold-text)]"
              >
                {{ toPersianDigits(product.discount_percent) }}٪ تخفیف
              </span>
              <span
                v-if="product.is_main_dish"
                class="rounded-full bg-[var(--color-surface-cream)] px-3 py-1 text-xs font-semibold text-[var(--color-brand-forest)]"
              >
                غذای اصلی
              </span>
            </div>

            <h1 class="text-2xl sm:text-3xl font-extrabold text-[var(--color-brand-forest)]">
              {{ product.name }}
            </h1>

            <p class="text-sm leading-relaxed text-[var(--color-text-secondary)]">
              {{ product.description }}
            </p>

            <div class="flex flex-wrap items-center gap-4 text-xs text-[var(--color-text-secondary)]">
              <span class="inline-flex items-center gap-1.5 font-semibold text-[var(--color-text-primary)]">
                <Clock :size="15" aria-hidden="true" class="text-[var(--color-brand-forest)]" />
                <span>زمان آماده‌سازی: {{ toPersianDigits(product.prep_time_minutes) }} دقیقه</span>
              </span>
            </div>

            <div class="flex items-baseline gap-3 pt-1">
              <span class="text-2xl font-extrabold text-[var(--color-brand-forest)]">
                {{ formatToman(product.price) }}
              </span>
              <span
                v-if="product.is_discounted && product.compare_at_price"
                class="text-sm text-[var(--color-text-muted)] line-through"
              >
                {{ formatToman(product.compare_at_price) }}
              </span>
            </div>

            <div v-if="product.addons.length > 0" class="space-y-3 pt-4 border-t border-[var(--color-border-subtle)]">
              <h2 class="text-sm font-bold text-[var(--color-text-primary)]">
                افزودنی‌های اختیاری این ردیف
              </h2>
              <div class="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                <div
                  v-for="addon in product.addons"
                  :key="addon.addon_id"
                  class="flex items-center justify-between gap-2 rounded-2xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)]/60 p-3"
                >
                  <div class="min-w-0">
                    <p class="text-xs font-bold text-[var(--color-text-primary)] truncate">
                      {{ addon.name }}
                    </p>
                    <p class="text-[11px] text-[var(--color-text-secondary)]">
                      +{{ formatToman(addon.price) }} (حداکثر {{ toPersianDigits(addon.max_quantity) }})
                    </p>
                  </div>
                  <div class="flex items-center gap-1.5 rounded-full border border-[var(--color-border-subtle)] bg-white px-1.5 py-1 shrink-0">
                    <button
                      type="button"
                      :disabled="(addonQuantities[addon.addon_id] ?? 0) <= 0"
                      @click="setAddonQty(addon, -1)"
                      class="touch-target flex h-8 w-8 items-center justify-center rounded-full hover:bg-[var(--color-surface-cream)] disabled:opacity-40"
                      :aria-label="`کاهش ${addon.name}`"
                    >
                      <Minus :size="14" aria-hidden="true" />
                    </button>
                    <span class="w-5 text-center text-xs font-bold">
                      {{ toPersianDigits(addonQuantities[addon.addon_id] ?? 0) }}
                    </span>
                    <button
                      type="button"
                      :disabled="(addonQuantities[addon.addon_id] ?? 0) >= addon.max_quantity"
                      @click="setAddonQty(addon, 1)"
                      class="touch-target flex h-8 w-8 items-center justify-center rounded-full hover:bg-[var(--color-surface-cream)] disabled:opacity-40"
                      :aria-label="`افزایش ${addon.name}`"
                    >
                      <Plus :size="14" aria-hidden="true" />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div class="flex flex-col sm:flex-row items-center gap-4 pt-4 border-t border-[var(--color-border-subtle)]">
              <div class="flex items-center gap-3 rounded-full border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] px-3 py-1.5">
                <button
                  type="button"
                  :disabled="!isAvailable || quantity <= 1"
                  @click="quantity = Math.max(1, quantity - 1)"
                  class="touch-target flex h-9 w-9 items-center justify-center rounded-full hover:bg-white disabled:opacity-40"
                  aria-label="کاهش تعداد"
                >
                  <Minus :size="16" aria-hidden="true" />
                </button>
                <span class="w-8 text-center text-sm font-bold">
                  {{ toPersianDigits(quantity) }}
                </span>
                <button
                  type="button"
                  :disabled="!isAvailable || quantity >= maxQty"
                  @click="quantity = Math.min(maxQty, quantity + 1)"
                  class="touch-target flex h-9 w-9 items-center justify-center rounded-full hover:bg-white disabled:opacity-40"
                  aria-label="افزایش تعداد"
                >
                  <Plus :size="16" aria-hidden="true" />
                </button>
              </div>

              <GooeyButton
                variant="primary"
                size="lg"
                :disabled="!isAvailable"
                class="flex-1 w-full !justify-between"
                @click="handleAddToCart"
              >
                <span>{{ isAvailable ? 'افزودن به سبد خرید' : 'این محصول ناموجود است' }}</span>
                <span v-if="isAvailable" class="text-sm font-extrabold text-[var(--color-accent-gold-soft)]">
                  {{ formatToman(totalPrice) }}
                </span>
              </GooeyButton>
            </div>
          </div>
        </div>
      </article>
    </div>
  </main>
</template>
