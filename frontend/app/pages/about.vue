<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { Clock, MapPin, Phone, Truck, UtensilsCrossed } from 'lucide-vue-next'
import { useCmsStore } from '~/stores/cms'

const cmsStore = useCmsStore()
const { formatToman, formatTime, toPersianDigits } = usePersian()

const aboutParagraphs = computed(() => {
  const body = cmsStore.aboutUsSection?.body ?? ''
  return body
    .split(/\n+/)
    .map(p => p.trim())
    .filter(Boolean)
})

const galleryAssets = computed(() =>
  cmsStore.mediaAssets.filter(asset => asset.kind === 'gallery' && asset.url)
)

onMounted(() => {
  cmsStore.fetchAll()
})

useHead({
  title: 'درباره ما | فست‌فودی',
})
</script>

<template>
  <main class="min-h-screen bg-[#FAF7F2] py-12 sm:py-16">
    <div class="container mx-auto max-w-6xl space-y-12 px-4">
      <section class="grid items-center gap-8 rounded-3xl border border-[#E8E5DC] bg-white p-6 shadow-sm sm:p-10 lg:grid-cols-12">
        <div class="space-y-5 lg:col-span-6">
          <h1 class="text-3xl font-extrabold text-[#292B27] sm:text-4xl">
            {{ cmsStore.aboutUsSection?.title || 'داستان آشپزخانه فست‌فودی' }}
          </h1>
          <div class="space-y-4 text-base leading-8 text-[#5A5D56]">
            <p v-for="(paragraph, idx) in aboutParagraphs" :key="idx">
              {{ paragraph }}
            </p>
            <p v-if="aboutParagraphs.length === 0">
              آشپزخانه فست‌فودی با تمرکز بر مواد اولیه تازه، پخت روزانه نان و سس‌های دست‌ساز آماده پذیرایی از سفارش‌های شماست.
            </p>
          </div>
          <div class="pt-2">
            <NuxtLink
              to="/menu"
              class="touch-target inline-flex items-center justify-center rounded-full bg-[#183A2D] px-7 py-3 text-sm font-bold text-white transition-colors hover:bg-[#12251D]"
            >
              مشاهده منوی غذاها
            </NuxtLink>
          </div>
        </div>

        <div class="lg:col-span-6">
          <div class="overflow-hidden rounded-2xl border border-[#E8E5DC] bg-[#F4EFE3]">
            <img
              v-if="cmsStore.aboutUsSection?.image_url"
              :src="cmsStore.aboutUsSection.image_url"
              :alt="cmsStore.aboutUsSection.title || 'درباره فست‌فودی'"
              class="aspect-4/3 w-full object-cover"
            />
            <div v-else class="flex aspect-4/3 items-center justify-center text-[#5A5D56]">
              <UtensilsCrossed class="h-12 w-12" />
            </div>
          </div>
        </div>
      </section>

      <section aria-labelledby="branch-info-heading">
        <h2 id="branch-info-heading" class="mb-6 text-2xl font-extrabold text-[#292B27]">
          ساعات کاری، ارسال و اطلاعات تماس
        </h2>
        <div class="grid gap-5 md:grid-cols-3">
          <div class="rounded-2xl border border-[#E8E5DC] bg-white p-6 shadow-sm">
            <div class="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-[#F4EFE3] text-[#183A2D]">
              <Clock class="h-5 w-5" />
            </div>
            <h3 class="text-base font-bold text-[#292B27]">ساعات سرویس‌دهی</h3>
            <p class="mt-2 text-sm text-[#5A5D56]">
              {{ cmsStore.footerSection?.working_hours_text || 'همه‌روزه از ۱۱:۰۰ تا ۲۳:۳۰' }}
            </p>
            <p v-if="cmsStore.restaurantStatus" class="mt-2 text-xs font-semibold text-[#183A2D]">
              ساعت کاری سامانه: {{ formatTime(cmsStore.restaurantStatus.open_time) }} تا {{ formatTime(cmsStore.restaurantStatus.close_time) }}
            </p>
            <span
              class="mt-3 inline-block rounded-full px-3 py-1 text-xs font-bold"
              :class="cmsStore.isOpen ? 'bg-[#EDF7ED] text-[#1E5E22]' : 'bg-[#FDE8E8] text-[#A61B1B]'"
            >
              {{ cmsStore.isOpen ? 'هم‌اکنون در حال پذیرش سفارش' : 'در حال حاضر بسته است' }}
            </span>
          </div>

          <div class="rounded-2xl border border-[#E8E5DC] bg-white p-6 shadow-sm">
            <div class="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-[#F4EFE3] text-[#183A2D]">
              <Truck class="h-5 w-5" />
            </div>
            <h3 class="text-base font-bold text-[#292B27]">تعرفه ارسال و زمان آماده‌سازی</h3>
            <dl class="mt-2 space-y-1.5 text-sm text-[#5A5D56]">
              <div class="flex items-center justify-between gap-2">
                <dt>محدوده اصلی:</dt>
                <dd class="font-bold text-[#292B27]">{{ formatToman(cmsStore.inZoneFee) }}</dd>
              </div>
              <div class="flex items-center justify-between gap-2">
                <dt>خارج از محدوده:</dt>
                <dd class="font-bold text-[#292B27]">{{ formatToman(cmsStore.outZoneFee) }}</dd>
              </div>
              <div class="flex items-center justify-between gap-2">
                <dt>بافر آماده‌سازی:</dt>
                <dd class="font-bold text-[#292B27]">
                  {{ toPersianDigits(cmsStore.restaurantStatus?.prep_time_buffer_minutes ?? 10) }} دقیقه
                </dd>
              </div>
            </dl>
          </div>

          <div class="rounded-2xl border border-[#E8E5DC] bg-white p-6 shadow-sm">
            <div class="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-[#F4EFE3] text-[#183A2D]">
              <MapPin class="h-5 w-5" />
            </div>
            <h3 class="text-base font-bold text-[#292B27]">نشانی و تلفن</h3>
            <p class="mt-2 text-sm leading-6 text-[#5A5D56]">
              {{ cmsStore.footerSection?.address || 'تهران، خیابان ولیعصر، نبش خیابان فرشته' }}
            </p>
            <a
              v-if="cmsStore.footerSection?.phone"
              :href="`tel:${cmsStore.footerSection.phone}`"
              dir="ltr"
              class="touch-target mt-3 inline-flex items-center gap-2 text-sm font-bold text-[#183A2D] hover:underline"
            >
              <Phone class="h-4 w-4" />
              <span>{{ toPersianDigits(cmsStore.footerSection.phone) }}</span>
            </a>
          </div>
        </div>
      </section>

      <section v-if="galleryAssets.length > 0" aria-labelledby="gallery-heading">
        <h2 id="gallery-heading" class="mb-6 text-2xl font-extrabold text-[#292B27]">
          نگارخانه فضا و آشپزخانه
        </h2>
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <figure
            v-for="(asset, idx) in galleryAssets"
            :key="`${asset.title}-${idx}`"
            class="overflow-hidden rounded-2xl border border-[#E8E5DC] bg-white shadow-sm"
          >
            <img
              :src="asset.url || ''"
              :alt="asset.alt_text || asset.title"
              class="aspect-4/3 w-full object-cover"
            />
            <figcaption v-if="asset.title" class="px-4 py-3 text-sm font-semibold text-[#292B27]">
              {{ asset.title }}
            </figcaption>
          </figure>
        </div>
      </section>
    </div>
  </main>
</template>
