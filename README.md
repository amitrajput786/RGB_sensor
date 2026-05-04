# RGB Fluorescence Analyzer

Streamlit app to extract R/G/B values from fluorescence images.

## Setup (first time only)

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Opens automatically at → http://localhost:8501

## Features
- Upload multiple images at once (JPG, PNG, BMP, TIFF)
- Mean, Median, Std Dev for R / G / B channels
- Normalised 0–1 values for calibration curves
- Colour swatch + HEX code
- Dominant channel highlight (R / G / B)
- Red box overlay showing the analysis region
- One-click CSV download of all results
- Toggle between **Center 50%** crop (default, cuvette focus) or **Full image**
