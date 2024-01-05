## Clipton (Clipboard Manager)

<img src="clipton.jpg" width="450">

## About

Clipton helps you go back to previous clipboard text.

It has 2 modes: the [Rofi](https://github.com/davatorium/rofi) menu, and the clipboard watcher.

The clipboard watcher is used to save copied text automatically.

The [Rofi](https://github.com/davatorium/rofi) menu is used to view and select saved items.

You can type something to filter the items.

When an item is selected it is copied to the clipboard.

Then you can paste it anywhere you want.

It can delete individual items or all items.

It has some extra features like joining items.

It can also convert text automatically.

It only deals with text, not binary files.

It has only been tested on `X11` and not `Wayland`.

## Installation

Install [xclip](https://archlinux.org/packages/extra/x86_64/xclip/)
and [rofi](https://archlinux.org/packages/extra/x86_64/rofi/) (Third-party programs):

`sudo pacman -S xclip rofi`

Clone this repo somewhere:

`git clone --depth=1 https://github.com/madprops/clipton`

Place [clipton.py](clipton.py) in `/usr/bin/clipton`.

Place [clipton.service](clipton.service) inside `/usr/lib/systemd/user/`.

Start the watcher with `systemctl --user start clipton`.

Make it autostart with `systemctl --user enable clipton`.

Restart it after an update with `systemctl --user restart clipton`.

Stop it (for some reason) with `systemctl --user stop clipton`.

If you want to start the watcher manually use `clipton watcher`.

Launch the [Rofi](https://github.com/davatorium/rofi) menu with `clipton`.

Add a keyboard shortcut (somehow) to run `clipton`.

For example bind it to `Ctrl + Backtick`.

The config directory is `~/.config/clipton/`.

The items, settings, and converters are placed there.

## Settings

The settings file is `~/.config/clipton/settings.toml`.

It uses the [TOML](https://github.com/toml-lang/toml) format and is not required to be edited.

Check the `Settings` class in [clipton.py](clipton.py) for the default values.

Override the settings you want to change by adding them to `settings.toml`:

```toml
max_items = 250
enable_titles = false
rofi_width = "50%"
```

## Converters

Converters are functions that automatically change copied text to something else.

They are python files that reside in `~/.config/clipton/converters/`.

Check out [converters/youtu_be.py](converters/youtu_be.py) for an example.

The function that is called is `convert(text: str) -> str`.

If nothing is converted it must return an empty string.

Add or remove the converter files you want to enable/disable.

There's a [script](copy_converters.sh) to copy all included converters to the config directory.

If the setting `save_originals` is enabled, the original text is also saved.

It's saved as `Original :: <text>` and it's placed below the converted text.

If the converted item is no longer the first item, the original is removed.

## Icons

There's 3 icons that appear next to the text items.

A green icon means the text is a single line.

A red icon means the text has multiple lines.

A blue globe icon means the text is a URL.

When the url icon is set

The icons are settings and can be changed in the settings file.

If you set them as empty ("") they won't be used.

You can disable all icons by setting `show_icons` to `false`.