This is a python-based clipboard manager with no extra dependencies needed.

A small c program called clipnotify is used to detect copy events.

Run `compile.sh` to compile it.

To start a daemon that listens to copy events and update the json file run the script with the `watcher` argument.

Running the program without an argument will show the Rofi item picker.

The number displayed on the left of items refer to the number of linebreaks the item contains. This way you can tell if the item is a short line or a multi-line code blob.