<script setup lang="ts">
import { computed } from 'vue'
import { ArrowLeft } from 'lucide-vue-next'
import { useMenuStore } from '~/stores/menu'
import ProductCard from '~/components/ProductCard.vue'

const menuStore = useMenuStore()

const specials = computed(() => menuStore.specialOffers.slice(0, 4))
</script>

<template>
  <section
    v-if="specials.length > 0"
    id="specials"
    class="bg-[var(--color-surface-ivory)] py-12 sm:py-16"
    aria-label="پیشنهادهای ویژه منو"
  >
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="mb-8 flex flex-col items-start justify-between gap-4 md:flex-row md:items-end">
        <div>
          <h2 class="text-2xl sm:text-3xl font-extrabold text-[var(--color-brand-forest)]">
            پیشنهادهای تخفیف‌دار و ویژه
          </h2>
          <p class="mt-2 text-xs sm:text-sm text-[var(--color-text-secondary)] max-w-xl">
            انتخاب‌های منتخب منوی روز با تخفیف ویژه و آماده‌سازی تازه در آشپزخانه فست‌فودی.
          </p>
        </div>

        <a
          href="#menu"
          class="inline-flex items-center gap-1.5 text-xs sm:text-sm font-bold text-[var(--color-brand-forest)] hover:underline"
        >
          <span>مشاهده همه موارد منو</span>
          <ArrowLeft :size="16" aria-hidden="true" class="icon-directional" />
        </a>
      </div>

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
