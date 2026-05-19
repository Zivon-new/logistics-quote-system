<template>
  <el-select v-bind="$attrs" :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <el-option v-for="c in CURRENCIES" :key="c.value" :label="c.label" :value="c.value" />
  </el-select>
</template>

<script setup>
defineOptions({ inheritAttrs: false })

defineProps({ modelValue: String })
defineEmits(['update:modelValue'])

const CURRENCIES = [
  { label: 'RMB',          value: 'RMB' },
  { label: 'USD 美元',     value: 'USD' },
  { label: 'EUR 欧元',     value: 'EUR' },
  { label: 'GBP 英镑',     value: 'GBP' },
  { label: 'AUD 澳元',     value: 'AUD' },
  { label: 'CAD 加元',     value: 'CAD' },
  { label: 'SGD 新加坡元', value: 'SGD' },
  { label: 'HKD 港元',     value: 'HKD' },
  { label: 'JPY 日元',     value: 'JPY' },
  { label: 'MYR 林吉特',   value: 'MYR' },
]
</script>
