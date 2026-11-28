<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    showRadialGradient?: boolean
    asBackdrop?: boolean
  }>(),
  {
    showRadialGradient: true,
    asBackdrop: false,
  }
)

const auroraGradient =
  '[--aurora:repeating-linear-gradient(100deg,rgba(24,58,45,0.32)_8%,rgba(214,168,75,0.28)_16%,rgba(34,78,61,0.25)_24%,rgba(244,239,227,0.45)_30%,rgba(24,58,45,0.32)_38%)]'
</script>

<template>
  <div
    v-if="asBackdrop"
    class="fixed inset-0 pointer-events-none z-0 overflow-hidden"
    aria-hidden="true"
  >
    <div
      class="absolute -inset-[10px] opacity-40 will-change-transform filter blur-[12px] invert"
      :class="[
        auroraGradient,
        `
        [--white-gradient:repeating-linear-gradient(100deg,var(--white)_0%,var(--white)_7%,var(--transparent)_10%,var(--transparent)_12%,var(--white)_16%)]
        [background-image:var(--white-gradient),var(--aurora)]
        [background-size:300%,_200%]
        [background-position:50%_50%,50%_50%]
        after:content-[''] after:absolute after:inset-0 after:[background-image:var(--white-gradient),var(--aurora)]
        after:[background-size:200%,_100%]
        after:animate-aurora after:[background-attachment:fixed] after:mix-blend-difference
        `,
        props.showRadialGradient &&
          `[mask-image:radial-gradient(ellipse_at_100%_0%,black_10%,var(--transparent)_70%)]`,
      ]"
    />
  </div>

  <div
    v-else
    class="relative flex flex-col min-h-screen items-center justify-center bg-[var(--color-surface-cream)] text-[var(--color-text-primary)] transition-colors"
  >
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div
        class="absolute -inset-[10px] opacity-50 will-change-transform filter blur-[10px] invert"
        :class="[
          auroraGradient,
          `
          [--white-gradient:repeating-linear-gradient(100deg,var(--white)_0%,var(--white)_7%,var(--transparent)_10%,var(--transparent)_12%,var(--white)_16%)]
          [background-image:var(--white-gradient),var(--aurora)]
          [background-size:300%,_200%]
          [background-position:50%_50%,50%_50%]
          after:content-[''] after:absolute after:inset-0 after:[background-image:var(--white-gradient),var(--aurora)]
          after:[background-size:200%,_100%]
          after:animate-aurora after:[background-attachment:fixed] after:mix-blend-difference
          `,
          props.showRadialGradient &&
            `[mask-image:radial-gradient(ellipse_at_100%_0%,black_10%,var(--transparent)_70%)]`,
        ]"
      />
    </div>

    <div class="relative z-10 w-full">
      <slot />
    </div>
  </div>
</template>
