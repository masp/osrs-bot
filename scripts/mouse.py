import rsenv

async def run(game: rsenv.Game, x: int, y: int):
    await game.move_mouse(x, y)