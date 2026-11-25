<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Check, LogOut, MapPin, Pencil, Plus, Receipt, Trash2, User } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { closeDialogSmoothly, useDialogLightDismiss } from '~/composables/useDialogControl'
import { useAuthStore } from '~/stores/auth'
import { useCmsStore } from '~/stores/cms'
import type { CustomerAddress, CustomerAddressPayload } from '~/types'

const authStore = useAuthStore()
const cmsStore = useCmsStore()
const { formatDateTime, formatToman, toEnglishDigits, toPersianDigits } = usePersian()

const addressDialogRef = ref<HTMLDialogElement | null>(null)
useDialogLightDismiss(addressDialogRef, () => {
  closeAddressDialog()
})

const editingAddressId = ref<number | null>(null)
const savingAddress = ref(false)
const formError = ref('')
const touched = reactive({
  address_text: false,
  recipient_phone: false,
})

const form = reactive<CustomerAddressPayload>({
  title: '',
  recipient_name: '',
  recipient_phone: '',
  address_text: '',
  is_out_of_zone: false,
  is_default: false,
})

function resetAddressDialog() {
  editingAddressId.value = null
  form.title = ''
  form.recipient_name = ''
  form.recipient_phone = ''
  form.address_text = ''
  form.is_out_of_zone = false
  form.is_default = false
  formError.value = ''
  touched.address_text = false
  touched.recipient_phone = false
}

function openCreateDialog() {
  resetAddressDialog()
  if (authStore.user) {
    form.recipient_name = authStore.user.full_name || ''
    form.recipient_phone = authStore.user.phone || ''
  }
  form.is_default = authStore.addresses.length === 0
  addressDialogRef.value?.showModal()
}

function openEditDialog(addr: CustomerAddress) {
  resetAddressDialog()
  editingAddressId.value = addr.id
  form.title = addr.title
  form.recipient_name = addr.recipient_name
  form.recipient_phone = addr.recipient_phone
  form.address_text = addr.address_text
  form.is_out_of_zone = addr.is_out_of_zone
  form.is_default = addr.is_default
  addressDialogRef.value?.showModal()
}

async function closeAddressDialog() {
  await closeDialogSmoothly(addressDialogRef.value)
  resetAddressDialog()
}

const addressTextError = computed(() => {
  if (!touched.address_text) return ''
  return form.address_text.trim().length < 5 ? 'لطفاً نشانی دقیق پستی را وارد کنید.' : ''
})

async function handleSaveAddress() {
  touched.address_text = true
  touched.recipient_phone = true
  formError.value = ''

  if (form.address_text.trim().length < 5) {
    formError.value = 'نشانی پستی باید حداقل ۵ کاراکتر باشد.'
    return
  }

  savingAddress.value = true
  try {
    const payload: CustomerAddressPayload = {
      title: form.title?.trim() || 'منزل',
      recipient_name: form.recipient_name?.trim() || undefined,
      recipient_phone: toEnglishDigits(form.recipient_phone?.trim()) || undefined,
      address_text: form.address_text.trim(),
      is_out_of_zone: Boolean(form.is_out_of_zone),
      is_default: Boolean(form.is_default),
    }

    if (editingAddressId.value !== null) {
      await authStore.updateAddress(editingAddressId.value, payload)
      toast.success('نشانی با موفقیت ویرایش شد')
    } else {
      await authStore.addAddress(payload)
      toast.success('نشانی جدید ثبت شد')
    }
    await closeAddressDialog()
  } catch (err) {
    formError.value = err instanceof Error ? err.message : 'ذخیره نشانی ناموفق بود.'
  } finally {
    savingAddress.value = false
  }
}

async function handleSetDefault(addr: CustomerAddress) {
  try {
    await authStore.updateAddress(addr.id, { is_default: true })
    toast.success('نشانی پیش‌فرض به‌روزرسانی شد')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در تغییر نشانی پیش‌فرض')
  }
}

async function handleDeleteAddress(addr: CustomerAddress) {
  try {
    await authStore.removeAddress(addr.id)
    toast.success('نشانی حذف شد')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در حذف نشانی')
  }
}

async function handleLogout() {
  await authStore.logout()
  toast.success('از حساب کاربری خارج شدید')
}

onMounted(async () => {
  await Promise.all([cmsStore.fetchAll(), authStore.hydrateSession()])
  if (authStore.isAuthenticated) {
    await authStore.fetchAddresses()
  }
})

useHead({
  title: 'حساب کاربری و نشانی‌ها | فست‌فودی',
})
</script>

<template>
  <main class="min-h-screen bg-[#FAF7F2] py-10 sm:py-14">
    <div class="container mx-auto max-w-5xl px-4">
      <header class="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-extrabold text-[#292B27] sm:text-3xl">حساب کاربری و دفترچه نشانی</h1>
          <p class="mt-1 text-sm text-[#5A5D56]">مدیریت اطلاعات حساب و نشانی‌های ارسال غذا</p>
        </div>
        <NuxtLink
          v-if="authStore.isAuthenticated"
          to="/orders"
          class="touch-target inline-flex items-center gap-2 rounded-full border border-[#E8E5DC] bg-white px-5 py-2.5 text-sm font-semibold text-[#183A2D] transition-colors hover:bg-[#F4EFE3]"
        >
          <Receipt class="h-4 w-4" />
          <span>سفارش‌های من</span>
        </NuxtLink>
      </header>

      <section
        v-if="!authStore.isAuthenticated"
        class="mx-auto max-w-lg rounded-3xl border border-[#E8E5DC] bg-white p-8 text-center shadow-sm"
      >
        <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#F4EFE3] text-[#183A2D]">
          <User class="h-7 w-7" />
        </div>
        <h2 class="text-xl font-bold text-[#292B27]">برای دسترسی وارد شوید</h2>
        <p class="mt-2 text-sm text-[#5A5D56]">
          با ورود از طریق شماره موبایل و کد یک‌بارمصرف، می‌توانید نشانی‌های خود را مدیریت کنید و سفارش‌ها را پیگیری نمایید.
        </p>
        <button
          type="button"
          class="touch-target mt-6 inline-flex items-center justify-center rounded-full bg-[#183A2D] px-8 py-3.5 text-sm font-bold text-white transition-colors hover:bg-[#12251D]"
          @click="authStore.openAuthModal()"
        >
          ورود با شماره موبایل
        </button>
      </section>

      <div v-else class="space-y-8">
        <section
          v-if="authStore.user?.is_blocked"
          role="alert"
          class="rounded-2xl border border-[#A61B1B]/30 bg-[#FDE8E8] p-4 text-sm font-medium text-[#A61B1B]"
        >
          حساب کاربری شما موقتاً محدود شده است و امکان ثبت سفارش جدید وجود ندارد. لطفاً با پشتیبانی رستوران تماس بگیرید.
        </section>

        <section class="rounded-3xl border border-[#E8E5DC] bg-white p-6 shadow-sm sm:p-8">
          <div class="flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center gap-4">
              <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#F4EFE3] text-[#183A2D]">
                <User class="h-7 w-7" />
              </div>
              <div>
                <h2 class="text-lg font-bold text-[#292B27]">
                  {{ authStore.user?.full_name || 'مشتری فست‌فودی' }}
                </h2>
                <p dir="ltr" class="mt-0.5 text-sm font-semibold text-[#5A5D56]">
                  {{ toPersianDigits(authStore.user?.phone) }}
                </p>
                <p v-if="authStore.user?.date_joined" class="mt-1 text-xs text-[#72756E]">
                  عضویت از {{ formatDateTime(authStore.user.date_joined) }}
                </p>
              </div>
            </div>

            <button
              type="button"
              class="touch-target inline-flex items-center gap-2 rounded-full border border-[#A61B1B]/25 bg-[#FDE8E8] px-5 py-2.5 text-sm font-semibold text-[#A61B1B] transition-colors hover:bg-[#A61B1B] hover:text-white"
              @click="handleLogout"
            >
              <LogOut class="h-4 w-4" />
              <span>خروج از حساب</span>
            </button>
          </div>
        </section>

        <section class="rounded-3xl border border-[#E8E5DC] bg-white p-6 shadow-sm sm:p-8">
          <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 class="text-xl font-bold text-[#292B27]">نشانی‌های ثبت‌شده</h2>
              <p class="mt-1 text-xs text-[#5A5D56]">
                هزینه ارسال داخل محدوده {{ formatToman(cmsStore.inZoneFee) }} و خارج از محدوده {{ formatToman(cmsStore.outZoneFee) }} است.
              </p>
            </div>
            <button
              type="button"
              class="touch-target inline-flex items-center gap-2 rounded-full bg-[#183A2D] px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#12251D]"
              @click="openCreateDialog"
            >
              <Plus class="h-4 w-4" />
              <span>افزودن نشانی جدید</span>
            </button>
          </div>

          <div v-if="authStore.loadingAddresses" class="grid gap-4 sm:grid-cols-2">
            <div v-for="i in 2" :key="i" class="h-40 animate-pulse rounded-2xl bg-[#F4EFE3]" />
          </div>

          <div
            v-else-if="authStore.addresses.length === 0"
            class="rounded-2xl border border-dashed border-[#E8E5DC] bg-[#FAF7F2] p-8 text-center"
          >
            <MapPin class="mx-auto mb-3 h-9 w-9 text-[#5A5D56]" />
            <p class="text-sm font-semibold text-[#292B27]">هنوز نشانی ذخیره شده‌ای ندارید</p>
            <p class="mt-1 text-xs text-[#5A5D56]">برای سفارش‌های تحویل در محل، نشانی خود را اضافه کنید.</p>
          </div>

          <div v-else class="grid gap-4 sm:grid-cols-2">
            <article
              v-for="addr in authStore.addresses"
              :key="addr.id"
              class="flex flex-col justify-between rounded-2xl border p-5 transition-colors"
              :class="addr.is_default ? 'border-[#183A2D] bg-[#FAF7F2]' : 'border-[#E8E5DC] bg-white'"
            >
              <div>
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <h3 class="text-base font-bold text-[#292B27]">{{ addr.title || 'نشانی' }}</h3>
                  <div class="flex flex-wrap items-center gap-1.5">
                    <span
                      v-if="addr.is_default"
                      class="rounded-full bg-[#EDF7ED] px-2.5 py-0.5 text-xs font-bold text-[#1E5E22]"
                    >
                      پیش‌فرض
                    </span>
                    <span
                      class="rounded-full px-2.5 py-0.5 text-xs font-bold"
                      :class="
                        addr.is_out_of_zone
                          ? 'bg-[#FFF4E5] text-[#9A4300]'
                          : 'bg-[#F8F3E8] text-[#8A651C]'
                      "
                    >
                      {{ addr.is_out_of_zone ? 'خارج از محدوده' : 'داخل محدوده' }}
                    </span>
                  </div>
                </div>
                <p class="mt-3 text-sm leading-6 text-[#292B27]">
                  {{ addr.address_text }}
                </p>
                <p class="mt-2 text-xs text-[#5A5D56]">
                  تحویل‌گیرنده: {{ addr.recipient_name || 'مشتری' }}
                  <span v-if="addr.recipient_phone" dir="ltr" class="mr-2 font-semibold">
                    ({{ toPersianDigits(addr.recipient_phone) }})
                  </span>
                </p>
              </div>

              <div class="mt-5 flex flex-wrap items-center gap-2 border-t border-[#E8E5DC] pt-4">
                <button
                  v-if="!addr.is_default"
                  type="button"
                  class="touch-target inline-flex items-center gap-1.5 rounded-full border border-[#E8E5DC] bg-white px-3.5 py-1.5 text-xs font-semibold text-[#183A2D] hover:bg-[#F4EFE3]"
                  @click="handleSetDefault(addr)"
                >
                  <Check class="h-3.5 w-3.5" />
                  <span>پیش‌فرض شود</span>
                </button>
                <button
                  type="button"
                  class="touch-target inline-flex items-center gap-1.5 rounded-full border border-[#E8E5DC] bg-white px-3.5 py-1.5 text-xs font-semibold text-[#292B27] hover:bg-[#F4EFE3]"
                  @click="openEditDialog(addr)"
                >
                  <Pencil class="h-3.5 w-3.5" />
                  <span>ویرایش</span>
                </button>
                <button
                  type="button"
                  class="touch-target inline-flex items-center gap-1.5 rounded-full border border-[#A61B1B]/20 bg-[#FDE8E8] px-3.5 py-1.5 text-xs font-semibold text-[#A61B1B] hover:bg-[#A61B1B] hover:text-white"
                  @click="handleDeleteAddress(addr)"
                >
                  <Trash2 class="h-3.5 w-3.5" />
                  <span>حذف</span>
                </button>
              </div>
            </article>
          </div>
        </section>
      </div>
    </div>

    <dialog
      ref="addressDialogRef"
      closedby="any"
      aria-labelledby="address-dialog-title"
      class="modal-top-layer m-auto w-full max-w-lg rounded-3xl border border-[#E8E5DC] bg-white p-0 text-[#292B27] shadow-xl"
    >
      <div class="p-6 sm:p-8">
        <div class="mb-6 flex items-center justify-between gap-4">
          <h2 id="address-dialog-title" class="text-xl font-extrabold text-[#292B27]">
            {{ editingAddressId !== null ? 'ویرایش نشانی' : 'افزودن نشانی جدید' }}
          </h2>
          <button
            type="button"
            class="touch-target rounded-full px-3 py-1.5 text-sm font-semibold text-[#5A5D56] hover:bg-[#F4EFE3]"
            @click="closeAddressDialog"
          >
            بستن
          </button>
        </div>

        <div
          v-if="formError"
          role="alert"
          aria-live="polite"
          class="mb-4 rounded-xl border border-[#A61B1B]/25 bg-[#FDE8E8] p-3 text-sm font-medium text-[#A61B1B]"
        >
          {{ formError }}
        </div>

        <form class="space-y-4" novalidate @submit.prevent="handleSaveAddress">
          <div>
            <label for="addr-title" class="mb-1.5 block text-sm font-semibold text-[#292B27]">
              عنوان نشانی
            </label>
            <input
              id="addr-title"
              v-model="form.title"
              type="text"
              autocomplete="address-level2"
              placeholder="مثلاً منزل یا محل کار"
              class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-4 py-3 text-sm text-[#292B27] focus:border-[#183A2D] focus:bg-white focus:outline-none"
            />
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label for="addr-recipient-name" class="mb-1.5 block text-sm font-semibold text-[#292B27]">
                نام تحویل‌گیرنده
              </label>
              <input
                id="addr-recipient-name"
                v-model="form.recipient_name"
                type="text"
                autocomplete="name"
                class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-4 py-3 text-sm text-[#292B27] focus:border-[#183A2D] focus:bg-white focus:outline-none"
              />
            </div>

            <div>
              <label for="addr-recipient-phone" class="mb-1.5 block text-sm font-semibold text-[#292B27]">
                شماره تماس تحویل‌گیرنده
              </label>
              <input
                id="addr-recipient-phone"
                v-model="form.recipient_phone"
                type="tel"
                dir="ltr"
                autocomplete="tel"
                inputmode="tel"
                placeholder="09123456789"
                class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-4 py-3 text-sm text-[#292B27] focus:border-[#183A2D] focus:bg-white focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label for="addr-text" class="mb-1.5 block text-sm font-semibold text-[#292B27]">
              نشانی کامل پستی *
            </label>
            <textarea
              id="addr-text"
              v-model="form.address_text"
              rows="3"
              autocomplete="street-address"
              required
              placeholder="خیابان، کوچه، پلاک و واحد را دقیق بنویسید"
              class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-4 py-3 text-sm text-[#292B27] focus:border-[#183A2D] focus:bg-white focus:outline-none"
              :aria-invalid="Boolean(addressTextError)"
              @blur="touched.address_text = true"
            />
            <p v-if="addressTextError" class="mt-1 text-xs font-medium text-[#A61B1B]">
              {{ addressTextError }}
            </p>
          </div>

          <label class="flex cursor-pointer items-center gap-3 rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] p-3.5 text-sm">
            <input
              v-model="form.is_out_of_zone"
              type="checkbox"
              class="h-4 w-4 accent-[#183A2D]"
            />
            <span>
              نشانی خارج از محدوده اصلی است (تعرفه ارسال: {{ formatToman(form.is_out_of_zone ? cmsStore.outZoneFee : cmsStore.inZoneFee) }})
            </span>
          </label>

          <label class="flex cursor-pointer items-center gap-3 rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] p-3.5 text-sm">
            <input
              v-model="form.is_default"
              type="checkbox"
              class="h-4 w-4 accent-[#183A2D]"
            />
            <span>تنظیم به عنوان نشانی پیش‌فرض</span>
          </label>

          <div class="flex flex-wrap items-center justify-end gap-3 pt-2">
            <button
              type="button"
              class="touch-target rounded-full border border-[#E8E5DC] bg-white px-6 py-2.5 text-sm font-semibold text-[#292B27] hover:bg-[#F4EFE3]"
              @click="closeAddressDialog"
            >
              انصراف
            </button>
            <button
              type="submit"
              :disabled="savingAddress"
              class="touch-target rounded-full bg-[#183A2D] px-7 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#12251D] disabled:opacity-60"
            >
              {{ savingAddress ? 'در حال ذخیره...' : 'ذخیره نشانی' }}
            </button>
          </div>
        </form>
      </div>
    </dialog>
  </main>
</template>
