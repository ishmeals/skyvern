from __future__ import annotations

import asyncio
import typing
from enum import StrEnum

import structlog
from playwright.async_api import Frame, FrameLocator, Locator, Page

from skyvern.constants import INPUT_TEXT_TIMEOUT, SKYVERN_ID_ATTR
from skyvern.exceptions import (
    ElementIsNotLabel,
    ElementIsNotSelect2Dropdown,
    MissingElement,
    MissingElementDict,
    MissingElementInCSSMap,
    MissingElementInIframe,
    MultipleElementsFound,
    NoneFrameError,
    SkyvernException,
)
from skyvern.forge.sdk.settings_manager import SettingsManager
from skyvern.webeye.scraper.scraper import ScrapedPage, get_select2_options

LOG = structlog.get_logger()


async def resolve_locator(
    scrape_page: ScrapedPage, page: Page, frame: str, css: str
) -> typing.Tuple[Locator, Page | Frame]:
    iframe_path: list[str] = []

    while frame != "main.frame":
        iframe_path.append(frame)

        frame_element = scrape_page.id_to_element_dict.get(frame)
        if frame_element is None:
            raise MissingElement(element_id=frame)

        parent_frame = frame_element.get("frame")
        if not parent_frame:
            raise SkyvernException(f"element without frame: {frame_element}")

        LOG.info(f"{frame} is a child frame of {parent_frame}")
        frame = parent_frame

    current_page: Page | FrameLocator = page
    current_frame: Page | Frame = page

    while len(iframe_path) > 0:
        child_frame = iframe_path.pop()

        frame_handler = await current_frame.query_selector(f"[{SKYVERN_ID_ATTR}='{child_frame}']")
        content_frame = await frame_handler.content_frame()
        if content_frame is None:
            raise NoneFrameError(frame_id=child_frame)
        current_frame = content_frame

        current_page = current_page.frame_locator(f"[{SKYVERN_ID_ATTR}='{child_frame}']")

    return current_page.locator(css), current_frame


class InteractiveElement(StrEnum):
    A = "a"
    INPUT = "input"
    SELECT = "select"
    BUTTON = "button"


class SkyvernOptionType(typing.TypedDict):
    optionIndex: int
    text: str


class SkyvernElement:
    """
    SkyvernElement is a python interface to interact with js elements built during the scarping.
    When you try to interact with these elements by python, you are supposed to use this class as an interface.
    """

    def __init__(self, locator: Locator, frame: Page | Frame, static_element: dict) -> None:
        self.__static_element = static_element
        self.__frame = frame
        self.locator = locator

    async def is_select2_dropdown(self) -> bool:
        tag_name = self.get_tag_name()
        element_class = await self.get_attr("class")
        if element_class is None:
            return False
        return (
            (tag_name == "a" and "select2-choice" in element_class)
            or (tag_name == "span" and "select2-chosen" in element_class)
            or (tag_name == "span" and "select2-arrow" in element_class)
            or (tag_name == "input" and "select2-input" in element_class)
        )

    async def is_checkbox(self) -> bool:
        tag_name = self.get_tag_name()
        if tag_name != "input":
            return False

        button_type = await self.get_attr("type")
        return button_type == "checkbox"

    async def is_radio(self) -> bool:
        tag_name = self.get_tag_name()
        if tag_name != "input":
            return False

        button_type = await self.get_attr("type")
        return button_type == "radio"

    def get_tag_name(self) -> str:
        return self.__static_element.get("tagName", "")

    def get_id(self) -> str:
        return self.__static_element.get("id", "")

    def get_attributes(self) -> typing.Dict:
        return self.__static_element.get("attributes", {})

    def get_options(self) -> typing.List[SkyvernOptionType]:
        options = self.__static_element.get("options", None)
        if options is None:
            return []

        return typing.cast(typing.List[SkyvernOptionType], options)

    def get_frame(self) -> Page | Frame:
        return self.__frame

    def get_locator(self) -> Locator:
        return self.locator

    async def get_select2_dropdown(self) -> Select2Dropdown:
        if not await self.is_select2_dropdown():
            raise ElementIsNotSelect2Dropdown(self.get_id(), self.__static_element)

        return Select2Dropdown(self.get_frame(), self)

    def find_element_id_in_label_children(self, element_type: InteractiveElement) -> str | None:
        tag_name = self.get_tag_name()
        if tag_name != "label":
            raise ElementIsNotLabel(tag_name)

        children: list[dict] = self.__static_element.get("children", [])
        for child in children:
            if not child.get("interactable"):
                continue

            if child.get("tagName") == element_type:
                return child.get("id")

        return None

    async def get_attr(
        self,
        attr_name: str,
        dynamic: bool = False,
        timeout: float = SettingsManager.get_settings().BROWSER_ACTION_TIMEOUT_MS,
    ) -> typing.Any:
        if not dynamic:
            if attr := self.get_attributes().get(attr_name):
                return attr

        return await self.locator.get_attribute(attr_name, timeout=timeout)

    async def input_sequentially(
        self, text: str, default_timeout: float = SettingsManager.get_settings().BROWSER_ACTION_TIMEOUT_MS
    ) -> None:
        await self.locator.press_sequentially(text, timeout=INPUT_TEXT_TIMEOUT)


class DomUtil:
    """
    DomUtil is a python interface to interact with the DOM.
    The ultimate goal here is to provide a full python-js interaction.
    Some functions like wait_for_xxx should be supposed to define here.
    """

    def __init__(self, scraped_page: ScrapedPage, page: Page) -> None:
        self.scraped_page = scraped_page
        self.page = page

    async def get_skyvern_element_by_id(self, element_id: str) -> SkyvernElement:
        element = self.scraped_page.id_to_element_dict.get(element_id)
        if not element:
            raise MissingElementDict(element_id)

        frame = self.scraped_page.id_to_frame_dict.get(element_id)
        if not frame:
            raise MissingElementInIframe(element_id)

        css = self.scraped_page.id_to_css_dict.get(element_id)
        if not css:
            raise MissingElementInCSSMap(element_id)

        locator, frame_content = await resolve_locator(self.scraped_page, self.page, frame, css)

        num_elements = await locator.count()
        if num_elements < 1:
            LOG.warning("No elements found with css. Validation failed.", css=css, element_id=element_id)
            raise MissingElement(selector=css, element_id=element_id)

        elif num_elements > 1:
            LOG.warning(
                "Multiple elements found with css. Expected 1. Validation failed.",
                num_elements=num_elements,
                selector=css,
                element_id=element_id,
            )
            raise MultipleElementsFound(num=num_elements, selector=css, element_id=element_id)

        return SkyvernElement(locator, frame_content, element)


class Select2Dropdown:
    def __init__(self, frame: Page | Frame, skyvern_element: SkyvernElement) -> None:
        self.skyvern_element = skyvern_element
        self.frame = frame

    async def open(self, timeout: float = SettingsManager.get_settings().BROWSER_ACTION_TIMEOUT_MS) -> None:
        await self.skyvern_element.get_locator().click(timeout=timeout)
        # wait for the options to load
        await asyncio.sleep(3)

    async def close(self, timeout: float = SettingsManager.get_settings().BROWSER_ACTION_TIMEOUT_MS) -> None:
        await self.frame.locator("#select2-drop").press("Escape", timeout=timeout)

    async def get_options(
        self, timeout: float = SettingsManager.get_settings().BROWSER_ACTION_TIMEOUT_MS
    ) -> typing.List[SkyvernOptionType]:
        element_handler = await self.skyvern_element.get_locator().element_handle(timeout=timeout)
        options = await get_select2_options(self.frame, element_handler)
        return typing.cast(typing.List[SkyvernOptionType], options)

    async def select_by_index(
        self, index: int, timeout: float = SettingsManager.get_settings().BROWSER_ACTION_TIMEOUT_MS
    ) -> None:
        anchor = self.frame.locator("#select2-drop li[role='option']")
        await anchor.nth(index).click(timeout=timeout)
