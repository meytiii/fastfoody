<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  variant?: 'primary' | 'gold' | 'secondary' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
  class?: string
  ariaLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  type: 'button',
  disabled: false,
  class: '',
  ariaLabel: undefined,
})

const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'text-xs px-4 py-2 min-h-[38px] rounded-full'
    case 'lg':
      return 'text-base px-8 py-3.5 min-h-[50px] rounded-full'
    case 'md':
    default:
      return 'text-sm px-6 py-3 min-h-[44px] rounded-full'
  }
})

const variantClass = computed(() => {
  return `gooey-button--${props.variant}`
})
</script>

<template>
  <button
    :type="type"
    :disabled="disabled"
    :aria-label="ariaLabel"
    :class="[
      'gooey-button touch-target group',
      variantClass,
      sizeClasses,
      props.class,
    ]"
    @click="(e) => emit('click', e)"
  >
    <span class="relative z-10 flex items-center justify-center gap-2 font-bold leading-none pointer-events-none">
      <slot />
    </span>
    <div class="bubbles" aria-hidden="true">
      <span v-for="i in 5" :key="i"></span>
    </div>
  </button>
</template>

