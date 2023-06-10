from rsenv import Game

async def run(game: Game):
    game.wait(1)
    game.click(100, 100)