<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ImagePlus, Plus, Trash2 } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import BackofficeShell from '~/components/backoffice/BackofficeShell.vue'
import { backofficeApi } from '~/services/api'
import { useCmsStore } from '~/stores/cms'
import type {
  MediaAssetAdmin,
  MediaAssetKind,
  SiteSectionKey,
  SiteSectionsMap,
} from '~/types'

const cmsStore = useCmsStore()
const { formatToman, toPersianDigits } = usePersian()

const activeTab = ref<'settings' | 'sections' | 'media'>('settings')
const loading = ref(true)
const savingSettings = ref(false)
const savingSection = ref(false)
const savingMedia = ref(false)

const settingsForm = reactive({
  open_time: '11:00',
  close_time: '23:30',
  is_temporarily_closed: false,
  in_zone_delivery_fee: 45000,
  out_zone_delivery_fee: 85000,
  prep_time_buffer_minutes: 10,
})

const sectionsState = ref<SiteSectionsMap | null>(null)
const selectedSectionKey = ref<SiteSectionKey>('hero')

const sectionLabels: Record<SiteSectionKey, string> = {
  hero: 'بخش اصلی (Hero)',
  header: 'هدر و برندینگ',
  footer: 'فوتر و اطلاعات تماس',
  announcement: 'نوار اطلاع‌رسانی بالا',
  lucky_wheel: 'گردونه شانس',
  about_us: 'درباره ما',
}

const mediaAssets = ref<MediaAssetAdmin[]>([])
const mediaKindFilter = ref<'' | MediaAssetKind>('')
const mediaForm = reactive({
  kind: 'gallery' as MediaAssetKind,
  title: '',
  alt_text: '',
  fileUrl: '',
})

async function loadCmsData() {
  loading.value = true
  try {
    const [settings, sections, assets] = await Promise.all([
      backofficeApi.cms.getRestaurantSettings(),
      backofficeApi.cms.getAllSiteSections(),
      backofficeApi.cms.listMediaAssets(mediaKindFilter.value || undefined),
    ])
    settingsForm.open_time = settings.open_time.slice(0, 5)
    settingsForm.close_time = settings.close_time.slice(0, 5)
    settingsForm.is_temporarily_closed = settings.is_temporarily_closed
    settingsForm.in_zone_delivery_fee = settings.in_zone_delivery_fee
    settingsForm.out_zone_delivery_fee = settings.out_zone_delivery_fee
    settingsForm.prep_time_buffer_minutes = settings.prep_time_buffer_minutes
    sectionsState.value = sections
    mediaAssets.value = assets
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در دریافت تنظیمات CMS')
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  savingSettings.value = true
  try {
    await backofficeApi.cms.updateRestaurantSettings({
      open_time: settingsForm.open_time,
      close_time: settingsForm.close_time,
      is_temporarily_closed: settingsForm.is_temporarily_closed,
      in_zone_delivery_fee: Number(settingsForm.in_zone_delivery_fee) || 0,
      out_zone_delivery_fee: Number(settingsForm.out_zone_delivery_fee) || 0,
      prep_time_buffer_minutes: Number(settingsForm.prep_time_buffer_minutes) || 0,
    })
    await cmsStore.fetchAll(true)
    toast.success('تنظیمات رستوران ذخیره و در فروشگاه اعمال شد')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'ذخیره تنظیمات ناموفق بود')
  } finally {
    savingSettings.value = false
  }
}

async function saveActiveSection() {
  if (!sectionsState.value) return
  savingSection.value = true
  try {
    const key = selectedSectionKey.value
    await backofficeApi.cms.updateSiteSection(key, sectionsState.value[key])
    await cmsStore.fetchAll(true)
    toast.success(`بخش «${sectionLabels[key]}» ذخیره شد`)
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'ذخیره بخش سایت ناموفق بود')
  } finally {
    savingSection.value = false
  }
}

function addSocialLink(target: 'header' | 'footer') {
  if (!sectionsState.value) return
  sectionsState.value[target].social_links.push({ label: '', url: '' })
}

function removeSocialLink(target: 'header' | 'footer', index: number) {
  if (!sectionsState.value) return
  sectionsState.value[target].social_links.splice(index, 1)
}

function handleMediaFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (file.size > 10 * 1024 * 1024) {
    toast.error('حجم فایل نباید بیش از ۱۰ مگابایت باشد')
    input.value = ''
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    if (typeof reader.result === 'string') {
      mediaForm.fileUrl = reader.result
    }
  }
  reader.readAsDataURL(file)
}

async function createMediaAsset() {
  if (!mediaForm.fileUrl.trim()) {
    toast.error('تصویر را انتخاب کنید یا نشانی فایل را وارد نمایید')
    return
  }
  savingMedia.value = true
  try {
    await backofficeApi.cms.createMediaAsset({
      kind: mediaForm.kind,
      fileUrl: mediaForm.fileUrl.trim(),
      title: mediaForm.title.trim(),
      alt_text: mediaForm.alt_text.trim(),
    })
    mediaForm.title = ''
    mediaForm.alt_text = ''
    mediaForm.fileUrl = ''
    await Promise.all([refreshMediaList(), cmsStore.fetchAll(true)])
    toast.success('فایل رسانه‌ای ثبت شد')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'ثبت رسانه ناموفق بود')
  } finally {
    savingMedia.value = false
  }
}

async function refreshMediaList() {
  mediaAssets.value = await backofficeApi.cms.listMediaAssets(mediaKindFilter.value || undefined)
}

async function updateAssetMeta(asset: MediaAssetAdmin) {
  try {
    await backofficeApi.cms.updateMediaAsset(asset.id, {
      title: asset.title,
      alt_text: asset.alt_text,
    })
    await cmsStore.fetchAll(true)
    toast.success('مشخصات تصویر به‌روزرسانی شد')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در به‌روزرسانی رسانه')
  }
}

async function deleteMediaAsset(id: number) {
  try {
    await backofficeApi.cms.deleteMediaAsset(id)
    await Promise.all([refreshMediaList(), cmsStore.fetchAll(true)])
    toast.success('فایل رسانه‌ای حذف شد')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'حذف رسانه ناموفق بود')
  }
}

onMounted(() => {
  loadCmsData()
})

useHead({
  title: 'تنظیمات و CMS | پنل مدیریت فست‌فودی',
})
</script>

<template>
  <div>
    <BackofficeShell
      title="تنظیمات رستوران و مدیریت محتوا (CMS)"
      subtitle="کنترل ساعات کاری، بستن اضطراری، تعرفه ارسال، متون و تصاویر سایت"
      @reset="loadCmsData"
    >
      <div class="space-y-6">
        <div role="tablist" aria-label="تب‌های تنظیمات و محتوا" class="flex flex-wrap gap-2">
          <button
            type="button"
            role="tab"
            :aria-selected="activeTab === 'settings'"
            class="touch-target rounded-full px-5 py-2.5 text-sm font-bold"
            :class="activeTab === 'settings' ? 'bg-[#183A2D] text-white' : 'border border-[#E8E5DC] bg-white text-[#292B27]'"
            @click="activeTab = 'settings'"
          >
            تنظیمات عملیات رستوران
          </button>
          <button
            type="button"
            role="tab"
            :aria-selected="activeTab === 'sections'"
            class="touch-target rounded-full px-5 py-2.5 text-sm font-bold"
            :class="activeTab === 'sections' ? 'bg-[#183A2D] text-white' : 'border border-[#E8E5DC] bg-white text-[#292B27]'"
            @click="activeTab = 'sections'"
          >
            محتوای بخش‌های سایت
          </button>
          <button
            type="button"
            role="tab"
            :aria-selected="activeTab === 'media'"
            class="touch-target rounded-full px-5 py-2.5 text-sm font-bold"
            :class="activeTab === 'media' ? 'bg-[#183A2D] text-white' : 'border border-[#E8E5DC] bg-white text-[#292B27]'"
            @click="activeTab = 'media'"
          >
            کتابخانه رسانه ({{ toPersianDigits(mediaAssets.length) }})
          </button>
        </div>

        <div v-if="loading" class="h-64 animate-pulse rounded-3xl bg-[#E8E5DC]" />

        <section
          v-else-if="activeTab === 'settings'"
          class="max-w-3xl rounded-3xl border border-[#E8E5DC] bg-white p-6 shadow-sm sm:p-8"
        >
          <form class="space-y-5 text-sm" @submit.prevent="saveSettings">
            <label
              class="flex cursor-pointer items-center justify-between gap-4 rounded-2xl border p-4"
              :class="
                settingsForm.is_temporarily_closed
                  ? 'border-[#A61B1B]/30 bg-[#FDE8E8]'
                  : 'border-[#E8E5DC] bg-[#FAF7F2]'
              "
            >
              <div>
                <p class="font-bold text-[#292B27]">بستن اضطراری سفارش‌گیری (موقت)</p>
                <p class="mt-0.5 text-xs text-[#5A5D56]">
                  در صورت فعال بودن، مشتریان نمی‌توانند سفارش جدید ثبت کنند و وضعیت فروشگاه «بسته» نمایش داده می‌شود.
                </p>
              </div>
              <input
                v-model="settingsForm.is_temporarily_closed"
                type="checkbox"
                class="h-5 w-5 accent-[#A61B1B]"
              />
            </label>

            <div class="grid gap-4 sm:grid-cols-2">
              <div>
                <label for="rs-open" class="mb-1 block font-semibold">ساعت شروع سرویس</label>
                <input
                  id="rs-open"
                  v-model="settingsForm.open_time"
                  type="time"
                  dir="ltr"
                  required
                  class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5"
                />
              </div>
              <div>
                <label for="rs-close" class="mb-1 block font-semibold">ساعت پایان سرویس</label>
                <input
                  id="rs-close"
                  v-model="settingsForm.close_time"
                  type="time"
                  dir="ltr"
                  required
                  class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5"
                />
              </div>
              <div>
                <label for="rs-in-fee" class="mb-1 block font-semibold">هزینه ارسال داخل محدوده (تومان)</label>
                <input
                  id="rs-in-fee"
                  v-model.number="settingsForm.in_zone_delivery_fee"
                  type="number"
                  min="0"
                  dir="ltr"
                  class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5"
                />
                <p class="mt-1 text-xs text-[#5A5D56]">معادل {{ formatToman(settingsForm.in_zone_delivery_fee) }}</p>
              </div>
              <div>
                <label for="rs-out-fee" class="mb-1 block font-semibold">هزینه ارسال خارج از محدوده (تومان)</label>
                <input
                  id="rs-out-fee"
                  v-model.number="settingsForm.out_zone_delivery_fee"
                  type="number"
                  min="0"
                  dir="ltr"
                  class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5"
                />
                <p class="mt-1 text-xs text-[#5A5D56]">معادل {{ formatToman(settingsForm.out_zone_delivery_fee) }}</p>
              </div>
              <div>
                <label for="rs-buffer" class="mb-1 block font-semibold">زمان بافر آشپزخانه (دقیقه)</label>
                <input
                  id="rs-buffer"
                  v-model.number="settingsForm.prep_time_buffer_minutes"
                  type="number"
                  min="0"
                  dir="ltr"
                  class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5"
                />
              </div>
            </div>

            <button
              type="submit"
              :disabled="savingSettings"
              class="touch-target rounded-full bg-[#183A2D] px-8 py-3 font-bold text-white hover:bg-[#12251D]"
            >
              {{ savingSettings ? 'در حال ذخیره...' : 'ذخیره تنظیمات رستوران' }}
            </button>
          </form>
        </section>

        <section
          v-else-if="activeTab === 'sections' && sectionsState"
          class="grid gap-6 lg:grid-cols-12"
        >
          <div class="space-y-2 lg:col-span-4">
            <button
              v-for="(label, key) in sectionLabels"
              :key="key"
              type="button"
              class="touch-target flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-start text-sm font-bold"
              :class="
                selectedSectionKey === key
                  ? 'border-[#183A2D] bg-[#183A2D] text-white'
                  : 'border-[#E8E5DC] bg-white text-[#292B27] hover:bg-[#F4EFE3]'
              "
              @click="selectedSectionKey = key"
            >
              <span>{{ label }}</span>
            </button>
          </div>

          <div class="rounded-3xl border border-[#E8E5DC] bg-white p-6 shadow-sm sm:p-8 lg:col-span-8">
            <h2 class="mb-5 text-lg font-extrabold text-[#292B27]">
              ویرایش {{ sectionLabels[selectedSectionKey] }}
            </h2>

            <form class="space-y-4 text-sm" @submit.prevent="saveActiveSection">
              <template v-if="selectedSectionKey === 'hero'">
                <div>
                  <label for="sec-hero-title" class="mb-1 block font-semibold">تیتر اصلی</label>
                  <input id="sec-hero-title" v-model="sectionsState.hero.title" type="text" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                </div>
                <div>
                  <label for="sec-hero-sub" class="mb-1 block font-semibold">زیرتیتر</label>
                  <textarea id="sec-hero-sub" v-model="sectionsState.hero.subtitle" rows="2" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                </div>
                <div class="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label for="sec-hero-cta" class="mb-1 block font-semibold">متن دکمه CTA</label>
                    <input id="sec-hero-cta" v-model="sectionsState.hero.cta_text" type="text" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                  </div>
                  <div>
                    <label for="sec-hero-link" class="mb-1 block font-semibold">مسیر لینک CTA</label>
                    <input id="sec-hero-link" v-model="sectionsState.hero.cta_link" type="text" dir="ltr" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                  </div>
                </div>
                <div>
                  <label for="sec-hero-bg" class="mb-1 block font-semibold">نشانی تصویر پس‌زمینه</label>
                  <input id="sec-hero-bg" v-model="sectionsState.hero.background_image_url" type="text" dir="ltr" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                </div>
              </template>

              <template v-else-if="selectedSectionKey === 'header'">
                <div class="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label for="sec-hdr-name" class="mb-1 block font-semibold">نام رستوران</label>
                    <input id="sec-hdr-name" v-model="sectionsState.header.restaurant_name" type="text" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                  </div>
                  <div>
                    <label for="sec-hdr-tag" class="mb-1 block font-semibold">شعار کوتاه</label>
                    <input id="sec-hdr-tag" v-model="sectionsState.header.tagline" type="text" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                  </div>
                  <div>
                    <label for="sec-hdr-phone" class="mb-1 block font-semibold">تلفن</label>
                    <input id="sec-hdr-phone" v-model="sectionsState.header.phone" type="text" dir="ltr" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                  </div>
                  <div>
                    <label for="sec-hdr-logo" class="mb-1 block font-semibold">نشانی لوگو</label>
                    <input id="sec-hdr-logo" v-model="sectionsState.header.logo_url" type="text" dir="ltr" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                  </div>
                </div>
                <div class="space-y-2 rounded-2xl bg-[#FAF7F2] p-4">
                  <div class="flex items-center justify-between">
                    <span class="font-bold">لینک‌های شبکه اجتماعی</span>
                    <button type="button" class="touch-target rounded-full bg-white px-3 py-1 text-xs font-bold" @click="addSocialLink('header')">
                      افزودن لینک
                    </button>
                  </div>
                  <div v-for="(link, idx) in sectionsState.header.social_links" :key="idx" class="flex gap-2">
                    <input v-model="link.label" type="text" placeholder="عنوان" class="w-1/3 rounded-xl border border-[#E8E5DC] bg-white px-3 py-2 text-xs" />
                    <input v-model="link.url" type="text" dir="ltr" placeholder="https://..." class="flex-1 rounded-xl border border-[#E8E5DC] bg-white px-3 py-2 text-xs" />
                    <button type="button" class="touch-target rounded-xl bg-[#FDE8E8] px-3 text-xs text-[#A61B1B]" @click="removeSocialLink('header', idx)">
                      حذف
                    </button>
                  </div>
                </div>
              </template>

              <template v-else-if="selectedSectionKey === 'footer'">
                <div>
                  <label for="sec-ftr-addr" class="mb-1 block font-semibold">نشانی رستوران</label>
                  <input id="sec-ftr-addr" v-model="sectionsState.footer.address" type="text" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                </div>
                <div class="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label for="sec-ftr-phone" class="mb-1 block font-semibold">تلفن تماس</label>
                    <input id="sec-ftr-phone" v-model="sectionsState.footer.phone" type="text" dir="ltr" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                  </div>
                  <div>
                    <label for="sec-ftr-hours" class="mb-1 block font-semibold">متن ساعات کاری</label>
                    <input id="sec-ftr-hours" v-model="sectionsState.footer.working_hours_text" type="text" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                  </div>
                </div>
                <div>
                  <label for="sec-ftr-copy" class="mb-1 block font-semibold">متن کپی‌رایت</label>
                  <input id="sec-ftr-copy" v-model="sectionsState.footer.copyright_text" type="text" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                </div>
                <div class="space-y-2 rounded-2xl bg-[#FAF7F2] p-4">
                  <div class="flex items-center justify-between">
                    <span class="font-bold">لینک‌های شبکه اجتماعی فوتر</span>
                    <button type="button" class="touch-target rounded-full bg-white px-3 py-1 text-xs font-bold" @click="addSocialLink('footer')">
                      افزودن لینک
                    </button>
                  </div>
                  <div v-for="(link, idx) in sectionsState.footer.social_links" :key="idx" class="flex gap-2">
                    <input v-model="link.label" type="text" placeholder="عنوان" class="w-1/3 rounded-xl border border-[#E8E5DC] bg-white px-3 py-2 text-xs" />
                    <input v-model="link.url" type="text" dir="ltr" placeholder="https://..." class="flex-1 rounded-xl border border-[#E8E5DC] bg-white px-3 py-2 text-xs" />
                    <button type="button" class="touch-target rounded-xl bg-[#FDE8E8] px-3 text-xs text-[#A61B1B]" @click="removeSocialLink('footer', idx)">
                      حذف
                    </button>
                  </div>
                </div>
              </template>

              <template v-else-if="selectedSectionKey === 'announcement'">
                <label class="flex items-center gap-2 font-semibold">
                  <input v-model="sectionsState.announcement.is_active" type="checkbox" class="h-4 w-4 accent-[#183A2D]" />
                  <span>نمایش نوار اطلاع‌رسانی در بالای سایت</span>
                </label>
                <div>
                  <label for="sec-ann-text" class="mb-1 block font-semibold">متن اطلاعیه</label>
                  <input id="sec-ann-text" v-model="sectionsState.announcement.text" type="text" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                </div>
                <div>
                  <label for="sec-ann-link" class="mb-1 block font-semibold">لینک (اختیاری)</label>
                  <input id="sec-ann-link" v-model="sectionsState.announcement.link" type="text" dir="ltr" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                </div>
              </template>

              <template v-else-if="selectedSectionKey === 'lucky_wheel'">
                <label class="flex items-center gap-2 font-semibold">
                  <input v-model="sectionsState.lucky_wheel.is_active" type="checkbox" class="h-4 w-4 accent-[#183A2D]" />
                  <span>گردونه شانس فعال باشد</span>
                </label>
                <div>
                  <label for="sec-lw-title" class="mb-1 block font-semibold">عنوان صفحه گردونه</label>
                  <input id="sec-lw-title" v-model="sectionsState.lucky_wheel.title" type="text" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                </div>
                <div>
                  <label for="sec-lw-sub" class="mb-1 block font-semibold">زیرنویس</label>
                  <textarea id="sec-lw-sub" v-model="sectionsState.lucky_wheel.subtitle" rows="2" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                </div>
              </template>

              <template v-else-if="selectedSectionKey === 'about_us'">
                <div>
                  <label for="sec-about-title" class="mb-1 block font-semibold">عنوان صفحه درباره ما</label>
                  <input id="sec-about-title" v-model="sectionsState.about_us.title" type="text" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                </div>
                <div>
                  <label for="sec-about-body" class="mb-1 block font-semibold">متن معرفی</label>
                  <textarea id="sec-about-body" v-model="sectionsState.about_us.body" rows="5" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                </div>
                <div>
                  <label for="sec-about-img" class="mb-1 block font-semibold">نشانی تصویر</label>
                  <input id="sec-about-img" v-model="sectionsState.about_us.image_url" type="text" dir="ltr" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
                </div>
              </template>

              <button
                type="submit"
                :disabled="savingSection"
                class="touch-target rounded-full bg-[#183A2D] px-8 py-3 font-bold text-white hover:bg-[#12251D]"
              >
                {{ savingSection ? 'در حال ذخیره...' : 'ذخیره تغییرات بخش' }}
              </button>
            </form>
          </div>
        </section>

        <section v-else class="space-y-6">
          <form
            class="grid gap-4 rounded-3xl border border-[#E8E5DC] bg-white p-6 shadow-sm sm:grid-cols-2 lg:grid-cols-4"
            @submit.prevent="createMediaAsset"
          >
            <div>
              <label for="ma-kind" class="mb-1 block text-xs font-semibold">نوع رسانه</label>
              <select id="ma-kind" v-model="mediaForm.kind" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3 py-2.5 text-sm">
                <option value="gallery">نگارخانه (Gallery)</option>
                <option value="banner">بنر (Banner)</option>
                <option value="logo">لوگو (Logo)</option>
              </select>
            </div>
            <div>
              <label for="ma-title" class="mb-1 block text-xs font-semibold">عنوان</label>
              <input id="ma-title" v-model="mediaForm.title" type="text" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3 py-2.5 text-sm" />
            </div>
            <div>
              <label for="ma-alt" class="mb-1 block text-xs font-semibold">متن جایگزین (Alt)</label>
              <input id="ma-alt" v-model="mediaForm.alt_text" type="text" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3 py-2.5 text-sm" />
            </div>
            <div>
              <label for="ma-url" class="mb-1 block text-xs font-semibold">نشانی فایل یا آپلود تصویر</label>
              <input id="ma-url" v-model="mediaForm.fileUrl" type="text" dir="ltr" placeholder="/img/..." class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3 py-2.5 text-sm" />
            </div>
            <div class="flex flex-wrap items-center justify-between gap-3 sm:col-span-2 lg:col-span-4">
              <label class="touch-target inline-flex cursor-pointer items-center gap-2 rounded-full border border-[#E8E5DC] bg-[#FAF7F2] px-4 py-2 text-xs font-semibold">
                <ImagePlus class="h-4 w-4" />
                <span>انتخاب فایل تصویر از سیستم</span>
                <input type="file" accept="image/*" class="hidden" @change="handleMediaFileChange" />
              </label>

              <button
                type="submit"
                :disabled="savingMedia"
                class="touch-target inline-flex items-center gap-1.5 rounded-full bg-[#183A2D] px-6 py-2.5 text-xs font-bold text-white"
              >
                <Plus class="h-4 w-4" />
                <span>{{ savingMedia ? 'در حال ثبت...' : 'افزودن به کتابخانه' }}</span>
              </button>
            </div>
          </form>

          <div class="flex items-center gap-3">
            <label for="ma-filter" class="text-xs font-semibold text-[#5A5D56]">فیلتر نوع:</label>
            <select
              id="ma-filter"
              v-model="mediaKindFilter"
              class="rounded-xl border border-[#E8E5DC] bg-white px-3 py-2 text-sm"
              @change="refreshMediaList"
            >
              <option value="">همه</option>
              <option value="gallery">نگارخانه</option>
              <option value="banner">بنر</option>
              <option value="logo">لوگو</option>
            </select>
          </div>

          <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <article
              v-for="asset in mediaAssets"
              :key="asset.id"
              class="overflow-hidden rounded-2xl border border-[#E8E5DC] bg-white shadow-sm"
            >
              <img :src="asset.webp_file || asset.file" :alt="asset.alt_text || asset.title" class="aspect-video w-full bg-[#F4EFE3] object-cover" />
              <div class="space-y-3 p-4 text-xs">
                <span class="inline-block rounded-full bg-[#F8F3E8] px-2.5 py-0.5 font-bold text-[#8A651C]">
                  {{ asset.kind }}
                </span>
                <div>
                  <label :for="`asset-t-${asset.id}`" class="mb-1 block font-semibold">عنوان</label>
                  <input :id="`asset-t-${asset.id}`" v-model="asset.title" type="text" class="w-full rounded-lg border border-[#E8E5DC] bg-[#FAF7F2] px-2.5 py-1.5" />
                </div>
                <div>
                  <label :for="`asset-a-${asset.id}`" class="mb-1 block font-semibold">Alt</label>
                  <input :id="`asset-a-${asset.id}`" v-model="asset.alt_text" type="text" class="w-full rounded-lg border border-[#E8E5DC] bg-[#FAF7F2] px-2.5 py-1.5" />
                </div>
                <div class="flex items-center justify-between gap-2 pt-1">
                  <button
                    type="button"
                    class="touch-target rounded-full bg-[#183A2D] px-4 py-1.5 font-bold text-white"
                    @click="updateAssetMeta(asset)"
                  >
                    ذخیره
                  </button>
                  <button
                    type="button"
                    class="touch-target rounded-full bg-[#FDE8E8] p-2 text-[#A61B1B]"
                    aria-label="حذف فایل رسانه"
                    @click="deleteMediaAsset(asset.id)"
                  >
                    <Trash2 class="h-4 w-4" />
                  </button>
                </div>
              </div>
            </article>
          </div>
        </section>
      </div>
    </BackofficeShell>
  </div>
</template>
