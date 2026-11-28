<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { Search, SlidersHorizontal, RotateCcw, ChevronRight, ChevronLeft } from 'lucide-vue-next'
import { useMenuStore } from '~/stores/menu'
import { usePersian } from '~/composables/usePersian'
import type { ProductSortChoice } from '~/types'
import CategoryNav from '~/components/CategoryNav.vue'
import ProductCard from '~/components/ProductCard.vue'
import SpecialOffers from '~/components/SpecialOffers.vue'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const menuStore = useMenuStore()
const route = useRoute()
const { toPersianDigits, toEnglishDigits } = usePersian()

const minPriceInput = ref('')
const maxPriceInput = ref('')
const showFilters = ref(false)
let searchDebounce: ReturnType<typeof setTimeout> | null = null

const sortOptions: Array<{ value: ProductSortChoice; label: string }> = [
  { value: 'default', label: 'پیشنهادی سرآشپز' },
  { value: 'popularity', label: 'محبوب‌ترین (بیشترین سفارش)' },
  { value: 'price_asc', label: 'ارزان‌ترین' },
  { value: 'price_desc', label: 'گران‌ترین' },
  { value: 'newest', label: 'جدیدترین' },
  { value: 'oldest', label: 'قدیمی‌ترین' },
  { value: 'relevance', label: 'بیشترین تطابق با جستجو' },
]

const activeCategoryTitle = computed(() => {
  if (menuStore.selectedCategory === 'all') return 'همه دسته‌ها'
  const cat = menuStore.menuCategories.find(c => c.slug === menuStore.selectedCategory)
  return cat ? cat.name : 'همه دسته‌ها'
})

const applyPriceFilter = async () => {
  const minVal = toEnglishDigits(minPriceInput.value).replace(/\D/g, '')
  const maxVal = toEnglishDigits(maxPriceInput.value).replace(/\D/g, '')
  menuStore.minPrice = minVal ? Number(minVal) : undefined
  menuStore.maxPrice = maxVal ? Number(maxVal) : undefined
  menuStore.offset = 0
  await menuStore.searchProducts()
}

const handleReset = async () => {
  minPriceInput.value = ''
  maxPriceInput.value = ''
  await menuStore.resetFilters()
}

watch(
  () => menuStore.searchQuery,
  () => {
    if (searchDebounce) clearTimeout(searchDebounce)
    searchDebounce = setTimeout(() => {
      menuStore.offset = 0
      menuStore.searchProducts()
    }, 220)
  }
)

watch(
  () => [
    menuStore.onlyInStock,
    menuStore.onlyDiscounted,
    menuStore.onlyMainDish,
    menuStore.sortBy,
  ],
  () => {
    menuStore.offset = 0
    menuStore.searchProducts()
  }
)

onMounted(async () => {
  await menuStore.fetchMenu()
  if (typeof route.query.q === 'string') {
    menuStore.searchQuery = route.query.q
  }
  if (typeof route.query.category === 'string') {
    menuStore.selectedCategory = route.query.category
  }
  await menuStore.searchProducts()
})

useHead({
  title: 'منوی کامل غذاها | فست‌فودی',
  meta: [
    {
      name: 'description',
      content: 'مشاهده منو، جستجو، فیلتر و سفارش آنلاین انواع پیتزا ناپلی تنوری، برگرهای دست‌ساز، پاستا و سالاد تازه در فست‌فودی',
    },
  ],
})
</script>

<template>
  <main class="min-h-screen pt-4 pb-20">
    <SpecialOffers />

    <section id="menu" class="py-10 sm:py-14 bg-white" aria-label="منوی غذاها">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-6">
        <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
          <div>
            <h1 class="text-2xl sm:text-3xl font-extrabold text-[var(--color-brand-forest)]">
              منوی کامل غذاها و نوشیدنی‌ها
            </h1>
            <p class="mt-1 text-xs sm:text-sm text-[var(--color-text-secondary)]">
              جستجو و انتخاب از میان غذاهای تازه و افزودنی‌های قابل شخصی‌سازی
            </p>
          </div>

          <div class="text-xs sm:text-sm font-medium text-[var(--color-text-secondary)]">
            نمایش <strong>{{ toPersianDigits(menuStore.totalCount) }}</strong> محصول در
            <span class="text-[var(--color-brand-forest)] font-bold">«{{ activeCategoryTitle }}»</span>
          </div>
        </div>

        <CategoryNav />

        <div class="rounded-3xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] p-4 sm:p-5 space-y-4">
          <div role="search">
            <form @submit.prevent="menuStore.searchProducts()" class="flex flex-col md:flex-row gap-3">
              <div class="relative flex-1">
                <Search :size="18" aria-hidden="true" class="absolute start-3.5 top-3.5 text-[var(--color-text-muted)]" />
                <label for="menu-search-input" class="visually-hidden">جستجو در منو</label>
                <input
                  id="menu-search-input"
                  v-model="menuStore.searchQuery"
                  type="search"
                  name="q"
                  enterkeyhint="search"
                  placeholder="جستجو بر اساس نام غذا، دسته‌بندی یا توضیح..."
                  class="h-12 w-full rounded-xl border border-[var(--color-border-subtle)] bg-white ps-10 pe-4 text-xs sm:text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-brand-forest)] focus:outline-none focus:ring-3 focus:ring-[rgba(24,58,45,0.12)]"
                />
              </div>

              <div class="flex flex-wrap items-center gap-2.5">
                <div class="flex items-center gap-2">
                  <label for="menu-sort-select" class="text-xs font-bold text-[var(--color-text-primary)] shrink-0">
                    مرتب‌سازی:
                  </label>
                  <select
                    id="menu-sort-select"
                    v-model="menuStore.sortBy"
                    class="h-12 rounded-xl border border-[var(--color-border-subtle)] bg-white px-3 text-xs font-semibold text-[var(--color-text-primary)] focus:border-[var(--color-brand-forest)] focus:outline-none"
                  >
                    <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">
                      {{ opt.label }}
                    </option>
                  </select>
                </div>

                <button
                  type="button"
                  @click="showFilters = !showFilters"
                  :aria-expanded="showFilters"
                  class="touch-target inline-flex h-12 items-center gap-2 rounded-xl border border-[var(--color-border-subtle)] bg-white px-4 text-xs font-bold text-[var(--color-text-primary)] hover:border-[var(--color-brand-forest)]"
                >
                  <SlidersHorizontal :size="15" aria-hidden="true" />
                  <span>فیلترهای پیشرفته</span>
                </button>
              </div>
            </form>
          </div>

          <div class="flex flex-wrap items-center gap-4 pt-1 text-xs">
            <label class="inline-flex items-center gap-2 font-semibold text-[var(--color-text-primary)]">
              <input
                v-model="menuStore.onlyInStock"
                type="checkbox"
                class="h-4 w-4 accent-[var(--color-brand-forest)]"
              />
              <span>فقط غذاهای موجود</span>
            </label>

            <label class="inline-flex items-center gap-2 font-semibold text-[var(--color-text-primary)]">
              <input
                v-model="menuStore.onlyDiscounted"
                type="checkbox"
                class="h-4 w-4 accent-[var(--color-brand-forest)]"
              />
              <span>فقط تخفیف‌دارها</span>
            </label>

            <label class="inline-flex items-center gap-2 font-semibold text-[var(--color-text-primary)]">
              <input
                v-model="menuStore.onlyMainDish"
                type="checkbox"
                class="h-4 w-4 accent-[var(--color-brand-forest)]"
              />
              <span>فقط غذاهای اصلی</span>
            </label>

            <button
              type="button"
              @click="handleReset"
              class="ms-auto inline-flex items-center gap-1.5 text-xs font-bold text-[var(--color-brand-forest)] hover:underline"
            >
              <RotateCcw :size="13" aria-hidden="true" />
              <span>بازنشانی فیلترها</span>
            </button>
          </div>

          <div
            v-if="showFilters"
            class="grid grid-cols-1 sm:grid-cols-3 gap-3 border-t border-[var(--color-border-subtle)] pt-4"
          >
            <div class="space-y-1">
              <label for="min-price-input" class="block text-xs font-bold text-[var(--color-text-primary)]">
                حداقل قیمت (تومان)
              </label>
              <input
                id="min-price-input"
                v-model="minPriceInput"
                type="text"
                inputmode="numeric"
                placeholder="مثال: ۱۰۰۰۰۰"
                class="h-11 w-full rounded-xl border border-[var(--color-border-subtle)] bg-white px-3 text-xs text-[var(--color-text-primary)]"
              />
            </div>

            <div class="space-y-1">
              <label for="max-price-input" class="block text-xs font-bold text-[var(--color-text-primary)]">
                حداکثر قیمت (تومان)
              </label>
              <input
                id="max-price-input"
                v-model="maxPriceInput"
                type="text"
                inputmode="numeric"
                placeholder="مثال: ۵۰۰۰۰۰"
                class="h-11 w-full rounded-xl border border-[var(--color-border-subtle)] bg-white px-3 text-xs text-[var(--color-text-primary)]"
              />
            </div>

            <div class="flex items-end">
              <GooeyButton
                type="button"
                variant="primary"
                size="sm"
                class="w-full h-11"
                @click="applyPriceFilter"
              >
                <span>اعمال بازه قیمت</span>
              </GooeyButton>
            </div>
          </div>
        </div>

        <div
          v-if="menuStore.productsLoading"
          class="grid grid-cols-2 gap-3 sm:gap-5 md:grid-cols-3 lg:grid-cols-4"
          aria-busy="true"
          aria-label="در حال بارگذاری منو"
        >
          <div
            v-for="n in 8"
            :key="n"
            class="h-80 rounded-2xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] animate-pulse"
          />
        </div>

        <div
          v-else-if="menuStore.productsError"
          role="alert"
          class="rounded-3xl border border-[var(--color-danger)]/30 bg-[var(--color-danger-bg)] p-8 text-center space-y-3"
        >
          <p class="text-sm font-bold text-[var(--color-danger)]">
            {{ menuStore.productsError }}
          </p>
          <GooeyButton variant="primary" size="sm" @click="menuStore.searchProducts()">
            <span>تلاش مجدد</span>
          </GooeyButton>
        </div>

        <template v-else-if="menuStore.products.length > 0">
          <div class="grid grid-cols-2 gap-3 sm:gap-5 md:grid-cols-3 lg:grid-cols-4">
            <ProductCard
              v-for="dish in menuStore.products"
              :key="dish.id"
              :product="dish"
            />
          </div>

          <nav
            v-if="menuStore.totalPages > 1"
            class="flex items-center justify-center gap-3 pt-6"
            aria-label="صفحه‌بندی منو"
          >
            <button
              type="button"
              :disabled="menuStore.currentPage <= 1"
              @click="menuStore.setPage(menuStore.currentPage - 1)"
              class="touch-target inline-flex items-center gap-1 rounded-full border border-[var(--color-border-subtle)] bg-white px-4 py-2 text-xs font-bold text-[var(--color-text-primary)] disabled:opacity-40"
            >
              <ChevronRight :size="15" aria-hidden="true" />
              <span>صفحه قبل</span>
            </button>

            <span class="text-xs font-bold text-[var(--color-text-secondary)]">
              صفحه {{ toPersianDigits(menuStore.currentPage) }} از {{ toPersianDigits(menuStore.totalPages) }}
            </span>

            <button
              type="button"
              :disabled="menuStore.currentPage >= menuStore.totalPages"
              @click="menuStore.setPage(menuStore.currentPage + 1)"
              class="touch-target inline-flex items-center gap-1 rounded-full border border-[var(--color-border-subtle)] bg-white px-4 py-2 text-xs font-bold text-[var(--color-text-primary)] disabled:opacity-40"
            >
              <span>صفحه بعد</span>
              <ChevronLeft :size="15" aria-hidden="true" />
            </button>
          </nav>
        </template>

        <div
          v-else
          class="flex flex-col items-center justify-center rounded-3xl border border-dashed border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)]/50 py-16 text-center px-4"
        >
          <div class="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-white text-[var(--color-text-secondary)] shadow-xs">
            <Search :size="28" aria-hidden="true" />
          </div>
          <h2 class="text-base font-bold text-[var(--color-text-primary)]">
            محصولی مطابق با جستجو یا فیلترهای انتخابی یافت نشد
          </h2>
          <p class="mt-1 text-xs text-[var(--color-text-secondary)] max-w-sm">
            می‌توانید عبارت جستجو را تغییر دهید یا تمام فیلترها را بازنشانی کنید.
          </p>
          <div
            v-if="menuStore.listDidYouMean"
            class="mt-3 flex flex-wrap items-center justify-center gap-2 text-xs text-[var(--color-text-primary)]"
          >
            <span>آیا منظور شما این بود:</span>
            <button
              type="button"
              @click="menuStore.searchQuery = menuStore.listDidYouMean || ''"
              class="touch-target rounded-full border border-[var(--color-brand-forest)]/30 bg-white px-3 py-1.5 font-bold text-[var(--color-brand-forest)] hover:bg-[var(--color-brand-forest)] hover:text-white transition-colors"
            >
              {{ menuStore.listDidYouMean }}
            </button>
          </div>
          <GooeyButton
            variant="primary"
            size="sm"
            class="mt-5"
            aria-label="مشاهده همه غذاها"
            @click="handleReset"
          >
            <span>نمایش همه غذاها</span>
          </GooeyButton>
        </div>
      </div>
    </section>
  </main>
</template>
