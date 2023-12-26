import re

def convert(text: str) -> str:
	if not text.startswith("https://youtu.be"):
		return ""

	regex = re.compile(r"^https:\/\/youtu.be\/(?P<video_id>[\w-]+)(\?t=(?P<timestamp>[\d]+))?[^ \n]*$")
	match = regex.search(text)

	if match and match.group("video_id"):
		video_id = match.group("video_id")
		timestamp = match.group("timestamp")

		if timestamp:
			return f'https://www.youtube.com/watch?v={video_id}&t={timestamp}s'
		else:
			return f'https://www.youtube.com/watch?v={video_id}'

	return ""