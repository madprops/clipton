#!/usr/bin/env python

# Clipton is a clipboard manager for Linux
# It has 2 functions, the Rofi menu and the clipboard watcher
# The clipboard watcher is used to save copied text
# It works by using 'copyevent' to detect a clipboard change
# The list is saved in a JSON file in the config directory
# The items file path is '~/.config/clipton/items.json'
# The Rofi menu is used to select previous items from the list
# When an item is selected it is copied to the clipboard
# Then you can paste it anywhere you want
# You need to install 'xclip' and 'rofi' for this to work
# You also need to install 'copyevent' for the watcher to work
# Then start the watcher with 'python clipton.py watcher'
# To launch the Rofi menu use 'python clipton.py'
# Add a keyboard shortcut to show the Rofi menu

# The settings file path is '~/.config/clipton/settings.json'
# The settings file can look like:

# {
# 	"enable_titles": false,
# 	"converts": {
# 		"youtube_music": false
# 	}
# }

# Just override the settings you want to change

import re
import sys
import json
import html
import shutil
import subprocess
import logging
from pathlib import Path
from typing import List
from urllib.request import urlopen
from html.parser import HTMLParser
from datetime import datetime

#----------
# GLOBALS
#----------

class Globals:
  # Items are held here internally
  items = []

  # Path to the config directory
  config_path = Path("~/.config/clipton").expanduser()

  # Path to the items file
  items_path = config_path / Path("items.json")

  # Path to the settings file
  settings_path = config_path / Path("settings.json")

#----------
# CONFIG
#----------

class Config:
  def setup():
    if not Globals.config_path.exists():
      Globals.config_path.mkdir(parents = True)

    Globals.items_path.touch(exist_ok = True)
    Globals.settings_path.touch(exist_ok = True)

#----------
# SETTINGS
#----------

class Settings:
  def read():
    file = open(Globals.settings_path, "r")
    content = file.read().strip()

    if not content:
      content = "{}"

    settings = json.loads(content)
    file.close()

  # How many items to store in the file
    Settings.max_items = settings.get("max_items", 2000)

  # Don't save to file if char length exceeds this
    Settings.heavy_paste = settings.get("heavy_paste", 5000)

  # If enabled the URL titles are fetched
    Settings.enable_titles = settings.get("enable_titles", True)

  # If enabled the text can be converted
    Settings.enable_converts = settings.get("enable_converts", True)

  # The specific converts to enable
    Settings.converts = settings.get("converts", {})

    if not Settings.converts:
      Settings.converts = {}

    if not "youtube_music" in Settings.converts:
      Settings.converts["youtube_music"] = True

#----------
# UTILS
#----------

class Utils:
  # HTML parser to get the title from a URL
  class TitleParser(HTMLParser):
    def __init__(self):
      HTMLParser.__init__(self)
      self.match = False
      self.title = ""

    def handle_starttag(self, tag, attributes):
      self.match = tag == "title"

    def handle_data(self, data):
      if self.match:
        self.title = data
        self.match = False

  # Log something for debugging
  def log(text: str) -> None:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt="%(asctime)s %(name)s.%(levelname)s: %(message)s", datefmt="%Y.%m.%d %H:%M:%S")
    handler = logging.StreamHandler(stream = sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info(text)

  # Check if a string contains a space
  def space(text: str) -> str:
    return any(char.isspace() for char in text)

  # Convert a number into a filled string
  def fillnum(num: int) -> str:
    snum = str(num)
    return snum.rjust(2, "0")

  # Get unix seconts
  def get_seconds() -> int:
    return int(datetime.now().timestamp())

  # Get timeago string based on minutes
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
  def get_url_type(url: str) -> str:
    try:
      r = urlopen(url)
      header = r.headers
      return header.get_content_type()
    except:
      return "none"

  # Get the title from a URL
  def get_title(text: str) -> str:
    if text.startswith("https://") and not Utils.space(text):
      if not Utils.get_url_type(text) == "text/html":
        print("Non HTML URL")
      else:
        print("Fetching title...")
        html = str(urlopen(text).read().decode("utf-8"))
        parser = Utils.TitleParser()
        parser.feed(html)
        return parser.title

    return ""

  # Copy text to the clipboard
  def copy_text(text: str) -> None:
    proc = subprocess.Popen("xclip -sel clip -f", stdout = subprocess.PIPE, \
    stdin = subprocess.PIPE, shell = True, text = True)
    proc.communicate(text, timeout = 3)

#----------
# CONVERTS
#----------

class Converts:
  # Convert text into something else
  def check(text: str) -> str:
    new_text = ""

    if Settings.converts["youtube_music"]:
      new_text = Converts.youtube_music(text)

    if new_text:
      Utils.copy_text(new_text)
      return new_text

    return text

  # Convert a Youtube Music URL into a Youtube URL
  def youtube_music(text: str) -> str:
    if Utils.space(text): return text

    new_text = ""

    if Settings.converts["youtube_music"]:
      regex = re.compile(r"https://music\.youtube\.com/(watch\?v=([\w-]+)|playlist\?list=([\w-]+))")
      match = regex.search(text)

      if match and match.group(2):
        video_id = match.group(2)
        new_text = f'https://www.youtube.com/watch?v={video_id}'

      if match and match.group(3):
        playlist_id = match.group(3)
        new_text = f'https://www.youtube.com/playlist?list={playlist_id}'

    return new_text

#----------
# ROFI
#----------

class Rofi:
  # Style for Rofi windows
  style = '-me-select-entry "" -me-accept-entry "MousePrimary" \
    -theme-str "window {width: 66%;}"'

  # Get a Rofi prompt
  def prompt(s: str) -> str:
    return f'rofi -dmenu -markup-rows -i -p "{s}"'

  # Show the Rofi menu with the items
  def show(selected: int = 0) -> None:
    opts: List[str] = []
    date_now = Utils.get_seconds()
    asterisk = f"<span> * </span>"

    for item in Globals.items:
      line = item["text"].strip()
      line = html.escape(line)
      line = re.sub(" *\n *", "\n", line)
      line = line.replace("\n", asterisk)
      line = re.sub(" +", " ", line)
      line = re.sub("</span> +", "</span>", line)
      num_lines = str(item["num_lines"]) + ")"
      num_lines = num_lines.ljust(5, " ")
      mins = round((date_now - item["date"]) / 60)
      timeago = Utils.get_timeago(mins)
      title = ""

      if "title" in item:
        title = item["title"]

        if title and title != "":
          title = title.replace("\n", "").strip()
          title = html.escape(title)
          line += f" ({title})"

      opts.append(f"<span>{timeago}(Lines: {num_lines}</span>{line}")

    prompt = Rofi.prompt("Alt+1 Delete | Alt+(2-9) Join | Alt+0 Clear")
    proc = subprocess.Popen(f"{prompt} -format i {Rofi.style} -selected-row {selected}", \
    stdout = subprocess.PIPE, stdin = subprocess.PIPE, shell = True, text = True)
    ans = proc.communicate("\n".join(opts))[0].strip()

    if ans != "":
      code = proc.returncode
      index = int(ans)

      if code == 10:
        Items.delete(index)
        Rofi.show(index)
      elif code >= 11 and code <= 18:
        Items.join(code - 9)
      elif code == 19:
        Items.confirm_delete()
      else:
        Items.select(index)

#----------
# ITEMS
#----------

class Items:
  def read() -> None:
    file = open(Globals.items_path, "r")
    content = file.read().strip()

    if content == "":
      content = "[]"

    Globals.items = json.loads(content)
    file.close()

  # Stringify the JSON object and save it into the file
  def write() -> None:
    file = open(Globals.items_path, "w")
    file.write(json.dumps(Globals.items))
    file.close()

  # When an item is selected through the Rofi menu
  def select(index: int) -> None:
    text = Globals.items[index]["text"]
    Utils.copy_text(text)

  # Delete an item from the item list
  def delete(index: int) -> None:
    del Globals.items[index]
    update_file()

  # Delete all the items
  def delete_all() -> None:
    Globals.items = []
    update_file()

  # Delete all items
  def confirm_delete() -> None:
    opts = ["No", "Yes"]
    prompt = Rofi.prompt("Delete all items?")
    proc = subprocess.Popen(f"{prompt} {Rofi.style} -selected-row 0", \
    stdout = subprocess.PIPE, stdin = subprocess.PIPE, shell = True, text = True)
    ans = proc.communicate("\n".join(opts))[0].strip()

    if ans == "Yes":
      Items.delete_all()

  # Join 2 or more items into one
  def join(num: int) -> None:
    s = " ".join(item["text"].strip() for item in reversed(Globals.items[0:num]))
    del Globals.items[0:num]
    update_file()
    Utils.copy_text(s)

  # Add an item to the items array
  # It performs some checks
  # It removes duplicates
  def add(text: str) -> None:
    text = text.rstrip()

    if text == "":
      return

    if text.startswith("file://"):
      return

    if len(text) > Settings.heavy_paste:
      return

    if Settings.enable_converts:
      text = Converts.check(text)

    item_exists = False

    for item in Globals.items:
      if item["text"] == text:
        the_item = item
        item_exists = True
        Globals.items.remove(the_item)
        break

    if not item_exists:
      title = ""

      if Settings.enable_titles:
        title = Utils.get_title(text)

      num_lines = text.count("\n") + 1
      the_item = {"date": Utils.get_seconds(), "text": text, "num_lines": num_lines, "title": title}

    Globals.items.insert(0, the_item)
    Globals.items = Globals.items[0:Settings.max_items]
    Items.write()

#----------
# WATCHER
#----------

class Watcher:
  # Start the clipboard watcher
  def start() -> None:
    if shutil.which("copyevent") is None:
      print("The watcher needs 'copyevent' to be installed.")
      exit(1)

    herepath = Path(__file__).parent.resolve()
    max_iterations = 100
    iterations = 0

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
              Items.add(clip)
              iterations = 0
      except Exception as err:
        Utils.log(err)

#----------
# MAIN
#----------

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