import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useRouteCopyStore = defineStore('routeCopy', () => {
  const copyTemplate = ref(null)
  const sourceLabel  = ref('')

  const setCopyTemplate = (data, label) => {
    copyTemplate.value = data
    sourceLabel.value  = label
  }

  const clearCopyTemplate = () => {
    copyTemplate.value = null
    sourceLabel.value  = ''
  }

  return { copyTemplate, sourceLabel, setCopyTemplate, clearCopyTemplate }
})
