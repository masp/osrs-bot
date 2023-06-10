"""
Login will click the existing user button and enter the username and password configured here
"""
import os

import rsenv

EXISTING_USER_BUTTON = (450, 290)
LOGIN_USER_FIELD = (310, 250)
LOGIN_PASSWORD_FIELD = (310, 265)
LOGIN_BUTTON = (310, 320)

async def run(game: rsenv.Game):
    username = os.environ["RS_USERNAME"]
    password = os.environ["RS_PASSWORD"]
    if username == "" or password == "":
        raise ValueError("RS_USERNAME and RS_PASSWORD must be set in the environment")

    existing_user_btn = await game.find_template("templates/existing_user_btn.png", timeout=2)
    await game.move_mouse_rect(existing_user_btn)
    game.window.mouse.click()
    await game.wait(1)

    print("Writing RS_USERNAME: ", username)
    await enter_field(game, LOGIN_USER_FIELD, username)
    print("Writing RS_PASSWORD: ", len(password)*"*")
    await enter_field(game, LOGIN_PASSWORD_FIELD, password)

    login_btn = await game.find_template("templates/login_btn.png", timeout=2)
    await game.move_mouse_rect(login_btn)
    game.window.mouse.click()
    await game.move_mouse(0, 0) # get mouse out of way for template

    play_btn = await game.find_template("templates/play_btn.png", timeout=30)
    await game.move_mouse_rect(play_btn)
    game.window.mouse.click() # Enter game

async def enter_field(game: rsenv.Game, field: tuple[int, int], text: str):
    await game.move_mouse(*field)
    game.window.mouse.click()
    await game.wait(1)

    for i in range(30):
        game.window.keyboard.press("Backspace")
    game.window.keyboard.write(text)


