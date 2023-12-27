## Clipton (Clipboard Manager)

<img src="clipton.jpg" width="420">

## About

Clipton helps you go back to previous clipboard text.

It has 2 functions, the Rofi menu and the clipboard watcher.

The clipboard watcher is used to save copied text automatically.

It works by using `copyevent` to detect clipboard changes.

The Rofi menu is used to view and select saved items.

You can type something to filter the items.

When an item is selected it is copied to the clipboard.

Then you can paste it anywhere you want.

It can delete indidiual items or all items.

It has some extra features like joining items.

It can also convert text automatically.

## Installation

Install `xclip` and `rofi` (Third party programs).

Place `clipton.py` somewhere in your path like `/usr/bin/`.

Compile `copyevent.c` and place `copyevent` in your path.

Compilation command is commented at the top of the c file.

Place `clipton.service` inside `/usr/lib/systemd/user/`.

Start the watcher with `systemctl --user start clipton`.

Make it autostart with `systemctl --user enable clipton`.

Launch the Rofi menu with `clipton.py`.

Add a keyboard shortcut (somehow) to run `clipton.py`.

For example bind it to `Ctrl + Backtick`.

The config path is `~/.config/clipton`.

The items, settings, and converters are placed there.

## Settings

The settings file path is `~/.config/clipton/settings.toml`.

It uses the TOML format and is not required to be edited.

Check the `Settings` class in [clipton.py](clipton.py) for the default values.

Override the settings you want to change by adding them:

```toml
max_items = 250
enable_titles = false
rofi_width = "50%"
```

## Converters

Converters are functions that automatically change copied text into something else.

They are python files that reside in `~/.config/clipton/converters`.

Check out `converters/youtube_music.py` for an example.

The function that is called is `convert(text: str) -> str`.

If nothing is converted it must return an empty string.

Add or remove the converter files you want to enable/disable.

There's a script to copy all converters to the config directory.

If the setting `save_originals` is enabled, the original text is also saved.

It's saved as `Original :: <text>` and it's placed below the converted text.

If the converted item is no longer the first item, the original is removed.