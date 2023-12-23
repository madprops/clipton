settings = {}

# How many items to store in the file
settings["max_items"] = 2000

# Don't save to file if char length exceeds this
settings["heavy_paste"] = 5000

# If enabled the URL titles are fetched
settings["enable_titles"] = True

# If enabled the text can be converted
settings["enable_converts"] = True

# The specific converts to enable
settings["converts"] = {
  "youtube_music": True,
}

def setting(key: str) -> any:
  return settings[key]