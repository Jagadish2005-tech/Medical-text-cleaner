from flask import Flask, render_template, request, send_file, redirect, url_for, session
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # ✅ Fix for Tkinter runtime error
import matplotlib.pyplot as plt
import tempfile, os
from datetime import datetime
from fpdf import FPDF
from cleanser import load_replacements, clean_notes

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for Flask session

# Load your shorthand dictionary
replacements, pattern = load_replacements('fully_expanded_dataset.csv')

# ------------------- Reading Functions -------------------

def read_csv_with_fallback(uploaded_file):
    try:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file)
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, encoding='ISO-8859-1')

def read_txt_with_fallback(uploaded_file):
    try:
        uploaded_file.seek(0)
        lines = uploaded_file.read().decode('utf-8').splitlines()
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        lines = uploaded_file.read().decode('ISO-8859-1').splitlines()
    return pd.DataFrame({'Clinical Notes': lines})

# ------------------- Save Functions -------------------

def save_log(counter):
    log_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w', encoding='utf-8')
    log_file.write("Shorthand,Full Form,Count\n")
    for k, v in counter.items():
        log_file.write(f"{k},{replacements.get(k, '?')},{v}\n")
    log_file.close()
    return log_file.name

def save_chart(counter):
    items = sorted(counter.items(), key=lambda x: x[1], reverse=True)
    keys, values = zip(*items)
    chart_path = os.path.join('static', 'replacement_chart.png')
    plt.figure(figsize=(8, 4))
    plt.bar(keys, values, color='skyblue')
    plt.title("Replacement Frequency")
    plt.xlabel("Shorthand")
    plt.ylabel("Count")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()
    return chart_path

def save_output(df, filetype):
    if filetype == 'txt':
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8')
        df['Cleaned Notes'].to_csv(tmp.name, index=False, header=False)
    elif filetype == 'excel':
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        df.to_excel(tmp.name, index=False)
    elif filetype == 'pdf':
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=11)
        pdf.cell(200, 10, txt="Clinical Notes Cleaning Report", ln=True, align='C')
        pdf.ln(10)
        for _, row in df.iterrows():
            pdf.multi_cell(0, 8, f"Original: {row['Original Notes']}", align='L')
            pdf.multi_cell(0, 8, f"Cleaned: {row['Cleaned Notes']}", align='L')
            pdf.ln(5)
        pdf.output(tmp.name)
    else:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        df.to_csv(tmp.name, index=False)
    tmp.close()
    return tmp.name

# ------------------- Main Routes -------------------

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded = request.files.get('file')
        filetype = request.form.get('format', 'csv')

        if not uploaded:
            return render_template('index.html', error="Please select a file to upload.", year=datetime.now().year)

        ext = uploaded.filename.split('.')[-1].lower()
        try:
            if ext == 'csv':
                df = read_csv_with_fallback(uploaded)
            elif ext == 'xlsx':
                uploaded.seek(0)
                df = pd.read_excel(uploaded)
            elif ext == 'txt':
                df = read_txt_with_fallback(uploaded)
            else:
                return render_template('index.html', error="Unsupported file type.", year=datetime.now().year)

            if 'Clinical Notes' not in df.columns:
                return render_template('index.html', error="No 'Clinical Notes' column found.", year=datetime.now().year)

            # Clean
            df_cleaned, counter = clean_notes(df, replacements, pattern)

            # Save files
            output_path = save_output(df_cleaned, filetype)
            log_path = save_log(counter)
            chart_path = save_chart(counter)

            # Store in session
            session['output_file'] = output_path
            session['log_file'] = log_path
            session['chart_url'] = chart_path
            session['counter'] = dict(counter)
            session['filetype'] = filetype

            return redirect(url_for('result'))

        except Exception as e:
            return render_template('index.html', error=f"Failed to process file: {e}", year=datetime.now().year)

    return render_template('index.html', year=datetime.now().year)

@app.route('/result')
def result():
    return render_template(
        'result.html',
        download_url=url_for(
            'download_file',
            filename=os.path.basename(session.get('output_file', '')),
            filetype=session.get('filetype', 'csv')
        ),
        log_url=url_for(
            'download_file',
            filename=os.path.basename(session.get('log_file', '')),
            filetype='log'
        ),
        chart_url='/' + session.get('chart_url', ''),
        counter=session.get('counter', {}),
        filetype=session.get('filetype', 'csv'),
        replacements=replacements
    )

@app.route('/download/<filename>')
def download_file(filename):
    filetype = request.args.get('filetype', 'csv')
    ext_map = {
        'csv': 'cleaned_data.csv',
        'excel': 'cleaned_data.xlsx',
        'txt': 'cleaned_data.txt',
        'pdf': 'cleaned_data.pdf',
        'log': 'replacement_log.csv'
    }
    download_name = ext_map.get(filetype, filename)
    path = os.path.join(tempfile.gettempdir(), filename)
    return send_file(path, as_attachment=True, download_name=download_name)

if __name__ == '__main__':
    app.run(debug=True)
