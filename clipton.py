import re
import os
import sys
import json
from pathlib import Path
from subprocess import Popen, PIPE
from typing import List
from datetime import datetime
from typing_extensions import TypedDict

# Item typed dictionary
Item = TypedDict("Item", {"date": int, "text": str, "num_lines": int})

# How many items to store in the file
max_items = 500

# Items are held here internally
items: List[Item]

# Path to the json file
filepath: Path

# Show the rofi menu with the items
def show_picker() -> None:
  opts: List[str] = []
  date_now = get_seconds()

  for item in items:
    line = item["text"].replace("\n", " ")
    line = re.sub(" +", " ", line)
    num_lines = item["num_lines"]
    diff = int((date_now - item["date"]) / 60)

    if diff >= 1440:
      if diff == 1440:
        sdiff = "day ago"
      else:
        sdiff = f"{diff} days ago"
    elif diff >= 60:
      if diff == 60:
        sdiff = f"{diff} hour ago"
      else:
        sdiff = f"{diff} hours ago"
    elif diff >= 1:
      if diff == 1:
        sdiff = f"{diff} minute ago"
      else:
        sdiff = f"{diff} minutes ago"
    elif diff == 0:
      sdiff = "just now"

    if num_lines == 1:
      slines = "line"
    else:
      slines = "lines"

    opts.append(f"({num_lines} {slines}) ({sdiff}) {line}")

  proc = Popen('rofi -dmenu -p "Select Item" -format i \
    -selected-row 0 -me-select-entry "" -me-accept-entry \
    "MousePrimary"', stdout=PIPE, stdin=PIPE, shell=True, text=True)

  ans = proc.communicate("\n".join(opts))[0].strip()

  if ans != "":
    on_selection(int(ans))

# When an item is selected through the rofi menu
def on_selection(index: int) -> None:
    text = items[index]["text"]
    proc = Popen('xclip -sel clip', stdout=PIPE, stdin=PIPE, shell=True, text=True)
    proc.communicate(text)
    del items[index]
    add_item(text)

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
  text = text.strip()
  if text == "":
    return
  if len(items) > 0 and items[0] == text:
    return
  items = list(filter(lambda x: x["text"] != text, items))
  num_lines = text.count("\n") + 1
  items.insert(0, {"date": get_seconds(), "text": text, "num_lines": num_lines})
  items = items[0:max_items]
  update_file()

# Main function
def main() -> None:
  mode = "show"

  if len(sys.argv) > 1:
    mode = sys.argv[1]

  get_items()

  if mode == "watcher":
    while True:
      os.popen(f"./clipnotify").read()
      add_item(os.popen("xclip -o").read())
  elif mode == "show":
    show_picker()

if __name__ == "__main__":
  main()