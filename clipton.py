#!/usr/bin/env python

VERSION = "32"
# https://github.com/madprops/clipton

import os
import re
import sys
import json
import html
import shutil
import time
import subprocess
import tomllib
import importlib.util
from pathlib import Path
from typing import List, Dict, Tuple, Any, Callable, Union
from urllib.request import urlopen
from html.parser import HTMLParser
from datetime import datetime
from dataclasses import dataclass

ORIGINAL = "Original :: "
CMD_TIMEOUT = 3

#-----------------
# SETTINGS
#-----------------

@dataclass
class Settings:
  # How many items to store in the file
  max_items: int = 1000

  # Don't save text if the character length exceeds this
  heavy_paste: int = 2000

  # If enabled, the URL titles are fetched by parsing the HTML
  enable_titles: bool = True

  # If enabled, the text can be converted
  enable_converters: bool = True

  # If enabled, the original text is saved before the converted text
  save_originals: bool = True

  # Show the date/timeago in the Rofi menu
  show_date: bool = True

  # Show the number of lines in the Rofi menu
  show_num_lines: bool = True

  # Show the name and version in the prompt
  show_name: bool = True

  # Show the number of items in the prompt
  show_num_items: bool = True

  # Show shortcuts in the prompt
  show_shortcuts: bool = True

  # Remove http:// or https:// from a line
  remove_http: bool = True

  # Remove www. from a line
  remove_www: bool = True

  # Show icons or not
  show_icons: bool = True

  # If enabled, the join function will reverse the order of the items
  reverse_join: bool = False

  # The width of the Rofi menu (percentage or pixels)
  rofi_width: str = "1080px"

  # Icon to use for URLs
  url_icon: str = "🌐"

  # Icon to use for items with a single line
  single_icon: str = "🟢"

  # Icon to use for items with multiple lines
  multi_icon: str = "🔴"

  # Read the settings file
  @staticmethod
  def read() -> None:
    data = Files.read_toml(Config.settings_path)
    props = Settings.__annotations__

    for prop in props.keys():
      if prop in data:
        setattr(Settings, prop, data[prop])

#-----------------
# CONFIG
#-----------------

@dataclass
class Config:
  # Path to the config directory
  config_path = Path("~/.config/clipton").expanduser()

  # Path to the items file
  items_path = config_path / Path("items.json")

  # Path to the settings file
  settings_path = config_path / Path("settings.toml")

  # Converters path
  converters_path = config_path / Path("converters")

  # Create the config directory and files
  @staticmethod
  def setup() -> None:
    if not Config.config_path.exists():
      Files.mkdir(Config.config_path)

    if not Config.converters_path.exists():
      Files.mkdir(Config.converters_path)

    Files.touch(Config.items_path)
    Files.touch(Config.settings_path)

#-----------------
# Files
#-----------------

class Files:
  # Read a file and return the content
  @staticmethod
  def read(path: Path, fallback: str = "") -> str:
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

  # Read a JSON file and return the
  @staticmethod
  def read_json(path: Path, hook: Callable[[Any], Any], fallback: str = "[]") -> Any:
    content = Files.read(path, fallback)

    if hook is not None:
      return json.loads(content, object_hook = hook)
    else:
      return json.loads(content)

  # Write to a JSON file
  @staticmethod
  def write_json(path: Path, data: Any, default: Callable[[Any], Any]) -> None:
    content = json.dumps(data, default=default, indent=2)
    Files.write(Config.items_path, content)

  # Read a TOML file and return the dictionary
  @staticmethod
  def read_toml(path: Path) -> Dict[str, Any]:
    with open(path, "rb") as file:
      return tomllib.load(file)

  # Create a file
  @staticmethod
  def touch(path: Path) -> None:
    path.touch(exist_ok=True)

  # Create a directory
  @staticmethod
  def mkdir(path: Path) -> None:
    path.mkdir(parents=True)

#-----------------
# UTILS
#-----------------

# Return data from commands
class CmdOutput:
  text: str
  code: int

  def __init__(self, text: str, code: int) -> None:
    self.text = text
    self.code = code

class Utils:
  # HTML parser to get the title from a URL
  class TitleParser(HTMLParser):
    def __init__(self) -> None:
      HTMLParser.__init__(self)
      self.match = False
      self.title = ""

    def handle_starttag(self, tag: str, attributes: List[Any]) -> None:
      self.match = tag == "title"

    def handle_data(self, data: str) -> None:
      if self.match:
        self.title = data
        self.match = False

  # Check if a string contains a space
  @staticmethod
  def space(text: str) -> bool:
    return any(char.isspace() for char in text)

  # Convert a number into a filled string
  @staticmethod
  def fill_num(num: int) -> str:
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
      timeago = f"{Utils.fill_num(d)} day"
    elif mins >= 60:
      d = round(mins / 60)
      timeago = f"{Utils.fill_num(d)} hrs"
    elif mins >= 0:
      timeago = f"{Utils.fill_num(mins)} min"

    return Utils.info(timeago, 9)

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
    http = text.startswith("http://")
    https = text.startswith("https://")

    if (http or https) and not Utils.space(text):
      if not Utils.get_url_type(text) == "text/html":
        Utils.msg("Non HTML URL")
      else:
        Utils.msg("Getting Title")
        html = str(urlopen(text).read().decode("utf-8"))
        parser = Utils.TitleParser()
        parser.feed(html)
        return parser.title

    return ""

  # Copy text to the clipboard
  @staticmethod
  def copy_text(text: str) -> None:
    Utils.run("xclip -sel clip -f", text, timeout=CMD_TIMEOUT)

  # Read the clipboard
  @staticmethod
  def read_clipboard() -> str:
    ans = Utils.run("xclip -o -sel clip", timeout=CMD_TIMEOUT)

    if ans.code == 0:
      return str(ans.text)

    return ""

  # Print text
  @staticmethod
  def msg(text: str) -> None:
    print(f"\033[92mClipton:\033[0m {text}")

  # Add a spaced info string
  @staticmethod
  def info(text: str, amount: int) -> str:
    text = text.ljust(amount, " ")
    return f"<b>{text}</b>"

  # Run a command
  @staticmethod
  def run(cmd: str, text: str = "", timeout: int = 0) -> CmdOutput:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, \
          stdin=subprocess.PIPE, shell=True, text=True)

    if timeout > 0:
      stdout, stderr = proc.communicate(text, timeout=timeout)
    else:
      stdout, stderr = proc.communicate(text)

    return CmdOutput(text=stdout.strip(), code=proc.returncode)

  # Check if a program is installed
  @staticmethod
  def need(name: str) -> None:
    if shutil.which(name) is None:
      Utils.msg(f"'{name}' must be installed.")
      exit(1)

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

class TextData:
  single: bool
  http: bool
  https: bool
  www: bool

  # Get the text data for a line
  @staticmethod
  def get(item: "Item") -> "TextData":
    data = TextData()
    data.single = item.num_lines == 1
    data.http = item.text.startswith("http://")
    data.https = item.text.startswith("https://")
    data.www = item.text.startswith("https://www.") or \
    item.text.startswith("http://www.")
    return data

class Rofi:
  # Get the style for the Rofi menu
  @staticmethod
  def style() -> str:
    return f'-me-select-entry "" -me-accept-entry "MousePrimary"' \
    f' -theme-str "window {{width: calc(100% min {Settings.rofi_width});}}"'

  # Get a Rofi prompt
  @staticmethod
  def prompt(s: str) -> str:
    return f'rofi -dmenu -markup-rows -i -p "{s}"'

  # Show the Rofi menu with the items
  @staticmethod
  def show(selected: int = 0) -> None:
    opts: List[str] = []
    asterisk = f"<span> * </span>"

    for item in Items.items:
      line = item.text.strip()
      line = html.escape(line)
      line = re.sub(" *\n *", "\n", line)
      line = line.replace("\n", asterisk)
      line = re.sub(" +", " ", line)
      line = re.sub("</span> +", "</span>", line)
      line += Rofi.get_title(item)
      opt_str = Rofi.get_info(item)
      text_data = TextData.get(item)
      line = Rofi.remove(item, line, text_data)
      opt_str += Rofi.get_icon(item, line, text_data)
      opts.append(opt_str)

    p = []

    if Settings.show_name:
      p.append(f"Clipton v{VERSION}")

    if Settings.show_num_items:
      num_items = len(Items.items)

      if num_items == 1:
        num = "1 Item"
      else:
        num = f"{num_items} Items"

      p.append(num)

    if Settings.show_shortcuts:
      p.append(f"Alt+1 Delete | Alt+(2-9) Join | Alt+0 Clear")

    prompt = Rofi.prompt(" | ".join(p))
    prompt = f"{prompt} -format i {Rofi.style()} -selected-row {selected}"
    ans = Utils.run(prompt, "\n".join(opts))

    if ans.text:
      code = ans.code
      index = int(ans.text)

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

  # Get the info strings for an item
  @staticmethod
  def get_info(item: "Item") -> str:
    num_lines = ""

    if Settings.show_num_lines:
      num_lines = Utils.fill_num(item.num_lines)
      num_lines = f"Ln: {num_lines}"
      num_lines = Utils.info(num_lines, 9)

    timeago = ""

    if Settings.show_date:
      date_now = Utils.get_seconds()
      mins = round((date_now - item.date) / 60)
      timeago = Utils.get_timeago(mins)

    s = "<span>"

    if timeago:
      s += timeago

    if num_lines:
      s += num_lines

    s += "</span>"
    return s

  # Get the title string for an item
  @staticmethod
  def get_title(item: "Item") -> str:
    if item.title:
      title = ""
      title = item.title

      if title:
        title = title.replace("\n", "").strip()
        title = html.escape(title)
        return f" <b>({title})</b>"

    return ""

  # Remove unwanted text from a line
  @staticmethod
  def remove(item: "Item", line: str, td: "TextData") -> str:
    if Settings.remove_http and td.single:
      removed = ""

      if Settings.remove_www:
        removed += re.sub(r"^(https?://(www\.)?)", "", line)
      else:
        removed += re.sub(r"^(https?://)", "", line)

      if removed:
        line = removed
        meta = ""

        if td.www:
          meta += "www."

        if td.http:
          line += f"\0meta\x1fhttp:// {meta}"
        elif td.https:
          line += f"\0meta\x1fhttps:// {meta}"

    return line

  # Get the icons for a line
  @staticmethod
  def get_icon(item: "Item", line: str, td: "TextData") -> str:
    s = ""

    if Settings.show_icons:
      if Settings.url_icon and (td.http or td.https):
        s += f"{Settings.url_icon} {line}"
      elif Settings.single_icon and td.single:
        s += f"{Settings.single_icon} {line}"
      elif Settings.multi_icon and (not td.single):
        s += f"{Settings.multi_icon} {line}"

    return s

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
    Items.items = Files.read_json(Config.items_path, Item.from_json)

  # Stringify the JSON object and save it in the items file
  @staticmethod
  def write() -> None:
    Files.write_json(Config.items_path, Items.items, Item.to_dict)

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
    prompt = f"{prompt} {Rofi.style()} -selected-row 0"
    ans = Utils.run(prompt, "\n".join(opts))

    if ans.text == "Yes":
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

    if not text:
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
        Utils.msg("Text Converted")

        if Settings.save_originals:
          Items.add(ORIGINAL + text)

        Items.add(converted)
        Utils.copy_text(converted)
        Items.title(converted)
        Items.clean()
        return

    Items.add(text)
    Items.title(text)
    Items.clean()

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

  # Remove unwanted items
  @staticmethod
  def clean() -> None:
    keep = []

    for index, item in enumerate(Items.items):
      if item.text.startswith(ORIGINAL):
        if index != 1:
          continue

      keep.append(item)

    if len(Items.items) != len(keep):
      Items.items = keep
      Items.write()

  # Show the Rofi menu
  @staticmethod
  def show() -> None:
    Utils.need("rofi")
    Items.read()
    Rofi.show()

#-----------------
# WATCHER
#-----------------

class Watcher:
  # The last text that was copied
  last_clip: str

  # Time interval in seconds to check the clipboard
  sleep_time = 0.5

  # Start the clipboard watcher
  # This is a loop that checks the clipboard periodically
  # It detects clipboard changes and adds to the item list
  @staticmethod
  def start() -> None:
    Utils.need("xclip")
    Watcher.last_clip = Utils.read_clipboard()
    Utils.msg("Watcher Started")

    while True:
      clip = Utils.read_clipboard()

      if clip and (clip != Watcher.last_clip):
        Watcher.last_clip = clip

        if clip.startswith("file://"):
          continue

        if clip.startswith(ORIGINAL):
          continue

        Items.read()
        Items.insert(clip)

      # Very important
      time.sleep(Watcher.sleep_time)

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
    Items.show()

# Start the program
if __name__ == "__main__":
  main()