#!/usr/bin/env python

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

# Items are held here internally
items = []

# Path to the json file
filepath: Path

#----------
# SETTINGS
#----------

class Settings:
  # How many items to store in the file
  max_items = 2000

  # Don't save to file if char length exceeds this
  heavy_paste = 5000

  # If enabled the URL titles are fetched
  enable_titles = True

  # If enabled the text can be converted
  enable_converts = True

  # The specific converts to enable
  converts = {
    "youtube_music": True,
  }

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
  @staticmethod
  def log(text: str) -> None:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt="%(asctime)s %(name)s.%(levelname)s: %(message)s", datefmt="%Y.%m.%d %H:%M:%S")
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info(text)

  # Check if a string contains a space
  @staticmethod
  def space(text: str) -> str:
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
      return header.get_content_type()
    except:
      return "none"

  # Get the title from a URL
  @staticmethod
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

  # Copy text to clipboard
  @staticmethod
  def copy_text(text: str) -> None:
    proc = subprocess.Popen("xclip -sel clip -f", stdout = subprocess.PIPE, stdin = subprocess.PIPE, shell = True, text = True)
    proc.communicate(text, timeout = 3)

#----------
# CONVERTS
#----------

class Converts:
  # Convert text into something else
  @staticmethod
  def convert(text: str) -> str:
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

    if new_text:
      Utils.copy_text(new_text)
      return new_text

    return text

#----------
# ROFI
#----------

class Rofi:
  # Style for rofi windows
  style = '-me-select-entry "" -me-accept-entry "MousePrimary" \
    -theme-str "window {width: 66%;}"'

  # Get a rofi prompt
  @staticmethod
  def prompt(s: str) -> str:
    return f'rofi -dmenu -markup-rows -i -p "{s}"'

  # Show the rofi menu with the items
  @staticmethod
  def show(selected: int = 0) -> None:
    opts: List[str] = []
    date_now = Utils.get_seconds()
    asterisk = f"<span> * </span>"

    for item in items:
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
    proc = subprocess.Popen(f"{prompt} -format i {Rofi.style} -selected-row {selected}", stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, text=True)
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
# Items
#----------

class Items:
  # When an item is selected through the rofi menu
  @staticmethod
  def select(index: int) -> None:
    text = items[index]["text"]
    Utils.copy_text(text)

  # Delete an item from the item list
  @staticmethod
  def delete(index: int) -> None:
    del items[index]
    update_file()

  # Delete all the items
  @staticmethod
  def delete_all() -> None:
    global items
    items = []
    update_file()

  # Delete all items
  @staticmethod
  def confirm_delete() -> None:
    opts = ["No", "Yes"]
    prompt = Rofi.prompt("Delete all items?")
    proc = subprocess.Popen(f"{prompt} {Rofi.style} -selected-row 0", stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True, text=True)
    ans = proc.communicate("\n".join(opts))[0].strip()

    if ans == "Yes":
      Items.delete_all()

  # Join 2 or more items into one
  @staticmethod
  def join(num: int) -> None:
    s = " ".join(item["text"].strip() for item in reversed(items[0:num]))
    del items[0:num]
    update_file()
    Utils.copy_text(s)

  # Read the items file and parse it to json
  @staticmethod
  def get() -> None:
    global items
    global filepath

    configdir = Path("~/.config/clipton").expanduser()

    if not configdir.exists():
      configdir.mkdir(parents=True)

    filepath = configdir / Path("items.json")
    filepath.touch(exist_ok=True)

    file = open(filepath, "r")
    content = file.read().strip()

    if content == "":
      content = "[]"

    items = json.loads(content)
    file.close()

  # Add an item to the items array
  # It performs some checks
  # It removes duplicates
  @staticmethod
  def add(text: str) -> None:
    global items
    text = text.rstrip()

    if text == "":
      return

    if text.startswith("file://"):
      return

    if len(text) > Settings.heavy_paste:
      return

    if Settings.enable_converts:
      text = Converts.convert(text)

    item_exists = False

    for item in items:
      if item["text"] == text:
        the_item = item
        item_exists = True
        items.remove(the_item)
        break

    if not item_exists:
      title = ""

      if Settings.enable_titles:
        title = Utils.get_title(text)

      num_lines = text.count("\n") + 1
      the_item = {"date": Utils.get_seconds(), "text": text, "num_lines": num_lines, "title": title}

    items.insert(0, the_item)
    items = items[0:Settings.max_items]
    update_file()

#----------
# MAIN
#----------

# Stringify the json object and save it into the file
def update_file() -> None:
  file = open(filepath, "w")
  file.write(json.dumps(items))
  file.close()

# Start the clipboard watcher
def start_watcher() -> None:
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
            Items.get()
            Items.add(clip)
            iterations = 0
    except Exception as err:
      Utils.log(err)

# Main function
def main() -> None:
  mode = "show"

  if len(sys.argv) > 1:
    mode = sys.argv[1]

  if mode == "watcher":
    try:
      start_watcher()
    except KeyboardInterrupt:
      exit(0)

  elif mode == "show":
    Items.get()
    Rofi.show()

# Start program
if __name__ == "__main__":
  main()