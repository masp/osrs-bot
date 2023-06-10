import sys
from typing import Callable
from Foundation import (
    NSObject,
    NSString,
    NSUTF8StringEncoding,
    NSFileHandle,
    NSNotificationCenter,
    NSFileHandleReadCompletionNotification,
    NSFileHandleNotificationDataItem,
)
from PyObjCTools import AppHelper


class FileObserver(NSObject):
    def initWithFileDescriptor_readCallback_errorCallback_(
        self, fileDescriptor, readCallback, errorCallback
    ):
        self = self.init()
        self.readCallback = readCallback
        self.errorCallback = errorCallback
        self.fileHandle = NSFileHandle.alloc().initWithFileDescriptor_(fileDescriptor)
        self.nc = NSNotificationCenter.defaultCenter()
        self.nc.addObserver_selector_name_object_(
            self,
            "fileHandleReadCompleted:",
            NSFileHandleReadCompletionNotification,
            self.fileHandle,
        )
        self.fileHandle.readInBackgroundAndNotify()
        return self

    def fileHandleReadCompleted_(self, aNotification):
        ui = aNotification.userInfo()
        newData = ui.objectForKey_(NSFileHandleNotificationDataItem)
        self.fileHandle.readInBackgroundAndNotify()
        s = NSString.alloc().initWithData_encoding_(newData, NSUTF8StringEncoding)
        if self.readCallback is not None:
            self.readCallback(self, str(s))

    def close(self):
        self.nc.removeObserver_(self)
        if self.fileHandle is not None:
            self.fileHandle.closeFile()
            self.fileHandle = None
        # break cycles in case these functions are closed over
        # an instance of us
        self.readCallback = None
        self.errorCallback = None

    def __del__(self):
        # Without this, if a notification fires after we are GC'ed
        # then the app will crash because NSNotificationCenter
        # doesn't retain observers.  In this example, it doesn't
        # matter, but it's worth pointing out.
        self.close()


def prompt():
    sys.stdout.write("bot> ")
    sys.stdout.flush()


def line_callback(callback):
    def cb(observer, line):
        line = line.rstrip(" \t\n")
        if line == "exit":
            print("")
            AppHelper.stopEventLoop()
        else:
            cmd, args = line.split(" ", 1)
            callback(cmd, args.split(" "))
    return cb


        
def err_callback(observer, err):
    print("error:", err)
    AppHelper.stopEventLoop()

def run(cmd_callback: Callable[[str, list[str]], None]):
    observer = FileObserver.alloc().initWithFileDescriptor_readCallback_errorCallback_(
        sys.stdin.fileno(), line_callback(cmd_callback), err_callback
    )
    prompt()
    AppHelper.runConsoleEventLoop(installInterrupt=True)