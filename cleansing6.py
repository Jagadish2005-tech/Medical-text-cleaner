import os
import pandas as pd
import re
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
from fpdf import FPDF

# === Setup Paths ===
input_dir = 'input'
output_dir = 'output'
visual_dir = os.path.join(output_dir, 'visuals')
log_dir = 'logs'
rep_file = 'fully_expanded_dataset.csv'

os.makedirs(output_dir, exist_ok=True)
os.makedirs(visual_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)

# === Load Replacement Dictionary ===
rep_df = pd.read_csv(rep_file).dropna()
rep_df.columns = [col.strip().lower() for col in rep_df.columns]
replacements = {
    row['shorthand'].strip().lower(): row['full_form'].strip().lower()
    for _, row in rep_df.iterrows()
}
replacement_pattern = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in replacements.keys()) + r')\b'
)

# === Cleaning Functions ===
def apply_regex(text):
    text = re.sub(r'[^\w\s,\/]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def bulk_replace(text, counter):
    def replace_match(match):
        word = match.group(0).lower()
        counter[word] += 1
        return replacements[word]
    return replacement_pattern.sub(replace_match, str(text).lower())

# === Visualization ===
def generate_wordcloud(text, title, file_path):
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(title)
    plt.tight_layout()
    plt.savefig(file_path)
    plt.close()

def generate_bar_chart(word_counts, title, file_path):
    word_counts = word_counts.sort_values(ascending=False)[:15]
    plt.figure(figsize=(10, 6))
    word_counts.plot(kind='bar', color='skyblue')
    plt.title(title)
    plt.xlabel('Words')
    plt.ylabel('Frequency')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(file_path)
    plt.close()

# === File Processing ===
def load_input_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.csv':
            return pd.read_csv(filepath, encoding='utf-8')
        elif ext == '.xlsx':
            return pd.read_excel(filepath)
        elif ext == '.txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            return pd.DataFrame({'Clinical Notes': [line.strip() for line in lines if line.strip()]})
    except UnicodeDecodeError:
        print(f"⚠️ UTF-8 decode failed for {filepath}. Retrying with ISO-8859-1...")
        if ext == '.csv':
            return pd.read_csv(filepath, encoding='ISO-8859-1')
        elif ext == '.txt':
            with open(filepath, 'r', encoding='ISO-8859-1') as f:
                lines = f.readlines()
            return pd.DataFrame({'Clinical Notes': [line.strip() for line in lines if line.strip()]})
    raise ValueError("Unsupported file type. Use .csv, .xlsx, or .txt")

# === Process Files ===
for filename in os.listdir(input_dir):
    if not filename.lower().endswith(('.csv', '.xlsx', '.txt')):
        continue

    print(f"\n🔄 Processing: {filename}")
    input_path = os.path.join(input_dir, filename)
    output_base = os.path.splitext(filename)[0]
    replacement_counts = Counter()

    try:
        df = load_input_file(input_path)
    except Exception as e:
        print(f"❌ Failed to load {filename}: {e}")
        continue

    if 'Clinical Notes' not in df.columns:
        print(f"⚠️ Skipped {filename} — 'Clinical Notes' column not found.")
        continue

    df['Original Notes'] = df['Clinical Notes'].astype(str)
    df['Cleaned Notes'] = df['Original Notes'].apply(
        lambda text: apply_regex(bulk_replace(text, replacement_counts))
    )

    # Save outputs
    df[['Original Notes', 'Cleaned Notes']].to_csv(os.path.join(output_dir, output_base + '.csv'), index=False)
    df[['Original Notes', 'Cleaned Notes']].to_excel(os.path.join(output_dir, output_base + '.xlsx'), index=False)
    df['Cleaned Notes'].to_csv(os.path.join(output_dir, output_base + '.txt'), index=False, header=False)

    # Save log
    with open(os.path.join(log_dir, f'replacement_summary_{output_base}.txt'), 'w', encoding='cp1252') as log_file:
        log_file.write(f"Replacement Summary for {filename}:\n\n")
        for word, count in replacement_counts.items():
            log_file.write(f"{word} -> {replacements[word]} : {count} replacements\n")

    # Save PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 10, txt="Clinical Notes Cleaning Report", ln=True, align='C')
    pdf.ln(10)
    for i, row in df.iterrows():
        pdf.multi_cell(0, 8, f"Original: {row['Original Notes']}", align='L')
        pdf.multi_cell(0, 8, f"Cleaned: {row['Cleaned Notes']}", align='L')
        pdf.ln(5)
        if i % 100 == 0 and i != 0:
            pdf.add_page()
    pdf.output(os.path.join(output_dir, output_base + '.pdf'))

    # Generate Visualizations
    original_words = pd.Series(re.findall(r'\b\w+\b', ' '.join(df['Original Notes']).lower()))
    cleaned_words = pd.Series(re.findall(r'\b\w+\b', ' '.join(df['Cleaned Notes']).lower()))
    generate_wordcloud(' '.join(df['Original Notes']), f"Original Text - {filename}", os.path.join(visual_dir, output_base + '_original_wc.png'))
    generate_wordcloud(' '.join(df['Cleaned Notes']), f"Cleaned Text - {filename}", os.path.join(visual_dir, output_base + '_cleaned_wc.png'))
    generate_bar_chart(original_words.value_counts(), f"Top Words (Original) - {filename}", os.path.join(visual_dir, output_base + '_original_bar.png'))
    generate_bar_chart(cleaned_words.value_counts(), f"Top Words (Cleaned) - {filename}", os.path.join(visual_dir, output_base + '_cleaned_bar.png'))

    print(f"✅ Completed processing: {filename}")

print("\n🎉 All files processed successfully.")



