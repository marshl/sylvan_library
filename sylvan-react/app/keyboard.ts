// Input types that don't take free text, so shortcuts still apply while they have focus.
// Number inputs are included because they ignore letters and Ctrl+arrow anyway.
const NON_TEXT_INPUT_TYPES = ['button', 'submit', 'reset', 'checkbox', 'radio', 'number'];

/**
 * Whether a key event target is somewhere the user types text, where shortcut keys
 * should behave normally
 */
export function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  if (target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement) return true;
  return target instanceof HTMLInputElement && !NON_TEXT_INPUT_TYPES.includes(target.type);
}
