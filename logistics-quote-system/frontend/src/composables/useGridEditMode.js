import { ref } from 'vue'

// Keys that drive cell-to-cell navigation when not in edit mode.
const NAV_KEYS = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Enter']

export function isRadioInput(el) {
  return el?.tagName === 'INPUT' && el.type === 'radio'
}

export function isCheckboxInput(el) {
  return el?.tagName === 'INPUT' && el.type === 'checkbox'
}

export function isTextInputElement(el) {
  if (!el) return false
  if (el.tagName === 'TEXTAREA') return true
  return el.tagName === 'INPUT' && el.type !== 'radio' && el.type !== 'checkbox'
}

// el-select / el-autocomplete reflect their open dropdown via aria-expanded,
// either on the input itself (el-select) or on a role="combobox" wrapper (el-autocomplete).
export function isExpandableControlOpen(el) {
  if (!el?.getAttribute) return false
  if (el.getAttribute('aria-expanded') === 'true') return true
  const combobox = el.closest?.('[role="combobox"]')
  return combobox?.getAttribute('aria-expanded') === 'true'
}

export function isPrintableKey(e) {
  return e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey
}

/**
 * Decide how a keydown on a grid cell should be handled, per
 * docs/adr/0001-grid-cell-navigation-edit-mode.md.
 *
 * - 'navigate'     caller should move focus to an adjacent cell (preventDefault as needed)
 * - 'pass-through' do nothing, let the browser/widget handle the key natively
 * - 'noop'         preventDefault and do nothing (↑↓ while editing text)
 * - 'enter-edit'   typing in selection mode — flip to edit mode, let native overwrite proceed
 * - 'ignore'       not a key this grid cares about
 */
export function decideKeyAction(e, isEditing) {
  const target = e.target

  if (isRadioInput(target) || isCheckboxInput(target)) {
    return NAV_KEYS.includes(e.key) ? 'navigate' : 'ignore'
  }

  if (!isTextInputElement(target)) return 'ignore'

  if (!NAV_KEYS.includes(e.key)) {
    return !isEditing && isPrintableKey(e) ? 'enter-edit' : 'ignore'
  }

  if (isExpandableControlOpen(target)) {
    return e.key === 'Enter' ? 'navigate' : 'pass-through'
  }

  if (isEditing) {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') return 'pass-through'
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') return 'noop'
    return 'navigate' // Enter
  }

  return 'navigate'
}

/**
 * Shared selection-mode/edit-mode state for one Excel-style grid.
 * Only one element can have focus at a time, so a single isEditing flag
 * is sufficient — instantiate one per grid (Step1/Step2/Step3 each get their own).
 */
export function useGridEditMode() {
  const isEditing = ref(false)

  const onCellFocusIn = (e) => {
    isEditing.value = false
    if (isTextInputElement(e.target)) {
      e.target.select()
    }
  }

  const onCellDblClick = (e) => {
    if (isTextInputElement(e.target)) {
      isEditing.value = true
    }
  }

  // Clicking a cell that already has focus repositions the text cursor,
  // so it should also enter edit mode (checked before focus changes).
  const onCellMouseDown = (e) => {
    if (isTextInputElement(e.target) && document.activeElement === e.target) {
      isEditing.value = true
    }
  }

  // Applies decideKeyAction's selection/edit-mode bookkeeping (entering edit
  // mode, no-opping ↑↓ while editing, ignoring/passing through). Returns true
  // if the caller should continue with its own cell/row navigation logic.
  const handleEditTransition = (e) => {
    const action = decideKeyAction(e, isEditing.value)
    switch (action) {
      case 'ignore':
      case 'pass-through':
        return false
      case 'enter-edit':
        isEditing.value = true
        return false
      case 'noop':
        e.preventDefault()
        return false
      default:
        return true
    }
  }

  return {
    isEditing,
    onCellFocusIn,
    onCellDblClick,
    onCellMouseDown,
    decideKeyAction,
    handleEditTransition,
  }
}
