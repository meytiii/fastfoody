<script setup lang="ts">
import { ref } from 'vue'
import { Star, Quote, CheckCircle2, ChevronRight, ChevronLeft } from 'lucide-vue-next'
import { usePersian } from '~/composables/usePersian'

const { toPersianDigits } = usePersian()

const reviews = [
  {
    id: 'r1',
    name: 'مهندس آرش طاهری',
    role: 'میهمان دائمی',
    rating: 5,
    dishOrdered: 'اسموکی فورست برگر',
    text: 'نان برگر فوق‌العاده تازه بود و کیفیت گوشت کاملاً با برگرهای مرسوم تجاری فرق داشت. قارچ ترافل عطر بی‌نظیری به غذا داده بود. ارسال پیک هم کاملاً داغ به دستم رسید.',
    highlight: true,
  },
  {
    id: 'r2',
    name: 'دکتر نگار شمس',
    role: 'سفارش آنلاین',
    rating: 5,
    dishOrdered: 'مارگریتا بوفالا ناپلی',
    text: 'خمیر پیتزا دقیقاً سبک ناپلی با حباب‌های ترد و سبک بود. پنیر بوفالای تازه و سس گوجه معطر بدون هیچ روغن اضافی. یک انتخاب عالی برای طرفداران غذای سالم.',
    highlight: false,
  },
  {
    id: 'r3',
    name: 'سامان فراهانی',
    role: 'میهمان رستوران',
    rating: 5,
    dishOrdered: 'بوول سالمون نروژی',
    text: 'محیط رستوران بسیار آرام و با موسیقی ملایم طراحی شده. سالاد سالمون با سس خردل و دیژون فوق‌العاده خوشمزه و تازه بود. به همه پیشنهاد می‌کنم رزرو میز را امتحان کنند.',
    highlight: false,
  },
]
</script>

<template>
  <section
    id="testimonials"
    class="bg-[var(--color-surface-ivory)] py-16 sm:py-24"
    aria-label="نظرات میهمانان و مشتریان"
  >
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <!-- Section Title -->
      <div class="mb-12 text-center max-w-2xl mx-auto space-y-3">
        <div class="inline-flex items-center gap-1.5 rounded-full bg-white/90 px-3.5 py-1 text-xs font-bold text-[var(--color-brand-forest)] shadow-2xs">
          <Star :size="13" class="fill-[var(--color-accent-gold)] text-[var(--color-accent-gold)]" />
          <span>دیدگاه‌های میهمانان</span>
        </div>
        <h2 class="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-[var(--color-brand-forest)]">
          آنچه مشتریان درباره طعم‌های فست‌فودی می‌گویند
        </h2>
        <p class="text-xs sm:text-sm text-[var(--color-text-secondary)]">
          بیش از ۳٬۵۰۰ مشتری وفادار هر هفته تازگی و طعم ارگانیک غذاهای ما را تجربه می‌کنند.
        </p>
      </div>

      <!-- Reviews Grid (1 Highlight Dark Card + 2 White Cards) -->
      <div class="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div
          v-for="review in reviews"
          :key="review.id"
          class="relative flex flex-col justify-between rounded-3xl p-6 sm:p-8 transition-all duration-300 shadow-[var(--shadow-sm)] hover:-translate-y-1 hover:shadow-[var(--shadow-md)]"
          :class="
            review.highlight
              ? 'bg-[var(--color-brand-forest)] text-white'
              : 'border border-[var(--color-border-subtle)] bg-white text-[var(--color-text-primary)]'
          "
        >
          <!-- Quote Icon -->
          <div class="mb-4 flex items-center justify-between">
            <div class="flex items-center gap-1">
              <Star
                v-for="s in 5"
                :key="s"
                :size="15"
                class="fill-[var(--color-accent-gold)] text-[var(--color-accent-gold)]"
              />
            </div>
            <Quote
              :size="28"
              :class="review.highlight ? 'text-white/20' : 'text-[var(--color-accent-gold)]/40'"
            />
          </div>

          <!-- Body Text -->
          <p
            class="text-xs sm:text-sm leading-relaxed mb-6"
            :class="review.highlight ? 'text-white/90' : 'text-[var(--color-text-secondary)]'"
          >
            «{{ review.text }}»
          </p>

          <!-- Author Info -->
          <div
            class="pt-4 border-t flex items-center justify-between"
            :class="review.highlight ? 'border-white/10' : 'border-[var(--color-border-subtle)]'"
          >
            <div class="flex items-center gap-3">
              <div
                class="flex h-11 w-11 items-center justify-center rounded-full font-bold text-sm"
                :class="
                  review.highlight
                    ? 'bg-white/15 text-white'
                    : 'bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)]'
                "
              >
                {{ review.name[0] }}
              </div>
              <div>
                <h4
                  class="text-xs sm:text-sm font-bold"
                  :class="review.highlight ? 'text-white' : 'text-[var(--color-text-primary)]'"
                >
                  {{ review.name }}
                </h4>
                <p
                  class="text-[11px]"
                  :class="review.highlight ? 'text-white/70' : 'text-[var(--color-text-secondary)]'"
                >
                  سفارش داده شده: {{ review.dishOrdered }}
                </p>
              </div>
            </div>

            <div
              class="flex items-center gap-1 text-[11px] font-medium"
              :class="review.highlight ? 'text-[var(--color-accent-gold-soft)]' : 'text-[var(--color-brand-success)]'"
            >
              <CheckCircle2 :size="13" />
              <span>تایید شده</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
