<script setup lang="ts">
import { computed } from 'vue'
import { Utensils, Search } from 'lucide-vue-next'
import { useMenuStore } from '~/stores/menu'
import { usePersian } from '~/composables/usePersian'
import HeroSection from '~/components/HeroSection.vue'
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
  title: 'فست‌فودی | منوی آنلاین برگر، پیتزا ناپلی و غذاهای ارگانیک',
  meta: [
    {
      name: 'description',
      content: 'سفارش آنلاین انواع برگر دست‌ساز، پیتزا ناپلی تنوری، پاستا و سالادهای تازه با مواد اولیه روز و ارسال گرم در فست‌فودی',
    },
  ],
})
</script>

<template>
  <main class="min-h-screen">
    <!-- Hero Section -->
    <HeroSection />

    <!-- Special Offers Section -->
    <SpecialOffers />

    <!-- Main Menu & Catalog Section -->
    <section id="menu" class="py-14 sm:py-20 bg-white" aria-label="منوی غذاها">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-8">
        <!-- Section Title & Category Filter Tabs -->
        <div class="space-y-6">
          <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
            <div>
              <div class="inline-flex items-center gap-1.5 rounded-full bg-[var(--color-surface-cream)] px-3 py-1 text-xs font-bold text-[var(--color-brand-forest)] mb-2">
                <Utensils :size="14" />
                <span>منوی کامل رستوران</span>
              </div>
              <h2 class="text-2xl sm:text-3xl font-extrabold text-[var(--color-brand-forest)]">
                طعم‌های دست‌ساز، تازه و متنوع
              </h2>
            </div>

            <!-- Counter -->
            <div class="text-xs sm:text-sm font-medium text-[var(--color-text-secondary)]">
              نمایش <strong>{{ toPersianDigits(menuStore.filteredProducts.length) }}</strong> آیتم در
              <span class="text-[var(--color-brand-forest)] font-bold">«{{ activeCategoryTitle }}»</span>
            </div>
          </div>

          <!-- Category Navigation Pills Carousel -->
          <CategoryNav />
        </div>

        <!-- Product Grid (4 cols desktop, 3 cols tablet, 2 cols mobile with 12px gap) -->
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

        <!-- Empty Filter State -->
        <div
          v-else
          class="flex flex-col items-center justify-center rounded-3xl border border-dashed border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)]/50 py-16 text-center"
        >
          <div class="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-white text-[var(--color-text-muted)] shadow-xs">
            <Search :size="28" />
          </div>
          <h3 class="text-base font-bold text-[var(--color-text-primary)]">
            هیچ غذایی در این دسته‌بندی یافت نشد
          </h3>
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

    <!-- Table Reservation Section -->
    <ReservationSection />

    <!-- Customer Reviews & Testimonials Section -->
    <TestimonialsSection />
  </main>
</template>

