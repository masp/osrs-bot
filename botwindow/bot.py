
from collections import namedtuple
import queue
import PyObjCTools.AppHelper as AH
import threading
import botwindow
import rsenv

rl = botwindow.find_runelite()

def runelite_handler(rl: botwindow.RuneLite):
    def handler(button: str, x: int, y: int):
        if button == rsenv.CLICK_LEFT:
            buttonCode = botwindow.LEFT_CLICK
        elif button == rsenv.CLICK_RIGHT:
            buttonCode = botwindow.RIGHT_CLICK
        elif button == rsenv.CLICK_MIDDLE:
            buttonCode = botwindow.MIDDLE_CLICK
        else:
            raise NotImplementedError(f"Runelite only supports left/right/middle click")
        rl.click(x, y, button=buttonCode)
    return handler


RunScript = namedtuple("RunScript", ["program_path"])
run_queue = queue.SimpleQueue()

def game_thread():
    game = rsenv.Game(runelite_handler(rl))
    while True:
        job = run_queue.get()
        if isinstance(job, RunScript):
            game.run(job.program_path)

threading.Thread(target=game_thread, daemon=True).start()

print("Found runelite: ", rl.pid)
print("Size: ", rl.size())
print("Position: ", rl.position())
def run_command(cmd: str, args: list[str]) -> None:
    if cmd == "run":
        filename = args[0]
        print("Running script: ", filename)
        run_queue.put(RunScript(program_path=filename))

botwindow.run(cmd_callback=run_command)