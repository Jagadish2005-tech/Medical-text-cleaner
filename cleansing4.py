import pandas as pd
import os
import re
from collections import Counter

# === Load replacement dictionary ===
replacement_df = pd.read_csv('fully_expanded_dataset.csv').dropna()
replacements = {
    row['shorthand'].strip().lower(): row['full_form'].strip().lower()
    for _, row in replacement_df.iterrows()
}

# Compile regex pattern to do all replacements at once
replacement_pattern = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in replacements.keys()) + r')\b'
)

def bulk_replace(text, counter):
    def replace_match(match):
        word = match.group(0).lower()
        counter[word] += 1
        return replacements[word]
    return replacement_pattern.sub(replace_match, str(text).lower())

# Updated: Keep commas in the text
def apply_regex(text):
    text = re.sub(r'[^\w\s,]', '', text)  # keep only word chars, spaces, and commas
    return re.sub(r'\s+', ' ', text).strip()

# === Paths ===
input_folder = 'input'
output_folder = 'output'
log_folder = 'logs'

os.makedirs(output_folder, exist_ok=True)
os.makedirs(log_folder, exist_ok=True)

# === Process each CSV file with chunking ===
for filename in os.listdir(input_folder):
    if not filename.endswith('.csv'):
        continue

    input_path = os.path.join(input_folder, filename)
    output_path = os.path.join(output_folder, filename)
    log_path = os.path.join(log_folder, f'replacement_summary_{filename}.txt')

    print(f"\n🔄 Processing: {filename}")
    chunk_size = 10000
    replacement_counts = Counter()
    is_first_chunk = True

    # Use encoding fallback
    try:
        reader = pd.read_csv(input_path, chunksize=chunk_size)
    except UnicodeDecodeError:
        reader = pd.read_csv(input_path, chunksize=chunk_size, encoding='ISO-8859-1')

    for chunk in reader:
        if 'Clinical Notes' not in chunk.columns:
            print(f"⚠️ Skipped {filename} — 'Clinical Notes' column not found.")
            break

        chunk['Original Notes'] = chunk['Clinical Notes'].astype(str)
        chunk['Cleaned Notes'] = chunk['Original Notes'].apply(
            lambda text: apply_regex(bulk_replace(text, replacement_counts))
        )

        columns_to_save = ['Original Notes', 'Cleaned Notes']
        chunk[columns_to_save].to_csv(
            output_path,
            mode='w' if is_first_chunk else 'a',
            index=False,
            header=is_first_chunk
        )
        is_first_chunk = False

    # Save log file
    with open(log_path, 'w', encoding='utf-8') as log_file:
        log_file.write(f"🔍 Replacement Summary for {filename}:\n\n")
        for word, count in replacement_counts.items():
            log_file.write(f"{word} ➜ {replacements[word]} : {count} replacements\n")

    print(f"✅ Cleaned file saved: {output_path}")
    print(f"📝 Log saved: {log_path}")
