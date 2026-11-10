<script setup lang="ts">
import { Sparkles, ArrowLeft, Star, ShieldCheck, Heart } from 'lucide-vue-next'
import { usePersian } from '~/composables/usePersian'

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
      <!-- Split Container -->
      <div
        class="grid grid-cols-1 items-center gap-8 lg:grid-cols-12 lg:gap-12"
      >
        <!-- Content Column (Right side in RTL, cols 7) -->
        <div class="flex flex-col items-start lg:col-span-7 space-y-6">
          <!-- Social Proof Tag -->
          <div
            class="inline-flex items-center gap-2.5 rounded-full border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] px-4 py-1.5 shadow-2xs"
          >
            <div class="flex -space-x-1.5 space-x-reverse">
              <span class="inline-block h-6 w-6 rounded-full bg-[var(--color-brand-forest)] text-[10px] font-bold text-white flex items-center justify-center ring-2 ring-white">
                م
              </span>
              <span class="inline-block h-6 w-6 rounded-full bg-[var(--color-accent-gold)] text-[10px] font-bold text-white flex items-center justify-center ring-2 ring-white">
                س
              </span>
              <span class="inline-block h-6 w-6 rounded-full bg-[var(--color-brand-forest-light)] text-[10px] font-bold text-white flex items-center justify-center ring-2 ring-white">
                ع
              </span>
            </div>
            <div class="flex items-center gap-1">
              <Star :size="13" class="fill-[var(--color-accent-gold)] text-[var(--color-accent-gold)]" />
              <span class="text-xs font-bold text-[var(--color-text-primary)]">
                +{{ toPersianDigits('۳۵۰۰') }} نظر رضایت‌بخش
              </span>
            </div>
          </div>

          <!-- Main Headline -->
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

          <!-- CTA Actions -->
          <div class="flex flex-wrap items-center gap-3.5 pt-2 w-full sm:w-auto">
            <button
              type="button"
              @click="scrollToMenu"
              class="touch-target group flex items-center justify-center gap-2 rounded-full bg-[var(--color-brand-forest)] px-7 py-3.5 text-sm font-bold text-white shadow-md transition-all hover:bg-[var(--color-brand-forest-light)] active:scale-95 w-full sm:w-auto"
            >
              <span>مشاهده منو و سفارش</span>
              <ArrowLeft :size="16" class="transition-transform group-hover:-translate-x-1 icon-directional" />
            </button>

            <button
              type="button"
              @click="scrollToReservation"
              class="touch-target flex items-center justify-center gap-2 rounded-full border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] px-6 py-3.5 text-sm font-bold text-[var(--color-text-primary)] transition-all hover:border-[var(--color-brand-forest)] hover:bg-[var(--color-surface-ivory)] active:scale-95 w-full sm:w-auto"
            >
              <span>رزرو میز در رستوران</span>
            </button>
          </div>

          <!-- Trust Badges -->
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

        <!-- Visual Column (Left side in RTL, cols 5) -->
        <div class="relative flex items-center justify-center lg:col-span-5">
          <!-- Soft Organic Ivory Mound -->
          <div
            class="relative flex h-[340px] w-[340px] sm:h-[420px] sm:w-[420px] items-center justify-center rounded-full bg-[var(--color-surface-ivory)] p-6 shadow-[var(--shadow-lg)]"
          >
            <!-- Circular Food Platter -->
            <img
              src="/img/placeholder.webp"
              alt="Fastfoody Signature Platter"
              class="h-[280px] w-[280px] sm:h-[350px] sm:w-[350px] rounded-full object-cover shadow-md transition-transform duration-700 hover:rotate-6"
            />

            <!-- Floating Special Dish Pill -->
            <div
              class="absolute -bottom-2 sm:bottom-2 inset-inline-start-2 sm:inset-inline-start-4 flex items-center gap-3 rounded-2xl border border-[var(--color-border-subtle)] bg-white/95 p-3 shadow-[var(--shadow-md)] backdrop-blur-md"
            >
              <div
                class="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)]"
              >
                <Sparkles :size="20" />
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

            <!-- Floating Top Rating Pill -->
            <div
              class="absolute -top-2 sm:top-4 inset-inline-end-2 sm:inset-inline-end-4 flex items-center gap-2 rounded-full border border-[var(--color-border-subtle)] bg-white/95 px-3.5 py-1.5 shadow-[var(--shadow-sm)] backdrop-blur-md"
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
