<script setup lang="ts">
import { Flame, ArrowLeft, Star } from 'lucide-vue-next'
import { usePersian } from '~/composables/usePersian'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const { toPersianDigits } = usePersian()

const scrollToMenu = () => {
  const el = document.getElementById('menu')
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' })
  }
}

const scrollToReservation = () => {
  const el = document.getElementById('reservation')
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' })
  }
}
</script>

<template>
  <section
    id="hero"
    class="relative overflow-hidden pt-4 pb-12 lg:pt-8 lg:pb-20"
    aria-label="بخش معرفی فست‌فودی"
  >
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      
      <div
        class="grid grid-cols-1 items-center gap-8 lg:grid-cols-12 lg:gap-12"
      >
        
        <div class="flex flex-col items-start lg:col-span-7 space-y-6">
          <div class="space-y-3">
            <h1
              class="text-3xl sm:text-4xl lg:text-5xl font-extrabold leading-[1.25] text-[var(--color-brand-forest)] tracking-tight"
            >
              طعم اصیل برگر و پیتزا،
              <span class="block text-[var(--color-text-primary)] font-bold">
                دست‌پخت سرآشپز با مواد ارگانیک
              </span>
            </h1>
            <p
              class="max-w-xl text-sm sm:text-base leading-relaxed text-[var(--color-text-secondary)]"
            >
              در فست‌فودی، فست‌فود را به یک ضیافت سالم و اشتهاآور تبدیل کرده‌ایم. گوشت تازه گوساله، خمیر تخمیر طبیعی ناپلی و سبزیجات روز با سس‌های دست‌ساز بدون نگه‌دارنده.
            </p>
          </div>

          
          <div class="flex flex-wrap items-center gap-3.5 pt-2 w-full sm:w-auto">
            <GooeyButton
              variant="primary"
              size="lg"
              class="w-full sm:w-auto"
              aria-label="مشاهده منو و سفارش آنلاین"
              @click="scrollToMenu"
            >
              <span>مشاهده منو و سفارش</span>
              <ArrowLeft :size="16" class="fine-hover-shift-end transition-transform duration-150 ease-[var(--ease-out)] icon-directional" />
            </GooeyButton>

            <GooeyButton
              variant="secondary"
              size="lg"
              class="w-full sm:w-auto"
              aria-label="رزرو آنلاین میز رستوران"
              @click="scrollToReservation"
            >
              <span>رزرو میز در رستوران</span>
            </GooeyButton>
          </div>

          
          <div
            class="grid grid-cols-3 gap-4 pt-4 border-t border-[var(--color-border-subtle)] w-full max-w-lg"
          >
            <div>
              <span class="block text-lg font-bold text-[var(--color-brand-forest)]">
                {{ toPersianDigits('۱۰۰') }}٪
              </span>
              <span class="text-xs text-[var(--color-text-secondary)]">مواد اولیه روز</span>
            </div>
            <div>
              <span class="block text-lg font-bold text-[var(--color-brand-forest)]">
                {{ toPersianDigits('۲۵') }} دقیقه
              </span>
              <span class="text-xs text-[var(--color-text-secondary)]">میانگین تحویل گرم</span>
            </div>
            <div>
              <span class="block text-lg font-bold text-[var(--color-brand-forest)]">
                {{ toPersianDigits('۴.۹') }} از ۵
              </span>
              <span class="text-xs text-[var(--color-text-secondary)]">رضایت مشتریان</span>
            </div>
          </div>
        </div>

        
        <div class="relative flex items-center justify-center lg:col-span-5">
          
          <div
            class="relative flex h-[340px] w-[340px] sm:h-[420px] sm:w-[420px] items-center justify-center rounded-full bg-[var(--color-surface-ivory)] p-6 shadow-[var(--shadow-lg)]"
          >
            
            <img
              src="/img/placeholder.webp"
              alt="Fastfoody Signature Platter"
              class="fine-hover-rotate h-[280px] w-[280px] sm:h-[350px] sm:w-[350px] rounded-full object-cover shadow-md transition-transform duration-250 ease-[var(--ease-out)]"
            />

            
            <div
              class="absolute -bottom-2 sm:bottom-2 start-2 sm:start-4 flex items-center gap-3 rounded-2xl border border-[var(--color-border-subtle)] bg-white/95 p-3 shadow-[var(--shadow-md)] backdrop-blur-md"
            >
              <div
                class="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)]"
              >
                <Flame :size="20" />
              </div>
              <div>
                <p class="text-xs font-bold text-[var(--color-text-primary)]">
                  پیشنهاد ویژه روز
                </p>
                <p class="text-[11px] font-semibold text-[var(--color-brand-forest)]">
                  اسموکی فورست برگر
                </p>
              </div>
            </div>

            
            <div
              class="absolute -top-2 sm:top-4 end-2 sm:end-4 flex items-center gap-2 rounded-full border border-[var(--color-border-subtle)] bg-white/95 px-3.5 py-1.5 shadow-[var(--shadow-sm)] backdrop-blur-md"
            >
              <Star :size="14" class="fill-[var(--color-accent-gold)] text-[var(--color-accent-gold)]" />
              <span class="text-xs font-bold text-[var(--color-text-primary)]">
                انتخاب محبوب هفته
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

