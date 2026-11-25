<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ArrowRight, ChefHat, Eye, EyeOff } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { useBackofficeStore } from '~/stores/backoffice'

const router = useRouter()
const backofficeStore = useBackofficeStore()
const { toEnglishDigits } = usePersian()

const phone = ref('')
const password = ref('')
const showPassword = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const touched = ref({ phone: false, password: false })

const phoneError = computed(() => {
  if (!touched.value.phone) return ''
  const digits = toEnglishDigits(phone.value).replace(/\D/g, '')
  return digits.length < 10 ? 'شماره موبایل معتبر وارد کنید.' : ''
})

const passwordError = computed(() => {
  if (!touched.value.password) return ''
  return password.value.length < 4 ? 'رمز عبور را وارد کنید.' : ''
})

function fillDemoCredentials() {
  phone.value = '09123456789'
  password.value = 'Test@1234'
  errorMessage.value = ''
}

async function handleSubmit() {
  touched.value.phone = true
  touched.value.password = true
  errorMessage.value = ''

  if (phoneError.value || passwordError.value) {
    errorMessage.value = 'لطفاً شماره موبایل و رمز عبور را کامل وارد کنید.'
    return
  }

  submitting.value = true
  try {
    await backofficeStore.login(toEnglishDigits(phone.value.trim()), password.value)
    toast.success('خوش آمدید')
    await router.replace('/backoffice')
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : 'ورود به پنل مدیریت ناموفق بود.'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await backofficeStore.hydrateSession()
  if (backofficeStore.isAuthenticated) {
    await router.replace('/backoffice')
  }
})

useHead({
  title: 'ورود مدیر | پنل مدیریت فست‌فودی',
})
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-[#FAF7F2] px-4 py-12">
    <div class="w-full max-w-md rounded-3xl border border-[#E8E5DC] bg-white p-6 shadow-md sm:p-8">
      <div class="mb-6 flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#183A2D] text-white">
            <ChefHat class="h-6 w-6" />
          </div>
          <div>
            <h1 class="text-xl font-extrabold text-[#292B27]">ورود به پنل مدیریت</h1>
            <p class="text-xs text-[#5A5D56]">ویژه مدیران و آشپزخانه فست‌فودی</p>
          </div>
        </div>
        <NuxtLink
          to="/"
          class="touch-target inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xs font-semibold text-[#5A5D56] hover:bg-[#F4EFE3] hover:text-[#292B27]"
        >
          <ArrowRight class="h-3.5 w-3.5" />
          <span>فروشگاه</span>
        </NuxtLink>
      </div>

      <div class="mb-5 rounded-2xl border border-[#E8E5DC] bg-[#F8F3E8] p-4 text-xs text-[#292B27]">
        <p class="font-bold text-[#8A651C]">اطلاعات آزمایشی مدیر در محیط تست:</p>
        <p class="mt-1">
          موبایل: <span dir="ltr" class="font-mono font-bold">09123456789</span> | رمز عبور:
          <span dir="ltr" class="font-mono font-bold">Test@1234</span>
        </p>
        <button
          type="button"
          class="mt-2.5 rounded-full bg-white px-3.5 py-1.5 text-xs font-bold text-[#183A2D] shadow-xs hover:bg-[#F4EFE3]"
          @click="fillDemoCredentials"
        >
          تکمیل خودکار اطلاعات آزمایشی
        </button>
      </div>

      <div
        v-if="errorMessage"
        role="alert"
        aria-live="polite"
        class="mb-4 rounded-xl border border-[#A61B1B]/25 bg-[#FDE8E8] p-3 text-sm font-medium text-[#A61B1B]"
      >
        {{ errorMessage }}
      </div>

      <form class="space-y-4" novalidate @submit.prevent="handleSubmit">
        <div>
          <label for="staff-phone" class="mb-1.5 block text-sm font-semibold text-[#292B27]">
            شماره موبایل مدیر
          </label>
          <input
            id="staff-phone"
            v-model="phone"
            name="username"
            type="tel"
            dir="ltr"
            autocomplete="username"
            inputmode="tel"
            required
            placeholder="09123456789"
            class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-4 py-3 text-sm text-[#292B27] focus:border-[#183A2D] focus:bg-white focus:outline-none"
            :aria-invalid="Boolean(phoneError)"
            @blur="touched.phone = true"
          />
          <p v-if="phoneError" class="mt-1 text-xs font-medium text-[#A61B1B]">
            {{ phoneError }}
          </p>
        </div>

        <div>
          <label for="staff-password" class="mb-1.5 block text-sm font-semibold text-[#292B27]">
            رمز عبور
          </label>
          <div class="relative">
            <input
              id="staff-password"
              v-model="password"
              name="password"
              :type="showPassword ? 'text' : 'password'"
              dir="ltr"
              autocomplete="current-password"
              required
              class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] py-3 ps-4 pe-12 text-sm text-[#292B27] focus:border-[#183A2D] focus:bg-white focus:outline-none"
              :aria-invalid="Boolean(passwordError)"
              @blur="touched.password = true"
            />
            <button
              type="button"
              class="touch-target absolute inset-y-0 end-1 flex items-center justify-center rounded-lg px-2 text-[#5A5D56] hover:text-[#292B27]"
              :aria-label="showPassword ? 'مخفی کردن رمز عبور' : 'نمایش رمز عبور'"
              :aria-pressed="showPassword"
              @click="showPassword = !showPassword"
            >
              <EyeOff v-if="showPassword" class="h-4 w-4" />
              <Eye v-else class="h-4 w-4" />
            </button>
          </div>
          <p v-if="passwordError" class="mt-1 text-xs font-medium text-[#A61B1B]">
            {{ passwordError }}
          </p>
        </div>

        <button
          type="submit"
          :disabled="submitting"
          class="touch-target w-full rounded-full bg-[#183A2D] py-3.5 text-sm font-bold text-white transition-colors hover:bg-[#12251D] disabled:opacity-60"
        >
          {{ submitting ? 'در حال ورود...' : 'ورود به پنل مدیریت' }}
        </button>
      </form>
    </div>
  </main>
</template>
