import re
import os
import sys
import json
import html
import mimetypes
from pathlib import Path
from subprocess import Popen, PIPE
from typing import List
from datetime import datetime
from typing_extensions import TypedDict
from urllib.request import urlopen
from bs4 import BeautifulSoup

# Item typed dictionary
Item = TypedDict("Item", {"date": int, "text": str, "num_lines": int, "title": str})

# How many items to store in the file
max_items = 1000

# Don't save to file if char length exceeds this
heavy_paste = 5000

# Items are held here internally
items: List[Item]

# Path to the json file
filepath: Path

# Color used for information
color_1 = "#1BBFFF"

# If enabled the url titles are fetched 
enable_title_fetch = True

# Convert a number into a filled string
def fillnum(num: int) -> str:
  snum = str(num)
  return snum.rjust(2, "0")

# Get the content type of a URL
def get_url_type(url: str) -> str:
  r = urlopen(url)
  header = r.headers
  return header.get_content_type()  

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

  return f"({timeago})".ljust(11, " ")

# Get a description of the size of the paste
def get_sizestring(size: int) -> str:
  if size <= 140:
    sizestring = "Small"
  elif size > 140 and size <= 1000:
    sizestring = "Normal"
  elif size > 1000 and size <= 2000:
    sizestring = "Big"
  elif size > 2000:
    sizestring = "Huge"
  
  return f"({sizestring})".ljust(9, " ")

# Show the rofi menu with the items
def show_picker() -> None:
  opts: List[str] = []
  date_now = get_seconds()
  asterisk = f"<span color='{color_1}'> * </span>"

  for item in items:
    line = item["text"].strip()
    line = html.escape(line)
    line = re.sub(" *\n *", "\n", line)
    line = line.replace("\n", asterisk)
    line = re.sub(" +", " ", line)
    line = re.sub("</span> +", "</span>", line)
    num_lines = str(item["num_lines"])
    num_lines = num_lines.ljust(3, " ")
    mins = round((date_now - item["date"]) / 60)
    timeago = get_timeago(mins)
    size = get_sizestring(len(line))
    title = ""
    
    if "title" in item:
      title = item["title"]
      if title and title != "":
        title = title.replace("\n", "").strip()
        title = html.escape(title)
        line += f" ({title})"
    
    opts.append(f"<span color='{color_1}'>{timeago}Ln: {num_lines}{size}</span>{line}")

  proc = Popen('rofi -dmenu -markup-rows -i -p "Select Item" -format i \
    -selected-row 0 -me-select-entry "" -me-accept-entry "MousePrimary" \
    -theme-str "window {width: 66%;}" \
    -theme-str "#element.selected.normal {background-color: rgba(0, 0, 0, 0%);}" \
    -theme-str "#element.selected.normal {border: 2px 2px 2px;}"'
    , stdout=PIPE, stdin=PIPE, shell=True, text=True)

  ans = proc.communicate("\n".join(opts))[0].strip()

  if ans != "":
    on_selection(int(ans))

# When an item is selected through the rofi menu
def on_selection(index: int) -> None:
  print(index)
  text = items[index]["text"]
  proc = Popen('xclip -sel clip -f', stdout=PIPE, stdin=PIPE, shell=True, text=True)
  proc.communicate(text)

def get_seconds() -> int:
  return int(datetime.now().timestamp())

# Read the items file and parse it to json
def get_items() -> None:
  global items
  global filepath
  thispath = Path(__file__).parent.resolve()
  filepath = Path(thispath) / Path("items.json")
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
  if len(items) > 0 and items[0] == text:
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
        try:
          if not get_url_type(text) == "text/html":
            print("Non HTML URL")
        except:
          pass
        else:
          try:
            print("Fetching title...")
            html = urlopen(text)
            soup = BeautifulSoup(html, 'lxml')
            title = soup.title.string
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
  herepath = Path(__file__).parent.resolve()
  clipath = Path(herepath) / Path("clipnotify")

  while True:
    # clipnotify exits on a copy event
    os.popen(str(clipath)).read()
    content = os.popen("xclip -o -sel clip").read()
    add_item(content)

# Main function
def main() -> None:
  mode = "show"

  if len(sys.argv) > 1:
    mode = sys.argv[1]

  get_items()

  if mode == "watcher":
    start_watcher()
  elif mode == "show":
    show_picker()

if __name__ == "__main__":
  main()