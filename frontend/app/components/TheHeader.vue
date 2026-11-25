<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import {
  Search,
  Menu as MenuIcon,
  ChefHat,
  ReceiptText,
  User,
} from 'lucide-vue-next'
import { useCartStore } from '~/stores/cart'
import { useUiStore } from '~/stores/ui'
import { useCmsStore } from '~/stores/cms'
import { useAuthStore } from '~/stores/auth'
import { usePersian } from '~/composables/usePersian'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const cartStore = useCartStore()
const uiStore = useUiStore()
const cmsStore = useCmsStore()
const authStore = useAuthStore()
const { toPersianDigits, formatToman } = usePersian()
const route = useRoute()

interface NavLinkItem {
  label: string
  href: string
  id: string
  icon?: any
  svg?: string
}

const navLinks: NavLinkItem[] = [
  { label: 'صفحه اصلی', href: '/', id: 'home', svg: '/svg/home.svg' },
  { label: 'منوی غذا', href: '/menu', id: 'menu', svg: '/svg/knife_fork.svg' },
  { label: 'گردونه شانس', href: '/lucky-wheel', id: 'lucky-wheel', svg: '/svg/lucky_wheel.svg' },
  { label: 'سفارش‌ها', href: '/orders', id: 'orders', icon: ReceiptText },
  { label: 'درباره ما', href: '/about', id: 'about', icon: ChefHat },
]

const brandName = computed(() => cmsStore.headerSection?.restaurant_name || 'فست‌فودی')
const brandTagline = computed(() => cmsStore.headerSection?.tagline || 'طعم اصیل و ارگانیک')
const brandLogo = computed(() => cmsStore.headerSection?.logo_url || '/svg/chef.svg')

const activeHref = ref(route.path)
const navRef = ref<HTMLElement | null>(null)
const linkRefs = new Map<string, HTMLElement>()

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

const handleNavClick = (href: string) => {
  uiStore.closeMobileMenu()
  activeHref.value = href
  nextTick(() => updateLampPosition())
  navigateTo(href)
}

const goToTop = () => {
  uiStore.closeMobileMenu()
  activeHref.value = '/'
  nextTick(() => updateLampPosition())
  navigateTo('/')
}

watch(
  () => route.path,
  (newPath) => {
    if (newPath.startsWith('/products')) {
      activeHref.value = '/menu'
    } else if (newPath.startsWith('/orders')) {
      activeHref.value = '/orders'
    } else {
      activeHref.value = newPath
    }
    nextTick(() => updateLampPosition())
  },
  { immediate: true }
)

onMounted(() => {
  nextTick(() => {
    updateLampPosition()
    window.addEventListener('resize', updateLampPosition, { passive: true })
    if (document.fonts) {
      document.fonts.ready.then(() => updateLampPosition())
    }
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', updateLampPosition)
})
</script>

<template>
  <header
    class="no-print sticky top-0 z-40 w-full transition-all duration-300 md:top-4 md:z-50"
    role="banner"
  >
    <div class="hidden w-full px-4 md:block">
      <div
        class="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 rounded-full border border-[var(--color-border-subtle)] bg-white/94 px-5 shadow-[var(--shadow-md)] backdrop-blur-md"
      >
      <a
        href="/"
        @click.prevent="goToTop"
        class="group flex items-center gap-3 transition-transform active:scale-95 cursor-pointer shrink-0"
        aria-label="صفحه اصلی فست‌فودی"
      >
        <div
          class="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--color-brand-forest)] text-white shadow-sm transition-colors group-hover:bg-[var(--color-brand-forest-light)]"
        >
          <img
            :src="brandLogo"
            :alt="brandName"
            width="24"
            height="24"
            class="h-6 w-6 filter invert brightness-0 object-contain"
          />
        </div>
        <div class="flex flex-col">
          <span class="text-base font-bold tracking-tight text-[var(--color-brand-forest)]">
            {{ brandName }}
          </span>
          <span class="text-[11px] font-medium text-[var(--color-text-secondary)]">
            {{ brandTagline }}
          </span>
        </div>
      </a>

      <nav
        ref="navRef"
        class="relative flex items-center gap-0.5 lg:gap-1"
        aria-label="ناوبری اصلی"
      >
        <div
          v-if="lampReady"
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
          <div class="h-full w-full rounded-full bg-[var(--color-brand-forest)]/[0.08]" />
          <div
            class="absolute -top-1.5 left-1/2 -translate-x-1/2 w-8 h-1 rounded-t-full bg-[var(--color-brand-forest)]"
          />
        </div>

        <a
          v-for="link in navLinks"
          :key="link.href"
          :ref="(el) => setLinkRef(el, link.href)"
          :href="link.href"
          :aria-current="activeHref === link.href ? 'page' : undefined"
          @click.prevent="handleNavClick(link.href)"
          class="relative z-10 flex items-center gap-1.5 px-3 py-1.5 text-xs lg:text-sm font-semibold transition-colors duration-200 rounded-full cursor-pointer select-none whitespace-nowrap group"
          :class="
            activeHref === link.href
              ? 'text-[var(--color-brand-forest)]'
              : 'text-[var(--color-text-secondary)] hover:text-[var(--color-brand-forest)] hover:bg-[var(--color-surface-cream)]/70'
          "
        >
          <img
            v-if="link.svg"
            :src="link.svg"
            alt=""
            width="18"
            height="18"
            aria-hidden="true"
            class="w-[18px] h-[18px] shrink-0 transition-all duration-200 object-contain"
            :class="activeHref === link.href ? 'scale-105 opacity-100' : 'opacity-70 group-hover:opacity-100'"
          />
          <component
            :is="link.icon"
            v-else-if="link.icon"
            :size="15"
            :stroke-width="2"
            aria-hidden="true"
            class="shrink-0 transition-transform duration-200"
            :class="activeHref === link.href ? 'scale-105 text-[var(--color-brand-forest)]' : 'opacity-70'"
          />
          <span>{{ link.label }}</span>
        </a>
      </nav>

      <div class="flex items-center gap-2 shrink-0">
        <button
          type="button"
          @click="uiStore.toggleSearch"
          class="touch-target flex h-10 w-10 items-center justify-center rounded-full border border-[var(--color-border-subtle)] text-[var(--color-text-primary)] transition-colors hover:border-[var(--color-brand-forest)] hover:bg-[var(--color-surface-cream)] active:scale-95"
          aria-label="جستجوی غذاها"
        >
          <Search :size="18" :stroke-width="1.75" aria-hidden="true" />
        </button>

        <NuxtLink
          v-if="authStore.isAuthenticated"
          to="/account"
          class="touch-target flex h-10 items-center gap-1.5 rounded-full border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] px-3 text-xs font-bold text-[var(--color-brand-forest)] hover:border-[var(--color-brand-forest)] whitespace-nowrap"
          aria-label="حساب کاربری و آدرس‌ها"
        >
          <User :size="15" aria-hidden="true" />
          <span class="hidden xl:inline">{{ authStore.user?.full_name || toPersianDigits(authStore.user?.phone) }}</span>
        </NuxtLink>

        <button
          v-else
          type="button"
          @click="authStore.openAuthModal()"
          class="touch-target flex h-10 items-center gap-1.5 rounded-full border border-[var(--color-border-subtle)] bg-white px-3 text-xs font-bold text-[var(--color-text-primary)] hover:border-[var(--color-brand-forest)] hover:bg-[var(--color-surface-cream)] whitespace-nowrap"
        >
          <User :size="15" aria-hidden="true" />
          <span>ورود</span>
        </button>

        <button
          type="button"
          @click="cartStore.toggleCart"
          class="touch-target group relative flex h-10 items-center gap-2 rounded-full border border-[var(--color-border-subtle)] bg-white px-3.5 text-xs font-medium text-[var(--color-text-primary)] shadow-sm transition-colors hover:border-[var(--color-brand-forest)] hover:bg-[var(--color-surface-cream)] active:scale-95 select-none whitespace-nowrap"
          aria-label="مشاهده سبد خرید"
        >
          <div class="relative flex items-center justify-center">
            <img
              src="/svg/cart.svg"
              alt=""
              width="20"
              height="20"
              aria-hidden="true"
              class="h-5 w-5 object-contain"
            />
            <span
              v-if="cartStore.totalCount > 0"
              :key="cartStore.totalCount"
              class="nav-cart-badge absolute -top-2.5 -right-2.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-[var(--color-brand-forest)] px-1 text-[11px] font-bold text-white shadow-xs"
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

        <GooeyButton
          variant="primary"
          size="sm"
          aria-label="سفارش آنلاین"
          class="ps-3.5 pe-4 whitespace-nowrap"
          @click="handleNavClick('/menu')"
        >
          <img
            src="/svg/order.svg"
            alt=""
            width="18"
            height="18"
            aria-hidden="true"
            class="h-4.5 w-4.5 object-contain"
          />
          <span>سفارش</span>
        </GooeyButton>
      </div>
      </div>
    </div>

    <div
      class="flex h-14 w-full items-center justify-between border-b border-[var(--color-border-subtle)] bg-white/95 px-4 backdrop-blur-md md:hidden"
    >
    <button
      type="button"
      @click="uiStore.toggleMobileMenu"
      class="touch-target flex h-11 items-center gap-1.5 rounded-full px-2 text-[var(--color-text-primary)] active:bg-[var(--color-surface-cream)]"
      aria-label="باز کردن منوی موبایل"
    >
      <MenuIcon :size="20" :stroke-width="1.75" aria-hidden="true" />
      <span class="text-xs font-bold">منو</span>
    </button>

    <a
      href="/"
      @click.prevent="goToTop"
      class="flex items-center gap-2 cursor-pointer"
      :aria-label="brandName"
    >
      <div
        class="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-brand-forest)] text-white"
      >
        <img
          :src="brandLogo"
          :alt="brandName"
          width="20"
          height="20"
          class="h-5 w-5 filter invert brightness-0 object-contain"
        />
      </div>
      <span class="text-base font-bold text-[var(--color-brand-forest)]">
        {{ brandName }}
      </span>
    </a>

    <div class="flex items-center gap-1">
      <button
        type="button"
        @click="uiStore.toggleSearch"
        class="touch-target flex h-10 w-10 items-center justify-center rounded-full text-[var(--color-text-primary)] active:bg-[var(--color-surface-cream)]"
        aria-label="جستجو"
      >
        <Search :size="20" :stroke-width="1.75" aria-hidden="true" />
      </button>

      <button
        type="button"
        @click="authStore.isAuthenticated ? navigateTo('/account') : authStore.openAuthModal()"
        class="touch-target flex h-10 w-10 items-center justify-center rounded-full text-[var(--color-text-primary)] active:bg-[var(--color-surface-cream)]"
        :aria-label="authStore.isAuthenticated ? 'حساب کاربری' : 'ورود'"
      >
        <User :size="20" :stroke-width="1.75" aria-hidden="true" />
      </button>
    </div>
    </div>
  </header>
</template>
