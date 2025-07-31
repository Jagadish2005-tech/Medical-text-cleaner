import pandas as pd
import os
import re
from collections import Counter
from fpdf import FPDF

# === Load replacement dictionary ===
replacement_df = pd.read_csv('fully_expanded_dataset.csv').dropna()
replacements = {
    row['shorthand'].strip().lower(): row['full_form'].strip().lower()
    for _, row in replacement_df.iterrows()
}

# Compile regex pattern for efficient replacements
replacement_pattern = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in replacements.keys()) + r')\b'
)

def bulk_replace(text, counter):
    def replace_match(match):
        word = match.group(0).lower()
        counter[word] += 1
        return replacements[word]
    return replacement_pattern.sub(replace_match, str(text).lower())

def apply_regex(text):
    text = re.sub(r'[^\w\s,\/]', '', text)  # Remove unwanted symbols
    text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
    return text

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

# === Folder Setup ===
input_folder = 'input'
output_folder = 'output'
log_folder = 'logs'

os.makedirs(output_folder, exist_ok=True)
os.makedirs(log_folder, exist_ok=True)

# === Process Each File ===
for filename in os.listdir(input_folder):
    if not filename.lower().endswith(('.csv', '.xlsx', '.txt')):
        continue

    input_path = os.path.join(input_folder, filename)
    output_base = os.path.splitext(filename)[0]
    output_csv_path = os.path.join(output_folder, output_base + '.csv')
    log_path = os.path.join(log_folder, f'replacement_summary_{output_base}.txt')

    print(f"\n🔄 Processing: {filename}")
    replacement_counts = Counter()
    all_cleaned_chunks = []

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

    columns_to_save = ['Original Notes', 'Cleaned Notes']
    df[columns_to_save].to_csv(output_csv_path, index=False)
    all_cleaned_chunks.append(df[columns_to_save].copy())

    # === Save Log File ===
    with open(log_path, 'w', encoding='utf-8') as log_file:
        log_file.write(f"🔍 Replacement Summary for {filename}:\n\n")
        for word, count in replacement_counts.items():
            log_file.write(f"{word} ➜ {replacements[word]} : {count} replacements\n")

    print(f"✅ CSV saved: {output_csv_path}")
    print(f"📝 Log saved: {log_path}")

    # === Export to TXT, Excel, PDF ===
    full_cleaned_df = pd.concat(all_cleaned_chunks, ignore_index=True)

    # Save TXT
    txt_output_path = os.path.join(output_folder, output_base + '.txt')
    with open(txt_output_path, 'w', encoding='utf-8') as txt_file:
        txt_file.write(full_cleaned_df.to_string(index=False))
    print(f"📄 TXT file saved: {txt_output_path}")

    # Save Excel
    excel_output_path = os.path.join(output_folder, output_base + '.xlsx')
    full_cleaned_df.to_excel(excel_output_path, index=False)
    print(f"📘 Excel file saved: {excel_output_path}")

    # Save PDF
    pdf_output_path = os.path.join(output_folder, output_base + '.pdf')
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    pdf.cell(200, 10, txt="Clinical Notes Cleaning Report", ln=True, align='C')
    pdf.ln(10)

    for i, row in full_cleaned_df.iterrows():
        pdf.multi_cell(0, 8, f"Original: {row['Original Notes']}", align='L')
        pdf.multi_cell(0, 8, f"Cleaned: {row['Cleaned Notes']}", align='L')
        pdf.ln(5)
        if i % 100 == 0 and i != 0:
            pdf.add_page()

    try:
        pdf.output(pdf_output_path)
        print(f"📕 PDF file saved: {pdf_output_path}")
    except Exception as e:
        print(f"❌ Failed to save PDF: {e}")
