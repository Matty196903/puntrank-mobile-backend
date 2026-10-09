import asyncio
import os
import subprocess
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
from emergentintegrations.llm.openai import OpenAITextToSpeech

SEGMENTS = [
    (0.2, 5.6, "Welcome to PuntRank Aus. First up, confirm you're eighteen or older to enter."),
    (5.8, 13.2, "Create your free account with just an email and password, or continue as a guest to browse."),
    (13.4, 18.2, "Here are today's meetings. Tap any track to open its race card."),
    (18.4, 24.9, "Tap a runner to see its win chance, confidence score, and the reasoning behind its ranking."),
    (25.1, 32.9, "A grade runners are the strongest bets of the day. B grade are solid chances. C grade are place hopes and exotics roughies."),
    (33.0, 35.5, "Ace's selections. Winners and places."),
    (35.7, 40.2, "The quaddie tab shows leg one free. Pro unlocks all four legs."),
    (40.4, 45.1, "On the reports page, tap download to grab the PDF form guide."),
    (45.3, 49.8, "It saves straight to your phone or computer."),
    (50.0, 54.7, "Go Pro to unlock everything. And remember, always gamble responsibly."),
]


def dur(path):
    out = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(out.stdout.strip())


async def main():
    tts = OpenAITextToSpeech(api_key=os.getenv("EMERGENT_LLM_KEY"))
    os.makedirs("/app/video_out", exist_ok=True)
    files = []
    for i, (start, end, text) in enumerate(SEGMENTS):
        raw = f"/app/video_out/seg{i}.mp3"
        audio = await tts.generate_speech(text=text, model="tts-1-hd", voice="onyx")
        with open(raw, "wb") as f:
            f.write(audio)
        window = end - start
        d = dur(raw)
        final = raw
        if d > window:
            tempo = min(1.6, d / window + 0.02)
            final = f"/app/video_out/seg{i}f.mp3"
            subprocess.run(["ffmpeg", "-y", "-i", raw, "-filter:a", f"atempo={tempo:.3f}", final],
                           capture_output=True)
            d = dur(final)
        print(f"seg{i}: window={window:.1f}s audio={d:.1f}s")
        files.append((start, final))

    inputs, delays = [], []
    for i, (start, f) in enumerate(files):
        inputs += ["-i", f]
        ms = int(start * 1000)
        delays.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
    n = len(files)
    fc = ";".join(delays) + ";" + "".join(f"[a{i}]" for i in range(n)) + \
         f"amix=inputs={n}:normalize=0[out]"
    subprocess.run(["ffmpeg", "-y", "-i", "/app/frontend/public/tutorial.mp4", *inputs,
                    "-filter_complex", fc, "-map", "0:v", "-map", "[out]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "96k", "-shortest",
                    "/app/frontend/public/tutorial_voiced.mp4"], capture_output=True)
    print("muxed:", os.path.getsize("/app/frontend/public/tutorial_voiced.mp4"))

asyncio.run(main())
