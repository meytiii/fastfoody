<script setup lang="ts">
import { computed } from 'vue'
import {
  X,
  Plus,
  Minus,
  Trash2,
  ShoppingBag,
  ArrowLeft,
  Truck,
  Sparkles,
} from 'lucide-vue-next'
import { useCartStore } from '~/stores/cart'
import { usePersian } from '~/composables/usePersian'

const cartStore = useCartStore()
const { toPersianDigits, formatToman, formatNumber } = usePersian()

const freeDeliveryThreshold = 450000
const progressToFreeDelivery = computed(() => {
  if (cartStore.subtotal >= freeDeliveryThreshold) return 100
  return Math.min(100, Math.round((cartStore.subtotal / freeDeliveryThreshold) * 100))
})
const remainingForFreeDelivery = computed(() => {
  return Math.max(0, freeDeliveryThreshold - cartStore.subtotal)
})

const goToCheckout = () => {
  cartStore.closeCart()
  navigateTo('/checkout')
}
</script>

<template>
  <!-- Backdrop -->
  <Transition
    enter-active-class="transition-opacity duration-300"
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

  <!-- Slide-out Drawer Panel (left side in RTL / inset-inline-start) -->
  <Transition
    enter-active-class="transition-transform duration-300 ease-out"
    enter-from-class="-translate-x-full"
    enter-to-class="translate-x-0"
    leave-active-class="transition-transform duration-200 ease-in"
    leave-from-class="translate-x-0"
    leave-to-class="-translate-x-full"
  >
    <aside
      v-if="cartStore.isOpen"
      class="fixed top-0 bottom-0 inset-inline-start-0 z-50 flex w-full flex-col bg-white shadow-[var(--shadow-lg)] sm:w-[420px] overscroll-contain"
      role="dialog"
      aria-label="سبد خرید شما"
    >
      <!-- Drawer Header -->
      <div
        class="flex h-18 items-center justify-between border-b border-[var(--color-border-subtle)] px-6"
      >
        <div class="flex items-center gap-3">
          <div
            class="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)]"
          >
            <ShoppingBag :size="20" />
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
          class="touch-target flex h-10 w-10 items-center justify-center rounded-full text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-cream)] active:scale-95"
          aria-label="بستن سبد خرید"
        >
          <X :size="20" />
        </button>
      </div>

      <!-- Free Delivery Progress Bar -->
      <div
        v-if="!cartStore.isEmpty"
        class="border-b border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] px-6 py-3"
      >
        <div class="flex items-center justify-between text-xs mb-1.5">
          <div class="flex items-center gap-1.5 text-[var(--color-brand-forest)] font-medium">
            <Truck :size="15" />
            <span v-if="remainingForFreeDelivery === 0">
              تبریک! ارسال سفارش شما <strong class="text-[var(--color-brand-success)]">کاملاً رایگان</strong> شد
            </span>
            <span v-else>
              فقط <strong>{{ formatToman(remainingForFreeDelivery) }}</strong> تا ارسال رایگان
            </span>
          </div>
          <span class="font-bold text-[var(--color-text-primary)]">
            {{ toPersianDigits(progressToFreeDelivery) }}٪
          </span>
        </div>
        <div class="h-2 w-full overflow-hidden rounded-full bg-[var(--color-border-subtle)]">
          <div
            class="h-full bg-[var(--color-brand-forest)] transition-all duration-500 rounded-full"
            :style="{ width: `${progressToFreeDelivery}%` }"
          />
        </div>
      </div>

      <!-- Item List Container -->
      <div class="flex-1 overflow-y-auto px-6 py-4">
        <!-- Empty State -->
        <div
          v-if="cartStore.isEmpty"
          class="flex h-full flex-col items-center justify-center py-12 text-center"
        >
          <div
            class="mb-4 flex h-24 w-24 items-center justify-center rounded-full bg-[var(--color-surface-cream)] text-[var(--color-text-muted)]"
          >
            <ShoppingBag :size="44" :stroke-width="1.25" />
          </div>
          <h3 class="text-base font-bold text-[var(--color-text-primary)]">
            سبد خرید شما هنوز خالی است
          </h3>
          <p class="mt-1.5 max-w-[260px] text-xs text-[var(--color-text-secondary)]">
            طعم‌های اصیل و ارگانیک فست‌فودی را کشف کنید و اولین سفارش خود را ثبت نمایید.
          </p>
          <button
            type="button"
            @click="cartStore.closeCart"
            class="touch-target mt-6 inline-flex items-center gap-2 rounded-full bg-[var(--color-brand-forest)] px-6 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-[var(--color-brand-forest-light)]"
          >
            <Sparkles :size="15" />
            <span>مشاهده منوی غذاها</span>
          </button>
        </div>

        <!-- Populated Items -->
        <div v-else class="space-y-4">
          <div
            v-for="item in cartStore.items"
            :key="item.id"
            class="flex items-start gap-3.5 rounded-2xl border border-[var(--color-border-subtle)] bg-white p-3.5 transition-all hover:border-[var(--color-brand-forest)]"
          >
            <!-- Dish Thumbnail -->
            <img
              :src="item.product.image"
              :alt="item.product.title"
              class="h-16 w-16 rounded-xl object-cover bg-[var(--color-surface-cream)] shrink-0"
            />

            <!-- Content Details -->
            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-2">
                <h4 class="text-sm font-bold text-[var(--color-text-primary)] truncate">
                  {{ item.product.title }}
                </h4>
                <button
                  type="button"
                  @click="cartStore.removeItem(item.id)"
                  class="text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors p-1"
                  aria-label="حذف این آیتم"
                >
                  <Trash2 :size="15" />
                </button>
              </div>

              <!-- Modifiers Display -->
              <div class="mt-1 space-y-0.5 text-[11px] text-[var(--color-text-secondary)]">
                <p v-if="item.selectedSize">
                  اندازه: {{ item.selectedSize.name }}
                </p>
                <p v-if="item.selectedAddons.length > 0">
                  افزودنی‌ها: {{ item.selectedAddons.map(a => a.name).join('، ') }}
                </p>
                <p v-if="item.specialInstructions" class="italic truncate text-[var(--color-text-muted)]">
                  «{{ item.specialInstructions }}»
                </p>
              </div>

              <!-- Price & Quantity Row -->
              <div class="mt-3 flex items-center justify-between">
                <span class="text-xs font-bold text-[var(--color-brand-forest)]">
                  {{ formatToman(item.totalPrice) }}
                </span>

                <!-- Stepper -->
                <div
                  class="flex items-center gap-2 rounded-full border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] px-2 py-1"
                >
                  <button
                    type="button"
                    @click="cartStore.updateQuantity(item.id, -1)"
                    class="touch-target flex h-6 w-6 items-center justify-center rounded-full text-[var(--color-text-primary)] hover:bg-white active:scale-90"
                    aria-label="کاهش تعداد"
                  >
                    <Minus :size="13" />
                  </button>
                  <span class="w-5 text-center text-xs font-bold text-[var(--color-text-primary)]">
                    {{ toPersianDigits(item.quantity) }}
                  </span>
                  <button
                    type="button"
                    @click="cartStore.updateQuantity(item.id, 1)"
                    class="touch-target flex h-6 w-6 items-center justify-center rounded-full text-[var(--color-text-primary)] hover:bg-white active:scale-90"
                    aria-label="افزایش تعداد"
                  >
                    <Plus :size="13" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Sticky Drawer Footer -->
      <div
        v-if="!cartStore.isEmpty"
        class="border-t border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)]/80 p-6 space-y-3"
      >
        <!-- Subtotal -->
        <div class="flex items-center justify-between text-xs text-[var(--color-text-secondary)]">
          <span>مجموع اقلام</span>
          <span class="font-semibold text-[var(--color-text-primary)]">
            {{ formatToman(cartStore.subtotal) }}
          </span>
        </div>

        <!-- Packaging Fee -->
        <div class="flex items-center justify-between text-xs text-[var(--color-text-secondary)]">
          <span>هزینه بسته‌بندی بهداشتی</span>
          <span class="font-semibold text-[var(--color-text-primary)]">
            {{ formatToman(cartStore.packagingFee) }}
          </span>
        </div>

        <!-- Delivery Fee -->
        <div class="flex items-center justify-between text-xs text-[var(--color-text-secondary)]">
          <span>هزینه ارسال پیک اختصاصی</span>
          <span
            v-if="cartStore.deliveryFee === 0"
            class="font-bold text-[var(--color-brand-success)]"
          >
            رایگان
          </span>
          <span v-else class="font-semibold text-[var(--color-text-primary)]">
            {{ formatToman(cartStore.deliveryFee) }}
          </span>
        </div>

        <div class="h-px w-full bg-[var(--color-border-subtle)] my-2"></div>

        <!-- Grand Total -->
        <div class="flex items-center justify-between">
          <span class="text-sm font-bold text-[var(--color-text-primary)]">
            مبلغ نهایی قابل پرداخت
          </span>
          <span class="text-base font-extrabold text-[var(--color-brand-forest)]">
            {{ formatToman(cartStore.grandTotal) }}
          </span>
        </div>

        <!-- Action Button -->
        <button
          type="button"
          @click="goToCheckout"
          class="touch-target mt-3 flex w-full items-center justify-center gap-2 rounded-full bg-[var(--color-brand-forest)] py-3.5 text-sm font-bold text-white shadow-md transition-all hover:bg-[var(--color-brand-forest-light)] active:scale-98"
        >
          <span>تکمیل و پرداخت نهایی</span>
          <ArrowLeft :size="18" class="icon-directional" />
        </button>
      </div>
    </aside>
  </Transition>
</template>
