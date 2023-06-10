import asyncio
import pathlib
import random
import time
import asyncvnc
import importlib
import numpy as np
import bezier
import cv2
import ultralytics


CLICK_LEFT = "left"
CLICK_RIGHT = "right"
CLICK_MIDDLE = "middle"

MAX_WIDTH = 765
MAX_HEIGHT = 503

INV_RECT = [(546, 204), (736, 467)] # The rectangle of the inventory
MINIMAP_RECT = [(518, 4), (764, 168)] # Includes minimap and prayer
GAME_RECT = [(0, 0), (515, 342)] # The actual game screen
CHAT_RECT = [(8, 345), (500, 460)] # The chat box (just messages received)

"""
Game manages states and actions within the tick system. Programs can submit actions and read
states for a given tick, or wait for a given tick to be reached. The game will run at a fixed
interval.
"""

MOUSE_MOVE_TIME = 0.2 # How long we take to move the mouse from one position to another
TICK_DUR_SEC = 0.6

class Game:
    _game_objects: list[object]
    _cached_screenshot: np.ndarray

    def __init__(self, window: asyncvnc.Client) -> None:
        self._start = time.time()
        self._snap_tick = 0
        self._mouse_noise = np.random.normal(0, 1, (MAX_WIDTH, MAX_HEIGHT))
        self.window: asyncvnc.Client = window
        self._yolo = ultralytics.YOLO(pathlib.Path("models/yolov8x.pt"))


    async def wait(self, ticks: int):
        """tick increments the clock, and returns any actions that have been submitted"""
        await asyncio.sleep(TICK_DUR_SEC*ticks)

    async def move_mouse_rect(self, rect: tuple[int, int, int, int]) -> None:
        """move_mouse_rect moves the mouse to a random position within the given rectangle"""
        rx = max(0.25, min(random.random(), 0.75))
        ry = max(0.25, min(random.random(), 0.75))
        x = int(rect[0] + rx*(rect[2] - rect[0]))
        y = int(rect[1] + ry*(rect[3] - rect[1]))
        await self.move_mouse(x, y)

    async def move_mouse(self, x: int, y: int) -> None:
        """click clicks on the screen using left, right, or middle click
        The x and y must be within a standard runescape window (765x503)
        """
        if x > MAX_WIDTH or y > MAX_HEIGHT:
            raise ValueError(f"click position ({x}, {y}) is outside of the standard runescape window")
        if x < 0 or y < 0:
            raise ValueError(f"click position ({x}, {y}) is negative")

        # Get point on line between s and (x, y)
        # Clamp mouse noise between 0.25 and 0.75
        src = (float(self.window.mouse.x), float(self.window.mouse.y))
        dst = (float(x), float(y))
        z = max(0.25, min(self._mouse_noise[x, y], 0.75))
        dx, dy = dst[0] - src[0], dst[1] - src[1]
        mid = src[0] + dx * z, src[1] + dy * z
        if abs(dx) > abs(dy):
            mid = mid[0], mid[1] + 0.1*dx
        else:
            mid = mid[0] + 0.1*dy, mid[1]

        curve = bezier.Curve(np.asfortranarray([
            [src[0], mid[0], dst[0]],
            [src[1], mid[1], dst[1]],
        ]), degree=2)
        ps = curve.evaluate_multi(np.linspace(0, 1, 10))
        for t in range(10):
            await asyncio.sleep(MOUSE_MOVE_TIME/10)
            self.window.mouse.move(int(ps[0][t]), int(ps[1][t]))

    async def find_template(self, template_path: str, threshold=0.9, timeout=10, period=1) -> tuple[int, int, int, int]:
        """find_template blocks until it finds a template on the screen with a high threshold"""
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        wait_time = 0
        while True:
            im = cv2.cvtColor(await self.window.screenshot(), cv2.COLOR_BGR2GRAY)
            res = np.array(cv2.matchTemplate(im, template, cv2.TM_CCOEFF_NORMED), dtype=np.float32)
            loc = np.where(res >= threshold)
            if len(loc[0]) > 0:
                w, h = template.shape[::-1]
                y, x = loc[0][0], loc[1][0]
                return x, y, x+w, y+h
            await asyncio.sleep(period)
            wait_time += 1
            if wait_time > timeout:
                raise TimeoutError("find_template timed out")

    async def run(self, script: str):
        """run runs a script"""
        script_name, invoke = script.split("(")
        mod = importlib.import_module(script_name.replace("/", "."))
        defs = mod.__dict__
        if not "run" in defs:
            raise ValueError("script must define a run function")
        await eval("mod.run(self, " + invoke)

    async def snap_game_window(self) -> np.ndarray:
        """snap_game_window takes a screenshot of the game window"""
        snap = await self.update_screen_if_needed()
        return _window(snap, GAME_RECT)
    
    async def snap_inventory(self) -> np.ndarray:
        """snap_inventory takes a screenshot of the inventory"""
        snap = await self.update_screen_if_needed()
        return _window(snap, INV_RECT)

    async def snap_minimap(self) -> np.ndarray:
        """snap_minimap takes a screenshot of the minimap"""
        snap = await self.update_screen_if_needed()
        return _window(snap, MINIMAP_RECT)
    
    async def snap_chat(self) -> np.ndarray:
        """snap_chat takes a screenshot of the chat"""
        snap = await self.update_screen_if_needed()
        return _window(snap, CHAT_RECT)
    
    async def update_screen_if_needed(self) -> np.ndarray:
        """update_screen_if_needed updates the screen if the tick has changed"""
        curr_tick = self.curr_tick()
        if self._snap_tick != curr_tick:
            self._cached_screenshot = await self.window.screenshot()
            self._snap_tick = curr_tick
        return self._cached_screenshot

    def curr_tick(self) -> int:
        """curr_tick returns the current tick since the bot was started"""
        return int((time.time() - self._start) / TICK_DUR_SEC)
    

def _window(img, rect):
    return img[rect[0][1]:rect[1][1], rect[0][0]:rect[1][0]]

