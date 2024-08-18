import re


# Convert a youtu.be URL to a YouTube URL
def convert(text: str) -> str:
    regex = re.compile(
        r"^https:\/\/youtu.be\/(?P<video_id>[\w-]+)(\?t=(?P<timestamp>[\d]+))?[^ \n]*$"
    )
    match = regex.search(text)

    if match and match.group("video_id"):
        video_id = match.group("video_id")
        timestamp = match.group("timestamp")

        if timestamp:
            return f"https://www.youtube.com/watch?v={video_id}&t={timestamp}s"
        else:
            return f"https://www.youtube.com/watch?v={video_id}"

    return ""
