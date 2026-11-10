<script setup lang="ts">
import { computed } from 'vue'
import { Sparkles, ArrowLeft, Star, Clock } from 'lucide-vue-next'
import { useMenuStore } from '~/stores/menu'
import { usePersian } from '~/composables/usePersian'
import ProductCard from '~/components/ProductCard.vue'

const menuStore = useMenuStore()
const { toPersianDigits } = usePersian()

const specials = computed(() => menuStore.specialOffers.slice(0, 4))
</script>

<template>
  <section
    id="specials"
    class="bg-[var(--color-surface-ivory)] py-14 sm:py-20"
    aria-label="پیشنهادهای ویژه سرآشپز"
  >
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <!-- Section Title & Intro -->
      <div class="mb-10 flex flex-col items-start justify-between gap-4 md:flex-row md:items-end">
        <div>
          <div class="inline-flex items-center gap-1.5 rounded-full bg-white/80 px-3 py-1 text-xs font-bold text-[var(--color-brand-forest)] mb-3">
            <Sparkles :size="14" />
            <span>منتخب سرآشپز</span>
          </div>
          <h2 class="text-2xl sm:text-3xl font-extrabold text-[var(--color-brand-forest)]">
            پیشنهادهای ویژه و خاص این هفته
          </h2>
          <p class="mt-2 text-xs sm:text-sm text-[var(--color-text-secondary)] max-w-xl">
            غذاهایی که با دستور پخت اختصاصی و مواد اولیه دست‌چین آماده شده‌اند و بیشترین رضایت میهمانان را به همراه داشته‌اند.
          </p>
        </div>

        <a
          href="#menu"
          class="inline-flex items-center gap-1.5 text-xs sm:text-sm font-bold text-[var(--color-brand-forest)] hover:underline"
        >
          <span>مشاهده همه موارد منو</span>
          <ArrowLeft :size="16" class="icon-directional" />
        </a>
      </div>

      <!-- 4-Column Grid on Desktop / 2-Column on Mobile -->
      <div class="grid grid-cols-2 gap-3.5 sm:gap-5 lg:grid-cols-4">
        <ProductCard
          v-for="dish in specials"
          :key="dish.id"
          :product="dish"
        />
      </div>
    </div>
  </section>
</template>
