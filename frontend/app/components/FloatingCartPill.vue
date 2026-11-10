<script setup lang="ts">
import { computed } from 'vue'
import { ArrowLeft } from 'lucide-vue-next'
import { useCartStore } from '~/stores/cart'
import { usePersian } from '~/composables/usePersian'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const cartStore = useCartStore()
const { toPersianDigits, formatToman } = usePersian()

const hasItems = computed(() => cartStore.totalCount > 0)
</script>

<template>
  <!-- Floating Cart Pill (Fixed at bottom-start / bottom-left in RTL) -->
  <Transition
    enter-active-class="transition duration-300 ease-out"
    enter-from-class="transform translate-y-12 opacity-0"
    enter-to-class="transform translate-y-0 opacity-100"
    leave-active-class="transition duration-200 ease-in"
    leave-from-class="transform translate-y-0 opacity-100"
    leave-to-class="transform translate-y-12 opacity-0"
  >
    <div
      v-if="hasItems"
      class="fixed bottom-4 inset-inline-start-4 z-40 md:bottom-6 md:inset-inline-start-6"
    >
      <GooeyButton
        variant="primary"
        class="!h-13 !px-5 text-white shadow-[var(--shadow-pill)]"
        aria-label="مشاهده سبد خرید و تسویه‌حساب"
        @click="cartStore.openCart"
      >
        <!-- Cart Icon & Gold Badge -->
        <div class="relative flex items-center justify-center">
          <div class="flex h-9 w-9 items-center justify-center rounded-full bg-white p-1.5 shadow-xs">
            <img
              src="/svg/cart.svg"
              alt="سبد خرید"
              class="h-5 w-5 object-contain"
            />
          </div>
          <span
            class="absolute -top-1.5 -right-1.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-[var(--color-accent-gold)] px-1 text-[11px] font-bold text-white shadow-xs"
            aria-live="polite"
          >
            {{ toPersianDigits(cartStore.totalCount) }}
          </span>
        </div>

        <!-- Vertical Divider -->
        <div class="h-5 w-px bg-white/20"></div>

        <!-- Cart Total -->
        <div class="flex flex-col text-start">
          <span class="text-[11px] font-medium text-white/80">
            سبد خرید شما
          </span>
          <span class="text-sm font-bold text-white">
            {{ formatToman(cartStore.subtotal) }}
          </span>
        </div>

        <!-- Arrow indicator (Mirrored in RTL) -->
        <div
          class="flex h-7 w-7 items-center justify-center rounded-full bg-white/10 transition-transform group-hover:-translate-x-1 icon-directional"
        >
          <ArrowLeft :size="16" />
        </div>
      </GooeyButton>
    </div>
  </Transition>
</template>
