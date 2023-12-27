import re

# Convert a YouTube Music URL to a YouTube URL
def convert(text: str) -> str:
	if "watch?v" in text:
		regex = re.compile("^https:\/\/music\.youtube\.com\/watch\?v=(?P<video_id>[\w-]+)[^ \n]*$")
		match = regex.search(text)

		if match and match.group("video_id"):
			arg = match.group("video_id")
			return f"https://www.youtube.com/watch?v={arg}"

	if "playlist?list" in text:
		regex = re.compile("^https:\/\/music\.youtube\.com\/playlist\?list=(?P<list_id>[\w-]+)[^ \n]*$")
		match = regex.search(text)

		if match and match.group("list_id"):
			arg = match.group("list_id")
			return f'https://www.youtube.com/playlist?list={arg}'

	return ""