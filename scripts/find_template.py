import rsenv

async def run(game: rsenv.Game, template: str):
    x, y, w, h = await game.find_template(f"templates/{template}.png")
    print("Found at: ", x, y, w, h)
    await game.move_mouse_rect((x, y, w, h))