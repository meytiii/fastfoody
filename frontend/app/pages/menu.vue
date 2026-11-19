<script setup lang="ts">
import { computed } from 'vue'
import { Search } from 'lucide-vue-next'
import { useMenuStore } from '~/stores/menu'
import { usePersian } from '~/composables/usePersian'
import CategoryNav from '~/components/CategoryNav.vue'
import ProductCard from '~/components/ProductCard.vue'
import SpecialOffers from '~/components/SpecialOffers.vue'
import ReservationSection from '~/components/ReservationSection.vue'
import TestimonialsSection from '~/components/TestimonialsSection.vue'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const menuStore = useMenuStore()
const { toPersianDigits } = usePersian()

const activeCategoryTitle = computed(() => {
  const cat = menuStore.categories.find(c => c.id === menuStore.selectedCategory)
  return cat ? cat.title : 'همه دسته‌ها'
})

useHead({
  title: 'منوی کامل غذاها | فست‌فودی',
  meta: [
    {
      name: 'description',
      content: 'مشاهده منو و سفارش آنلاین انواع پیتزا ناپلی تنوری، برگرهای دست‌ساز، ساندویچ و سالاد تازه در فست‌فودی',
    },
  ],
})
</script>

<template>
  <main class="min-h-screen pt-4 pb-20">
    <SpecialOffers />

    <section id="menu" class="py-12 sm:py-16 bg-white" aria-label="منوی غذاها">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-8">
        <div class="space-y-6">
          <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
            <div>
              <h1 class="text-2xl sm:text-3xl font-extrabold text-[var(--color-brand-forest)]">
                طعم‌های دست‌ساز، تازه و متنوع
              </h1>
            </div>

            <div class="text-xs sm:text-sm font-medium text-[var(--color-text-secondary)]">
              نمایش <strong>{{ toPersianDigits(menuStore.filteredProducts.length) }}</strong> آیتم در
              <span class="text-[var(--color-brand-forest)] font-bold">«{{ activeCategoryTitle }}»</span>
            </div>
          </div>

          <CategoryNav />
        </div>

        <div
          v-if="menuStore.filteredProducts.length > 0"
          class="grid grid-cols-2 gap-3 sm:gap-5 md:grid-cols-3 lg:grid-cols-4"
        >
          <ProductCard
            v-for="dish in menuStore.filteredProducts"
            :key="dish.id"
            :product="dish"
          />
        </div>

        <div
          v-else
          class="flex flex-col items-center justify-center rounded-3xl border border-dashed border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)]/50 py-16 text-center"
        >
          <div class="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-white text-[var(--color-text-muted)] shadow-xs">
            <Search :size="28" />
          </div>
          <h2 class="text-base font-bold text-[var(--color-text-primary)]">
            هیچ غذایی در این دسته‌بندی یافت نشد
          </h2>
          <p class="mt-1 text-xs text-[var(--color-text-secondary)] max-w-sm">
            می‌توانید سایر دسته‌بندی‌ها را انتخاب کنید یا عبارت دیگری را جستجو فرمایید.
          </p>
          <GooeyButton
            variant="primary"
            size="sm"
            class="mt-5"
            aria-label="مشاهده همه غذاها"
            @click="menuStore.setCategory('all')"
          >
            <span>مشاهده همه غذاها</span>
          </GooeyButton>
        </div>
      </div>
    </section>

    <ReservationSection />

    <TestimonialsSection />
  </main>
</template>
