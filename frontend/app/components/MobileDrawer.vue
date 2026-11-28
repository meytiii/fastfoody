<script setup lang="ts">
import { computed } from 'vue'
import { X, Phone, MapPin, Clock, User, LogOut, ShieldCheck } from 'lucide-vue-next'
import { useUiStore } from '~/stores/ui'
import { useCmsStore } from '~/stores/cms'
import { useAuthStore } from '~/stores/auth'
import { usePersian } from '~/composables/usePersian'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const uiStore = useUiStore()
const cmsStore = useCmsStore()
const authStore = useAuthStore()
const { formatTime, toPersianDigits } = usePersian()

const links = [
  { label: 'صفحه اصلی', href: '/' },
  { label: 'منوی کامل غذاها', href: '/menu' },
  { label: 'گردونه انتخاب غذا', href: '/lucky-wheel' },
  { label: 'سفارش‌های من', href: '/orders' },
  { label: 'حساب کاربری و آدرس‌ها', href: '/account' },
  { label: 'درباره ما', href: '/about' },
]

const brandName = computed(() => cmsStore.headerSection?.restaurant_name || 'فست‌فودی')
const footerAddress = computed(
  () => cmsStore.footerSection?.address || 'تهران، خیابان ولیعصر، نرسیده به پارک وی، پلاک ۱۲۴'
)
const footerPhone = computed(() => cmsStore.footerSection?.phone || '۰۲۱-۲۲۰۰۵۵۸۸')
const workingHours = computed(() => {
  if (!cmsStore.restaurantStatus) return '۱۱:۰۰ تا ۰۱:۰۰'
  return `${formatTime(cmsStore.restaurantStatus.open_time)} الی ${formatTime(cmsStore.restaurantStatus.close_time)}`
})

const navigateToSection = (href: string) => {
  uiStore.closeMobileMenu()
  navigateTo(href)
}

const handleLogout = async () => {
  await authStore.logout()
  uiStore.closeMobileMenu()
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
      v-if="uiStore.isMobileMenuOpen"
      class="fixed inset-0 z-50 bg-[rgba(18,37,29,0.5)] backdrop-blur-xs md:hidden"
      @click="uiStore.closeMobileMenu"
    />
  </Transition>

  <Transition
    enter-active-class="transition-transform duration-280 ease-[var(--ease-drawer)]"
    enter-from-class="translate-x-full"
    enter-to-class="translate-x-0"
    leave-active-class="transition-transform duration-200 ease-[var(--ease-out)]"
    leave-from-class="translate-x-0"
    leave-to-class="translate-x-full"
  >
    <div
      v-if="uiStore.isMobileMenuOpen"
      class="fixed top-0 bottom-0 start-0 z-50 flex w-[300px] flex-col bg-white shadow-[var(--shadow-lg)] md:hidden overscroll-contain"
      role="dialog"
      aria-modal="true"
      aria-label="منوی دسترسی موبایل"
      @keydown.escape="uiStore.closeMobileMenu"
    >
      <div class="flex h-16 items-center justify-between border-b border-[var(--color-border-subtle)] px-5">
        <a
          href="/"
          @click.prevent="navigateToSection('/')"
          class="flex items-center gap-2.5 cursor-pointer"
          :aria-label="brandName"
        >
          <div class="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--color-brand-forest)] text-white">
            <img
              src="/svg/chef.svg"
              :alt="brandName"
              width="20"
              height="20"
              class="h-5 w-5 filter invert brightness-0"
            />
          </div>
          <span class="text-base font-bold text-[var(--color-brand-forest)]">
            {{ brandName }}
          </span>
        </a>

        <button
          type="button"
          @click="uiStore.closeMobileMenu"
          class="touch-target flex h-10 w-10 items-center justify-center rounded-full text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-cream)] active:scale-[0.97] transition-[background-color,transform] duration-150 ease-[var(--ease-out)]"
          aria-label="بستن منو"
        >
          <X :size="20" aria-hidden="true" />
        </button>
      </div>

      <nav class="flex-1 overflow-y-auto px-4 py-5 space-y-5" aria-label="منوی موبایل">
        <div v-if="authStore.isAuthenticated" class="rounded-2xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] p-3.5 flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div class="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--color-brand-forest)] text-white">
              <User :size="16" aria-hidden="true" />
            </div>
            <div class="text-xs">
              <p class="font-bold text-[var(--color-text-primary)]">
                {{ authStore.user?.full_name || 'کاربر فست‌فودی' }}
              </p>
              <p class="text-[var(--color-text-secondary)]">
                <bdi>{{ toPersianDigits(authStore.user?.phone) }}</bdi>
              </p>
            </div>
          </div>
          <button
            type="button"
            @click="handleLogout"
            class="touch-target flex h-9 w-9 items-center justify-center rounded-full text-[var(--color-danger)] hover:bg-white"
            aria-label="خروج از حساب"
          >
            <LogOut :size="16" aria-hidden="true" />
          </button>
        </div>

        <button
          v-else
          type="button"
          @click="() => { uiStore.closeMobileMenu(); authStore.openAuthModal() }"
          class="touch-target flex w-full items-center justify-center gap-2 rounded-2xl border border-[var(--color-brand-forest)] bg-[var(--color-surface-cream)] px-4 py-3 text-sm font-bold text-[var(--color-brand-forest)]"
        >
          <User :size="16" aria-hidden="true" />
          <span>ورود / ثبت‌نام با شماره موبایل</span>
        </button>

        <ul class="space-y-1">
          <li v-for="item in links" :key="item.href">
            <a
              :href="item.href"
              @click.prevent="navigateToSection(item.href)"
              class="flex items-center rounded-xl px-4 py-3 text-sm font-semibold text-[var(--color-text-primary)] transition-colors hover:bg-[var(--color-surface-cream)] hover:text-[var(--color-brand-forest)]"
            >
              {{ item.label }}
            </a>
          </li>
          <li>
            <a
              href="/backoffice"
              @click.prevent="navigateToSection('/backoffice')"
              class="flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-surface-cream)] hover:text-[var(--color-brand-forest)]"
            >
              <ShieldCheck :size="16" aria-hidden="true" />
              <span>پنل مدیریت و آشپزخانه</span>
            </a>
          </li>
        </ul>

        <div class="rounded-2xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] p-4 text-xs text-[var(--color-text-secondary)] space-y-3">
          <div class="flex items-start gap-2.5">
            <MapPin :size="16" aria-hidden="true" class="mt-0.5 text-[var(--color-brand-forest)] shrink-0" />
            <span>{{ footerAddress }}</span>
          </div>
          <div class="flex items-center gap-2.5">
            <Clock :size="16" aria-hidden="true" class="text-[var(--color-brand-forest)] shrink-0" />
            <span>همه‌روزه از <bdi>{{ workingHours }}</bdi></span>
          </div>
          <div class="flex items-center gap-2.5">
            <Phone :size="16" aria-hidden="true" class="text-[var(--color-brand-forest)] shrink-0" />
            <bdi class="font-bold text-[var(--color-text-primary)]">{{ footerPhone }}</bdi>
          </div>
        </div>
      </nav>

      <div class="border-t border-[var(--color-border-subtle)] p-4">
        <GooeyButton
          variant="primary"
          size="md"
          class="w-full"
          aria-label="مشاهده منو و سفارش"
          @click="navigateToSection('/menu')"
        >
          <span>مشاهده منو و سفارش</span>
        </GooeyButton>
      </div>
    </div>
  </Transition>
</template>
