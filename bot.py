import asyncio, asyncvnc
from concurrent.futures import ThreadPoolExecutor
import os
import rsenv
from matplotlib import pyplot as plt
from pprint import pprint
import atexit
import readline

histfile = os.path.join(os.path.expanduser("~"), ".bot_history")
try:
    readline.read_history_file(histfile)
    # default history len is -1 (infinite), which may grow unruly
    readline.set_history_length(1000)
except FileNotFoundError:
    pass

atexit.register(readline.write_history_file, histfile)

# async def refresh_display(client: asyncvnc.Client):
#     pixels = await client.screenshot()
#     im = plt.imshow(pixels)
#     plt.ion()
#     while True:
#         pixels = await client.screenshot()
#         im.set_data(pixels)
#         plt.pause(0.2)

# async def move_mouse(client: asyncvnc.Client):
#     while True:
#         await asyncio.sleep(1)
#         x, y = random.randint(0, 300), random.randint(0, 300)
#         client.mouse.move(x, y)

def read_input(loop: asyncio.AbstractEventLoop, game: rsenv.Game):
    asyncio.set_event_loop(loop)
    while True:
        cmd = input("bot> ")
        if cmd == "exit":
            print("exiting...")
            return
        elif cmd == "":
            continue
        else:
            coro = game.run(os.path.join("scripts", cmd))
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            result = future.result()

def exception_handler(loop, context):
    print('Exception handler called')
    pprint(context)

async def main():

    async with asyncvnc.connect('localhost') as client:
        print("Connected to RuneLite server")
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(exception_handler)
        game = rsenv.Game(client)
        await loop.run_in_executor(None, read_input, loop, game)

asyncio.run(main())