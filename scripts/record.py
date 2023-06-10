
import rsenv
import cv2

async def run(game: rsenv.Game):
    i = 0
    while True:
        game_window = await game.snap_game_window()
        game_window = cv2.cvtColor(game_window, cv2.COLOR_RGBA2BGR)
        cv2.imwrite(f"datasets/forestry/images/im{i}.png", game_window)
        i += 1
        await game.wait(10)