<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    showRadialGradient?: boolean
    variant?: 'brand' | 'classic'
    asBackdrop?: boolean
  }>(),
  {
    showRadialGradient: true,
    variant: 'brand',
    asBackdrop: false,
  }
)

const auroraGradient = computed(() => {
  if (props.variant === 'classic') {
    return '[--aurora:repeating-linear-gradient(100deg,var(--blue-500)_10%,var(--indigo-300)_15%,var(--blue-300)_20%,var(--violet-200)_25%,var(--blue-400)_30%)]'
  }
  // Brand Scandinavian Aurora (Forest Green #183A2D, Muted Gold #D6A84B, Warm Ivory #F4EFE3)
  return '[--aurora:repeating-linear-gradient(100deg,rgba(24,58,45,0.32)_8%,rgba(214,168,75,0.28)_16%,rgba(34,78,61,0.25)_24%,rgba(244,239,227,0.45)_30%,rgba(24,58,45,0.32)_38%)]'
})
</script>

<template>
  <!-- As Fixed Backdrop Underlay for All Pages -->
  <div
    v-if="asBackdrop"
    class="fixed inset-0 pointer-events-none z-0 overflow-hidden"
    aria-hidden="true"
  >
    <div
      class="absolute -inset-[10px] opacity-40 will-change-transform filter blur-[12px] invert dark:invert-0"
      :class="[
        auroraGradient,
        `
        [--white-gradient:repeating-linear-gradient(100deg,var(--white)_0%,var(--white)_7%,var(--transparent)_10%,var(--transparent)_12%,var(--white)_16%)]
        [--dark-gradient:repeating-linear-gradient(100deg,var(--black)_0%,var(--black)_7%,var(--transparent)_10%,var(--transparent)_12%,var(--black)_16%)]
        [background-image:var(--white-gradient),var(--aurora)]
        dark:[background-image:var(--dark-gradient),var(--aurora)]
        [background-size:300%,_200%]
        [background-position:50%_50%,50%_50%]
        after:content-[''] after:absolute after:inset-0 after:[background-image:var(--white-gradient),var(--aurora)]
        after:dark:[background-image:var(--dark-gradient),var(--aurora)]
        after:[background-size:200%,_100%]
        after:animate-aurora after:[background-attachment:fixed] after:mix-blend-difference
        `,
        showRadialGradient &&
          `[mask-image:radial-gradient(ellipse_at_100%_0%,black_10%,var(--transparent)_70%)]`,
      ]"
    />
  </div>

  <!-- As Container Component -->
  <div
    v-else
    class="relative flex flex-col min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-900 text-slate-950 transition-colors"
  >
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div
        class="absolute -inset-[10px] opacity-50 will-change-transform filter blur-[10px] invert dark:invert-0"
        :class="[
          auroraGradient,
          `
          [--white-gradient:repeating-linear-gradient(100deg,var(--white)_0%,var(--white)_7%,var(--transparent)_10%,var(--transparent)_12%,var(--white)_16%)]
          [--dark-gradient:repeating-linear-gradient(100deg,var(--black)_0%,var(--black)_7%,var(--transparent)_10%,var(--transparent)_12%,var(--black)_16%)]
          [background-image:var(--white-gradient),var(--aurora)]
          dark:[background-image:var(--dark-gradient),var(--aurora)]
          [background-size:300%,_200%]
          [background-position:50%_50%,50%_50%]
          after:content-[''] after:absolute after:inset-0 after:[background-image:var(--white-gradient),var(--aurora)]
          after:dark:[background-image:var(--dark-gradient),var(--aurora)]
          after:[background-size:200%,_100%]
          after:animate-aurora after:[background-attachment:fixed] after:mix-blend-difference
          `,
          showRadialGradient &&
            `[mask-image:radial-gradient(ellipse_at_100%_0%,black_10%,var(--transparent)_70%)]`,
        ]"
      />
    </div>

    <div class="relative z-10 w-full">
      <slot />
    </div>
  </div>
</template>
