// composables/useGridEditMode.test.js
import { describe, it, expect, vi } from 'vitest'
import {
  decideKeyAction,
  isRadioInput,
  isCheckboxInput,
  isTextInputElement,
  isExpandableControlOpen,
  isPrintableKey,
  useGridEditMode,
} from './useGridEditMode'

// Minimal mock of a DOM element, only implementing what decideKeyAction touches.
const mockEl = ({ tagName = 'INPUT', type = 'text', expanded = false, comboboxExpanded = null } = {}) => ({
  tagName,
  type,
  getAttribute: (name) => (name === 'aria-expanded' ? (expanded ? 'true' : 'false') : null),
  closest: (selector) =>
    selector === '[role="combobox"]' && comboboxExpanded !== null
      ? { getAttribute: () => (comboboxExpanded ? 'true' : 'false') }
      : null,
})

const keydown = (key, target, extra = {}) => ({ key, target, ctrlKey: false, metaKey: false, altKey: false, ...extra })

describe('isRadioInput', () => {
  it('returns true for radio inputs', () => {
    expect(isRadioInput(mockEl({ type: 'radio' }))).toBe(true)
  })

  it('returns false for text inputs', () => {
    expect(isRadioInput(mockEl({ type: 'text' }))).toBe(false)
  })

  it('returns false for null', () => {
    expect(isRadioInput(null)).toBe(false)
  })
})

describe('isCheckboxInput', () => {
  it('returns true for checkbox inputs', () => {
    expect(isCheckboxInput(mockEl({ type: 'checkbox' }))).toBe(true)
  })

  it('returns false for text inputs', () => {
    expect(isCheckboxInput(mockEl({ type: 'text' }))).toBe(false)
  })

  it('returns false for null', () => {
    expect(isCheckboxInput(null)).toBe(false)
  })
})

describe('isTextInputElement', () => {
  it('returns true for text/number inputs', () => {
    expect(isTextInputElement(mockEl({ type: 'text' }))).toBe(true)
    expect(isTextInputElement(mockEl({ type: 'number' }))).toBe(true)
  })

  it('returns true for textarea', () => {
    expect(isTextInputElement(mockEl({ tagName: 'TEXTAREA' }))).toBe(true)
  })

  it('returns false for radio and checkbox inputs', () => {
    expect(isTextInputElement(mockEl({ type: 'radio' }))).toBe(false)
    expect(isTextInputElement(mockEl({ type: 'checkbox' }))).toBe(false)
  })

  it('returns false for buttons', () => {
    expect(isTextInputElement(mockEl({ tagName: 'BUTTON' }))).toBe(false)
  })
})

describe('isExpandableControlOpen', () => {
  it('detects an open el-select via aria-expanded on the input itself', () => {
    expect(isExpandableControlOpen(mockEl({ expanded: true }))).toBe(true)
  })

  it('returns false when collapsed', () => {
    expect(isExpandableControlOpen(mockEl({ expanded: false }))).toBe(false)
  })

  it('detects an open el-autocomplete via the role=combobox wrapper', () => {
    expect(isExpandableControlOpen(mockEl({ expanded: false, comboboxExpanded: true }))).toBe(true)
  })
})

describe('isPrintableKey', () => {
  it('returns true for single-character keys', () => {
    expect(isPrintableKey({ key: 'a', ctrlKey: false, metaKey: false, altKey: false })).toBe(true)
    expect(isPrintableKey({ key: '5', ctrlKey: false, metaKey: false, altKey: false })).toBe(true)
  })

  it('returns false for multi-character key names', () => {
    expect(isPrintableKey({ key: 'Backspace', ctrlKey: false, metaKey: false, altKey: false })).toBe(false)
    expect(isPrintableKey({ key: 'Tab', ctrlKey: false, metaKey: false, altKey: false })).toBe(false)
  })

  it('returns false when a modifier key is held', () => {
    expect(isPrintableKey({ key: 'a', ctrlKey: true, metaKey: false, altKey: false })).toBe(false)
  })
})

describe('decideKeyAction — selection mode (isEditing = false)', () => {
  const target = mockEl({ type: 'text' })

  it('navigates on arrow keys', () => {
    expect(decideKeyAction(keydown('ArrowUp', target), false)).toBe('navigate')
    expect(decideKeyAction(keydown('ArrowDown', target), false)).toBe('navigate')
    expect(decideKeyAction(keydown('ArrowLeft', target), false)).toBe('navigate')
    expect(decideKeyAction(keydown('ArrowRight', target), false)).toBe('navigate')
  })

  it('navigates on Enter', () => {
    expect(decideKeyAction(keydown('Enter', target), false)).toBe('navigate')
  })

  it('enters edit mode when a printable character is typed', () => {
    expect(decideKeyAction(keydown('a', target), false)).toBe('enter-edit')
  })

  it('ignores non-printable, non-nav keys', () => {
    expect(decideKeyAction(keydown('Backspace', target), false)).toBe('ignore')
    expect(decideKeyAction(keydown('Shift', target), false)).toBe('ignore')
  })
})

describe('decideKeyAction — edit mode (isEditing = true)', () => {
  const target = mockEl({ type: 'text' })

  it('passes Left/Right through to native cursor movement', () => {
    expect(decideKeyAction(keydown('ArrowLeft', target), true)).toBe('pass-through')
    expect(decideKeyAction(keydown('ArrowRight', target), true)).toBe('pass-through')
  })

  it('no-ops on Up/Down', () => {
    expect(decideKeyAction(keydown('ArrowUp', target), true)).toBe('noop')
    expect(decideKeyAction(keydown('ArrowDown', target), true)).toBe('noop')
  })

  it('still navigates on Enter (commit + move)', () => {
    expect(decideKeyAction(keydown('Enter', target), true)).toBe('navigate')
  })

  it('ignores further printable characters (already editing)', () => {
    expect(decideKeyAction(keydown('a', target), true)).toBe('ignore')
  })
})

describe('decideKeyAction — expanded el-select/autocomplete', () => {
  const target = mockEl({ type: 'text', expanded: true })

  it('passes arrow keys through for option highlighting, regardless of isEditing', () => {
    expect(decideKeyAction(keydown('ArrowDown', target), false)).toBe('pass-through')
    expect(decideKeyAction(keydown('ArrowDown', target), true)).toBe('pass-through')
    expect(decideKeyAction(keydown('ArrowLeft', target), false)).toBe('pass-through')
  })

  it('still navigates on Enter (commit + move) even while expanded', () => {
    expect(decideKeyAction(keydown('Enter', target), false)).toBe('navigate')
  })
})

describe('decideKeyAction — radio inputs (是否新品)', () => {
  const target = mockEl({ type: 'radio' })

  it('always navigates on arrow keys, regardless of isEditing', () => {
    expect(decideKeyAction(keydown('ArrowUp', target), false)).toBe('navigate')
    expect(decideKeyAction(keydown('ArrowDown', target), true)).toBe('navigate')
    expect(decideKeyAction(keydown('ArrowLeft', target), false)).toBe('navigate')
    expect(decideKeyAction(keydown('ArrowRight', target), false)).toBe('navigate')
  })

  it('navigates on Enter', () => {
    expect(decideKeyAction(keydown('Enter', target), false)).toBe('navigate')
  })

  it('ignores other keys (value only changes via click)', () => {
    expect(decideKeyAction(keydown(' ', target), false)).toBe('ignore')
  })
})

describe('decideKeyAction — checkbox/switch inputs (核算)', () => {
  const target = mockEl({ type: 'checkbox' })

  it('always navigates on arrow keys, regardless of isEditing', () => {
    expect(decideKeyAction(keydown('ArrowUp', target), false)).toBe('navigate')
    expect(decideKeyAction(keydown('ArrowDown', target), true)).toBe('navigate')
    expect(decideKeyAction(keydown('ArrowLeft', target), false)).toBe('navigate')
    expect(decideKeyAction(keydown('ArrowRight', target), false)).toBe('navigate')
  })

  it('navigates on Enter', () => {
    expect(decideKeyAction(keydown('Enter', target), false)).toBe('navigate')
  })

  it('ignores other keys (value only changes via click)', () => {
    expect(decideKeyAction(keydown(' ', target), false)).toBe('ignore')
  })
})

describe('decideKeyAction — non-input targets', () => {
  it('ignores everything for buttons and other elements', () => {
    const target = mockEl({ tagName: 'BUTTON' })
    expect(decideKeyAction(keydown('ArrowDown', target), false)).toBe('ignore')
    expect(decideKeyAction(keydown('Enter', target), false)).toBe('ignore')
  })
})

describe('useGridEditMode — handleEditTransition', () => {
  it('returns true (continue) on navigation keys without changing isEditing', () => {
    const { handleEditTransition, isEditing } = useGridEditMode()
    const target = mockEl({ type: 'text' })
    expect(handleEditTransition(keydown('ArrowDown', target))).toBe(true)
    expect(isEditing.value).toBe(false)
  })

  it('enters edit mode and stops on a printable key in selection mode', () => {
    const { handleEditTransition, isEditing } = useGridEditMode()
    const target = mockEl({ type: 'text' })
    expect(handleEditTransition(keydown('a', target))).toBe(false)
    expect(isEditing.value).toBe(true)
  })

  it('prevents default and stops on ArrowUp/Down while editing', () => {
    const { handleEditTransition, isEditing } = useGridEditMode()
    isEditing.value = true
    const target = mockEl({ type: 'text' })
    const e = { ...keydown('ArrowDown', target), preventDefault: vi.fn() }
    expect(handleEditTransition(e)).toBe(false)
    expect(e.preventDefault).toHaveBeenCalled()
  })

  it('stops without side effects for ignore/pass-through actions', () => {
    const { handleEditTransition, isEditing } = useGridEditMode()
    const target = mockEl({ tagName: 'BUTTON' })
    expect(handleEditTransition(keydown('ArrowDown', target))).toBe(false)
    expect(isEditing.value).toBe(false)
  })
})
