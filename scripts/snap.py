import rsenv
import cv2

async def run(game: rsenv.Game):
    im = await game.window.screenshot()
    cv2.imwrite("screenshot.png", cv2.cvtColor(im, cv2.COLOR_RGB2BGR))