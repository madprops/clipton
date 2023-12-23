import sys
import logging
from urllib.request import urlopen
from html.parser import HTMLParser
from datetime import datetime

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
def log(text):
  logger = logging.getLogger(__name__)
  logger.setLevel(logging.INFO)
  formatter = logging.Formatter(fmt="%(asctime)s %(name)s.%(levelname)s: %(message)s", datefmt="%Y.%m.%d %H:%M:%S")
  handler = logging.StreamHandler(stream=sys.stdout)
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
    timeago = f"{fillnum(d)} days"
  elif mins >= 60:
    d = round(mins / 60)
    timeago = f"{fillnum(d)} hours"
  elif mins >= 1:
    timeago = f"{fillnum(mins)} mins"
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
  if text.startswith("https://") and not space(text):
    if not get_url_type(text) == "text/html":
      print("Non HTML URL")
    else:
      print("Fetching title...")
      html = str(urlopen(text).read().decode("utf-8"))
      parser = TitleParser()
      parser.feed(html)
      return parser.title

  return ""