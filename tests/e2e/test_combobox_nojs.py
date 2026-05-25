"""No-JS tests of the combobox example.

Each combobox has a Search button that refreshes the suggestions with a
plain form post.
"""

from playwright.sync_api import expect


def _goto(page, nav):
    with page.expect_navigation():
        nav.get_by_role("link", name="Combobox").click()


def _submit(page, selector):
    """Click a submit button and wait for the page that comes back."""
    with page.expect_navigation():
        page.locator(selector).click()


def test_single_search_then_select_nojs(page_nojs, nav_nojs):
    """Type, click Search, click a suggestion. A chip with the picked code appears."""
    _goto(page_nojs, nav_nojs)

    _submit(page_nojs, '#country-value button[name="country-remove"][value="FR"]')

    page_nojs.locator("input[name='country-query']").fill("germany")
    _submit(page_nojs, "button[name='country-search']")

    _submit(page_nojs, '#country-suggestions button[value="DE"]')
    expect(page_nojs.locator('#country-value .chip[data-value="DE"]')).to_have_count(1)


def test_multi_search_then_add_nojs(page_nojs, nav_nojs):
    """Type, click Search, click a suggestion to add a chip."""
    _goto(page_nojs, nav_nojs)

    page_nojs.locator("input[name='countries-query']").fill("palestine")
    _submit(page_nojs, "button[name='countries-search']")

    _submit(page_nojs, '#countries-suggestions button[value="PS"]')
    chip = page_nojs.locator("#countries-value .chip", has_text="Palestine")
    expect(chip).to_have_count(1)


def test_multi_chip_remove_nojs(page_nojs, nav_nojs):
    """Clicking the chip ``×`` posts ``remove`` and removes the chip."""
    _goto(page_nojs, nav_nojs)

    _submit(page_nojs, '#countries-value button[name="countries-remove"][value="FR"]')
    chip = page_nojs.locator("#countries-value .chip", has_text="France")
    expect(chip).to_have_count(0)


def test_multi_pick_renders_autofocus_on_query_nojs(page_nojs, nav_nojs):
    """After a no-JS multi pick, the query input renders ``autofocus``."""
    _goto(page_nojs, nav_nojs)

    page_nojs.locator("input[name='countries-query']").fill("palestine")
    _submit(page_nojs, "button[name='countries-search']")

    _submit(page_nojs, '#countries-suggestions button[value="PS"]')

    expect(page_nojs.locator("#countries-query")).to_have_attribute("autofocus", "")


def test_single_free_synthetic_pick_nojs(page_nojs, nav_nojs):
    """Type off-catalog, Search, click the "Add ..." synthetic option: chip appears."""
    _goto(page_nojs, nav_nojs)

    page_nojs.locator("input[name='country_free-query']").fill("Atlantis")
    _submit(page_nojs, "button[name='country_free-search']")

    _submit(page_nojs, '#country_free-suggestions button[value="Atlantis"]')
    expect(
        page_nojs.locator('#country_free-value .chip[data-value="Atlantis"]')
    ).to_have_count(1)


def test_multi_free_synthetic_pick_nojs(page_nojs, nav_nojs):
    """Type off-catalog, Search, click the "Add ..." option to add a chip."""
    _goto(page_nojs, nav_nojs)

    page_nojs.locator("input[name='countries_free-query']").fill("Atlantis")
    _submit(page_nojs, "button[name='countries_free-search']")

    _submit(page_nojs, '#countries_free-suggestions button[value="Atlantis"]')
    expect(
        page_nojs.locator('#countries_free-value .chip[data-value="Atlantis"]')
    ).to_have_count(1)


def test_enter_in_a_query_searches_without_javascript(browser, live_server):
    """With JavaScript off, Enter in a query input refreshes the suggestions."""
    context = browser.new_context(java_script_enabled=False)
    page = context.new_page()
    page.goto(f"{live_server}/patterns/combobox")

    query = page.locator("input[name='countries-query']")
    query.fill("palestine")
    with page.expect_navigation():
        query.press("Enter")

    expect(page.locator('#countries-suggestions button[value="PS"]')).to_have_count(1)
    expect(page.locator('#country-value .chip[data-value="FR"]')).to_have_count(1)
    expect(page.locator('#countries-value .chip[data-value="FR"]')).to_have_count(1)
    context.close()
