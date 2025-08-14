"""
This script reads .txt files from a specified input directory, sends their contents
to an OpenAI model, and generates five levels of adversarial perturbations ranging
from light character noise to heavy semantic distortion. Augmented outputs are saved
in separate subfolders by level, and any associated image files sharing the same
basename are copied alongside the augmented text. The script supports skipping
previously processed files, enforces API rate limits, and writes a detailed CSV log
of all operations performed.
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
from openai import AsyncOpenAI

# === Load OpenAI API Key from JSON ===
with open("openai_api_key.json", "r") as f:
    api_data = json.load(f)

# === Instantiate the async OpenAI client ===
client = AsyncOpenAI(api_key=api_data["openai_api_key"])

# === User Configuration ===
in_dir      = "/path/to/input/directory"
out_dir     = "/path/to/output/directory"
log_file    = os.path.join(out_dir, "augmentation_openai_log.csv")
s_aug_dir   = "/path/to/skip_already_augmented_dir"  # optional: skip files in this dir

ATT_STR                 = 100
MAX_REQUESTS_PER_MINUTE = 100  # OpenAI rate limit
BATCH_SIZE              = 1    # files per API request
DELAY_BETWEEN_REQUESTS  = 1    # seconds between requests
OPENAI_MODEL            = "gpt-4.1-mini"

# For rate limiting
request_times   = deque()
rate_limit_lock = asyncio.Lock()


def build_batched_prompt(texts):
    """
    Construct the adversarial perturbation prompt for the OpenAI API.
    Accepts a list of original texts and adds detailed instructions.
    """
    prompt = """
You are an adversarial text generator. Your task is to perturb the input text to fool downstream models such as classifiers or OCR engines. Generate five versions of the input text, each with a different level of perturbation as defined below.

Perturbation Levels:
Level 1 — Minimal (light noise): Minor character-level changes. Mostly readable and retains original meaning. Mimics accidental typos or OCR noise. (e.g., swap adjacent letters, lowercase/uppercase inconsistency, “O” to “0”, “l” to “1”)
Level 2 — Mild (readable but noisier): Combine character-level noise with small paraphrases or word substitutions. Still semantically faithful but noticeably altered.
Level 3 — Moderate (semantics shift): Introduce paraphrasing, antonyms, misleading insertions, or reordered phrases. Meaning is partially changed; models may misclassify it.
Level 4 — Strong (semantic inversion): Aggressively alter meaning through word replacements, phrase reversals, and misleading information. Still somewhat readable.
Level 5 — Extreme (highly adversarial): Severe character and semantic distortion. Text is hard to read or nonsensical, and original meaning is obscured or inverted completely.

Instructions:

1. For each level, label the output clearly as Level 1:, Level 2:, etc.
2. Each version must be unique.
3. Do not explain your changes.
4. Return the output in plain text only.
"""
    # Append each original text to the prompt
    for i, text in enumerate(texts, 1):
        prompt += f"\n\nOriginal Text:\n{text.strip()}"
    return prompt


def extract_augmented_texts(response_text):
    """
    Parse the API response into a dictionary keyed by perturbation level (1–5).
    """
    level_texts = {}
    for level in range(1, 6):
        start_tag = f"Level {level}:"
        end_tag = f"Level {level + 1}:" if level < 5 else None
        start = response_text.find(start_tag)
        end = response_text.find(end_tag) if end_tag else len(response_text)
        if start == -1:
            level_texts[level] = ""
        else:
            level_texts[level] = response_text[start + len(start_tag):end].strip()
    return level_texts


async def respect_rate_limit():
    """
    Enforce MAX_REQUESTS_PER_MINUTE by delaying requests when necessary.
    Uses a deque to track timestamps of recent requests.
    """
    async with rate_limit_lock:
        now = time.monotonic()
        # Remove timestamps older than 60 seconds
        while request_times and (now - request_times[0]) > 60:
            request_times.popleft()

        # If at limit, sleep until we can send the next request
        if len(request_times) >= MAX_REQUESTS_PER_MINUTE:
            sleep_time = 60 - (now - request_times[0])
            print(f"Rate limit hit, sleeping for {sleep_time:.2f} seconds...")
            await asyncio.sleep(sleep_time)
            now = time.monotonic()
            while request_times and (now - request_times[0]) > 60:
                request_times.popleft()

        request_times.append(time.monotonic())


async def send_batched_prompt(batch):
    """
    Send a batch of texts to the OpenAI API for augmentation.
    Returns augmented outputs, file paths, status, and error messages.
    """
    await respect_rate_limit()
    await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

    paths, texts = zip(*batch)
    prompt = build_batched_prompt(texts)

    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.7,
            max_tokens=4096,
        )

        response_text = response.choices[0].message.content.strip()
        return [extract_augmented_texts(response_text) for _ in batch], paths, "success", ""

    except Exception as e:
        print(f"❌ API call failed for batch {[p for p,_ in batch]}:", e)
        return {}, paths, "fail", str(e)


async def process_directory(in_dir, out_dir):
    """
    Process all .txt files in the input directory, skipping already augmented ones,
    and write augmented versions to separate level-based subfolders.
    """
    os.makedirs(out_dir, exist_ok=True)
    log_entries    = []
    all_to_process = []

    # Index files already augmented (if skipping is enabled)
    prior_augmented = set()
    if s_aug_dir:
        for root, _, files in os.walk(s_aug_dir):
            for file in files:
                if file.lower().endswith(".txt"):
                    prior_augmented.add(file)
    print(f"Indexed {len(prior_augmented)} previously augmented .txt files from {s_aug_dir!r}")

    # Collect files to process
    for root, _, files in os.walk(in_dir):
        rel_root = os.path.relpath(root, in_dir)
        out_root = os.path.join(out_dir, rel_root)
        os.makedirs(out_root, exist_ok=True)

        for file in sorted(files):
            if not file.lower().endswith(".txt"):
                continue
            if file in prior_augmented:
                print(f"Skipping (already augmented): {file}")
                continue

            src_path = os.path.join(root, file)
            dst_path = os.path.join(out_root, file)
            all_to_process.append((src_path, dst_path))
    print(f"Queued {len(all_to_process)} .txt files for augmentation")

    # Create async tasks for each batch
    batches = [all_to_process[i:i + BATCH_SIZE] for i in range(0, len(all_to_process), BATCH_SIZE)]
    tasks   = []
    for batch in batches:
        texts = []
        for src, _ in batch:
            try:
                async with aiofiles.open(src, "r", encoding="utf-8") as f:
                    texts.append(await f.read())
            except Exception as e:
                log_entries.append([src, "fail", f"Read error: {e}"])
                texts.append("")
        tasks.append(asyncio.create_task(send_batched_prompt(list(zip(batch, texts)))))

    # Collect results as tasks complete
    for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Processing Batches"):
        augmented_map, paths, status, message = await future
        for i, (src, dst) in enumerate(paths):
            if status == "success":
                level_outputs = augmented_map[i]  # dict {level_num: text}
                rel_dst_path  = os.path.relpath(dst, out_dir)

                for level_num, text in level_outputs.items():
                    level_dir     = os.path.join(out_dir, f"l{level_num}")
                    full_out_path = os.path.join(level_dir, rel_dst_path)
                    os.makedirs(os.path.dirname(full_out_path), exist_ok=True)
                    try:
                        # Save augmented text
                        async with aiofiles.open(full_out_path, "w", encoding="utf-8") as f:
                            await f.write(text)

                        # Copy matching image (if exists) alongside augmented text
                        base_name, _ = os.path.splitext(os.path.basename(src))
                        img_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".webp"]
                        for ext in img_extensions:
                            candidate_path = os.path.join(os.path.dirname(src), base_name + ext)
                            if os.path.exists(candidate_path):
                                target_img_path = os.path.join(level_dir, os.path.relpath(candidate_path, in_dir))
                                os.makedirs(os.path.dirname(target_img_path), exist_ok=True)
                                shutil.copy2(candidate_path, target_img_path)
                                break

                        log_entries.append([src, f"augmented_level_{level_num}", ""])
                    except Exception as e:
                        log_entries.append([src, f"fail_level_{level_num}", f"Write error: {e}"])
            else:
                log_entries.append([src, "fail", message or "Missing augmented output"])

    # Write process log to CSV
    with open(log_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filepath", "status", "message"])
        writer.writerows(log_entries)
    print(f"\nLog saved to: {log_file}")


if __name__ == "__main__":
    asyncio.run(process_directory(in_dir, out_dir))
