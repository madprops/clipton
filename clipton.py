#!/usr/bin/env python
VERSION = "6.0"

# Clipton is a clipboard manager for Linux
# Repo: https://github.com/madprops/clipton

# ABOUT

# It has 2 functions, the Rofi menu and the clipboard watcher
# The clipboard watcher is used to save copied text
# It works by using 'copyevent' to detect clipboard changes
# The list is saved in a JSON file in the config directory
# The items file path is '~/.config/clipton/items.json'
# The Rofi menu is used to view and select items from the list
# When an item is selected it is copied to the clipboard
# Then you can paste it anywhere you want

# INSTALLATION

# Install 'xclip' and 'rofi'
# Place 'clipton.py' somewhere in your path
# Compile and place 'copyevent' somewhere in your path
# Compilation command is commented at the top of the file
# Place 'clipton.service' inside '/usr/lib/systemd/user/'
# Start the watcher with 'systemctl --user start clipton'
# Make it autostart with 'systemctl --user enable clipton'
# Launch the Rofi menu with 'clipton.py'
# Add a keyboard shortcut to run 'clipton.py'
# For example 'Ctrl + Backtick'

# SETTINGS

# The settings file path is '~/.config/clipton/settings.json'
# Create it and override the settings you want to change:

# {
#   "heavy_paste": 3000,
#   "enable_titles": false
# }

# CONVERTERS

# Converters are functions that automatically change copied text into something else
# They are python files that reside in '~/.config/clipton/converters'
# Check out 'converters/youtube_music.py' for an example
# The function that is called is 'convert(text: str) -> str'
# If nothing is converted it must return an empty string
# Add or remove the converter files you want to enable/disable
# There's a script to copy all converters to the config directory

import os
import re
import sys
import json
import html
import shutil
import time
import subprocess
import logging
import importlib.util
from pathlib import Path
from typing import List, Dict, Tuple, Any
from urllib.request import urlopen
from html.parser import HTMLParser
from datetime import datetime

ORIGINAL = "Original: "

#-----------------
# SETTINGS
#-----------------

class Settings:
  max_items: int
  heavy_paste: int
  enable_titles: bool
  enable_converters: bool
  reverse_join: bool
  save_originals: bool
  rofi_width: int
  show_date: bool
  show_num_lines: bool

  # Read the settings file
  # Fill the settings class with the values
  @staticmethod
  def read() -> None:
    content = Files.read(Config.settings_path, "{}")
    settings = json.loads(content)

    # How many items to store in the file
    Settings.max_items = settings.get("max_items", 2000)

    # Don't save text if the character length exceeds this
    Settings.heavy_paste = settings.get("heavy_paste", 5000)

    # If enabled, the URL titles are fetched by parsing the HTML
    Settings.enable_titles = settings.get("enable_titles", True)

    # If enabled, the text can be converted
    Settings.enable_converters = settings.get("enable_converters", True)

    # If enabled, the join function will reverse the order of the items
    Settings.reverse_join = settings.get("reverse_join", False)

    # If enabled, the original text is saved before the converted text
    Settings.save_originals = settings.get("save_originals", True)

    # The percentage width of the Rofi menu
    Settings.rofi_width = settings.get("rofi_width", 66)

    # Show the date/timeago in the Rofi menu
    Settings.show_date = settings.get("show_date", True)

    # Show the number of lines in the Rofi menu
    Settings.show_num_lines = settings.get("show_num_lines", True)

#-----------------
# CONFIG
#-----------------

class Config:
  # Path to the config directory
  config_path = Path("~/.config/clipton").expanduser()

  # Path to the items file
  items_path = config_path / Path("items.json")

  # Path to the settings file
  settings_path = config_path / Path("settings.json")

  # Converters path
  converters_path = config_path / Path("converters")

  # Create the config directory and files
  @staticmethod
  def setup() -> None:
    if not Config.config_path.exists():
      Config.config_path.mkdir(parents = True)

    Config.items_path.touch(exist_ok = True)
    Config.settings_path.touch(exist_ok = True)

    if not Config.converters_path.exists():
      Config.converters_path.mkdir()

#-----------------
# Files
#-----------------

class Files:
  # Read a file and return the content
  @staticmethod
  def read(path: Path, fallback: str) -> str:
    file = open(path, "r")
    content = file.read().strip()

    if not content:
      content = fallback

    file.close()
    return content

  # Write to a file
  @staticmethod
  def write(path: Path, content: str) -> None:
    file = open(path, "w")
    file.write(content)
    file.close()

#-----------------
# UTILS
#-----------------

class Utils:
  # HTML parser to get the title from a URL
  class TitleParser(HTMLParser):
    def __init__(self) -> None:
      HTMLParser.__init__(self)
      self.match = False
      self.title = ""

    def handle_starttag(self, tag: str, attributes: List[Tuple[str, str | None]]) -> None:
      self.match = tag == "title"

    def handle_data(self, data: str) -> None:
      if self.match:
        self.title = data
        self.match = False

  # Log something for debugging
  @staticmethod
  def log(text: str) -> None:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt="%(asctime)s %(name)s.%(levelname)s: %(message)s", datefmt="%Y.%m.%d %H:%M:%S")
    handler = logging.StreamHandler(stream = sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info(text)

  # Check if a string contains a space
  @staticmethod
  def space(text: str) -> bool:
    return any(char.isspace() for char in text)

  # Convert a number into a filled string
  @staticmethod
  def fillnum(num: int) -> str:
    snum = str(num)
    return snum.rjust(2, "0")

  # Get unix seconts
  @staticmethod
  def get_seconds() -> int:
    return int(datetime.now().timestamp())

  # Get timeago string based on minutes
  @staticmethod
  def get_timeago(mins: int) -> str:
    if mins >= 1440:
      d = round(mins / 1440)
      timeago = f"{Utils.fillnum(d)} days"
    elif mins >= 60:
      d = round(mins / 60)
      timeago = f"{Utils.fillnum(d)} hours"
    elif mins >= 1:
      timeago = f"{Utils.fillnum(mins)} mins"
    elif mins == 0:
      timeago = "just now"

    return f"({timeago})".ljust(12, " ")

  # Get the content type of a URL
  @staticmethod
  def get_url_type(url: str) -> str:
    try:
      r = urlopen(url)
      header = r.headers
      return str(header.get_content_type())
    except:
      return "none"

  # Get the title from a URL
  @staticmethod
  def get_title(text: str) -> str:
    if text.startswith("https://") and not Utils.space(text):
      if not Utils.get_url_type(text) == "text/html":
        print("Non HTML URL")
      else:
        print("Getting Title")
        html = str(urlopen(text).read().decode("utf-8"))
        parser = Utils.TitleParser()
        parser.feed(html)
        return parser.title

    return ""

  # Copy text to the clipboard
  @staticmethod
  def copy_text(text: str) -> None:
    proc = subprocess.Popen("xclip -sel clip -f", stdout = subprocess.PIPE, \
    stdin = subprocess.PIPE, shell = True, text = True)
    proc.communicate(text, timeout = 3)

#-----------------
# CONVERTERS
#-----------------

class Converters:
  @staticmethod
  # Load all the converters and run them
  def convert(text: str) -> str:
    files = os.listdir(Config.converters_path)
    py_files = [file for file in files if file.endswith(".py")]

    for file in py_files:
      module_name = os.path.splitext(file)[0]
      module_path = Path(Config.converters_path / file)
      spec = importlib.util.spec_from_file_location(module_name, module_path)

      if spec is None:
        return ""

      if spec.loader is None:
        return ""

      module = importlib.util.module_from_spec(spec)
      spec.loader.exec_module(module)

      if hasattr(module, "convert") and callable(module.convert):
        new_text = module.convert(text)

        if new_text:
          return str(new_text)

    return ""

#-----------------
# ROFI
#-----------------

class Rofi:
  # Get the style for the Rofi menu
  @staticmethod
  def style() -> str:
    return f'-me-select-entry "" -me-accept-entry "MousePrimary"' \
    f' -theme-str "window {{width: {Settings.rofi_width}%;}}"'

  # Get a Rofi prompt
  @staticmethod
  def prompt(s: str) -> str:
    return f'rofi -dmenu -markup-rows -i -p "{s}"'

  # Show the Rofi menu with the items
  @staticmethod
  def show(selected: int = 0) -> None:
    opts: List[str] = []
    date_now = Utils.get_seconds()
    asterisk = f"<span> * </span>"

    for item in Items.items:
      line = item.text.strip()
      line = html.escape(line)
      line = re.sub(" *\n *", "\n", line)
      line = line.replace("\n", asterisk)
      line = re.sub(" +", " ", line)
      line = re.sub("</span> +", "</span>", line)
      num_lines = ""

      if Settings.show_num_lines:
        num_lines = str(item.num_lines) + ")"
        num_lines = num_lines.ljust(5, " ")
        num_lines = f"(Lines: {num_lines}"

      mins = round((date_now - item.date) / 60)
      timeago = ""

      if Settings.show_date:
        timeago = Utils.get_timeago(mins)

      title = ""

      if item.title:
        title = item.title

        if title and title != "":
          title = title.replace("\n", "").strip()
          title = html.escape(title)
          line += f" ({title})"

      opt_str = "<span>"

      if timeago:
        opt_str += timeago

      if num_lines:
        opt_str += num_lines

      opt_str += "</span>"
      opt_str += line
      opts.append(opt_str)

    num_items = len(Items.items)

    if num_items == 1:
      num = "1 Item"
    else:
      num = f"{num_items} Items"

    prompt = Rofi.prompt(f"Clipton {VERSION} | {num} | Alt+1 Delete | Alt+(2-9) Join | Alt+0 Clear")
    proc = subprocess.Popen(f"{prompt} -format i {Rofi.style()} -selected-row {selected}", \
    stdout = subprocess.PIPE, stdin = subprocess.PIPE, shell = True, text = True)
    ans = proc.communicate("\n".join(opts))[0].strip()

    if ans != "":
      code = proc.returncode
      index = int(ans)

      if code == 10:
        Items.delete(index)
        Rofi.show(index)
      elif code >= 11 and code <= 18:
        Items.join(index, code - 9)
        Rofi.show()
      elif code == 19:
        Items.confirm_delete()
      else:
        Items.select(index)

#-----------------
# ITEMS
#-----------------

class Item:
  # An item has these properties:
  # text: The text that was copied
  # date: The date when the text was copied
  # num_lines: The number of lines in the text
  # title: The title of the URL (if any)

  text: str
  date: int
  num_lines: int
  title: str

  # Create an item from a JSON object
  @staticmethod
  def from_json(obj: Dict[str, Any]) -> "Item":
    item = Item()
    item.text = obj["text"]
    item.date = obj["date"]
    item.num_lines = obj["num_lines"]
    item.title = obj["title"]
    return item

  # Create an item from text
  @staticmethod
  def from_text(text: str, title: str = "") -> "Item":
    item = Item()
    item.text = text
    item.date = Utils.get_seconds()
    item.num_lines = text.count("\n") + 1
    item.title = title
    return item

  # Convert an item to a dictionary
  def to_dict(self) -> Dict[str, Any]:
    return self.__dict__

class Items:
  # List with all the items
  items: List[Item] = []

  # Read the items file and fill the item list
  @staticmethod
  def read() -> None:
    content = Files.read(Config.items_path, "[]")
    Items.items = json.loads(content, object_hook = Item.from_json)

  # Stringify the JSON object and save it in the items file
  @staticmethod
  def write() -> None:
    content = json.dumps(Items.items, default = Item.to_dict, indent = 2)
    Files.write(Config.items_path, content)

  # When an item is selected through the Rofi menu
  @staticmethod
  def select(index: int) -> None:
    text = Items.items[index].text
    Utils.copy_text(text)

  # Delete an item from the item list
  @staticmethod
  def delete(index: int) -> None:
    del Items.items[index]
    Items.write()

  # Delete all the items
  @staticmethod
  def delete_all() -> None:
    Items.items = []
    Items.write()

  # Delete all items
  @staticmethod
  def confirm_delete() -> None:
    opts = ["No", "Yes"]
    prompt = Rofi.prompt("Delete all items?")
    proc = subprocess.Popen(f"{prompt} {Rofi.style()} -selected-row 0", \
    stdout = subprocess.PIPE, stdin = subprocess.PIPE, shell = True, text = True)
    ans = proc.communicate("\n".join(opts))[0].strip()

    if ans == "Yes":
      Items.delete_all()

  # Join 2 or more items into one
  @staticmethod
  def join(index: int, num: int) -> None:
    index_2 = index + num

    if Settings.reverse_join:
      item_slice = list(reversed(Items.items[index:index_2]))
    else:
      item_slice = Items.items[index:index_2]

    s = " ".join(item.text.strip() for item in item_slice)
    del Items.items[index:index_2]
    Items.add(s)
    Items.write()
    Utils.copy_text(s)

  # Add an item to the item list
  # It performs some checks
  # It removes duplicates
  @staticmethod
  def add(text: str) -> None:
    text = text.rstrip()

    if text == "":
      return

    if text.startswith("file://"):
      return

    if len(text) > Settings.heavy_paste:
      return

    item_exists = False

    for item in Items.items:
      if item.text == text:
        the_item = item
        item_exists = True
        Items.items.remove(the_item)
        break

    if not item_exists:
      the_item = Item.from_text(text)

    Items.items.insert(0, the_item)
    Items.items = Items.items[0:Settings.max_items]
    Items.write()

  # Insert an item into the item list
  # Try to convert the text
  # Get the title afterwards
  @staticmethod
  def insert(text: str) -> None:
    original = text.startswith(ORIGINAL)

    if Settings.enable_converters and not original:
      converted = Converters.convert(text)

      if converted:
        print("Text Converted")

        if Settings.save_originals:
          Items.add(ORIGINAL + text)

        Items.add(converted)
        Utils.copy_text(converted)
        Items.title(converted)
        return

    Items.add(text)
    Items.title(text)

  # Add a title to an item
  @staticmethod
  def title(text: str) -> None:
    if not Settings.enable_titles:
      return

    for item in Items.items:
      if item.text == text:
        if item.title:
          return

        title = Utils.get_title(text)

        if title:
          item.title = title

        Items.write()
        break

#-----------------
# WATCHER
#-----------------

class Watcher:
  # Start the clipboard watcher
  @staticmethod
  def start() -> None:
    if shutil.which("copyevent") is None:
      print("The watcher needs 'copyevent' to be installed.")
      exit(1)

    herepath = Path(__file__).parent.resolve()
    max_iterations = 100
    iterations = 0
    print("Watcher Started")

    while True:
      try:
        iterations += 1

        if iterations > max_iterations:
          Utils.log("Too many iterations")
          exit(1)

        ans = subprocess.run("copyevent -s clipboard", capture_output = True, shell = True)

        if ans.returncode == 0:
          ans = subprocess.run("xclip -o -sel clip", capture_output = True, shell = True, timeout = 3)

          if ans.returncode == 0:
            clip = ans.stdout.decode()

            if clip:
              Items.read()
              Items.insert(clip)
              iterations = 0

              # Give clipboard operations some time
              time.sleep(0.1)
      except Exception as err:
        Utils.log(err)

#-----------------
# MAIN
#-----------------

# Main function
def main() -> None:
  Config.setup()
  Settings.read()
  mode = "show"

  if len(sys.argv) > 1:
    mode = sys.argv[1]

  if mode == "watcher":
    try:
      Watcher.start()
    except KeyboardInterrupt:
      exit(0)

  elif mode == "show":
    Items.read()
    Rofi.show()

# Start the program
if __name__ == "__main__":
  main()