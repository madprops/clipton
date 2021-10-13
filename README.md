This is a python-based clipboard manager that uses Rofi as the frontend.

A small c program called clipnotify is used to detect copy events.

Run `compile.sh` to compile it.

`xsel` is required to read and write to the clipboard.

To start a daemon that listens to copy events and update the json file run the script with the `watcher` argument.

Running the program without an argument will show the Rofi item picker.

The number displayed on the left of items refer to the number of linebreaks the item contains. This way you can tell if the item is a short line or a multi-line code blob.