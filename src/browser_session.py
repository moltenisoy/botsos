"""
Módulo de Sesión del Navegador.

Maneja la automatización del navegador usando Playwright con medidas anti-detección.
Diseñado para Windows.
"""

import asyncio
import logging
import random
import time
from typing import Optional, List
from pathlib import Path
from dataclasses import dataclass

from .session_config import SessionConfig
from .fingerprint_manager import FingerprintManager, DeviceFingerprint
from .proxy_manager import ProxyManager, ProxyEntry


logger = logging.getLogger(__name__)


@dataclass
class BrowserAction:
    """Representa una acción del navegador a ejecutar."""
    action_type: str  # navigate, click, type, scroll, wait
    selector: Optional[str] = None
    value: Optional[str] = None
    timeout: int = 30000


class BrowserSession:
    """Manages a single browser automation session with anti-detection."""
    
    def __init__(
        self,
        session_config: SessionConfig,
        fingerprint_manager: FingerprintManager,
        proxy_manager: Optional[ProxyManager] = None
    ):
        """Initialize the browser session.
        
        Args:
            session_config: Session configuration.
            fingerprint_manager: Manager for device fingerprints.
            proxy_manager: Optional proxy pool manager.
        """
        self.config = session_config
        self.fingerprint_manager = fingerprint_manager
        self.proxy_manager = proxy_manager
        
        self.browser = None
        self.context = None
        self.page = None
        self.fingerprint: Optional[DeviceFingerprint] = None
        self.current_proxy: Optional[ProxyEntry] = None
        
        self._is_running = False
        self._action_count = 0
    
    async def start(self) -> bool:
        """Start the browser session.
        
        Returns:
            True if started successfully, False otherwise.
        """
        try:
            from playwright.async_api import async_playwright
            
            # Generate fingerprint
            self.fingerprint = self.fingerprint_manager.generate_fingerprint(
                preset_name=self.config.fingerprint.device_preset,
                randomize=True
            )
            
            # Get proxy if enabled
            proxy_config = None
            if self.config.proxy.enabled:
                if self.proxy_manager:
                    self.current_proxy = self.proxy_manager.get_next_proxy()
                    if self.current_proxy:
                        proxy_config = {
                            "server": f"{self.current_proxy.proxy_type}://{self.current_proxy.server}:{self.current_proxy.port}"
                        }
                        if self.current_proxy.username:
                            proxy_config["username"] = self.current_proxy.username
                            proxy_config["password"] = self.current_proxy.password
                elif self.config.proxy.server:
                    proxy_config = {
                        "server": f"{self.config.proxy.proxy_type}://{self.config.proxy.server}:{self.config.proxy.port}"
                    }
                    if self.config.proxy.username:
                        proxy_config["username"] = self.config.proxy.username
                        proxy_config["password"] = self.config.proxy.password
            
            # Start Playwright
            self._playwright = await async_playwright().start()
            
            # Launch browser
            browser_type = getattr(self._playwright, self.config.browser_type)
            self.browser = await browser_type.launch(
                headless=self.config.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
            
            # Create context with fingerprint
            context_options = self.fingerprint.to_playwright_context()
            if proxy_config:
                context_options["proxy"] = proxy_config
            
            # Add persistent context if configured
            if self.config.persistent_context:
                context_dir = Path(self.config.context_dir) / self.config.session_id
                context_dir.mkdir(parents=True, exist_ok=True)
                # Note: persistent context requires different approach
                # For now, use regular context
                self.context = await self.browser.new_context(**context_options)
            else:
                self.context = await self.browser.new_context(**context_options)
            
            # Inject anti-detection scripts
            for script in self.fingerprint.get_spoofing_scripts():
                await self.context.add_init_script(script)
            
            # Create page
            self.page = await self.context.new_page()
            
            # Additional stealth measures
            await self._apply_stealth_measures()
            
            self._is_running = True
            logger.info(f"Browser session started: {self.config.session_id}")
            return True
            
        except ImportError:
            logger.error(
                "Playwright is not installed. Install with: "
                "pip install playwright && playwright install chromium"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to start browser session: {e}")
            return False
    
    async def stop(self) -> None:
        """Stop the browser session."""
        self._is_running = False
        
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, '_playwright'):
                await self._playwright.stop()
        except Exception as e:
            logger.error(f"Error stopping browser session: {e}")
        
        logger.info(f"Browser session stopped: {self.config.session_id}")
    
    async def _apply_stealth_measures(self) -> None:
        """Apply additional stealth measures to the page."""
        if not self.page:
            return
        
        # Remove webdriver property
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        # Mock permissions
        await self.page.add_init_script("""
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        # Mock plugins
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer' },
                    { name: 'Chromium PDF Plugin', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' }
                ]
            });
        """)
    
    async def navigate(self, url: str, wait_until: str = "load") -> bool:
        """Navigate to a URL.
        
        Args:
            url: URL to navigate to.
            wait_until: When to consider navigation complete.
            
        Returns:
            True if navigation successful, False otherwise.
        """
        if not self.page or not self._is_running:
            return False
        
        try:
            await self._random_delay()
            await self.page.goto(url, wait_until=wait_until)
            self._action_count += 1
            logger.debug(f"Navigated to: {url}")
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False
    
    async def click(self, selector: str, timeout: int = 30000) -> bool:
        """Click an element.
        
        Args:
            selector: CSS selector of the element.
            timeout: Maximum wait time in milliseconds.
            
        Returns:
            True if click successful, False otherwise.
        """
        if not self.page or not self._is_running:
            return False
        
        try:
            await self._random_delay()
            await self._human_mouse_move(selector)
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            if element:
                await element.click()
                self._action_count += 1
                logger.debug(f"Clicked: {selector}")
                return True
            return False
        except Exception as e:
            logger.error(f"Click failed on {selector}: {e}")
            return False
    
    async def type_text(self, selector: str, text: str, timeout: int = 30000) -> bool:
        """Type text into an element with human-like delays.
        
        Args:
            selector: CSS selector of the element.
            text: Text to type.
            timeout: Maximum wait time in milliseconds.
            
        Returns:
            True if typing successful, False otherwise.
        """
        if not self.page or not self._is_running:
            return False
        
        try:
            await self._random_delay()
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            if element:
                await element.click()
                
                # Type with human-like delays
                # For performance, use batch delays instead of per-character
                if len(text) <= 10:
                    # Short text: type character by character
                    for char in text:
                        await self.page.keyboard.type(char, delay=random.randint(50, 150))
                else:
                    # Longer text: type in small chunks with delays between chunks
                    chunk_size = 5
                    for i in range(0, len(text), chunk_size):
                        chunk = text[i:i + chunk_size]
                        await self.page.keyboard.type(chunk, delay=random.randint(30, 80))
                        if i + chunk_size < len(text):
                            await asyncio.sleep(random.uniform(0.05, 0.15))
                
                self._action_count += 1
                logger.debug(f"Typed text in: {selector}")
                return True
            return False
        except Exception as e:
            logger.error(f"Type failed on {selector}: {e}")
            return False
    
    async def scroll(self, delta_y: int = 300) -> bool:
        """Scroll the page.
        
        Args:
            delta_y: Amount to scroll (positive = down, negative = up).
            
        Returns:
            True if scroll successful, False otherwise.
        """
        if not self.page or not self._is_running:
            return False
        
        try:
            await self._random_delay()
            await self.page.mouse.wheel(0, delta_y)
            self._action_count += 1
            return True
        except Exception as e:
            logger.error(f"Scroll failed: {e}")
            return False
    
    async def wait(self, seconds: float) -> None:
        """Wait for a specified duration.
        
        Args:
            seconds: Duration to wait in seconds.
        """
        if self._is_running:
            await asyncio.sleep(seconds)
    
    async def wait_random(self, min_sec: float, max_sec: float) -> None:
        """Wait for a random duration.
        
        Args:
            min_sec: Minimum wait time in seconds.
            max_sec: Maximum wait time in seconds.
        """
        await self.wait(random.uniform(min_sec, max_sec))
    
    async def _random_delay(self) -> None:
        """Apply random delay between actions."""
        min_ms = self.config.behavior.action_delay_min_ms
        max_ms = self.config.behavior.action_delay_max_ms
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
    
    async def _human_mouse_move(self, selector: str) -> None:
        """Move mouse to element in a human-like way.
        
        Args:
            selector: CSS selector of the target element.
        """
        if not self.page:
            return
        
        try:
            element = await self.page.query_selector(selector)
            if element:
                box = await element.bounding_box()
                if box:
                    # Add some randomness to target position
                    target_x = box['x'] + box['width'] / 2 + random.randint(-5, 5)
                    target_y = box['y'] + box['height'] / 2 + random.randint(-5, 5)
                    
                    # Move mouse with some jitter
                    current_x, current_y = 0, 0
                    steps = random.randint(5, 15)
                    
                    for i in range(steps):
                        progress = (i + 1) / steps
                        jitter_x = random.randint(-3, 3)
                        jitter_y = random.randint(-3, 3)
                        
                        x = current_x + (target_x - current_x) * progress + jitter_x
                        y = current_y + (target_y - current_y) * progress + jitter_y
                        
                        await self.page.mouse.move(x, y)
                        await asyncio.sleep(random.uniform(0.01, 0.03))
        except Exception:
            pass  # Mouse movement is optional
    
    async def get_page_content(self) -> str:
        """Get the current page content.
        
        Returns:
            HTML content of the page.
        """
        if self.page:
            return await self.page.content()
        return ""
    
    async def get_page_title(self) -> str:
        """Get the current page title.
        
        Returns:
            Title of the page.
        """
        if self.page:
            return await self.page.title()
        return ""
    
    async def take_screenshot(self, path: str) -> bool:
        """Take a screenshot of the current page.
        
        Args:
            path: Path to save the screenshot.
            
        Returns:
            True if screenshot saved, False otherwise.
        """
        if self.page:
            try:
                await self.page.screenshot(path=path)
                return True
            except Exception as e:
                logger.error(f"Screenshot failed: {e}")
        return False
    
    async def element_exists(self, selector: str, timeout: int = 5000) -> bool:
        """Check if an element exists on the page.
        
        Args:
            selector: CSS selector of the element.
            timeout: Maximum wait time in milliseconds.
            
        Returns:
            True if element exists, False otherwise.
        """
        if not self.page:
            return False
        
        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            return element is not None
        except Exception:
            return False
    
    async def execute_actions(self, actions: List[BrowserAction]) -> bool:
        """Execute a list of browser actions.
        
        Args:
            actions: List of actions to execute.
            
        Returns:
            True if all actions succeeded, False otherwise.
        """
        for action in actions:
            if not self._is_running:
                return False
            
            if action.action_type == "navigate":
                if not await self.navigate(action.value or ""):
                    return False
            elif action.action_type == "click":
                if not await self.click(action.selector or "", action.timeout):
                    return False
            elif action.action_type == "type":
                if not await self.type_text(action.selector or "", action.value or "", action.timeout):
                    return False
            elif action.action_type == "scroll":
                if not await self.scroll(int(action.value or 300)):
                    return False
            elif action.action_type == "wait":
                await self.wait(float(action.value or 1))
        
        return True
    
    @property
    def is_running(self) -> bool:
        """Check if the session is currently running."""
        return self._is_running
    
    @property
    def action_count(self) -> int:
        """Get the number of actions performed."""
        return self._action_count


class YouTubeAutomation:
    """YouTube-specific automation routines."""
    
    # YouTube selectors (may need updates as YouTube changes)
    SELECTORS = {
        "search_box": 'input[name="search_query"]',
        "search_button": 'button#search-icon-legacy',
        "video_result": 'ytd-video-renderer a#video-title',
        "play_button": 'button.ytp-play-button',
        "skip_ad": 'button.ytp-ad-skip-button',
        "skip_ad_alt": 'button.ytp-ad-skip-button-modern',
        "like_button": 'ytd-toggle-button-renderer#top-level-buttons-computed button[aria-label*="like"]',
        "comment_box": 'ytd-comments #placeholder-area',
        "comment_input": 'ytd-commentbox #contenteditable-root',
        "comment_submit": 'ytd-commentbox #submit-button',
        "subscribe_button": 'ytd-subscribe-button-renderer button',
        "video_player": 'video.html5-main-video',
        "ad_overlay": '.ytp-ad-overlay-container'
    }
    
    def __init__(self, browser_session: BrowserSession):
        """Initialize YouTube automation.
        
        Args:
            browser_session: The browser session to use.
        """
        self.session = browser_session
    
    async def search_and_play(self, query: str) -> bool:
        """Search for a video and play the first result.
        
        Args:
            query: Search query.
            
        Returns:
            True if successful, False otherwise.
        """
        # Navigate to YouTube
        if not await self.session.navigate("https://www.youtube.com"):
            return False
        
        await self.session.wait_random(2, 4)
        
        # Search
        if not await self.session.type_text(self.SELECTORS["search_box"], query):
            return False
        
        await self.session.wait_random(0.5, 1)
        
        if not await self.session.click(self.SELECTORS["search_button"]):
            # Try pressing Enter instead
            await self.session.page.keyboard.press("Enter")
        
        await self.session.wait_random(2, 4)
        
        # Click first video result
        if not await self.session.click(self.SELECTORS["video_result"]):
            return False
        
        await self.session.wait_random(2, 4)
        return True
    
    async def skip_ad_if_present(self) -> bool:
        """Skip ad if present and skippable.
        
        Returns:
            True if ad was skipped or no ad present, False on error.
        """
        try:
            # Wait for skip button
            if await self.session.element_exists(self.SELECTORS["skip_ad"], timeout=3000):
                await self.session.click(self.SELECTORS["skip_ad"])
                return True
            elif await self.session.element_exists(self.SELECTORS["skip_ad_alt"], timeout=1000):
                await self.session.click(self.SELECTORS["skip_ad_alt"])
                return True
            return True  # No ad to skip
        except Exception:
            return True  # Continue anyway
    
    async def like_video(self) -> bool:
        """Like the current video.
        
        Returns:
            True if successful, False otherwise.
        """
        return await self.session.click(self.SELECTORS["like_button"])
    
    async def post_comment(self, comment: str) -> bool:
        """Post a comment on the current video.
        
        Args:
            comment: Comment text to post.
            
        Returns:
            True if successful, False otherwise.
        """
        # Scroll to comments section
        await self.session.scroll(500)
        await self.session.wait_random(1, 2)
        
        # Click comment box to expand
        if not await self.session.click(self.SELECTORS["comment_box"]):
            return False
        
        await self.session.wait_random(1, 2)
        
        # Type comment
        if not await self.session.type_text(self.SELECTORS["comment_input"], comment):
            return False
        
        await self.session.wait_random(0.5, 1)
        
        # Submit comment
        return await self.session.click(self.SELECTORS["comment_submit"])
    
    async def watch_video(self, duration_sec: int) -> bool:
        """Watch the current video for a specified duration.
        
        Args:
            duration_sec: Duration to watch in seconds.
            
        Returns:
            True if watched successfully, False otherwise.
        """
        start_time = time.time()
        
        while time.time() - start_time < duration_sec:
            if not self.session.is_running:
                return False
            
            # Check for and skip ads periodically
            await self.skip_ad_if_present()
            
            # Random scroll or pause
            if random.random() < 0.1:
                await self.session.scroll(random.randint(-100, 300))
            
            await self.session.wait_random(5, 10)
        
        return True
    
    async def subscribe_to_channel(self) -> bool:
        """Subscribe to the current channel.
        
        Returns:
            True if successful, False otherwise.
        """
        return await self.session.click(self.SELECTORS["subscribe_button"])
