import sys
from youtube_transcript_api import YouTubeTranscriptApi

ids = sys.argv[1].split(',')
step = int(sys.argv[2]) if len(sys.argv) > 2 else 90
out = sys.argv[3] if len(sys.argv) > 3 else 'tools/_digests.txt'

api = YouTubeTranscriptApi()
lines = []
for vid in ids:
    lines.append(f"==== {vid} ====")
    try:
        data = api.fetch(vid, languages=['ko', 'ko-KR']).to_raw_data()
    except Exception as e:
        lines.append(f"ERR {e!r}")
        lines.append("")
        continue
    total = data[-1]['start'] if data else 0
    lines.append(f"(length ~{int(total//60)}:{int(total%60):02d}, {len(data)} segs)")
    last = -1000.0
    for seg in data:
        st = float(seg['start'])
        if st >= last + step:
            mm = int(st // 60); ss = int(st % 60)
            lines.append(f"{mm:02d}:{ss:02d} {' '.join(seg['text'].split())}")
            last = st
    lines.append("")

with open(out, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print("WROTE", out, len(lines), "lines for", len(ids), "videos")
