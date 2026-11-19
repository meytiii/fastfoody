<script setup lang="ts">
import { ArrowLeft, Sparkles } from 'lucide-vue-next'
import GooeyButton from '~/components/ui/GooeyButton.vue'

useHead({
  title: 'درباره ما | فست‌فودی',
  meta: [
    {
      name: 'description',
      content: 'آشنایی با فلسفه پخت، مواد اولیه تازه و دست‌ساز رستوران فست‌فودی',
    },
  ],
})

const navigateToMenu = () => {
  navigateTo('/menu')
}
</script>

<template>
  <main class="min-h-screen pt-12 pb-24 px-4 sm:px-6 lg:px-8">
    <div class="mx-auto max-w-4xl">
      <div class="text-center mb-12">
        <h1 class="text-3xl sm:text-4xl lg:text-5xl font-black text-[var(--color-brand-forest)] tracking-tight">
          درباره رستوران فست‌فودی
        </h1>

        <p class="mt-4 text-sm sm:text-base text-[var(--color-text-secondary)] max-w-xl mx-auto leading-relaxed">
          داستان ما از یک باور ساده آغاز شد: فست‌فود می‌تواند سالم، دست‌ساز و سرشار از طعم‌های اصیل باشد.
        </p>
      </div>

      <div class="rounded-3xl border border-[var(--color-border-subtle)] bg-white p-8 sm:p-14 shadow-[var(--shadow-md)] text-center relative overflow-hidden">
        <div class="absolute -top-24 -right-24 w-48 h-48 rounded-full bg-[var(--color-accent-gold)]/10 blur-3xl pointer-events-none" />
        <div class="absolute -bottom-24 -left-24 w-48 h-48 rounded-full bg-[var(--color-brand-forest)]/10 blur-3xl pointer-events-none" />

        <div class="relative z-10 max-w-md mx-auto space-y-6">
          <div class="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-[var(--color-surface-ivory)] text-[var(--color-brand-forest)] shadow-xs">
            <Sparkles :size="36" class="text-[var(--color-accent-gold)]" />
          </div>

          <div class="space-y-2">
            <h2 class="text-xl font-bold text-[var(--color-text-primary)]">
              داستان ما به زودی کامل می‌شود
            </h2>
            <p class="text-xs sm:text-sm text-[var(--color-text-secondary)] leading-relaxed">
              این صفحه به معرفی فلسفه پخت، انتخاب خمیرهای ناپلی با تخمیر ۴۸ ساعته و تیم سرآشپزان فست‌فودی اختصاص دارد و هم‌اکنون در حال آماده‌سازی نهایی است.
            </p>
          </div>

          <div class="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
            <GooeyButton
              variant="primary"
              size="md"
              aria-label="مشاهده منوی غذاها"
              @click="navigateToMenu"
            >
              <span>مشاهده منوی غذاها</span>
              <ArrowLeft :size="16" class="icon-directional" />
            </GooeyButton>

            <NuxtLink
              to="/"
              class="touch-target inline-flex items-center justify-center px-6 py-3 rounded-full text-xs font-bold text-[var(--color-text-secondary)] hover:text-[var(--color-brand-forest)] hover:bg-[var(--color-surface-cream)] transition-colors"
            >
              بازگشت به صفحه اصلی
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>
