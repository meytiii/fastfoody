<script setup lang="ts">
import { computed } from 'vue'
import { ArrowLeft, Clock } from 'lucide-vue-next'
import { useCmsStore } from '~/stores/cms'
import { usePersian } from '~/composables/usePersian'
import GooeyButton from '~/components/ui/GooeyButton.vue'
import NimbuMirchi from '~/components/ui/NimbuMirchi.vue'

const cmsStore = useCmsStore()
const { formatTime } = usePersian()

const heroTitle = computed(
  () => cmsStore.heroSection?.title || 'فست‌فودی؛ ضیافت طعم‌های دست‌ساز'
)
const heroSubtitle = computed(
  () =>
    cmsStore.heroSection?.subtitle ||
    'در فست‌فودی، پیتزای تنوری ناپلی و برگرهای دست‌ساز با خمیر تخمیر طبیعی ۴۸ ساعته، پنیر تازه و سس‌های روز بدون مواد افزودنی آماده می‌شوند.'
)
const ctaText = computed(() => cmsStore.heroSection?.cta_text || 'مشاهده منو')
const ctaLink = computed(() => cmsStore.heroSection?.cta_link || '/menu')
const heroBgImage = computed(
  () => cmsStore.heroSection?.background_image_url || '/img/homepage.webp'
)

useHead({
  title: 'فست‌فودی | رستوران و کافه غذاهای دست‌ساز',
  meta: [
    {
      name: 'description',
      content: 'پیتزای ناپلی تنوری، برگرهای دست‌ساز و سالادهای تازه با مواد اولیه روز در رستوران فست‌فودی',
    },
  ],
})
</script>

<template>
  <main class="w-full px-3 sm:px-6 lg:px-8 pt-1 pb-6">
    <section
      class="relative w-full min-h-[calc(100svh-5.5rem)] rounded-3xl sm:rounded-[2.5rem] overflow-hidden bg-[var(--color-brand-forest)] border border-[var(--color-brand-forest-light)]/30 shadow-[var(--shadow-lg)] flex items-center"
      aria-label="بنر معرفی فست‌فودی"
    >
      <img
        :src="heroBgImage"
        alt="میز غذاهای دست‌ساز فست‌فودی"
        width="1600"
        height="900"
        fetchpriority="high"
        decoding="async"
        class="absolute inset-0 h-full w-full object-cover object-[80%_center] lg:object-right pointer-events-none"
      />

      <div
        class="absolute inset-0 pointer-events-none overflow-hidden opacity-30 mix-blend-screen"
        aria-hidden="true"
      >
        <div
          class="absolute -inset-[10px] filter blur-[14px] will-change-transform [--aurora:repeating-linear-gradient(100deg,rgba(214,168,75,0.35)_10%,rgba(34,78,61,0.25)_20%,rgba(244,239,227,0.3)_30%)] [--white-gradient:repeating-linear-gradient(100deg,rgba(255,255,255,0.08)_0%,transparent_12%)] [background-image:var(--white-gradient),var(--aurora)] [background-size:250%,_150%] animate-aurora"
        />
      </div>

      <div
        class="absolute inset-0 bg-gradient-to-t from-[var(--color-brand-forest-deep)]/95 via-[var(--color-brand-forest-deep)]/45 to-transparent lg:hidden pointer-events-none"
        aria-hidden="true"
      />

      <div
        class="absolute inset-0 hidden lg:block bg-gradient-to-l from-[var(--color-brand-forest-deep)]/85 via-[var(--color-brand-forest)]/35 to-transparent pointer-events-none"
        aria-hidden="true"
      />

      <ClientOnly>
        <div class="absolute inset-0 z-20 pointer-events-none">
          <NimbuMirchi class="w-full h-full" />
        </div>
      </ClientOnly>

      <div class="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-0 flex items-center justify-start" style="direction: ltr;">
        <div
          class="w-full max-w-lg lg:max-w-[420px] xl:max-w-[460px] text-start rounded-3xl p-6 sm:p-8 lg:p-0 bg-[#12251D]/88 lg:bg-transparent backdrop-blur-md lg:backdrop-blur-none border border-white/10 lg:border-0 shadow-[var(--shadow-lg)] lg:shadow-none"
          style="direction: rtl;"
        >
          <h1 class="text-3xl sm:text-4xl lg:text-5xl font-black text-white leading-[1.25] tracking-tight">
            {{ heroTitle }}
          </h1>

          <p class="mt-4 text-xs sm:text-sm lg:text-base text-[#F4EFE3]/95 leading-relaxed max-w-md">
            {{ heroSubtitle }}
          </p>

          <p
            v-if="cmsStore.restaurantStatus"
            class="mt-4 inline-flex items-center gap-2 text-xs font-semibold text-white/90"
          >
            <Clock :size="14" aria-hidden="true" class="text-[var(--color-accent-gold)] shrink-0" />
            <span v-if="cmsStore.isOpen">
              پذیرش سفارش فعال تا <bdi>{{ formatTime(cmsStore.restaurantStatus.close_time) }}</bdi>
            </span>
            <span v-else>
              در حال حاضر بسته است (شروع کار <bdi>{{ formatTime(cmsStore.restaurantStatus.open_time) }}</bdi>)
            </span>
          </p>

          <div class="mt-6 sm:mt-7 flex flex-wrap items-center gap-3 pt-1">
            <GooeyButton
              variant="gold"
              size="lg"
              class="hero-btn-enter-1 shadow-[0_4px_16px_rgba(214,168,75,0.28)]"
              :aria-label="ctaText"
              @click="navigateTo(ctaLink)"
            >
              <span>{{ ctaText }}</span>
              <span class="fine-hover-shift-end inline-flex items-center transition-transform duration-200 ease-[var(--ease-out)] will-change-transform">
                <ArrowLeft :size="16" aria-hidden="true" class="icon-directional" />
              </span>
            </GooeyButton>

            <GooeyButton
              v-if="cmsStore.luckyWheelSection?.is_active !== false"
              variant="outline"
              size="lg"
              class="hero-btn-enter-2 !bg-white/15 !text-white !border-white/35 hover:!bg-white/25 hover:!border-white/60"
              aria-label="گردونه شانس غذا"
              @click="navigateTo('/lucky-wheel')"
            >
              <img
                src="/svg/lucky_wheel.svg"
                alt=""
                width="20"
                height="20"
                aria-hidden="true"
                class="h-5 w-5 shrink-0 object-contain"
              />
              <span>گردونه انتخاب غذا</span>
            </GooeyButton>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>
