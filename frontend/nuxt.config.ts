import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: false },
  modules: ['@pinia/nuxt'],
  css: ['~/assets/css/main.css'],
  vite: {
    plugins: [
      tailwindcss(),
    ],
  },
  app: {
    head: {
      htmlAttrs: {
        lang: 'fa',
        dir: 'rtl',
      },
      title: 'فست‌فودی | فست‌فود دست‌ساز با مواد اولیه تازه',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'تجربه طعم‌های اصیل و سالم؛ برگر، پیتزا ناپلی، پاستا و سالادهای ارگانیک دست‌ساز با ارسال گرم در فست‌فودی' },
        { name: 'theme-color', content: '#183A2D' },
      ],
      link: [
        { rel: 'icon', type: 'image/png', href: '/favicon.png' },
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Vazirmatn:wght@300;400;500;600;700;800&display=swap' },
      ],
    },
  },
})
