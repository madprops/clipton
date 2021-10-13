#!/bin/bash
gcc clipnotify.c -o clipnotify -I/usr/X11R6/include -L/usr/X11R6/lib -lX11 -lXfixes