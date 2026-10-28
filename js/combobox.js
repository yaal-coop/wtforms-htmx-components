/* Keyboard navigation for the combobox, per the ARIA 1.2 combobox pattern.
 * Handlers sit on the document, so they keep working after htmx swaps.
 * [data-combobox] marks the element that holds the parts of a combobox.
 * Each option is a submit button with role="option". */
(function () {
  const ROOT = "[data-combobox]";
  const OPTION = '[role="option"]';

  function optionButtons(root) {
    return Array.from(root.querySelectorAll(OPTION));
  }

  document.addEventListener("keydown", function (e) {
    const target = e.target;

    // Arrows in the input focus the first or last option, or move from the
    // hovered one. Reopen first: a hidden element cannot take focus.
    if (
      target.matches?.('[role="combobox"]') &&
      (e.key === "ArrowDown" || e.key === "ArrowUp")
    ) {
      const root = target.closest(ROOT);
      if (!root) return;
      delete root.dataset.comboboxClosed;
      const buttons = optionButtons(root);
      if (!buttons.length) return;
      e.preventDefault();
      const hovered = root.querySelector(`${OPTION}:hover`);
      const len = buttons.length;
      let nextIdx;
      if (e.key === "ArrowDown") {
        const startIdx = hovered ? buttons.indexOf(hovered) : -1;
        nextIdx = (startIdx + 1) % len;
      } else {
        const startIdx = hovered ? buttons.indexOf(hovered) : len;
        nextIdx = (startIdx - 1 + len) % len;
      }
      buttons[nextIdx].focus();
      return;
    }

    // Arrow keys / Home / End on an option button
    if (target.matches?.(OPTION)) {
      const root = target.closest(ROOT);
      if (!root) return;
      const buttons = optionButtons(root);
      const idx = buttons.indexOf(target);

      if (e.key === "ArrowDown") {
        e.preventDefault();
        buttons[(idx + 1) % buttons.length].focus();
        return;
      }

      if (e.key === "ArrowUp") {
        e.preventDefault();
        // From the first option, go back to the input.
        if (idx === 0) {
          root.querySelector('[role="combobox"]')?.focus();
        } else {
          buttons[idx - 1].focus();
        }
        return;
      }

      if (e.key === "Home") {
        e.preventDefault();
        buttons[0].focus();
        return;
      }

      if (e.key === "End") {
        e.preventDefault();
        buttons[buttons.length - 1].focus();
        return;
      }
    }

    // Backspace in an empty query removes the last chip (if any).
    if (
      e.key === "Backspace" &&
      target.matches?.('[role="combobox"]') &&
      target.value === ""
    ) {
      const root = target.closest(ROOT);
      if (!root) return;
      const removes = root.querySelectorAll("[data-combobox-remove]");
      if (!removes.length) return;
      e.preventDefault();
      removes[removes.length - 1].click();
      return;
    }

    // Enter in the input picks the first option. Otherwise the browser
    // would click the first button of the form, which can be a chip's ×.
    if (e.key === "Enter" && target.matches?.('[role="combobox"]')) {
      const root = target.closest(ROOT);
      if (!root) return;
      e.preventDefault();
      const buttons = optionButtons(root);
      if (buttons.length) {
        buttons[0].click();
      }
      return;
    }

    // Escape closes the listbox and keeps the focus on the input.
    // data-combobox-closed lets CSS hide the listbox despite :focus-within.
    if (e.key === "Escape" && target.closest?.(ROOT)) {
      const root = target.closest(ROOT);
      e.preventDefault();
      // Focus before setting the flag, so the focus events cannot clear it.
      root.querySelector('[role="combobox"]')?.focus();
      root.dataset.comboboxClosed = "true";
    }
  });

  // Typing reopens the listbox. So does a click on the input.
  function clearClosedState(e) {
    const root = e.target.closest?.(ROOT);
    if (root && root.dataset.comboboxClosed) {
      delete root.dataset.comboboxClosed;
    }
  }
  document.addEventListener("input", clearClosedState);
  document.addEventListener("click", function (e) {
    if (e.target.matches?.('[role="combobox"]')) clearClosedState(e);
  });

  // Focus that comes from outside the combobox reopens the listbox. Focus
  // that moves inside it does not: in Firefox, the Escape handler's
  // refocus would clear the flag it sets.
  document.addEventListener("focusin", function (e) {
    const root = e.target.closest?.(ROOT);
    if (!root) return;
    if (e.relatedTarget?.closest?.(ROOT) === root) return;
    clearClosedState(e);
  });

  // Keep the focus in the input when the user presses an option. Safari does
  // not focus a clicked button: without this, the input would lose the focus
  // to nothing, the listbox would close, and the click would miss the option.
  document.addEventListener("mousedown", function (e) {
    if (e.target.closest?.(OPTION)?.closest(ROOT)) e.preventDefault();
  });

  // Moving the focus out of the combobox closes the listbox.
  document.addEventListener("focusout", function (e) {
    const root = e.target.closest?.(ROOT);
    if (!root) return;
    if (e.relatedTarget?.closest?.(ROOT) === root) return;
    root.dataset.comboboxClosed = "true";
  });

  // When an option has the focus, hovering another option moves the focus
  // to it. Hovering never takes the focus from the input.
  document.addEventListener("mouseover", function (e) {
    const btn = e.target.closest?.(OPTION);
    if (!btn) return;
    if (!btn.closest(ROOT)) return;
    const active = document.activeElement;
    if (!active?.matches?.(OPTION)) return;
    if (active === btn) return;
    btn.focus({ preventScroll: true });
  });

  // Browsers ignore autofocus on swapped content: apply it after a pick.
  if (!window.htmx) return;
  htmx.onLoad(function (elt) {
    const inputs = elt.matches?.('[role="combobox"][autofocus]')
      ? [elt]
      : Array.from(elt.querySelectorAll?.('[role="combobox"][autofocus]') || []);
    if (inputs.length === 0) return;
    const root = inputs[0].closest(ROOT);
    if (root && root.dataset.comboboxClosed) {
      delete root.dataset.comboboxClosed;
    }
    inputs[0].focus();
  });
})();
