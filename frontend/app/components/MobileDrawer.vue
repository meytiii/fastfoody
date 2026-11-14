<script setup lang="ts">
import { X, Phone, MapPin, Clock } from 'lucide-vue-next'
import { useUiStore } from '~/stores/ui'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const uiStore = useUiStore()
const route = useRoute()

// Removed 'صفحه اصلی' link; brand logo handles navigation to top of homepage
const links = [
  { label: 'منوی کامل غذاها', href: '/#menu' },
  { label: 'پیشنهادهای ویژه سرآشپز', href: '/#specials' },
  { label: 'رزرو آنلاین میز', href: '/#reservation' },
  { label: 'نظرات مشتریان', href: '/#testimonials' },
]

const navigateToSection = (href: string) => {
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
  <Transition
    enter-active-class="transition-opacity duration-300"
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
    enter-active-class="transition-transform duration-300 ease-out"
    enter-from-class="translate-x-full"
    enter-to-class="translate-x-0"
    leave-active-class="transition-transform duration-200 ease-in"
    leave-from-class="translate-x-0"
    leave-to-class="translate-x-full"
  >
    <div
      v-if="uiStore.isMobileMenuOpen"
      class="fixed top-0 bottom-0 inset-inline-end-0 z-50 flex w-[300px] flex-col bg-white shadow-[var(--shadow-lg)] md:hidden overscroll-contain"
      role="dialog"
      aria-label="منوی دسترسی موبایل"
    >
      <!-- Header with Brand Logo Clickable to Top -->
      <div
        class="flex h-16 items-center justify-between border-b border-[var(--color-border-subtle)] px-5"
      >
        <a
          href="/"
          @click.prevent="goToTop"
          class="flex items-center gap-2.5 cursor-pointer"
          aria-label="رفتن به بالای صفحه اصلی"
        >
          <div
            class="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--color-brand-forest)] text-white"
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

        <button
          type="button"
          @click="uiStore.closeMobileMenu"
          class="touch-target flex h-10 w-10 items-center justify-center rounded-full text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-cream)] active:scale-95"
          aria-label="بستن منو"
        >
          <X :size="20" />
        </button>
      </div>

      <!-- Links List -->
      <nav class="flex-1 overflow-y-auto px-4 py-6" aria-label="منوی موبایل">
        <ul class="space-y-2">
          <li v-for="item in links" :key="item.href">
            <a
              :href="item.href"
              @click.prevent="navigateToSection(item.href)"
              class="flex items-center rounded-xl px-4 py-3 text-base font-semibold text-[var(--color-text-primary)] transition-colors hover:bg-[var(--color-surface-cream)] hover:text-[var(--color-brand-forest)]"
            >
              {{ item.label }}
            </a>
          </li>
        </ul>

        <!-- Fast Contact Info -->
        <div
          class="mt-8 rounded-2xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] p-4 text-xs text-[var(--color-text-secondary)] space-y-3"
        >
          <div class="flex items-start gap-2.5">
            <MapPin :size="16" class="mt-0.5 text-[var(--color-brand-forest)] shrink-0" />
            <span>تهران، خیابان ولیعصر، نرسیده به پارک وی، پلاک ۱۲۴</span>
          </div>
          <div class="flex items-center gap-2.5">
            <Clock :size="16" class="text-[var(--color-brand-forest)] shrink-0" />
            <span>همه‌روزه از ۱۱:۳۰ الی ۲۳:۴۵</span>
          </div>
          <div class="flex items-center gap-2.5">
            <Phone :size="16" class="text-[var(--color-brand-forest)] shrink-0" />
            <bdi class="font-bold text-[var(--color-text-primary)]">۰۲۱-۲۲۰۰۵۵۸۸</bdi>
          </div>
        </div>
      </nav>

      <!-- Bottom Order CTA -->
      <div class="border-t border-[var(--color-border-subtle)] p-4">
        <GooeyButton
          variant="primary"
          size="md"
          class="w-full"
          aria-label="مشاهده منو و سفارش"
          @click="navigateToSection('/#menu')"
        >
          <span>مشاهده منو و سفارش</span>
        </GooeyButton>
      </div>
    </div>
  </Transition>
</template>
