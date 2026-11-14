<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue'
import {
  Search,
  Menu as MenuIcon,
  UtensilsCrossed,
  ChefHat,
  CalendarCheck,
  MessageSquareQuote,
} from 'lucide-vue-next'
import { useCartStore } from '~/stores/cart'
import { useUiStore } from '~/stores/ui'
import { usePersian } from '~/composables/usePersian'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const cartStore = useCartStore()
const uiStore = useUiStore()
const { toPersianDigits, formatToman } = usePersian()
const route = useRoute()

const navLinks = [
  { label: 'منوی غذا', href: '/#menu', id: 'menu', icon: UtensilsCrossed },
  { label: 'پیشنهاد سرآشپز', href: '/#specials', id: 'specials', icon: ChefHat },
  { label: 'رزرو میز', href: '/#reservation', id: 'reservation', icon: CalendarCheck },
  { label: 'نظرات میهمانان', href: '/#testimonials', id: 'testimonials', icon: MessageSquareQuote },
]

const activeHref = ref('/#menu')
const navRef = ref<HTMLElement | null>(null)
const linkRefs = new Map<string, HTMLElement>()
let isClickScrolling = false
let scrollTimeout: ReturnType<typeof setTimeout> | null = null

const setLinkRef = (el: any, href: string) => {
  if (el) {
    linkRefs.set(href, el as HTMLElement)
  } else {
    linkRefs.delete(href)
  }
}

const lampStyle = reactive({
  left: 0,
  top: 0,
  width: 0,
  height: 0,
  opacity: 0,
})
const lampReady = ref(false)

const updateLampPosition = () => {
  if (!activeHref.value || !navRef.value) {
    lampStyle.opacity = 0
    return
  }
  const el = linkRefs.get(activeHref.value)
  if (!el) {
    lampStyle.opacity = 0
    return
  }

  const navRect = navRef.value.getBoundingClientRect()
  const elRect = el.getBoundingClientRect()

  lampStyle.left = elRect.left - navRect.left
  lampStyle.top = elRect.top - navRect.top
  lampStyle.width = elRect.width
  lampStyle.height = elRect.height
  lampStyle.opacity = 1
  lampReady.value = true
}

const scrollTo = (href: string) => {
  uiStore.closeMobileMenu()
  activeHref.value = href
  nextTick(() => updateLampPosition())

  if (href.startsWith('/#')) {
    const id = href.replace('/#', '')
    const el = document.getElementById(id)
    if (el) {
      isClickScrolling = true
      if (scrollTimeout) clearTimeout(scrollTimeout)
      el.scrollIntoView({ behavior: 'smooth' })
      scrollTimeout = setTimeout(() => {
        isClickScrolling = false
        updateLampPosition()
      }, 750)
    }
  }
}

const goToTop = () => {
  uiStore.closeMobileMenu()
  activeHref.value = '/#menu'
  nextTick(() => updateLampPosition())
  if (route.path === '/') {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } else {
    navigateTo('/')
  }
}

const onScroll = () => {
  if (isClickScrolling || route.path !== '/') return

  const scrollY = window.scrollY
  const offset = 220

  if (scrollY < 260) {
    if (activeHref.value !== '/#menu') {
      activeHref.value = '/#menu'
      updateLampPosition()
    }
    return
  }

  const sections = ['testimonials', 'reservation', 'specials', 'menu']
  for (const id of sections) {
    const el = document.getElementById(id)
    if (el) {
      const top = el.offsetTop - offset
      if (scrollY >= top) {
        const targetHref = `/#${id}`
        if (activeHref.value !== targetHref) {
          activeHref.value = targetHref
          updateLampPosition()
        }
        return
      }
    }
  }
}

watch(
  () => route.path,
  (newPath) => {
    if (newPath !== '/') {
      lampStyle.opacity = 0
    } else {
      nextTick(() => {
        updateLampPosition()
      })
    }
  }
)

onMounted(() => {
  nextTick(() => {
    updateLampPosition()
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', updateLampPosition, { passive: true })
    if (document.fonts) {
      document.fonts.ready.then(() => updateLampPosition())
    }
  })
})

onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('resize', updateLampPosition)
  if (scrollTimeout) clearTimeout(scrollTimeout)
})
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

      <!-- Center Navigation Links with Tubelight Effect & Spring Animation -->
      <nav
        ref="navRef"
        class="relative flex items-center gap-1 lg:gap-1.5"
        role="tablist"
        aria-label="ناوبری اصلی"
      >
        <!-- Sliding Tubelight Indicator -->
        <div
          v-if="lampReady && route.path === '/'"
          class="pointer-events-none absolute z-0 rounded-full transition-all duration-300 ease-[cubic-bezier(0.25,1,0.5,1)]"
          :style="{
            left: `${lampStyle.left}px`,
            top: `${lampStyle.top}px`,
            width: `${lampStyle.width}px`,
            height: `${lampStyle.height}px`,
            opacity: lampStyle.opacity,
          }"
          aria-hidden="true"
        >
          <!-- Active Pill Background Tint -->
          <div class="h-full w-full rounded-full bg-[var(--color-brand-forest)]/[0.08]" />

          <!-- Tubelight Fixture & Glowing Multi-layer Ambient Beams -->
          <div
            class="absolute -top-1.5 left-1/2 -translate-x-1/2 w-8 h-1 rounded-t-full bg-[var(--color-brand-forest)] shadow-[0_0_8px_rgba(24,58,45,0.45)]"
          >
            <!-- Wide Soft Glow -->
            <div class="absolute -top-2 -left-2 w-12 h-6 rounded-full bg-[var(--color-brand-forest)]/25 blur-md pointer-events-none" />
            <!-- Muted Gold Ambient Light -->
            <div class="absolute -top-1 left-0 w-8 h-6 rounded-full bg-[var(--color-accent-gold)]/30 blur-md pointer-events-none" />
            <!-- Intense Lamp Core Spark -->
            <div class="absolute top-0 left-2 w-4 h-4 rounded-full bg-[var(--color-brand-forest)]/40 blur-xs pointer-events-none" />
          </div>
        </div>

        <!-- Navigation Buttons -->
        <a
          v-for="link in navLinks"
          :key="link.href"
          :ref="(el) => setLinkRef(el, link.href)"
          :href="link.href"
          role="tab"
          :aria-selected="activeHref === link.href"
          @click.prevent="scrollTo(link.href)"
          class="relative z-10 flex items-center gap-1.5 px-3.5 py-1.5 text-sm font-semibold transition-colors duration-200 rounded-full cursor-pointer select-none"
          :class="
            activeHref === link.href
              ? 'text-[var(--color-brand-forest)]'
              : 'text-[var(--color-text-secondary)] hover:text-[var(--color-brand-forest)] hover:bg-[var(--color-surface-cream)]/70'
          "
        >
          <component
            :is="link.icon"
            :size="15"
            :stroke-width="2.2"
            class="shrink-0 transition-transform duration-200"
            :class="activeHref === link.href ? 'scale-105 text-[var(--color-brand-forest)]' : 'opacity-70'"
          />
          <span>{{ link.label }}</span>
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
        <GooeyButton
          variant="primary"
          size="sm"
          aria-label="سفارش آنلاین"
          class="ps-3.5 pe-4.5"
          @click="scrollTo('/#menu')"
        >
          <img
            src="/svg/order.svg"
            alt="سفارش"
            class="h-5 w-5 object-contain"
          />
          <span>سفارش</span>
        </GooeyButton>
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
