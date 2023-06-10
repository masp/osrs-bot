from __future__ import annotations 
import Quartz as Q
import ApplicationServices as AS
import CoreFoundation as CF
import objc
from .stdin import run

import cv2
import numpy
import mss

LEFT_CLICK = Q.kCGMouseButtonLeft
RIGHT_CLICK = Q.kCGMouseButtonRight
MIDDLE_CLICK = Q.kCGMouseButtonCenter

MAC_MENU_BAR_HEIGHT = 28
RUNELITE_TOOLBAR_WIDTH = 36

def observerCallback(rl: RuneLite):
    @objc.callbackFor(AS.AXObserverCreate, 1)
    def cb(observer, element, notification, _):
        rl.event(observer, element, notification)
    
    return cb

class RuneLite:
    def __init__(self) -> None:
        self.pid = None
        self.observer = None
        self.app = None
        self.mainWindowRef = None

        self.windowPos = (0, 0)
        self.windowSize = (0, 0)
        self.activated = False

    def event(self, observer, element, notification):
        if notification == AS.kAXWindowMovedNotification:
            x, y = self.position()
            if (x, y) != self.windowPos:
                print("Window moved, updating position")
                self.windowPos = x, y
        elif notification == AS.kAXWindowResizedNotification:
            w, h = self.size()
            if (w, h) != self.windowSize:
                print("Window resized, updating size")
                self.windowSize = w, h
        elif notification == AS.kAXApplicationActivatedNotification:
            print("Bot activated")
            self.activated = True
        elif notification == AS.kAXApplicationDeactivatedNotification:
            print("Bot deactivated")
            self.activated = False

    def position(self) -> tuple[int, int]:
        err, pos = AS.AXUIElementCopyAttributeValue(self.mainWindowRef, AS.kAXPositionAttribute, None)
        checkErr("AXUIElementCopyAttributeValue Position", err)
        _, p = AS.AXValueGetValue(pos, AS.kAXValueCGPointType, None)
        return p[0], p[1]
    
    def size(self) -> tuple[int, int]:
        err, size = AS.AXUIElementCopyAttributeValue(self.mainWindowRef, AS.kAXSizeAttribute, None)
        checkErr("AXUIElementCopyAttributeValue Window Size", err)
        _, p = AS.AXValueGetValue(size, AS.kAXValueCGSizeType, None)
        return p[0], p[1]
    
    def game_rect(self) -> tuple[int, int, int, int]:
        x, y = self.windowPos
        w, h = self.windowSize
        return x, y+MAC_MENU_BAR_HEIGHT, w-RUNELITE_TOOLBAR_WIDTH, h-MAC_MENU_BAR_HEIGHT
    
    def screenshot(self) -> numpy.ndarray:
        if not self.activated:
            return None
        x, y, w, h = self.game_rect()
        with mss.mss() as sct:
            monitor = {"top": y, "left": x, "width": w, "height": h}
            return cv2.resize(numpy.array(sct.grab(monitor)), (765, 503))

    def move(self, x: int, y: int):
        point = Q.CGPointMake(x, y)
        err = AS.AXUIElementSetAttributeValue(self.mainWindowRef, AS.kAXPositionAttribute, AS.AXValueCreate(AS.kAXValueCGPointType, point))
        checkErr("AXUIElementSetAttributeValue Position", err)

    def click(self, x: int, y: int, button=Q.kCGMouseButtonLeft):
        if not self.activated:
            return
        
        event = Q.CGEventCreateMouseEvent(None, Q.kCGEventLeftMouseDown, (x, y), button)
        Q.CGEventPost(Q.kCGHIDEventTap, event)
        event = Q.CGEventCreateMouseEvent(None, Q.kCGEventLeftMouseUp, (x, y), button)
        Q.CGEventPost(Q.kCGHIDEventTap, event)

    def key(self, keycode):
        event = Q.CGEventCreateKeyboardEvent(None, keycode, True)
        Q.CGEventPostToPid(self.pid, event)
        event = Q.CGEventCreateKeyboardEvent(None, keycode, False)
        Q.CGEventPostToPid(self.pid, event)

def find_runelite() -> RuneLite:
    runelite = RuneLite()
    windows = Q.CGWindowListCopyWindowInfo(Q.kCGWindowListOptionOnScreenOnly, Q.kCGNullWindowID)
    for window in windows:
        try:
            if window['kCGWindowOwnerName'] == 'RuneLite':
                runelite.pid = window['kCGWindowOwnerPID']
                runelite.app = AS.AXUIElementCreateApplication(runelite.pid)
                runelite.windowPos = window['kCGWindowBounds']['X'], window['kCGWindowBounds']['Y']
                runelite.windowSize = window['kCGWindowBounds']['Width'], window['kCGWindowBounds']['Height']

                err, runelite.observer = AS.AXObserverCreate(runelite.pid, observerCallback(runelite), None)
                if err != 0:
                    raise ValueError("Failed to create observer: ", err)
                CF.CFRunLoopAddSource(
                    CF.CFRunLoopGetCurrent(),
                    AS.AXObserverGetRunLoopSource(runelite.observer),
                    CF.kCFRunLoopDefaultMode)
                
                AS.AXObserverAddNotification(runelite.observer, runelite.app, AS.kAXApplicationActivatedNotification, None)
                AS.AXObserverAddNotification(runelite.observer, runelite.app, AS.kAXApplicationDeactivatedNotification, None)

                err, runeliteWindows = AS.AXUIElementCopyAttributeValue(runelite.app, AS.kAXWindowsAttribute, None)
                if len(runeliteWindows) < 1:
                    raise ValueError("No runelite windows found visible: ", err)

                runelite.mainWindowRef = runeliteWindows[0]
                AS.AXObserverAddNotification(runelite.observer, runelite.mainWindowRef, AS.kAXWindowMovedNotification, None)
                
                err, role = AS.AXUIElementCopyAttributeValue(runelite.mainWindowRef, AS.kAXRoleAttribute, None)
                checkErr("AXUIElementCopyAttributeValue AXRoleAttribute", err)
                if role != AS.kAXWindowRole:
                    raise ValueError("Expected RuneLite to have window role, got: ", role)
                break
        except KeyError:
            pass
    if runelite.pid is None:
        raise ValueError("No window with title RuneLite found")
    
    runelite.windowSize = runelite.size()
    runelite.windowPos = runelite.position()
    return runelite

def checkErr(msg: str, err: int):
    if err != 0:
        raise ValueError(f"objc: {msg}: {err}")