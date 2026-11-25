<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { MapPin, Search, ShieldAlert, ShieldCheck, Trash2, User } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import BackofficeShell from '~/components/backoffice/BackofficeShell.vue'
import { backofficeApi } from '~/services/api'
import type { Customer360Detail, CustomerListRow } from '~/types'

const { formatDateTime, formatToman, toPersianDigits } = usePersian()

const customers = ref<CustomerListRow[]>([])
const loading = ref(true)
const searchQuery = ref('')
const blockedFilter = ref<'' | 'true' | 'false'>('')

const selectedCustomer = ref<Customer360Detail | null>(null)
const loadingDetail = ref(false)
const editableName = ref('')
const newNoteText = ref('')
const savingCustomer = ref(false)
const savingNote = ref(false)

async function fetchCustomers() {
  loading.value = true
  try {
    const res = await backofficeApi.crm.listCustomers({
      search: searchQuery.value || undefined,
      is_blocked:
        blockedFilter.value === '' ? undefined : blockedFilter.value === 'true',
      limit: 50,
    })
    customers.value = res.results
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در دریافت لیست مشتریان')
  } finally {
    loading.value = false
  }
}

async function selectCustomer(id: number) {
  loadingDetail.value = true
  try {
    const detail = await backofficeApi.crm.getCustomer360(id)
    selectedCustomer.value = detail
    editableName.value = detail.full_name
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در دریافت پرونده مشتری')
  } finally {
    loadingDetail.value = false
  }
}

async function saveCustomerName() {
  if (!selectedCustomer.value) return
  savingCustomer.value = true
  try {
    await backofficeApi.crm.updateCustomer(selectedCustomer.value.id, {
      full_name: editableName.value.trim(),
    })
    await Promise.all([selectCustomer(selectedCustomer.value.id), fetchCustomers()])
    toast.success('نام مشتری به‌روزرسانی شد')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در ذخیره اطلاعات مشتری')
  } finally {
    savingCustomer.value = false
  }
}

async function toggleBlockCustomer() {
  if (!selectedCustomer.value) return
  savingCustomer.value = true
  try {
    await backofficeApi.crm.updateCustomer(selectedCustomer.value.id, {
      is_blocked: !selectedCustomer.value.is_blocked,
    })
    await Promise.all([selectCustomer(selectedCustomer.value.id), fetchCustomers()])
    toast.success(
      selectedCustomer.value.is_blocked ? 'محدودیت مشتری برداشته شد' : 'حساب مشتری مسدود شد'
    )
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'تغییر وضعیت مشتری ناموفق بود')
  } finally {
    savingCustomer.value = false
  }
}

async function addNote() {
  if (!selectedCustomer.value || !newNoteText.value.trim()) return
  savingNote.value = true
  try {
    await backofficeApi.crm.createCustomerNote(selectedCustomer.value.id, newNoteText.value.trim())
    newNoteText.value = ''
    await selectCustomer(selectedCustomer.value.id)
    toast.success('یادداشت داخلی ثبت شد')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'ثبت یادداشت ناموفق بود')
  } finally {
    savingNote.value = false
  }
}

async function removeNote(noteId: number) {
  if (!selectedCustomer.value) return
  try {
    await backofficeApi.crm.deleteCustomerNote(selectedCustomer.value.id, noteId)
    await selectCustomer(selectedCustomer.value.id)
    toast.success('یادداشت حذف شد')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'حذف یادداشت ناموفق بود')
  }
}

onMounted(() => {
  fetchCustomers()
})

useHead({
  title: 'مشتریان (CRM) | پنل مدیریت فست‌فودی',
})
</script>

<template>
  <div>
    <BackofficeShell
      title="مدیریت مشتریان (CRM 360)"
      subtitle="سوابق خرید، نشانی‌ها، مسدودسازی و یادداشت‌های داخلی کارکنان"
      @reset="fetchCustomers"
    >
      <div class="grid gap-6 lg:grid-cols-12">
        <section class="space-y-4 lg:col-span-5">
          <form class="flex flex-wrap gap-2 rounded-2xl border border-[#E8E5DC] bg-white p-3" @submit.prevent="fetchCustomers">
            <div class="relative min-w-44 flex-1">
              <label for="crm-search" class="visually-hidden">جستجوی مشتری</label>
              <input
                id="crm-search"
                v-model="searchQuery"
                type="search"
                placeholder="جستجو با موبایل یا نام..."
                class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] py-2 ps-3 pe-9 text-sm"
              />
              <Search class="pointer-events-none absolute top-2.5 end-3 h-4 w-4 text-[#5A5D56]" />
            </div>
            <div>
              <label for="crm-blocked-filter" class="visually-hidden">فیلتر وضعیت</label>
              <select
                id="crm-blocked-filter"
                v-model="blockedFilter"
                class="rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3 py-2 text-sm"
                @change="fetchCustomers"
              >
                <option value="">همه</option>
                <option value="false">عادی</option>
                <option value="true">مسدودشده</option>
              </select>
            </div>
            <button
              type="submit"
              class="touch-target rounded-xl bg-[#183A2D] px-4 py-2 text-xs font-bold text-white"
            >
              جستجو
            </button>
          </form>

          <div v-if="loading" class="space-y-2">
            <div v-for="i in 4" :key="i" class="h-16 animate-pulse rounded-2xl bg-[#E8E5DC]" />
          </div>

          <div v-else-if="customers.length === 0" class="rounded-2xl border border-[#E8E5DC] bg-white p-8 text-center text-sm text-[#5A5D56]">
            مشتری مطابق جستجو یافت نشد.
          </div>

          <div v-else class="space-y-2">
            <button
              v-for="cust in customers"
              :key="cust.id"
              type="button"
              class="touch-target flex w-full items-center justify-between gap-3 rounded-2xl border p-4 text-start transition-colors"
              :class="
                selectedCustomer?.id === cust.id
                  ? 'border-[#183A2D] bg-[#F4EFE3]'
                  : 'border-[#E8E5DC] bg-white hover:bg-[#FAF7F2]'
              "
              @click="selectCustomer(cust.id)"
            >
              <div>
                <p class="font-bold text-[#292B27]">{{ cust.full_name || 'بدون نام' }}</p>
                <p dir="ltr" class="mt-0.5 text-xs font-semibold text-[#5A5D56]">
                  {{ toPersianDigits(cust.phone) }}
                </p>
              </div>
              <span
                class="rounded-full px-3 py-1 text-xs font-bold"
                :class="cust.is_blocked ? 'bg-[#FDE8E8] text-[#A61B1B]' : 'bg-[#EDF7ED] text-[#1E5E22]'"
              >
                {{ cust.is_blocked ? 'مسدود' : 'عادی' }}
              </span>
            </button>
          </div>
        </section>

        <section class="lg:col-span-7">
          <div v-if="loadingDetail" class="h-80 animate-pulse rounded-3xl bg-[#E8E5DC]" />

          <div
            v-else-if="!selectedCustomer"
            class="flex min-h-72 flex-col items-center justify-center rounded-3xl border border-[#E8E5DC] bg-white p-10 text-center"
          >
            <User class="mb-3 h-10 w-10 text-[#5A5D56]" />
            <p class="text-base font-bold text-[#292B27]">یک مشتری را از فهرست انتخاب کنید</p>
            <p class="mt-1 text-xs text-[#5A5D56]">پرونده کامل شامل آمار خرید، نشانی‌ها و یادداشت‌ها اینجا نمایش داده می‌شود.</p>
          </div>

          <div v-else class="space-y-6 rounded-3xl border border-[#E8E5DC] bg-white p-6 shadow-sm">
            <div class="flex flex-wrap items-start justify-between gap-4 border-b border-[#E8E5DC] pb-4">
              <div>
                <h2 class="text-xl font-extrabold text-[#292B27]">
                  {{ selectedCustomer.full_name || 'مشتری فست‌فودی' }}
                </h2>
                <p dir="ltr" class="mt-0.5 text-sm font-semibold text-[#5A5D56]">
                  {{ toPersianDigits(selectedCustomer.phone) }}
                </p>
                <p class="mt-1 text-xs text-[#72756E]">
                  عضویت: {{ formatDateTime(selectedCustomer.date_joined) }}
                </p>
              </div>

              <button
                type="button"
                :disabled="savingCustomer"
                class="touch-target inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-bold transition-colors"
                :class="
                  selectedCustomer.is_blocked
                    ? 'bg-[#EDF7ED] text-[#1E5E22] hover:bg-[#1E5E22] hover:text-white'
                    : 'bg-[#FDE8E8] text-[#A61B1B] hover:bg-[#A61B1B] hover:text-white'
                "
                @click="toggleBlockCustomer"
              >
                <ShieldCheck v-if="selectedCustomer.is_blocked" class="h-4 w-4" />
                <ShieldAlert v-else class="h-4 w-4" />
                <span>{{ selectedCustomer.is_blocked ? 'رفع مسدودیت' : 'مسدودسازی مشتری' }}</span>
              </button>
            </div>

            <div class="grid gap-3 sm:grid-cols-3">
              <div class="rounded-2xl bg-[#FAF7F2] p-4">
                <p class="text-xs text-[#5A5D56]">تعداد سفارش‌ها</p>
                <p class="mt-1 text-lg font-extrabold text-[#292B27]">
                  {{ toPersianDigits(selectedCustomer.orders_count) }}
                  <span class="text-xs font-normal text-[#5A5D56]">
                    ({{ toPersianDigits(selectedCustomer.completed_orders_count) }} تکمیل‌شده)
                  </span>
                </p>
              </div>
              <div class="rounded-2xl bg-[#FAF7F2] p-4">
                <p class="text-xs text-[#5A5D56]">مجموع خرید (LTV)</p>
                <p class="mt-1 text-lg font-extrabold text-[#183A2D]">
                  {{ formatToman(selectedCustomer.lifetime_value) }}
                </p>
              </div>
              <div class="rounded-2xl bg-[#FAF7F2] p-4">
                <p class="text-xs text-[#5A5D56]">آخرین سفارش</p>
                <p class="mt-1 text-xs font-bold text-[#292B27]">
                  {{ selectedCustomer.last_order_at ? formatDateTime(selectedCustomer.last_order_at) : 'ثبت نشده' }}
                </p>
              </div>
            </div>

            <form class="flex flex-wrap items-end gap-3" @submit.prevent="saveCustomerName">
              <div class="flex-1">
                <label for="cust-edit-name" class="mb-1 block text-xs font-semibold text-[#5A5D56]">
                  ویرایش نام و نام خانوادگی
                </label>
                <input
                  id="cust-edit-name"
                  v-model="editableName"
                  type="text"
                  class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5 text-sm"
                />
              </div>
              <button
                type="submit"
                :disabled="savingCustomer"
                class="touch-target rounded-full bg-[#183A2D] px-5 py-2.5 text-xs font-bold text-white"
              >
                ذخیره نام
              </button>
            </form>

            <div>
              <h3 class="mb-2 text-sm font-bold text-[#292B27]">نشانی‌های ثبت‌شده</h3>
              <p v-if="selectedCustomer.addresses.length === 0" class="text-xs text-[#5A5D56]">
                نشانی ثبت نشده است.
              </p>
              <ul v-else class="space-y-2">
                <li
                  v-for="addr in selectedCustomer.addresses"
                  :key="addr.id"
                  class="flex items-start gap-2 rounded-2xl border border-[#E8E5DC] bg-[#FAF7F2] p-3 text-xs"
                >
                  <MapPin class="mt-0.5 h-4 w-4 shrink-0 text-[#183A2D]" />
                  <div>
                    <p class="font-bold text-[#292B27]">
                      {{ addr.title || 'نشانی' }}
                      <span v-if="addr.is_out_of_zone" class="mr-1 rounded-full bg-[#FFF4E5] px-2 py-0.5 text-[#9A4300]">
                        خارج از محدوده
                      </span>
                    </p>
                    <p class="mt-0.5 text-[#5A5D56]">{{ addr.address_text }}</p>
                  </div>
                </li>
              </ul>
            </div>

            <div class="border-t border-[#E8E5DC] pt-4">
              <h3 class="mb-3 text-sm font-bold text-[#292B27]">یادداشت‌های داخلی کارکنان</h3>
              <form class="mb-4 flex flex-col gap-2 sm:flex-row" @submit.prevent="addNote">
                <label for="cust-note-input" class="visually-hidden">متن یادداشت جدید</label>
                <input
                  id="cust-note-input"
                  v-model="newNoteText"
                  type="text"
                  placeholder="یادداشت جدید درباره مشتری..."
                  class="flex-1 rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5 text-sm"
                />
                <button
                  type="submit"
                  :disabled="savingNote || !newNoteText.trim()"
                  class="touch-target rounded-full bg-[#183A2D] px-5 py-2.5 text-xs font-bold text-white disabled:opacity-50"
                >
                  ثبت یادداشت
                </button>
              </form>

              <ul v-if="selectedCustomer.notes.length > 0" class="space-y-2">
                <li
                  v-for="note in selectedCustomer.notes"
                  :key="note.id"
                  class="flex items-start justify-between gap-3 rounded-2xl border border-[#E8E5DC] bg-[#FAF7F2] p-3 text-xs"
                >
                  <div>
                    <p class="font-semibold text-[#292B27]">{{ note.text }}</p>
                    <p class="mt-1 text-[#72756E]">
                      ثبت‌شده در {{ formatDateTime(note.created_at) }}
                      <span v-if="note.author_phone" dir="ltr">({{ toPersianDigits(note.author_phone) }})</span>
                    </p>
                  </div>
                  <button
                    type="button"
                    class="touch-target rounded-lg p-1.5 text-[#A61B1B] hover:bg-[#FDE8E8]"
                    aria-label="حذف یادداشت"
                    @click="removeNote(note.id)"
                  >
                    <Trash2 class="h-3.5 w-3.5" />
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </section>
      </div>
    </BackofficeShell>
  </div>
</template>
