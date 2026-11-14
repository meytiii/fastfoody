<script setup lang="ts">
import { ref } from 'vue'
import {
  ChefHat,
  MapPin,
  Phone,
  Mail,
  Clock,
  Instagram,
  Send,
  ArrowLeft,
} from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const emailInput = ref('')

const handleSubscribe = () => {
  if (!emailInput.value) return
  toast.success('ایمیل شما با موفقیت در خبرنامه ویژه فست‌فودی ثبت شد')
  emailInput.value = ''
}
</script>

<template>
  <footer
    class="bg-[var(--color-brand-forest-deep)] text-white/80 pt-16 pb-12"
    role="contentinfo"
  >
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      
      <div class="grid grid-cols-1 gap-10 md:grid-cols-2 lg:grid-cols-12 pb-12 border-b border-white/10">
        
        <div class="space-y-4 lg:col-span-4">
          <div class="flex items-center gap-3">
            <div
              class="flex h-11 w-11 items-center justify-center rounded-full bg-[var(--color-brand-forest)] text-white shadow-xs"
            >
              <img
                src="/svg/chef.svg"
                alt="Chef"
                class="h-6 w-6 filter invert brightness-0"
              />
            </div>
            <div>
              <span class="text-xl font-bold tracking-tight text-white">
                فست‌فودی
              </span>
              <p class="text-[11px] text-[var(--color-accent-gold)]">
                دست‌پخت اصیل • مواد ارگانیک
              </p>
            </div>
          </div>

          <p class="text-xs leading-relaxed text-white/70 max-w-sm">
            فست‌فودی با تلفیق هنر آشپزی اسکاندیناوی و میهمان‌نوازی گرم ایرانی، برگرها، پیتزاها و سالادهای دست‌ساز سالم را با بالاترین استانداردهای بهداشتی و طعم فراموش‌نشدنی ارائه می‌دهد.
          </p>

          <div class="space-y-2 pt-2 text-xs">
            <div class="flex items-start gap-2.5">
              <MapPin :size="16" class="mt-0.5 text-[var(--color-accent-gold)] shrink-0" />
              <span>تهران، خیابان ولیعصر، نرسیده به پارک وی، پلاک ۱۲۴</span>
            </div>
            <div class="flex items-center gap-2.5">
              <Phone :size="16" class="text-[var(--color-accent-gold)] shrink-0" />
              <bdi class="text-white font-semibold">۰۲۱-۲۲۰۰۵۵۸۸</bdi>
            </div>
          </div>
        </div>

        
        <div class="space-y-3 lg:col-span-2">
          <h4 class="text-sm font-bold text-white">دسترسی سریع</h4>
          <ul class="space-y-2 text-xs">
            <li>
              <a href="/#hero" class="hover:text-white transition-colors">صفحه نخست</a>
            </li>
            <li>
              <a href="/#menu" class="hover:text-white transition-colors">منوی کامل غذاها</a>
            </li>
            <li>
              <a href="/#specials" class="hover:text-white transition-colors">پیشنهاد سرآشپز</a>
            </li>
            <li>
              <a href="/#reservation" class="hover:text-white transition-colors">رزرو آنلاین میز</a>
            </li>
            <li>
              <a href="/#testimonials" class="hover:text-white transition-colors">نظرات مشتریان</a>
            </li>
          </ul>
        </div>

        
        <div class="space-y-3 lg:col-span-3">
          <h4 class="text-sm font-bold text-white">ساعات کاری و تحویل</h4>
          <div class="space-y-2.5 text-xs text-white/70">
            <div class="rounded-xl bg-white/5 p-3 border border-white/5 space-y-1">
              <div class="flex items-center justify-between text-white font-semibold">
                <span>شنبه تا چهارشنبه:</span>
                <bdi>۱۱:۳۰ الی ۲۳:۴۵</bdi>
              </div>
              <p class="text-[11px] text-white/50">ارسال پیک درون‌شهری تا ۲۳:۳۰</p>
            </div>

            <div class="rounded-xl bg-white/5 p-3 border border-white/5 space-y-1">
              <div class="flex items-center justify-between text-white font-semibold">
                <span>پنج‌شنبه و جمعه:</span>
                <bdi>۱۲:۰۰ الی ۲۴:۰۰</bdi>
              </div>
              <p class="text-[11px] text-[var(--color-accent-gold)]">پیشنهاد می‌شود از قبل میز رزرو نمایید</p>
            </div>
          </div>
        </div>

        
        <div class="space-y-3 lg:col-span-3">
          <h4 class="text-sm font-bold text-white">باشگاه مشتریان فست‌فودی</h4>
          <p class="text-xs text-white/70">
            با عضویت در خبرنامه، از تخفیف‌های فصلی و منوی مخفی سرآشپز مطلع شوید.
          </p>
          <form @submit.prevent="handleSubscribe" class="space-y-2">
            <div class="relative">
              <input
                v-model="emailInput"
                type="email"
                placeholder="ایمیل خود را وارد نمایید..."
                class="w-full rounded-full border border-white/10 bg-white/5 py-2.5 ps-4 pe-10 text-xs text-white placeholder-white/40 focus:border-[var(--color-accent-gold)] focus:outline-none"
              />
              <GooeyButton
                type="submit"
                variant="gold"
                class="!absolute inset-inline-end-1 top-1 bottom-1 !h-7 !w-7 !min-h-0 !p-0 !rounded-full"
                aria-label="عضویت در خبرنامه"
              >
                <ArrowLeft :size="14" class="icon-directional" />
              </GooeyButton>
            </div>
          </form>
        </div>
      </div>

      
      <div class="pt-8 flex items-center justify-center text-xs text-white/50">
        <p>
          طراحی شده توسط تیم Besporman
        </p>
      </div>
    </div>
  </footer>
</template>

