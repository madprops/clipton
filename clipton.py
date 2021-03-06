#!/usr/bin/env python

import re
import os
import sys
import json
import html
import shutil
from pathlib import Path
from subprocess import Popen, PIPE
from typing import List
from datetime import datetime
from urllib.request import urlopen
from html.parser import HTMLParser

class TitleParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.match = False
    self.title = ''

  def handle_starttag(self, tag, attributes):
    self.match = tag == 'title'

  def handle_data(self, data):
    if self.match:
      self.title = data
      self.match = False

# How many items to store in the file
max_items = 2000

# Don't save to file if char length exceeds this
heavy_paste = 5000

# Items are held here internally
items = []

# Path to the json file
filepath: Path

# If enabled the url titles are fetched 
enable_title_fetch = True

# Style for rofi windows
rofi_style = '-me-select-entry "" -me-accept-entry "MousePrimary" \
  -theme-str "window {width: 66%;}"'

# Get a rofi prompt
def rofi_prompt(s: str) -> str:
  return f'rofi -dmenu -markup-rows -i -p "{s}"'

# Convert a number into a filled string
def fillnum(num: int) -> str:
  snum = str(num)
  return snum.rjust(2, "0")

# Get the content type of a URL
def get_url_type(url: str) -> str:
  try:
    r = urlopen(url)
    header = r.headers
    return header.get_content_type()
  except:
    return "none"

# Get timeago string based on minutes
def get_timeago(mins: int) -> str:
  if mins >= 1440:
    d = round(mins / 1440)
    timeago = f"{fillnum(d)} days"
  elif mins >= 60:
    d = round(mins / 60)
    timeago = f"{fillnum(d)} hours"
  elif mins >= 1:
    timeago = f"{fillnum(mins)} mins"
  elif mins == 0:
    timeago = "just now" 

  return f"({timeago})".ljust(12, " ")

# Show the rofi menu with the items
def show_picker(selected: int = 0) -> None:
  opts: List[str] = []
  date_now = get_seconds()
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
    timeago = get_timeago(mins)
    title = ""
    
    if "title" in item:
      title = item["title"]
      if title and title != "":
        title = title.replace("\n", "").strip()
        title = html.escape(title)
        line += f" ({title})"
    
    opts.append(f"<span>{timeago}(Lines: {num_lines}</span>{line}")

  prompt = rofi_prompt("Alt+1 Delete | Alt+(2-9) Join | Alt+0 Clear")
  proc = Popen(f'{prompt} -format i {rofi_style} -selected-row {selected}', stdout=PIPE, stdin=PIPE, shell=True, text=True)
  ans = proc.communicate("\n".join(opts))[0].strip()

  if ans != "":
    code = proc.returncode
    index = int(ans)
    
    if code == 10:
      delete_item(index)
      show_picker(index)
    elif code >= 11 and code <= 18:
      join_items(code - 9)
    elif code == 19:
      confirm_delete_items()
    else:
      select_item(index)

# Copy text to clipboar
def copy_text(text: str) -> None:
  proc = Popen('xclip -sel clip -f', stdout=PIPE, stdin=PIPE, shell=True, text=True)
  proc.communicate(text)      

# When an item is selected through the rofi menu
def select_item(index: int) -> None:
  text = items[index]["text"]
  copy_text(text)

# Delete an item from the item list
def delete_item(index: int) -> None:
  del items[index]
  update_file()

# Delete all items
def confirm_delete_items() -> None:
  opts = ["No", "Yes"]
  prompt = rofi_prompt("Delete all items?")
  proc = Popen(f'{prompt} {rofi_style} -selected-row 0', stdout=PIPE, stdin=PIPE, shell=True, text=True)
  ans = proc.communicate("\n".join(opts))[0].strip()
  if ans == "Yes":
    delete_items()

# Delete all the items
def delete_items() -> None:
  global items
  items = []
  update_file()

# Get unix seconts
def get_seconds() -> int:
  return int(datetime.now().timestamp())

# Join 2 or more items into one
def join_items(num: int) -> None:
  s = " ".join(item["text"].strip() for item in reversed(items[0:num]))
  del items[0:num]
  update_file()
  copy_text(s)

# Read the items file and parse it to json
def get_items() -> None:
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

# Stringify the json object and save it into the file
def update_file() -> None:
  file = open(filepath, "w")
  file.write(json.dumps(items))
  file.close()

# Add an item to the items array
# It performs some checks
# It removes duplicates
def add_item(text: str) -> None:
  global items
  text = text.rstrip()

  if text == "":
    return
  if text.startswith("file://"):
    return
  if len(text) > heavy_paste:
    return
  
  item_exists = False
  
  for item in items:
    if item["text"] == text:
      the_item = item
      item_exists = True
      items.remove(the_item)
      break
  
  if not item_exists:
    title = ""

    if enable_title_fetch:
      if text.startswith("https://") and len(text.split(" ")) == 1:
        if not get_url_type(text) == "text/html":
          print("Non HTML URL")
        else:
          try:
            print("Fetching title...")
            html = str(urlopen(text).read())
            parser = TitleParser()
            parser.feed(html)
            title = parser.title
            print(title)
          except:
            pass

    num_lines = text.count("\n") + 1
    the_item = {"date": get_seconds(), "text": text, "num_lines": num_lines, "title": title}

  items.insert(0, the_item)
  items = items[0:max_items]
  update_file()

# Start the clipboard watcher
def start_watcher() -> None:
  if shutil.which("copyevent") is None:
    print("The watcher needs 'copyevent' to be installed.")
    exit(1)

  herepath = Path(__file__).parent.resolve()

  while True:
    # copyevent exits on a copy event
    os.popen("copyevent -s clipboard").read()
    clip = os.popen("xclip -o -sel clip").read()
    print(f"clip: {clip}")
    get_items()
    add_item(clip)

# Main function
def main() -> None:
  mode = "show"

  if len(sys.argv) > 1:
    mode = sys.argv[1]

  if mode == "watcher":
    start_watcher()
  elif mode == "show":
    get_items()
    show_picker()

if __name__ == "__main__":
  main()