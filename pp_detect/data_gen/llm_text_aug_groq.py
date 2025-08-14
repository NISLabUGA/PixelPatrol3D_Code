"""
This script performs text data augmentation using the Groq API. It processes .txt files
from specified input directories, sending batches of texts for keyword-based synonym
replacement while preserving overall meaning. For each text file, it saves the augmented
output and copies any associated image with the same filename. Already-augmented files
are skipped, and results are logged to a CSV file. Processing is asynchronous with
built-in rate limiting to respect API request quotas.
"""


import os
import json
import shutil
import aiofiles
import asyncio
import csv
import time
from collections import deque
from pathlib import Path
from tqdm.asyncio import tqdm
from groq import AsyncGroq

# === Load Groq API Key from JSON ===
with open("groq_api_key.json", "r") as f:
    api_data = json.load(f)
    groq_api_key = api_data["groq_api_key"]

# Instantiate asynchronous Groq client
client = AsyncGroq(api_key=groq_api_key)

# === User Configuration ===
input_dir_list = [
    # Replace these with your input directories containing .txt files
    "/path/to/input_dir_1",
    "/path/to/input_dir_2",
    "/path/to/input_dir_3"
]

MAX_REQUESTS_PER_MINUTE = 100   # API rate limit
BATCH_SIZE              = 10   # Files per API request
DELAY_BETWEEN_REQUESTS  = 0.5  # Seconds between requests
GROQ_MODEL              = "llama-3.3-70b-versatile"

# Supported image file extensions (for copying alongside augmented .txt files)
IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"]

# === Internal state ===
request_times   = deque()       # Tracks timestamps of recent requests for rate limiting
rate_limit_lock = asyncio.Lock()

# === Prompt construction ===
def build_batched_prompt(texts):
    """
    Builds a batch prompt for Groq API.
    For each text, adds a numbered 'Text X:' label and instructs the model to perform
    keyword-based synonym replacement while preserving meaning and structure.
    """
    prompt = ""
    for i, text in enumerate(texts, 1):
        prompt += f"Text {i}:\n{text.strip()}\n\n"
    prompt += (
        "Please perform data augmentation on the texts above. "
        "Modify each text while preserving its overall meaning and structure. "
        "Use keyword-based synonym replacement, focusing on semantically important words (e.g., verbs, nouns, adjectives). "
        "Do not clean up or correct any nonsensical phrases—leave them unchanged. "
        "Each augmented response should be unique and written in plain text. "
        "Please do not add any other information, notes. or text other than what is described below. "
        "Clearly label each output as 'Text #:' matching the input numbering. "
        "Example: Text 1: This is an example response."
    )
    return prompt

def extract_augmented_texts(response_text, batch_size):
    """
    Extracts the augmented outputs from the API response.
    Ensures each 'Text X:' block corresponds to the correct input.
    Removes any internal reasoning (<think> tags) if present.
    """
    split_tag = "</think>"
    body = response_text.split(split_tag, 1)[-1].strip() if split_tag in response_text else response_text.strip()
    augmented = {}
    for i in range(1, batch_size + 1):
        tag = f"Text {i}:"
        start = body.find(tag)
        if start == -1:
            augmented[i] = ""
            continue
        end = body.find(f"Text {i+1}:", start) if i < batch_size else len(body)
        content = body[start + len(tag):end].strip()
        augmented[i] = content
    return augmented

# === Rate limiting ===
async def respect_rate_limit():
    """
    Enforces the MAX_REQUESTS_PER_MINUTE constraint.
    Uses a deque to track timestamps of API calls and sleeps if limit is reached.
    """
    async with rate_limit_lock:
        now = time.monotonic()
        while request_times and (now - request_times[0]) > 60:
            request_times.popleft()
        if len(request_times) >= MAX_REQUESTS_PER_MINUTE:
            sleep_time = 60 - (now - request_times[0])
            print(f"⏳ Rate limit hit, sleeping for {sleep_time:.2f} seconds...")
            await asyncio.sleep(sleep_time)
            now = time.monotonic()
            while request_times and (now - request_times[0]) > 60:
                request_times.popleft()
        request_times.append(time.monotonic())

# === API call ===
async def send_batched_prompt(batch):
    """
    Sends a batch of texts to the Groq API and returns augmented results.
    """
    await respect_rate_limit()
    await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
    paths, texts = zip(*batch)
    prompt = build_batched_prompt(texts)
    try:
        chat_completion = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that performs keyword-based synonym replacement."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_completion_tokens=4096,
            top_p=1,
            stop=None,
            stream=False,
        )
        response_text = chat_completion.choices[0].message.content.strip()
        return extract_augmented_texts(response_text, len(batch)), paths, "success", ""
    except Exception as e:
        return {}, paths, "fail", str(e)

# === File utilities ===
def copy_associated_images(txt_path, dst_txt_path):
    """
    Copies any associated image with the same basename as the .txt file to the output directory.
    """
    base_src = os.path.splitext(txt_path)[0]
    base_dst = os.path.splitext(dst_txt_path)[0]
    dst_dir  = os.path.dirname(dst_txt_path)
    for ext in IMAGE_EXTENSIONS:
        img_file = base_src + ext
        if os.path.exists(img_file):
            dst_file = os.path.join(dst_dir, os.path.basename(base_dst + ext))
            try:
                shutil.copy2(img_file, dst_file)
                print(f"🖼️ Copied image: {img_file}")
            except Exception as e:
                print(f"❌ Failed to copy image {img_file}: {e}")

# === Main processing ===
async def process_directory(in_dir):
    """
    Processes all .txt files in the given directory:
    - Skips already augmented files
    - Sends batches to Groq API
    - Writes augmented text and copies associated images
    - Logs results to CSV
    """
    out_dir   = in_dir + "_text_aug"
    os.makedirs(out_dir, exist_ok=True)
    log_file  = os.path.join(out_dir, "augmentation_groq_log.csv")
    s_aug_dir = out_dir

    log_entries  = []
    copy_later   = []
    all_to_process = []

    # Collect filenames that are already augmented
    prior_augmented_filenames = set()
    for root, _, files in os.walk(s_aug_dir):
        for file in files:
            if file.endswith(".txt"):
                prior_augmented_filenames.add(file)
    print(f"✅ Indexed {len(prior_augmented_filenames)} previously augmented .txt files from {s_aug_dir}")

    # Walk through input directory and collect new .txt files
    for root, _, files in os.walk(in_dir):
        rel_root = os.path.relpath(root, in_dir)
        out_root = os.path.join(out_dir, rel_root)
        os.makedirs(out_root, exist_ok=True)
        for file in sorted(files):
            src_path = os.path.join(root, file)
            dst_path = os.path.join(out_root, file)
            if not file.endswith(".txt"):
                continue
            if file in prior_augmented_filenames:
                print(f"⏩ Skipping (already augmented): {file}")
                continue
            if file.endswith("_ORIGINAL.txt"):
                copy_later.append((src_path, dst_path))
            else:
                all_to_process.append((src_path, dst_path))

    # Create batches for API requests
    batches = [all_to_process[i:i + BATCH_SIZE] for i in range(0, len(all_to_process), BATCH_SIZE)]
    batch_tasks = []
    for batch in batches:
        texts = []
        for src_path, _ in batch:
            try:
                async with aiofiles.open(src_path, "r", encoding="utf-8") as f:
                    content = await f.read()
                texts.append(content)
            except Exception as e:
                log_entries.append([src_path, "fail", f"Read error: {e}"])
                texts.append("")
        batch_tasks.append(asyncio.create_task(send_batched_prompt(list(zip(batch, texts)))))

    # Process batches asynchronously as they complete
    for batch_future in tqdm(asyncio.as_completed(batch_tasks), total=len(batch_tasks), desc=f"Processing {in_dir}"):
        augmented_map, paths, status, message = await batch_future
        for i, (src_path, dst_path) in enumerate(paths, 1):
            if status == "success" and augmented_map.get(i):
                try:
                    async with aiofiles.open(dst_path, "w", encoding="utf-8") as f:
                        await f.write(augmented_map[i])
                    copy_associated_images(src_path, dst_path)
                    log_entries.append([src_path, "augmented", ""])
                except Exception as e:
                    log_entries.append([src_path, "fail", f"Write error: {e}"])
            else:
                log_entries.append([src_path, "fail", message or "Missing augmented output"])

    # Copy "_ORIGINAL" text files without modification
    for src_path, dst_path in copy_later:
        try:
            shutil.copy2(src_path, dst_path)
            copy_associated_images(src_path, dst_path)
            print(f"📄 Copied: {src_path}")
            log_entries.append([src_path, "copied", ""])
        except Exception as e:
            log_entries.append([src_path, "fail", f"Copy error: {e}"])

    # Write processing log to CSV
    with open(log_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filepath", "status", "message"])
        writer.writerows(log_entries)
    print(f"\n📜 Log saved to: {log_file}")

# === Entrypoint ===
if __name__ == "__main__":
    async def main():
        for in_dir in input_dir_list:
            await process_directory(in_dir)
    asyncio.run(main())
