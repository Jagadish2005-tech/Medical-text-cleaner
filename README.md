# 🏥 Medical Text Cleaner

A simple and efficient **Flask web application** to clean and standardize clinical notes by converting medical shorthand into their full forms.

🔗 **Live App:** [https://medical-text-cleaner.onrender.com](https://medical-text-cleaner.onrender.com)

---

## ✨ Features

- Upload clinical notes in **CSV, Excel, or TXT**
- Automatically replace medical shorthand with full terms
- Generate **replacement logs** (CSV)
- View and download **replacement frequency charts**
- Download cleaned data as **CSV, TXT, Excel, or PDF**

---

## 🛠 Tech Stack

- **Backend:** Flask (Python)
- **Libraries:** pandas, numpy, matplotlib, openpyxl, fpdf
- **Deployment:** Render + Gunicorn

---

## ⚡ Quick Start

Clone the repository:

```bash
git clone https://github.com/<your-username>/Medical-text-cleaner.git
cd Medical-text-cleaner
