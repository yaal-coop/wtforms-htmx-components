/* Keyboard navigation for the combobox, per the ARIA 1.2 combobox pattern.
 * Handlers sit on the document, so they keep working after htmx swaps. */
(function () {
  function optionButtons(wrap) {
    return Array.from(wrap.querySelectorAll('[role="option"] > button'));
  }

  document.addEventListener("keydown", function (e) {
    const target = e.target;

    // Arrows in the input focus the first or last option, or move from the
    // hovered one. Reopen first: a hidden element cannot take focus.
    if (
      target.matches?.('[role="combobox"]') &&
      (e.key === "ArrowDown" || e.key === "ArrowUp")
    ) {
      const wrap = target.closest(".combobox-wrap");
      if (!wrap) return;
      delete wrap.dataset.comboboxClosed;
      const buttons = optionButtons(wrap);
      if (!buttons.length) return;
      e.preventDefault();
      const hovered = wrap.querySelector('[role="option"] > button:hover');
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
    if (target.matches?.('[role="option"] > button')) {
      const wrap = target.closest(".combobox-wrap");
      if (!wrap) return;
      const buttons = optionButtons(wrap);
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
          wrap.querySelector('[role="combobox"]')?.focus();
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
      const wrap = target.closest(".combobox-wrap");
      if (!wrap) return;
      const chips = wrap.querySelectorAll(".chip");
      if (!chips.length) return;
      e.preventDefault();
      chips[chips.length - 1].querySelector(".chip-remove")?.click();
      return;
    }

    // Enter in the input picks the first option. Otherwise the browser
    // would click the first button of the form, which can be a chip's ×.
    if (e.key === "Enter" && target.matches?.('[role="combobox"]')) {
      const wrap = target.closest(".combobox-wrap");
      if (!wrap) return;
      e.preventDefault();
      const buttons = optionButtons(wrap);
      if (buttons.length) {
        buttons[0].click();
      }
      return;
    }

    // Escape closes the listbox and keeps the focus on the input.
    // data-combobox-closed lets CSS hide the listbox despite :focus-within.
    if (e.key === "Escape" && target.closest?.(".combobox-wrap")) {
      const wrap = target.closest(".combobox-wrap");
      e.preventDefault();
      // Focus before setting the flag, so the focus events cannot clear it.
      wrap.querySelector('[role="combobox"]')?.focus();
      wrap.dataset.comboboxClosed = "true";
    }
  });

  // Typing reopens the listbox. Not on focusin: in Firefox, the Escape
  // handler's refocus would clear the flag it sets.
  function clearClosedState(e) {
    const wrap = e.target.closest?.(".combobox-wrap");
    if (wrap && wrap.dataset.comboboxClosed) {
      delete wrap.dataset.comboboxClosed;
    }
  }
  document.addEventListener("input", clearClosedState);

  // Moving the focus out of the combobox closes the listbox.
  document.addEventListener("focusout", function (e) {
    const wrap = e.target.closest?.(".combobox-wrap");
    if (!wrap) return;
    if (e.relatedTarget?.closest?.(".combobox-wrap") === wrap) return;
    wrap.dataset.comboboxClosed = "true";
  });

  // When an option has the focus, hovering another option moves the focus
  // to it. Hovering never takes the focus from the input.
  document.addEventListener("mouseover", function (e) {
    const btn = e.target.closest?.('[role="option"] > button');
    if (!btn) return;
    if (!btn.closest(".combobox-wrap")) return;
    const active = document.activeElement;
    if (!active?.matches?.('[role="option"] > button')) return;
    if (active === btn) return;
    btn.focus({ preventScroll: true });
  });

  // Browsers ignore autofocus on swapped content: apply it after a pick.
  if (!window.htmx) return;
  htmx.onLoad(function (root) {
    const inputs = root.matches?.('[role="combobox"][autofocus]')
      ? [root]
      : Array.from(root.querySelectorAll?.('[role="combobox"][autofocus]') || []);
    if (inputs.length === 0) return;
    const wrap = inputs[0].closest(".combobox-wrap");
    if (wrap && wrap.dataset.comboboxClosed) {
      delete wrap.dataset.comboboxClosed;
    }
    inputs[0].focus();
  });
})();
