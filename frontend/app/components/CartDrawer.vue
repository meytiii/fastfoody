<script setup lang="ts">
import { computed, watch } from 'vue'
import {
  X,
  Plus,
  Minus,
  Trash2,
  ArrowLeft,
  Clock,
  AlertTriangle,
} from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { useCartStore } from '~/stores/cart'
import { useMenuStore } from '~/stores/menu'
import { useCmsStore } from '~/stores/cms'
import { usePersian } from '~/composables/usePersian'
import type { UpsellProductPublic } from '~/types'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const cartStore = useCartStore()
const menuStore = useMenuStore()
const cmsStore = useCmsStore()
const { toPersianDigits, formatToman } = usePersian()

watch(
  () => cartStore.isOpen,
  open => {
    if (open) {
      void menuStore.fetchUpsell()
    }
  },
  { immediate: true }
)

const upsellSuggestions = computed(() => {
  const inCartIds = new Set(cartStore.items.map(i => i.productId))
  return menuStore.upsellItems.filter(p => !inCartIds.has(p.id)).slice(0, 4)
})

const addUpsellItem = (item: UpsellProductPublic) => {
  const matchedProduct = menuStore.menuCategories
    .flatMap(c => c.products)
    .find(p => p.id === item.id)
  cartStore.addItem(
    {
      id: item.id,
      slug: item.slug,
      name: item.name,
      price: item.price,
      compare_at_price: item.compare_at_price,
      prep_time_minutes: matchedProduct?.prep_time_minutes ?? 10,
      image_url: item.image_url,
      status: matchedProduct?.status ?? 'AVAILABLE',
      category_id: item.category_id,
    },
    1,
    []
  )
  toast.success(`${item.name} به سبد خرید اضافه شد`)
}

const goToCheckout = () => {
  cartStore.closeCart()
  navigateTo('/checkout')
}
</script>

<template>
  <Transition
    enter-active-class="transition-opacity duration-250"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition-opacity duration-200"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="cartStore.isOpen"
      class="fixed inset-0 z-50 bg-[rgba(18,37,29,0.45)] backdrop-blur-xs"
      @click="cartStore.closeCart"
    />
  </Transition>

  <Transition
    enter-active-class="transition-transform duration-280 ease-[var(--ease-drawer)]"
    enter-from-class="-translate-x-full"
    enter-to-class="translate-x-0"
    leave-active-class="transition-transform duration-200 ease-[var(--ease-out)]"
    leave-from-class="translate-x-0"
    leave-to-class="-translate-x-full"
  >
    <aside
      v-if="cartStore.isOpen"
      class="fixed top-0 bottom-0 start-0 z-50 flex w-full flex-col bg-white shadow-[var(--shadow-lg)] sm:w-[420px] overscroll-contain"
      role="dialog"
      aria-label="سبد خرید شما"
    >
      <div class="flex h-18 items-center justify-between border-b border-[var(--color-border-subtle)] px-6">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--color-surface-cream)] p-2">
            <img src="/svg/cart.svg" alt="" width="24" height="24" aria-hidden="true" class="h-6 w-6 object-contain" />
          </div>
          <div>
            <h2 class="text-base font-bold text-[var(--color-text-primary)]">
              سبد خرید شما
            </h2>
            <p class="text-xs text-[var(--color-text-secondary)]">
              {{ toPersianDigits(cartStore.totalCount) }} آیتم انتخابی
            </p>
          </div>
        </div>

        <button
          type="button"
          @click="cartStore.closeCart"
          class="touch-target flex h-10 w-10 items-center justify-center rounded-full text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-cream)] active:scale-[0.97] transition-[background-color,transform] duration-150 ease-[var(--ease-out)]"
          aria-label="بستن سبد خرید"
        >
          <X :size="20" aria-hidden="true" />
        </button>
      </div>

      <div
        v-if="!cmsStore.isOpen"
        class="border-b border-[var(--color-warning)]/20 bg-[var(--color-warning-bg)] px-6 py-2.5 text-xs font-semibold text-[var(--color-warning)] flex items-center gap-2"
      >
        <AlertTriangle :size="15" aria-hidden="true" class="shrink-0" />
        <span>رستوران در حال حاضر بسته است و امکان ثبت سفارش وجود ندارد.</span>
      </div>

      <div class="flex-1 overflow-y-auto overscroll-contain px-6 py-4 space-y-6">
        <div
          v-if="cartStore.isEmpty"
          class="flex h-full flex-col items-center justify-center py-12 text-center"
        >
          <div class="mb-4 flex h-24 w-24 items-center justify-center rounded-full bg-[var(--color-surface-cream)] p-4 shadow-2xs border border-[var(--color-border-subtle)]">
            <img src="/svg/cart.svg" alt="" width="56" height="56" aria-hidden="true" class="h-14 w-14 object-contain" />
          </div>
          <h3 class="text-base font-bold text-[var(--color-text-primary)]">
            سبد خرید شما هنوز خالی است
          </h3>
          <p class="mt-1.5 max-w-[260px] text-xs text-[var(--color-text-secondary)]">
            غذاهای تازه و دست‌ساز فست‌فودی را مرور کنید و سفارش خود را ثبت نمایید.
          </p>
          <GooeyButton
            variant="primary"
            size="sm"
            aria-label="مشاهده منوی غذاها"
            class="mt-6"
            @click="() => { cartStore.closeCart(); navigateTo('/menu') }"
          >
            <img src="/svg/knife_fork.svg" alt="" width="18" height="18" aria-hidden="true" class="h-4.5 w-4.5 object-contain" />
            <span>مشاهده منوی غذاها</span>
          </GooeyButton>
        </div>

        <template v-else>
          <div class="space-y-3.5">
            <div
              v-for="item in cartStore.items"
              :key="item.id"
              class="flex items-start gap-3.5 rounded-2xl border border-[var(--color-border-subtle)] bg-white p-3.5"
            >
              <img
                :src="item.product.image_url || '/img/placeholder.webp'"
                :alt="item.product.name"
                width="64"
                height="64"
                class="h-16 w-16 rounded-xl object-cover bg-[var(--color-surface-cream)] shrink-0"
              />

              <div class="flex-1 min-w-0">
                <div class="flex items-start justify-between gap-2">
                  <h4 class="text-sm font-bold text-[var(--color-text-primary)] truncate">
                    {{ item.product.name }}
                  </h4>
                  <button
                    type="button"
                    @click="cartStore.removeItem(item.id)"
                    class="touch-target flex h-8 w-8 items-center justify-center rounded-full text-[var(--color-text-secondary)] hover:text-[var(--color-danger)] transition-colors"
                    :aria-label="`حذف ${item.product.name}`"
                  >
                    <Trash2 :size="15" aria-hidden="true" />
                  </button>
                </div>

                <div v-if="item.selectedAddons.length > 0" class="mt-1 space-y-0.5 text-[11px] text-[var(--color-text-secondary)]">
                  <p v-for="addon in item.selectedAddons" :key="addon.addon_id">
                    + {{ addon.name }} ({{ toPersianDigits(addon.quantity) }} عدد)
                  </p>
                </div>

                <div class="mt-3 flex items-center justify-between">
                  <span class="text-xs font-bold text-[var(--color-brand-forest)]">
                    {{ formatToman(item.totalPrice) }}
                  </span>

                  <div class="flex items-center gap-1.5 rounded-full border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] px-1.5 py-0.5">
                    <button
                      type="button"
                      @click="cartStore.updateQuantity(item.id, -1)"
                      class="touch-target flex h-8 w-8 items-center justify-center rounded-full text-[var(--color-text-primary)] hover:bg-white"
                      aria-label="کاهش تعداد"
                    >
                      <Minus :size="13" aria-hidden="true" />
                    </button>
                    <span class="w-5 text-center text-xs font-bold text-[var(--color-text-primary)]">
                      {{ toPersianDigits(item.quantity) }}
                    </span>
                    <button
                      type="button"
                      @click="cartStore.updateQuantity(item.id, 1)"
                      class="touch-target flex h-8 w-8 items-center justify-center rounded-full text-[var(--color-text-primary)] hover:bg-white"
                      aria-label="افزایش تعداد"
                    >
                      <Plus :size="13" aria-hidden="true" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="upsellSuggestions.length > 0" class="space-y-2.5 pt-2 border-t border-[var(--color-border-subtle)]">
            <h3 class="text-xs font-bold text-[var(--color-text-primary)]">
              پیشنهاد در کنار سفارش (نوشیدنی، سالاد و دسر)
            </h3>
            <div class="grid grid-cols-1 gap-2">
              <div
                v-for="upsell in upsellSuggestions"
                :key="upsell.id"
                class="flex items-center justify-between gap-3 rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)]/60 p-2.5"
              >
                <div class="flex items-center gap-2.5 min-w-0">
                  <img
                    :src="upsell.image_url || '/img/placeholder.webp'"
                    :alt="upsell.name"
                    width="40"
                    height="40"
                    class="h-10 w-10 rounded-lg object-cover bg-white shrink-0"
                  />
                  <div class="min-w-0">
                    <p class="text-xs font-bold text-[var(--color-text-primary)] truncate">
                      {{ upsell.name }}
                    </p>
                    <p class="text-[11px] font-semibold text-[var(--color-brand-forest)]">
                      {{ formatToman(upsell.price) }}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  @click="addUpsellItem(upsell)"
                  class="touch-target inline-flex items-center gap-1 rounded-full border border-[var(--color-brand-forest)] bg-white px-3 py-1.5 text-xs font-bold text-[var(--color-brand-forest)] hover:bg-[var(--color-brand-forest)] hover:text-white transition-colors shrink-0"
                >
                  <Plus :size="13" aria-hidden="true" />
                  <span>افزودن</span>
                </button>
              </div>
            </div>
          </div>
        </template>
      </div>

      <div
        v-if="!cartStore.isEmpty"
        class="border-t border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)]/85 p-6 space-y-2.5"
      >
        <div class="flex items-center justify-between text-xs text-[var(--color-text-secondary)]">
          <span>مجموع اقلام</span>
          <span class="font-bold text-[var(--color-text-primary)]">
            {{ formatToman(cartStore.subtotal) }}
          </span>
        </div>

        <div class="flex items-center justify-between text-xs text-[var(--color-text-secondary)]">
          <span class="inline-flex items-center gap-1">
            <Clock :size="13" aria-hidden="true" />
            <span>زمان تقریبی آماده‌سازی</span>
          </span>
          <span class="font-semibold text-[var(--color-text-primary)]">
            {{ toPersianDigits(cartStore.estimatedPrepMinutes) }} دقیقه
          </span>
        </div>

        <div class="flex items-center justify-between text-xs text-[var(--color-text-secondary)]">
          <span>هزینه ارسال</span>
          <span class="text-[11px] font-medium text-[var(--color-text-primary)]">
            {{ formatToman(cmsStore.inZoneFee) }} تا {{ formatToman(cmsStore.outZoneFee) }} (تحویل حضوری: رایگان)
          </span>
        </div>

        <GooeyButton
          variant="primary"
          size="lg"
          aria-label="ادامه و تکمیل سفارش"
          class="mt-3 w-full"
          @click="goToCheckout"
        >
          <span>ادامه و انتخاب روش تحویل</span>
          <ArrowLeft :size="18" aria-hidden="true" class="icon-directional" />
        </GooeyButton>
      </div>
    </aside>
  </Transition>
</template>
