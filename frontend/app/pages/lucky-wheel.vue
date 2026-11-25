<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RotateCw } from 'lucide-vue-next'
import { storefrontApi } from '~/services/api'
import { useCmsStore } from '~/stores/cms'
import { useMenuStore } from '~/stores/menu'
import type { LuckyWheelProduct } from '~/types'

const cmsStore = useCmsStore()
const menuStore = useMenuStore()
const { formatToman, toPersianDigits } = usePersian()

const selectedCategorySlug = ref<string>('')
const products = ref<LuckyWheelProduct[]>([])
const loading = ref(true)
const errorMessage = ref('')

const isSpinning = ref(false)
const rotationDeg = ref(0)
const winner = ref<LuckyWheelProduct | null>(null)
const reducedMotion = ref(false)

const visibleSlices = computed(() => products.value.slice(0, 12))

const slicePalette = [
  { bg: '#183A2D', text: '#FFFFFF' },
  { bg: '#F4EFE3', text: '#183A2D' },
  { bg: '#224E3D', text: '#FFFFFF' },
  { bg: '#FFFFFF', text: '#183A2D' },
]

function resolveSliceColors(idx: number, count: number) {
  if (count >= 2 && count % 2 === 1 && idx === count - 1) {
    return { bg: '#D6A84B', text: '#12251D' }
  }
  return slicePalette[idx % slicePalette.length] ?? { bg: '#183A2D', text: '#FFFFFF' }
}

function formatSliceLines(name: string, count: number): string[] {
  const cleaned = name.trim().replace(/\s+/g, ' ')
  const maxLineChars = count <= 6 ? 19 : count <= 9 ? 18 : 16
  if (cleaned.length <= maxLineChars) {
    return [cleaned]
  }

  const words = cleaned.split(' ')
  if (words.length >= 2) {
    const mid = cleaned.length / 2
    let bestSplit = 1
    let bestDiff = Infinity
    let acc = 0

    for (let i = 0; i < words.length - 1; i++) {
      const w = words[i] ?? ''
      acc += (i > 0 ? 1 : 0) + w.length
      const diff = Math.abs(acc - mid)
      if (diff < bestDiff) {
        bestDiff = diff
        bestSplit = i + 1
      }
    }

    const line1 = words.slice(0, bestSplit).join(' ')
    const line2 = words.slice(bestSplit).join(' ')
    const clampLine = (line: string) =>
      line.length > maxLineChars ? `${line.slice(0, maxLineChars - 1)}…` : line
    return [clampLine(line1), clampLine(line2)]
  }

  return [
    cleaned.slice(0, maxLineChars),
    cleaned.length > maxLineChars * 2
      ? `${cleaned.slice(maxLineChars, maxLineChars * 2 - 1)}…`
      : cleaned.slice(maxLineChars),
  ]
}

const sliceGeometry = computed(() => {
  const count = visibleSlices.value.length
  if (count === 0) return []
  const step = 360 / count
  const radius = 208
  const cx = 220
  const cy = 220

  return visibleSlices.value.map((item, idx) => {
    const startAngle = idx * step - 90
    const endAngle = startAngle + step
    const startRad = (startAngle * Math.PI) / 180
    const endRad = (endAngle * Math.PI) / 180

    const x1 = cx + radius * Math.cos(startRad)
    const y1 = cy + radius * Math.sin(startRad)
    const x2 = cx + radius * Math.cos(endRad)
    const y2 = cy + radius * Math.sin(endRad)

    const largeArcFlag = step > 180 ? 1 : 0
    const d =
      count === 1
        ? `M ${cx} ${cy} m -${radius}, 0 a ${radius},${radius} 0 1,0 ${radius * 2},0 a ${radius},${radius} 0 1,0 -${radius * 2},0`
        : `M ${cx} ${cy} L ${x1.toFixed(2)} ${y1.toFixed(2)} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2.toFixed(2)} ${y2.toFixed(2)} Z`

    const midAngle = startAngle + step / 2
    const midRad = (midAngle * Math.PI) / 180
    const lines = formatSliceLines(item.name, count)
    const labelRadius =
      count <= 4
        ? radius * 0.54
        : lines.length > 1 && count >= 9
          ? radius * 0.64
          : radius * 0.59
    const tx = cx + labelRadius * Math.cos(midRad)
    const ty = cy + labelRadius * Math.sin(midRad)
    const isLeftHalf = Math.cos(midRad) < -0.001
    const labelAngle = isLeftHalf ? midAngle + 180 : midAngle
    const baseFontSize = count <= 6 ? 12 : count <= 9 ? 11 : 10
    const fontSize = lines.length > 1 ? baseFontSize - 0.5 : baseFontSize
    const palette = resolveSliceColors(idx, count)

    return {
      product: item,
      path: d,
      fill: palette.bg,
      textColor: palette.text,
      tx: tx.toFixed(2),
      ty: ty.toFixed(2),
      labelAngle: labelAngle.toFixed(2),
      fontSize,
      lines,
    }
  })
})

const wheelStyle = computed(() => ({
  transform: `rotate(${rotationDeg.value}deg)`,
  transition: reducedMotion.value
    ? 'transform 120ms linear'
    : 'transform 4200ms cubic-bezier(0.16, 1, 0.3, 1)',
}))

async function loadWheelProducts(slug = '') {
  loading.value = true
  errorMessage.value = ''
  winner.value = null
  try {
    const res = await storefrontApi.catalog.getLuckyWheel(slug || undefined)
    products.value = res.products
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : 'خطا در دریافت محصولات گردونه شانس'
  } finally {
    loading.value = false
  }
}

function selectCategory(slug: string) {
  if (isSpinning.value) return
  selectedCategorySlug.value = slug
  loadWheelProducts(slug)
}

function spinWheel() {
  if (isSpinning.value || visibleSlices.value.length === 0) return

  winner.value = null
  const count = visibleSlices.value.length
  const winningIndex = Math.floor(Math.random() * count)
  const chosen = visibleSlices.value[winningIndex]
  if (!chosen) return
  const step = 360 / count
  const targetMidAngle = winningIndex * step + step / 2
  const desiredMod = (360 - (targetMidAngle % 360)) % 360

  if (reducedMotion.value) {
    const base = Math.floor(rotationDeg.value / 360) * 360
    rotationDeg.value = base + desiredMod
    isSpinning.value = true
    window.setTimeout(() => {
      isSpinning.value = false
      winner.value = chosen
    }, 150)
    return
  }

  const currentMod = ((rotationDeg.value % 360) + 360) % 360
  const deltaMod = (desiredMod - currentMod + 360) % 360
  const extraSpins = 5 * 360
  rotationDeg.value += extraSpins + deltaMod
  isSpinning.value = true

  window.setTimeout(() => {
    isSpinning.value = false
    winner.value = chosen
  }, 4300)
}

function openWinnerModal() {
  if (!winner.value) return
  menuStore.openProductModal(winner.value.slug)
}

onMounted(async () => {
  reducedMotion.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  await Promise.all([cmsStore.fetchAll(), menuStore.fetchMenu()])
  if (cmsStore.luckyWheelSection?.is_active !== false) {
    await loadWheelProducts('')
  } else {
    loading.value = false
  }
})

useHead({
  title: 'گردونه شانس غذا | فست‌فودی',
})
</script>

<template>
  <main class="min-h-screen bg-[#FAF7F2] py-10 sm:py-16">
    <div class="container mx-auto max-w-6xl px-4">
      <header class="mb-10 text-center">
        <h1 class="text-3xl font-extrabold text-[#292B27] sm:text-4xl">
          {{ cmsStore.luckyWheelSection?.title || 'انتخاب تصادفی با گردونه شانس' }}
        </h1>
        <p class="mx-auto mt-3 max-w-2xl text-base text-[#5A5D56]">
          {{ cmsStore.luckyWheelSection?.subtitle || 'نمی‌دانید امشب چه غذایی سفارش دهید؟ دسته‌بندی دلخواه را انتخاب کنید و گردونه را بچرخانید.' }}
        </p>
      </header>

      <section
        v-if="cmsStore.luckyWheelSection && !cmsStore.luckyWheelSection.is_active"
        class="mx-auto max-w-xl rounded-3xl border border-[#E8E5DC] bg-white p-8 text-center shadow-sm"
      >
        <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#F4EFE3]">
          <img
            src="/svg/lucky_wheel.svg"
            alt=""
            width="32"
            height="32"
            aria-hidden="true"
            class="h-8 w-8 object-contain"
          />
        </div>
        <h2 class="text-xl font-bold text-[#292B27]">گردونه شانس موقتاً غیرفعال است</h2>
        <p class="mt-2 text-sm text-[#5A5D56]">
          می‌توانید تمامی غذاهای موجود را مستقیماً در منوی رستوران بررسی و انتخاب کنید.
        </p>
        <NuxtLink
          to="/menu"
          class="touch-target mt-6 inline-flex items-center justify-center rounded-full bg-[#183A2D] px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#12251D]"
        >
          مشاهده منوی کامل
        </NuxtLink>
      </section>

      <template v-else>
        <div
          class="mb-10 flex flex-wrap items-center justify-center gap-2"
          role="group"
          aria-label="فیلتر دسته‌بندی گردونه"
        >
          <button
            type="button"
            class="touch-target rounded-full px-5 py-2.5 text-sm font-medium transition-colors"
            :class="
              selectedCategorySlug === ''
                ? 'bg-[#183A2D] text-white shadow-sm'
                : 'border border-[#E8E5DC] bg-white text-[#292B27] hover:bg-[#F4EFE3]'
            "
            :disabled="isSpinning"
            @click="selectCategory('')"
          >
            همه غذاها
          </button>
          <button
            v-for="cat in menuStore.topCategories"
            :key="cat.id"
            type="button"
            class="touch-target rounded-full px-5 py-2.5 text-sm font-medium transition-colors"
            :class="
              selectedCategorySlug === cat.slug
                ? 'bg-[#183A2D] text-white shadow-sm'
                : 'border border-[#E8E5DC] bg-white text-[#292B27] hover:bg-[#F4EFE3]'
            "
            :disabled="isSpinning"
            @click="selectCategory(cat.slug)"
          >
            {{ cat.name }}
          </button>
        </div>

        <div
          v-if="errorMessage"
          role="alert"
          class="mx-auto mb-8 max-w-xl rounded-2xl border border-[#A61B1B]/25 bg-[#FDE8E8] p-4 text-center text-sm font-medium text-[#A61B1B]"
        >
          {{ errorMessage }}
        </div>

        <div
          v-if="loading"
          class="grid items-center gap-10 lg:grid-cols-12"
        >
          <div class="flex justify-center lg:col-span-7">
            <div class="h-[300px] w-[300px] animate-pulse rounded-full bg-[#E8E5DC] sm:h-[420px] sm:w-[420px]" />
          </div>
          <div class="mx-auto w-full max-w-[340px] space-y-4 rounded-3xl border border-[#E8E5DC] bg-white p-5 lg:col-span-5">
            <div class="h-5 w-1/2 animate-pulse rounded-lg bg-[#E8E5DC]" />
            <div class="aspect-[3/4] w-full animate-pulse rounded-2xl bg-[#F4EFE3]" />
            <div class="h-6 w-2/3 animate-pulse rounded-lg bg-[#E8E5DC]" />
            <div class="h-11 w-full animate-pulse rounded-full bg-[#E8E5DC]" />
          </div>
        </div>

        <div
          v-else-if="visibleSlices.length === 0"
          class="mx-auto max-w-xl rounded-3xl border border-[#E8E5DC] bg-white p-10 text-center shadow-sm"
        >
          <img src="/svg/knife_fork.svg" alt="" width="40" height="40" aria-hidden="true" class="mx-auto mb-3 h-10 w-10 object-contain" />
          <h2 class="text-lg font-bold text-[#292B27]">غذای آماده‌ای در این دسته یافت نشد</h2>
          <p class="mt-2 text-sm text-[#5A5D56]">
            دسته‌بندی دیگری را انتخاب کنید یا به منوی کامل سر بزنید.
          </p>
        </div>

        <div
          v-else
          class="grid items-center gap-10 lg:grid-cols-12"
        >
          <div class="flex min-w-0 flex-col items-center lg:col-span-7">
            <div class="relative flex max-w-full items-center justify-center">
              <div
                aria-hidden="true"
                class="absolute inset-x-0 -top-4 z-20 mx-auto w-fit drop-shadow-md"
              >
                <svg width="34" height="40" viewBox="0 0 34 40" fill="none">
                  <path
                    d="M17 40L2.27757 14.5C0.737971 11.8333 2.66247 8.5 5.74167 8.5H28.2583C31.3375 8.5 33.262 11.8333 31.7224 14.5L17 40Z"
                    fill="#D6A84B"
                    stroke="#183A2D"
                    stroke-width="2.5"
                  />
                </svg>
              </div>

              <div class="relative rounded-full border-[6px] border-[#183A2D] bg-[#183A2D] p-1 shadow-xl sm:border-8">
                <svg
                  viewBox="0 0 440 440"
                  class="h-[272px] w-[272px] sm:h-[420px] sm:w-[420px] lg:h-[440px] lg:w-[440px]"
                  :style="wheelStyle"
                  role="img"
                  :aria-label="`گردونه شانس شامل ${toPersianDigits(visibleSlices.length)} گزینه`"
                >
                  <defs>
                    <clipPath
                      v-for="slice in sliceGeometry"
                      :id="`wheel-clip-${slice.product.id}`"
                      :key="`clip-${slice.product.id}`"
                    >
                      <path :d="slice.path" />
                    </clipPath>
                  </defs>
                  <g v-for="slice in sliceGeometry" :key="slice.product.id">
                    <path
                      :d="slice.path"
                      :fill="slice.fill"
                      stroke="#FFFFFF"
                      stroke-width="1.5"
                    />
                    <g :clip-path="`url(#wheel-clip-${slice.product.id})`">
                      <text
                        x="0"
                        y="0"
                        :transform="`translate(${slice.tx}, ${slice.ty}) rotate(${slice.labelAngle})`"
                        :fill="slice.textColor"
                        :font-size="slice.fontSize"
                        font-family="var(--font-persian)"
                        font-weight="700"
                        text-anchor="middle"
                        direction="rtl"
                        unicode-bidi="plaintext"
                      >
                        <template v-if="slice.lines.length === 1">
                          <tspan x="0" dy="0.35em">{{ slice.lines[0] }}</tspan>
                        </template>
                        <template v-else>
                          <tspan x="0" dy="-0.35em">{{ slice.lines[0] }}</tspan>
                          <tspan x="0" dy="1.35em">{{ slice.lines[1] }}</tspan>
                        </template>
                      </text>
                    </g>
                  </g>
                  <circle cx="220" cy="220" r="28" fill="#FFFFFF" stroke="#D6A84B" stroke-width="5" />
                  <circle cx="220" cy="220" r="6" fill="#183A2D" />
                </svg>
              </div>
            </div>

            <button
              type="button"
              class="touch-target mt-8 inline-flex items-center justify-center gap-2 rounded-full bg-[#183A2D] px-8 py-4 text-base font-bold text-white shadow-md transition-colors hover:bg-[#12251D] disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="isSpinning"
              @click="spinWheel"
            >
              <RotateCw class="h-5 w-5" :class="{ 'animate-spin': isSpinning }" />
              <span>{{ isSpinning ? 'در حال چرخش...' : winner ? 'چرخاندن دوباره' : 'چرخاندن گردونه' }}</span>
            </button>
          </div>

          <div class="min-w-0 lg:col-span-5">
            <div
              aria-live="polite"
              class="mx-auto w-full rounded-3xl border border-[#E8E5DC] bg-white shadow-sm"
              :class="winner ? 'max-w-[340px] p-4 sm:p-5' : 'max-w-md p-6 sm:p-8'"
            >
              <template v-if="winner">
                <span class="inline-block rounded-full bg-[#F8F3E8] px-3 py-1 text-xs font-bold text-[#8A651C]">
                  پیشنهاد گردونه برای شما
                </span>
                <div class="mt-3 overflow-hidden rounded-2xl border border-[#E8E5DC] bg-[#FAF7F2]">
                  <img
                    v-if="winner.image_url"
                    :src="winner.image_url"
                    :alt="winner.name"
                    width="300"
                    height="400"
                    class="aspect-[3/4] w-full object-cover"
                  />
                  <div v-else class="flex aspect-[3/4] items-center justify-center">
                    <img src="/svg/knife_fork.svg" alt="" width="40" height="40" aria-hidden="true" class="h-10 w-10 object-contain" />
                  </div>
                </div>
                <h2 class="mt-3.5 text-lg font-extrabold text-[#292B27] leading-snug">
                  {{ winner.name }}
                </h2>
                <p class="mt-1 text-base font-bold text-[#183A2D]">
                  {{ formatToman(winner.price) }}
                </p>
                <div class="mt-4 flex items-center gap-2">
                  <button
                    type="button"
                    class="touch-target flex-1 whitespace-nowrap rounded-full bg-[#183A2D] px-4 py-2.5 text-xs font-bold text-white transition-colors hover:bg-[#12251D] sm:text-[13px]"
                    @click="openWinnerModal"
                  >
                    مشاهده و افزودن به سبد
                  </button>
                  <NuxtLink
                    :to="`/products/${winner.slug}`"
                    class="touch-target inline-flex shrink-0 items-center justify-center whitespace-nowrap rounded-full border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5 text-xs font-semibold text-[#292B27] transition-colors hover:bg-[#F4EFE3] sm:text-[13px]"
                  >
                    صفحه محصول
                  </NuxtLink>
                </div>
              </template>

              <template v-else>
                <h2 class="text-xl font-bold text-[#292B27]">
                  {{ isSpinning ? 'در حال انتخاب تصادفی...' : 'آماده چرخش هستید؟' }}
                </h2>
                <p class="mt-2 text-sm leading-7 text-[#5A5D56]">
                  {{
                    isSpinning
                      ? 'لطفاً چند لحظه صبر کنید تا گردونه روی انتخاب بعدی شما بایستد.'
                      : `در حال حاضر ${toPersianDigits(visibleSlices.length)} غذای موجود در این گردونه قرار دارد. برای شروع دکمه چرخاندن را بزنید.`
                  }}
                </p>
                <ul class="mt-5 grid grid-cols-2 gap-2 text-xs text-[#5A5D56]">
                  <li
                    v-for="item in visibleSlices.slice(0, 6)"
                    :key="item.id"
                    class="truncate rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3 py-2 font-medium text-[#292B27]"
                  >
                    {{ item.name }}
                  </li>
                </ul>
              </template>
            </div>
          </div>
        </div>
      </template>
    </div>
  </main>
</template>
