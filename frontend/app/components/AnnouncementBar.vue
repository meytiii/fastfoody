<script setup lang="ts">
import { computed } from 'vue'
import { X, AlertTriangle, Megaphone, ArrowLeft } from 'lucide-vue-next'
import { useCmsStore } from '~/stores/cms'
import { useUiStore } from '~/stores/ui'
import { usePersian } from '~/composables/usePersian'

const cmsStore = useCmsStore()
const uiStore = useUiStore()
const { formatTime } = usePersian()

const showClosedBanner = computed(() => {
  return cmsStore.loaded && !cmsStore.isOpen
})

const showAnnouncement = computed(() => {
  return (
    cmsStore.loaded &&
    !uiStore.announcementDismissed &&
    cmsStore.announcement.is_active &&
    Boolean(cmsStore.announcement.text.trim())
  )
})
</script>

<template>
  <div class="no-print">
    <div
      v-if="showClosedBanner"
      role="status"
      aria-live="polite"
      class="border-b border-[var(--color-warning)]/20 bg-[var(--color-warning-bg)] px-4 py-2.5 text-xs text-[var(--color-warning)]"
    >
      <div class="mx-auto flex max-w-7xl flex-wrap items-center justify-center gap-2 text-center font-semibold">
        <AlertTriangle :size="15" aria-hidden="true" class="shrink-0" />
        <span v-if="cmsStore.restaurantStatus?.is_temporarily_closed">
          رستوران موقتاً بسته است و در حال حاضر سفارش جدید ثبت نمی‌شود.
        </span>
        <span v-else-if="cmsStore.restaurantStatus">
          رستوران خارج از ساعت کاری است. ساعات پذیرش سفارش:
          <bdi>{{ formatTime(cmsStore.restaurantStatus.open_time) }}</bdi>
          تا
          <bdi>{{ formatTime(cmsStore.restaurantStatus.close_time) }}</bdi>
        </span>
      </div>
    </div>

    <div
      v-if="showAnnouncement"
      class="border-b border-[var(--color-brand-forest-light)]/30 bg-[var(--color-brand-forest-deep)] px-4 py-2 text-xs text-white"
    >
      <div class="mx-auto flex max-w-7xl items-center justify-between gap-3">
        <div class="flex flex-1 items-center justify-center gap-2 text-center">
          <Megaphone :size="14" aria-hidden="true" class="shrink-0 text-[var(--color-accent-gold)]" />
          <p class="font-medium text-white/95">
            {{ cmsStore.announcement.text }}
          </p>
          <NuxtLink
            v-if="cmsStore.announcement.link"
            :to="cmsStore.announcement.link"
            class="touch-target inline-flex items-center gap-1 px-2 font-bold text-[var(--color-accent-gold)] hover:underline shrink-0"
          >
            <span>مشاهده</span>
            <ArrowLeft :size="13" aria-hidden="true" class="icon-directional" />
          </NuxtLink>
        </div>

        <button
          type="button"
          @click="uiStore.dismissAnnouncement"
          class="touch-target flex shrink-0 items-center justify-center rounded-full text-white/80 hover:bg-white/10 hover:text-white active:scale-[0.97] transition-[background-color,transform] duration-150 ease-[var(--ease-out)]"
          aria-label="بستن اعلان"
        >
          <X :size="14" aria-hidden="true" />
        </button>
      </div>
    </div>
  </div>
</template>
