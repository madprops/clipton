![](https://i.imgur.com/ZZYmqXd.jpg)

## Info

This is a python-based clipboard manager that uses Rofi as the frontend.

`copyevent` is required to detect copy events.

`xclip` is required to read and write to the clipboard.

To start a daemon that listens to copy events and update the json file run the script with the `watcher` argument.

Running the program without an argument will show the Rofi item picker.

The number displayed on the left of items refer to the number of linebreaks the item contains. This way you can tell if the item is a short line or a multi-line code blob.

It also displays how long ago the item was copied.

It can fetch titles from urls, which is enabled by default (it requires pip install bs4).

## Installation

There is an aur package called clipton-git

After installing, enable the user service:

`systemctl --user enable clipton.service`

`systemctl --user start clipton.service`