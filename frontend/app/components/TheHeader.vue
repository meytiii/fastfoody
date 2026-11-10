<script setup lang="ts">
import { computed } from 'vue'
import {
  Search,
  Menu as MenuIcon,
  X,
  PhoneCall,
} from 'lucide-vue-next'
import { useCartStore } from '~/stores/cart'
import { useUiStore } from '~/stores/ui'
import { usePersian } from '~/composables/usePersian'

const cartStore = useCartStore()
const uiStore = useUiStore()
const { toPersianDigits, formatToman } = usePersian()
const route = useRoute()

// Removed 'صفحه اصلی' button from navbar links; clicking brand logo handles top of homepage
const navLinks = [
  { label: 'منوی غذا', href: '/#menu' },
  { label: 'پیشنهاد سرآشپز', href: '/#specials' },
  { label: 'رزرو میز', href: '/#reservation' },
  { label: 'نظرات میهمانان', href: '/#testimonials' },
]

const scrollTo = (href: string) => {
  uiStore.closeMobileMenu()
  if (href.startsWith('/#')) {
    const id = href.replace('/#', '')
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' })
    }
  }
}

const goToTop = () => {
  uiStore.closeMobileMenu()
  if (route.path === '/') {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } else {
    navigateTo('/')
  }
}
</script>

<template>
  <!-- Desktop Floating Island Header -->
  <header
    class="sticky top-4 z-50 hidden w-full px-4 md:block transition-all duration-300"
    role="banner"
  >
    <div
      class="mx-auto flex h-16 max-w-5xl items-center justify-between rounded-full border border-[var(--color-border-subtle)] bg-white/92 px-6 shadow-[var(--shadow-md)] backdrop-blur-md"
    >
      <!-- Brand Logo & Name (Clicking scrolls to top of homepage) -->
      <a
        href="/"
        @click.prevent="goToTop"
        class="group flex items-center gap-3 transition-transform active:scale-95 cursor-pointer"
        aria-label="رفتن به بالای صفحه اصلی فست‌فودی"
      >
        <div
          class="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--color-brand-forest)] text-white shadow-sm transition-colors group-hover:bg-[var(--color-brand-forest-light)]"
        >
          <img
            src="/svg/chef.svg"
            alt="Fastfoody Chef Logo"
            class="h-6 w-6 filter invert brightness-0"
          />
        </div>
        <div class="flex flex-col">
          <span
            class="text-lg font-bold tracking-tight text-[var(--color-brand-forest)]"
          >
            فست‌فودی
          </span>
          <span
            class="text-[11px] font-medium text-[var(--color-text-secondary)]"
          >
            طعم اصیل و ارگانیک
          </span>
        </div>
      </a>

      <!-- Center Navigation Links -->
      <nav class="flex items-center gap-1 lg:gap-2" aria-label="ناوبری اصلی">
        <a
          v-for="link in navLinks"
          :key="link.href"
          :href="link.href"
          @click.prevent="scrollTo(link.href)"
          class="relative px-3.5 py-1.5 text-sm font-medium text-[var(--color-text-primary)] transition-colors hover:text-[var(--color-brand-forest)] rounded-full hover:bg-[var(--color-surface-cream)]"
        >
          {{ link.label }}
        </a>
      </nav>

      <!-- Left Actions (Search, Cart, Order CTA) -->
      <div class="flex items-center gap-2.5">
        <!-- Search Trigger -->
        <button
          type="button"
          @click="uiStore.toggleSearch"
          class="touch-target flex h-10 w-10 items-center justify-center rounded-full border border-[var(--color-border-subtle)] text-[var(--color-text-primary)] transition-all hover:border-[var(--color-brand-forest)] hover:bg-[var(--color-surface-cream)] active:scale-95"
          aria-label="جستجوی غذاها"
        >
          <Search :size="18" :stroke-width="1.75" />
        </button>

        <!-- Cart Trigger Button using cart.svg with project color palette -->
        <button
          type="button"
          @click="cartStore.toggleCart"
          class="touch-target relative flex h-10 items-center gap-2 rounded-full border border-[var(--color-border-subtle)] bg-white px-3.5 text-sm font-medium text-[var(--color-text-primary)] shadow-sm transition-all hover:border-[var(--color-brand-forest)] hover:bg-[var(--color-surface-cream)] active:scale-95"
          aria-label="مشاهده سبد خرید"
        >
          <div class="relative flex items-center justify-center">
            <img
              src="/svg/cart.svg"
              alt="سبد خرید"
              class="h-5 w-5 object-contain"
            />
            <span
              v-if="cartStore.totalCount > 0"
              class="absolute -top-2.5 -right-2.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-[var(--color-accent-gold)] px-1 text-[11px] font-bold text-white shadow-xs"
              aria-live="polite"
            >
              {{ toPersianDigits(cartStore.totalCount) }}
            </span>
          </div>
          <span v-if="cartStore.subtotal > 0" class="hidden font-bold lg:inline">
            {{ formatToman(cartStore.subtotal) }}
          </span>
          <span v-else class="text-xs text-[var(--color-text-secondary)]">
            سبد خرید
          </span>
        </button>

        <!-- Order Button using order.svg with text "سفارش" -->
        <button
          type="button"
          @click="scrollTo('/#menu')"
          class="touch-target inline-flex items-center gap-2 rounded-full bg-[var(--color-brand-forest)] ps-3 pe-4 py-2 text-sm font-semibold text-white shadow-sm transition-all hover:bg-[var(--color-brand-forest-light)] active:scale-95"
          aria-label="سفارش آنلاین"
        >
          <img
            src="/svg/order.svg"
            alt="سفارش"
            class="h-5 w-5 object-contain"
          />
          <span>سفارش</span>
        </button>
      </div>
    </div>
  </header>

  <!-- Mobile Top Bar -->
  <header
    class="sticky top-0 z-40 flex h-14 w-full items-center justify-between border-b border-[var(--color-border-subtle)] bg-white/95 px-4 backdrop-blur-md md:hidden"
    role="banner"
  >
    <!-- Hamburger Button -->
    <button
      type="button"
      @click="uiStore.toggleMobileMenu"
      class="touch-target flex h-10 w-10 items-center justify-center rounded-full text-[var(--color-text-primary)] active:bg-[var(--color-surface-cream)]"
      aria-label="باز کردن منوی موبایل"
    >
      <MenuIcon :size="22" :stroke-width="1.75" />
    </button>

    <!-- Centered Brand Logo (Clicking scrolls to top) -->
    <a
      href="/"
      @click.prevent="goToTop"
      class="flex items-center gap-2 cursor-pointer"
      aria-label="فست‌فودی"
    >
      <div
        class="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-brand-forest)] text-white"
      >
        <img
          src="/svg/chef.svg"
          alt="Fastfoody"
          class="h-5 w-5 filter invert brightness-0"
        />
      </div>
      <span class="text-base font-bold text-[var(--color-brand-forest)]">
        فست‌فودی
      </span>
    </a>

    <!-- Search Button on Mobile -->
    <button
      type="button"
      @click="uiStore.toggleSearch"
      class="touch-target flex h-10 w-10 items-center justify-center rounded-full text-[var(--color-text-primary)] active:bg-[var(--color-surface-cream)]"
      aria-label="جستجو"
    >
      <Search :size="20" :stroke-width="1.75" />
    </button>
  </header>
</template>
