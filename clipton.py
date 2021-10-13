import re
import os
import sys
import json
from pathlib import Path
from subprocess import Popen, PIPE
from typing import List

# How many items to store in the file
max_items = 500

# Items are held here internally
items: List[str]

# Path to the json file
filepath: Path

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
def add_item(content: str) -> None:
  global items
  content = content.strip()
  if content == "":
    return
  if len(items) > 0 and items[0] == content:
    return
  items = list(filter(lambda x: x != content, items))
  items.insert(0, content)
  items = items[0:max_items]
  update_file()

# Show the rofi menu with the items
def show_picker() -> None:
  opts: List[str] = []
  
  for item in items:
    nlines = item.count("\n") + 1
    line = item.replace("\n", " ")
    line = re.sub(" +", " ", line)
    opts.append(f"({nlines}) {line}")
  
  options = "\n".join(opts)

  p1 = Popen('rofi -dmenu -p "Select Item" -format i \
    -selected-row 0 -me-select-entry "" -me-accept-entry \
    "MousePrimary"', stdout=PIPE, stdin=PIPE, shell=True, text=True)

  ans = p1.communicate(options)[0].strip()

  if ans != "":
    on_selection(int(ans))

# When an item is selected through the rofi menu
def on_selection(index: int) -> None:
    oitem = items[index]
    item = oitem.encode("unicode_escape").decode("utf-8")
    os.popen(f"echo '{item}' | xclip -sel clip")
    del items[index]
    add_item(oitem)  

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