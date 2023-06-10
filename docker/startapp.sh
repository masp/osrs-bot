#!/bin/sh
export HOME=/config
export _JAVA_OPTIONS="-Duser.home=$HOME"

exec java -Duser.home=$HOME -jar /RuneLite.jar --launch-mode=REFLECT --mode=OFF