import pandas as pd
import re
from collections import Counter

def load_replacements(rep_file='fully_expanded_dataset.csv'):
    rep_df = pd.read_csv(rep_file).dropna()
    rep_df.columns = [col.strip().lower() for col in rep_df.columns]
    replacements = {
        row['shorthand'].strip().lower(): row['full_form'].strip().lower()
        for _, row in rep_df.iterrows()
    }
    pattern = re.compile(
        r'\b(' + '|'.join(re.escape(k) for k in replacements.keys()) + r')\b'
    )
    return replacements, pattern

def apply_regex(text):
    text = re.sub(r'[^\w\s,\/]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def bulk_replace(text, replacements, pattern, counter):
    def replace_match(match):
        word = match.group(0).lower()
        counter[word] += 1
        return replacements[word]
    return pattern.sub(replace_match, str(text).lower())

def clean_notes(df, replacements, pattern):
    counter = Counter()
    df['Original Notes'] = df['Clinical Notes'].astype(str)
    df['Cleaned Notes'] = df['Original Notes'].apply(
        lambda text: apply_regex(bulk_replace(text, replacements, pattern, counter))
    )
    return df, counter