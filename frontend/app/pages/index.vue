<script setup lang="ts">
import { ArrowLeft } from 'lucide-vue-next'
import GooeyButton from '~/components/ui/GooeyButton.vue'
import NimbuMirchi from '~/components/ui/NimbuMirchi.vue'

useHead({
  title: 'فست‌فودی | رستوران و کافه غذاهای ارگانیک و دست‌ساز',
  meta: [
    {
      name: 'description',
      content: 'پیتزای ناپلی تنوری، برگرهای دست‌ساز و سالادهای تازه با مواد اولیه روز و طعم اصیل در رستوران فست‌فودی',
    },
  ],
})

const navigateToMenu = () => {
  navigateTo('/menu')
}

const navigateToAbout = () => {
  navigateTo('/about')
}
</script>

<template>
  <main class="w-full px-3 sm:px-6 lg:px-8 pt-1 pb-6">
    <section
      class="relative w-full min-h-[calc(100dvh-5.5rem)] rounded-3xl sm:rounded-[2.5rem] overflow-hidden bg-[#143527] bg-no-repeat bg-cover bg-[position:80%_center] lg:bg-[position:right_center] border border-[#224E3D]/30 shadow-[0_24px_64px_-16px_rgba(20,53,39,0.45)] flex items-center"
      style="background-image: url('/img/homepage.webp');"
      aria-label="بنر معرفی فست‌فودی"
    >
      <div
        class="absolute inset-0 pointer-events-none overflow-hidden opacity-30 mix-blend-screen"
        aria-hidden="true"
      >
        <div
          class="absolute -inset-[10px] filter blur-[14px] will-change-transform [--aurora:repeating-linear-gradient(100deg,rgba(214,168,75,0.35)_10%,rgba(34,78,61,0.25)_20%,rgba(244,239,227,0.3)_30%)] [--white-gradient:repeating-linear-gradient(100deg,rgba(255,255,255,0.08)_0%,transparent_12%)] [background-image:var(--white-gradient),var(--aurora)] [background-size:250%,_150%] animate-aurora"
        />
      </div>

      <div
        class="absolute inset-0 bg-gradient-to-t from-[#143527]/95 via-[#143527]/40 to-transparent lg:hidden pointer-events-none"
        aria-hidden="true"
      />

      <div
        class="absolute inset-0 hidden lg:block bg-gradient-to-r from-[#143527]/50 via-transparent to-transparent pointer-events-none"
        aria-hidden="true"
      />

      <ClientOnly>
        <div class="absolute inset-0 z-20 pointer-events-none">
          <NimbuMirchi class="w-full h-full" />
        </div>
      </ClientOnly>

      <div class="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-0 flex items-center justify-start" style="direction: ltr;">
        <div
          class="w-full max-w-lg lg:max-w-[390px] xl:max-w-[420px] text-right rounded-3xl p-6 sm:p-8 lg:p-0 bg-[#12251D]/85 lg:bg-transparent backdrop-blur-md lg:backdrop-blur-none border border-white/10 lg:border-0 shadow-2xl lg:shadow-none"
          style="direction: rtl;"
        >
          <h1 class="text-3xl sm:text-4xl lg:text-5xl font-black text-white leading-[1.2] tracking-tight">
            فست‌فودی؛
            <span class="block text-[var(--color-accent-gold)] text-2xl sm:text-3xl lg:text-4xl font-extrabold mt-1 sm:mt-2">
              ضیافت طعم‌های دست‌ساز
            </span>
          </h1>

          <p class="mt-4 text-xs sm:text-sm lg:text-base text-[#F4EFE3]/90 leading-relaxed max-w-md">
            در فست‌فودی، پیتزای تنوری ناپلی و برگرهای دست‌ساز با خمیر تخمیر طبیعی ۴۸ ساعته، پنیر تازه و سس‌های روز بدون مواد افزودنی آماده می‌شوند. طعمی خالص از دل آتش و نان تازه.
          </p>

          <div class="mt-7 sm:mt-8 flex flex-wrap items-center gap-3.5 pt-1">
            <GooeyButton
              variant="gold"
              size="lg"
              class="hero-btn-enter-1 shadow-[0_4px_16px_rgba(214,168,75,0.28)]"
              aria-label="مشاهده منوی کامل غذاها"
              @click="navigateToMenu"
            >
              <span>مشاهده منو</span>
              <span class="inline-flex items-center transition-transform duration-200 ease-out group-hover:-translate-x-1.5 will-change-transform">
                <ArrowLeft :size="16" class="icon-directional" />
              </span>
            </GooeyButton>

            <GooeyButton
              variant="outline"
              size="lg"
              class="hero-btn-enter-2 !bg-white/10 !text-white !border-white/30 hover:!bg-white/20 hover:!border-white/50 backdrop-blur-xs"
              aria-label="درباره رستوران فست‌فودی"
              @click="navigateToAbout"
            >
              <span>درباره ما</span>
            </GooeyButton>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>
