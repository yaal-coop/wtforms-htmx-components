"""End-to-end tests of the combobox example.

The page has five comboboxes: ``country`` (single, strict),
``country_free`` (single, free), ``countries`` (multi, strict),
``countries_free`` (multi, free) and ``continents`` (multi, suggested
on focus).
"""

from playwright.sync_api import expect


def _goto(page, nav):
    with page.expect_navigation():
        nav.get_by_role("link", name="Combobox").click()


def _wait_for_settle(page):
    """Wait until htmx 2 has processed the swapped elements."""
    page.wait_for_function("!document.querySelector('.htmx-settling')")


def _clear_country_chip(page):
    """Remove the initial FR chip so the search input shows."""
    page.locator('#country-value .chip[data-value="FR"] .chip-remove').click()
    expect(page.locator("#country-value .chip")).to_have_count(0)
    _wait_for_settle(page)


def test_combobox_single_keystroke_swaps_only_listbox(page, nav):
    """Typing in the search input swaps just the listbox, not the input."""
    _goto(page, nav)
    _clear_country_chip(page)
    search = page.locator("input#country-query")
    search.fill("ger")
    listbox = page.locator("ul#country-suggestions")
    expect(listbox.locator("li[role='option']").first).to_be_visible()
    expect(
        listbox.locator("li[role='option'] button", has_text="Germany")
    ).not_to_have_count(0)


def test_combobox_single_click_renders_chip(page, nav):
    """Clicking a suggestion replaces the input with a chip carrying the picked code."""
    _goto(page, nav)
    _clear_country_chip(page)
    page.locator("input#country-query").fill("ger")
    expect(
        page.locator("ul#country-suggestions li[role='option']").first
    ).to_be_visible()
    page.locator("ul#country-suggestions button", has_text="Germany").click()
    chip = page.locator('#country-value .chip[data-value="DE"]')
    expect(chip).to_have_count(1)


def test_combobox_single_remove_chip_clears_value(page, nav):
    """Clicking the chip's × clears the value and restores the search input."""
    _goto(page, nav)
    chip = page.locator('#country-value .chip[data-value="FR"]')
    expect(chip).to_be_visible()
    chip.locator(".chip-remove").click()
    expect(page.locator("#country-value .chip")).to_have_count(0)
    expect(page.locator("input#country-query")).to_be_visible()


def test_combobox_multi_add_chip(page, nav):
    """Clicking a multi-suggestion adds a chip for that country."""
    _goto(page, nav)
    page.locator("input#countries-query").fill("ger")
    expect(
        page.locator("ul#countries-suggestions li[role='option']").first
    ).to_be_visible()
    page.locator("ul#countries-suggestions button", has_text="Germany").click()
    chip = page.locator("#countries-value .chip", has_text="Germany")
    expect(chip).to_have_count(1)


def test_combobox_multi_listbox_reopens_after_pick(page, nav):
    """Typing again after a pick must re-populate the listbox."""
    _goto(page, nav)
    page.locator("input#countries-query").fill("ger")
    expect(
        page.locator("ul#countries-suggestions li[role='option']").first
    ).to_be_visible()
    page.locator("ul#countries-suggestions button", has_text="Germany").click()
    expect(page.locator("#countries-value .chip", has_text="Germany")).to_be_visible()
    expect(page.locator("input#countries-query")).to_have_value("")
    _wait_for_settle(page)

    # Refill with a query whose match isn't already picked.
    page.locator("input#countries-query").fill("spa")
    expect(
        page.locator("ul#countries-suggestions li[role='option']").first
    ).to_be_visible()
    expect(
        page.locator(
            "ul#countries-suggestions li[role='option'] button", has_text="Spain"
        )
    ).not_to_have_count(0)


def test_combobox_multi_remove_chip(page, nav):
    """Clicking the chip's ``×`` removes it from the list."""
    _goto(page, nav)
    page.locator("input#countries-query").fill("ger")
    expect(
        page.locator("ul#countries-suggestions li[role='option']").first
    ).to_be_visible()
    page.locator("ul#countries-suggestions button", has_text="Germany").click()
    chip = page.locator("#countries-value .chip", has_text="Germany")
    expect(chip).to_be_visible()

    chip.locator(".chip-remove").click()
    expect(page.locator('#countries-value .chip[data-value="DE"]')).to_have_count(0)


def test_combobox_multi_focus_returns_to_query_after_pick(page, nav):
    """Picking a multi suggestion returns focus to the query input."""
    _goto(page, nav)
    page.locator("input#countries-query").fill("ger")
    expect(
        page.locator("ul#countries-suggestions li[role='option']").first
    ).to_be_visible()
    page.locator("ul#countries-suggestions button", has_text="Germany").click()
    expect(page.locator("input#countries-query")).to_be_focused()


def test_combobox_backspace_removes_last_chip(page, nav):
    """Backspace in an empty query removes the last chip."""
    _goto(page, nav)
    query = page.locator("input#countries-query")
    query.fill("ger")
    expect(
        page.locator("ul#countries-suggestions li[role='option']").first
    ).to_be_visible()
    page.locator("ul#countries-suggestions button", has_text="Germany").click()
    expect(page.locator("#countries-value .chip", has_text="Germany")).to_be_visible()
    query.press("Backspace")
    expect(page.locator('#countries-value .chip[data-value="DE"]')).to_have_count(0)


def test_combobox_single_free_synthetic_option_appears(page, nav):
    """Typing an off-catalog query surfaces an "Add" option in the listbox."""
    _goto(page, nav)
    page.locator("input#country_free-query").fill("Atlantis")
    listbox = page.locator("ul#country_free-suggestions")
    expect(listbox.locator("li[role='option']").first).to_be_visible()
    expect(listbox.locator("button", has_text='Add "Atlantis"')).to_have_count(1)


def test_combobox_single_free_pick_synthetic_renders_chip(page, nav):
    """Clicking the synthetic option commits the raw query and surfaces a chip."""
    _goto(page, nav)
    page.locator("input#country_free-query").fill("Atlantis")
    expect(
        page.locator("ul#country_free-suggestions li[role='option']").first
    ).to_be_visible()
    page.locator("ul#country_free-suggestions button", has_text="Atlantis").click()
    chip = page.locator('#country_free-value .chip[data-value="Atlantis"]')
    expect(chip).to_have_count(1)


def test_combobox_single_free_synthetic_suppressed_when_catalog_match(page, nav):
    """An exact catalog label doesn't double up with a synthetic option."""
    _goto(page, nav)
    page.locator("input#country_free-query").fill("France")
    listbox = page.locator("ul#country_free-suggestions")
    expect(listbox.locator("li[role='option']").first).to_be_visible()
    expect(listbox.locator("button", has_text='Add "France"')).to_have_count(0)


def test_combobox_multi_free_synthetic_pick_adds_chip(page, nav):
    """Picking the synthetic option appends a chip with the raw query."""
    _goto(page, nav)
    page.locator("input#countries_free-query").fill("Atlantis")
    expect(
        page.locator("ul#countries_free-suggestions li[role='option']").first
    ).to_be_visible()
    page.locator("ul#countries_free-suggestions button", has_text="Atlantis").click()
    chip = page.locator('#countries_free-value .chip[data-value="Atlantis"]')
    expect(chip).to_have_count(1)


def test_combobox_arrow_down_from_input_focuses_first_option(page, nav):
    """↓ from the input moves focus to the first suggestion button."""
    _goto(page, nav)
    query = page.locator("input#countries-query")
    query.fill("fr")
    first_option = page.locator(
        "ul#countries-suggestions li[role='option'] button"
    ).first
    expect(first_option).to_be_visible()
    query.press("ArrowDown")
    expect(first_option).to_be_focused()


def test_combobox_arrow_navigation_between_options(page, nav):
    """↓/↑ cycle through options; ↑ from the first returns focus to the input."""
    _goto(page, nav)
    query = page.locator("input#countries-query")
    query.fill("a")
    options = page.locator("ul#countries-suggestions li[role='option'] button")
    expect(options.first).to_be_visible()

    query.press("ArrowDown")
    expect(options.nth(0)).to_be_focused()

    options.nth(0).press("ArrowDown")
    expect(options.nth(1)).to_be_focused()

    options.nth(1).press("ArrowUp")
    expect(options.nth(0)).to_be_focused()

    options.nth(0).press("ArrowUp")
    expect(query).to_be_focused()


def test_combobox_home_end_jump_to_extremes(page, nav):
    """Home/End jumps focus to the first/last option."""
    _goto(page, nav)
    query = page.locator("input#countries-query")
    query.fill("a")
    options = page.locator("ul#countries-suggestions li[role='option'] button")
    expect(options.first).to_be_visible()

    query.press("ArrowDown")
    options.nth(0).press("End")
    expect(options.last).to_be_focused()

    options.last.press("Home")
    expect(options.nth(0)).to_be_focused()


def test_combobox_escape_closes_listbox(page, nav):
    """Esc hides the listbox and keeps focus on the input."""
    _goto(page, nav)
    query = page.locator("input#countries-query")
    query.fill("fr")
    listbox = page.locator("ul#countries-suggestions")
    expect(listbox.locator("li[role='option']").first).to_be_visible()

    query.press("Escape")
    expect(query).to_be_focused()
    expect(listbox).not_to_be_visible()


def test_combobox_escape_from_option_closes_listbox(page, nav):
    """Esc still closes the listbox when focus is on a suggestion button."""
    _goto(page, nav)
    query = page.locator("input#countries-query")
    query.fill("fr")
    listbox = page.locator("ul#countries-suggestions")
    expect(listbox.locator("li[role='option']").first).to_be_visible()

    query.press("ArrowDown")
    options = page.locator("ul#countries-suggestions li[role='option'] button")
    expect(options.first).to_be_focused()

    options.first.press("Escape")
    expect(query).to_be_focused()
    expect(listbox).not_to_be_visible()


def test_combobox_arrow_up_from_input_focuses_last_option(page, nav):
    """↑ from the input opens the listbox at the last option (APG)."""
    _goto(page, nav)
    query = page.locator("input#countries-query")
    query.fill("fr")
    options = page.locator("ul#countries-suggestions li[role='option'] button")
    expect(options.first).to_be_visible()

    query.press("ArrowUp")
    expect(options.last).to_be_focused()


def test_combobox_arrow_down_after_hover_advances_from_hovered(page, nav):
    """↓ from input with a hovered option moves focus past it, not to option 0."""
    _goto(page, nav)
    query = page.locator("input#countries-query")
    query.fill("fr")
    options = page.locator("ul#countries-suggestions li[role='option'] button")
    expect(options.first).to_be_visible()

    options.nth(3).hover()
    query.press("ArrowDown")
    expect(options.nth(4)).to_be_focused()


def test_combobox_arrow_up_after_hover_steps_back_from_hovered(page, nav):
    """↑ from input with a hovered option moves focus to the previous one."""
    _goto(page, nav)
    query = page.locator("input#countries-query")
    query.fill("fr")
    options = page.locator("ul#countries-suggestions li[role='option'] button")
    expect(options.first).to_be_visible()

    options.nth(3).hover()
    query.press("ArrowUp")
    expect(options.nth(2)).to_be_focused()


def test_combobox_mouseover_follows_keyboard_focus(page, nav):
    """When focus is on an option, hovering another moves focus to it."""
    _goto(page, nav)
    query = page.locator("input#countries-query")
    query.fill("fr")
    options = page.locator("ul#countries-suggestions li[role='option'] button")
    expect(options.first).to_be_visible()

    query.press("ArrowDown")
    expect(options.nth(0)).to_be_focused()

    options.nth(4).hover()
    expect(options.nth(4)).to_be_focused()


def test_combobox_mouseover_does_not_steal_focus_from_input(page, nav):
    """Hovering an option while typing in the input must not move focus."""
    _goto(page, nav)
    query = page.locator("input#countries-query")
    query.fill("fr")
    options = page.locator("ul#countries-suggestions li[role='option'] button")
    expect(options.first).to_be_visible()

    options.nth(2).hover()
    expect(query).to_be_focused()


def test_combobox_click_back_into_input_after_escape_keeps_listbox_closed(page, nav):
    """Refocusing the input after Esc does not reopen the listbox."""
    _goto(page, nav)
    query = page.locator("input#countries-query")
    query.fill("fr")
    listbox = page.locator("ul#countries-suggestions")
    expect(listbox.locator("li[role='option']").first).to_be_visible()

    query.press("Escape")
    expect(listbox).not_to_be_visible()

    page.locator("h1").click()
    query.click()
    expect(query).to_be_focused()
    expect(listbox).not_to_be_visible()


def test_combobox_click_outside_closes_listbox(page, nav):
    """Clicking outside the wrap closes the listbox."""
    _goto(page, nav)
    query = page.locator("input#countries-query")
    query.fill("fr")
    listbox = page.locator("ul#countries-suggestions")
    expect(listbox.locator("li[role='option']").first).to_be_visible()

    page.locator("h1").click()
    expect(listbox).not_to_be_visible()


def test_combobox_arrow_down_reopens_after_escape(page, nav):
    """↓ from the input after Esc reopens the listbox and focuses the first option."""
    _goto(page, nav)
    query = page.locator("input#countries-query")
    query.fill("fr")
    listbox = page.locator("ul#countries-suggestions")
    expect(listbox.locator("li[role='option']").first).to_be_visible()

    query.press("Escape")
    expect(listbox).not_to_be_visible()

    query.press("ArrowDown")
    expect(listbox).to_be_visible()
    expect(
        page.locator("ul#countries-suggestions li[role='option'] button").first
    ).to_be_focused()


def test_combobox_resume_typing_reopens_after_escape(page, nav):
    """Resuming typing after Esc clears the closed flag and re-shows the listbox."""
    _goto(page, nav)
    query = page.locator("input#countries-query")
    query.fill("fr")
    listbox = page.locator("ul#countries-suggestions")
    expect(listbox.locator("li[role='option']").first).to_be_visible()

    query.press("Escape")
    expect(listbox).not_to_be_visible()

    query.press("a")
    expect(listbox.locator("li[role='option']").first).to_be_visible()
    expect(listbox).to_be_visible()


def test_combobox_min_query_length_zero_suggests_on_focus(page, nav):
    """The continents listbox is empty on load and lists every continent on focus."""
    _goto(page, nav)
    options = page.locator("#continents-suggestions li[role='option']")
    expect(options).to_have_count(0)

    page.locator("input#continents-query").focus()
    expect(options).to_have_count(7)
    _wait_for_settle(page)

    page.locator("input#continents-query").fill("am")
    expect(options).to_have_count(2)


def test_combobox_min_query_length_zero_suggests_the_rest_after_a_pick(page, nav):
    """After a pick, the listbox lists the continents not picked yet."""
    _goto(page, nav)
    page.locator("input#continents-query").focus()
    page.locator('#continents-suggestions button[value="Asia"]').click()

    expect(page.locator('#continents-value .chip[data-value="Asia"]')).to_have_count(1)
    expect(page.locator("#continents-suggestions li[role='option']")).to_have_count(6)
