"""
RGB Color Analyzer  –  Fluorescence Image Tool
===============================================
Run:   streamlit run app.py
"""

import io
import csv
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RGB Fluorescence Analyzer",
    page_icon="🔬",
    layout="wide",
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def analyze(img: Image.Image, region: str) -> dict:
    rgb = img.convert("RGB")
    arr = np.array(rgb, dtype=np.float32)
    h, w = arr.shape[:2]

    if region == "Center 50%":
        crop = arr[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]
        box = (w // 4, h // 4, 3 * w // 4, 3 * h // 4)
    else:
        crop = arr
        box = (0, 0, w, h)

    r, g, b = crop[:,:,0], crop[:,:,1], crop[:,:,2]

    r_m, g_m, b_m = float(np.mean(r)), float(np.mean(g)), float(np.mean(b))
    brightness = 0.299*r_m + 0.587*g_m + 0.114*b_m
    dominant   = ["R","G","B"][np.argmax([r_m, g_m, b_m])]
    hex_code   = "#{:02X}{:02X}{:02X}".format(int(r_m), int(g_m), int(b_m))

    return dict(
        R_mean    = round(r_m, 2),
        G_mean    = round(g_m, 2),
        B_mean    = round(b_m, 2),
        R_norm    = round(r_m/255, 4),
        G_norm    = round(g_m/255, 4),
        B_norm    = round(b_m/255, 4),
        R_median  = round(float(np.median(r)), 2),
        G_median  = round(float(np.median(g)), 2),
        B_median  = round(float(np.median(b)), 2),
        R_std     = round(float(np.std(r)), 2),
        G_std     = round(float(np.std(g)), 2),
        B_std     = round(float(np.std(b)), 2),
        Brightness= round(brightness, 2),
        Dominant  = dominant,
        HEX       = hex_code,
        Pixels    = crop.shape[0] * crop.shape[1],
        _box      = box,
    )


def draw_box(img: Image.Image, box: tuple) -> Image.Image:
    out = img.convert("RGB").copy()
    draw = ImageDraw.Draw(out)
    draw.rectangle(box, outline=(255, 0, 0), width=max(3, img.width // 200))
    return out


def color_swatch(hex_code: str, size: int = 60) -> Image.Image:
    r = int(hex_code[1:3], 16)
    g = int(hex_code[3:5], 16)
    b = int(hex_code[5:7], 16)
    img = Image.new("RGB", (size, size), (r, g, b))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, size-1, size-1], outline=(80, 80, 80), width=2)
    return img


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔬 RGB Analyzer")
    st.markdown("**Fluorescence Image Tool**")
    st.divider()

    region = st.radio(
        "Analysis region",
        ["Center 50%", "Full image"],
        help="Center 50% focuses on the cuvette area and ignores dark chamber edges.",
    )

    show_box = st.checkbox("Show analysis region on image", value=True)
    show_channels = st.checkbox("Show R / G / B channel breakdown", value=True)

    st.divider()
    st.caption("Upload images on the right →")


# ── Main area ─────────────────────────────────────────────────────────────────
st.title("RGB Color Analyzer  –  Fluorescence Images")
st.markdown(
    "Upload one or many fluorescence images. "
    "Get mean R/G/B, normalised values, dominant channel, and a CSV export."
)

uploaded = st.file_uploader(
    "Drop images here (JPG / PNG / BMP / TIFF)",
    type=["jpg","jpeg","png","bmp","tiff","tif"],
    accept_multiple_files=True,
)

if not uploaded:
    st.info("⬆️  Upload images using the box above to get started.")
    st.stop()

# ── Process ───────────────────────────────────────────────────────────────────
rows = []
for f in uploaded:
    img = Image.open(f)
    res = analyze(img, region)
    box = res.pop("_box")
    res["Filename"] = f.name
    res["Width"]    = img.width
    res["Height"]   = img.height
    rows.append((f.name, img, box, res))

df = pd.DataFrame([r for *_, r in rows])
# reorder columns
front = ["Filename","R_mean","G_mean","B_mean","HEX","Dominant","Brightness",
         "R_norm","G_norm","B_norm"]
rest  = [c for c in df.columns if c not in front]
df = df[front + rest]

# ── Summary table ─────────────────────────────────────────────────────────────
st.subheader(f"Results  –  {len(rows)} image(s)   [region: {region}]")

def style_dominant(val):
    colors = {"R": "#ffcccc", "G": "#ccffcc", "B": "#cce0ff"}
    return f"background-color: {colors.get(val,'')}"

styled = (
    df[["Filename","R_mean","G_mean","B_mean","HEX","Dominant","Brightness",
        "R_norm","G_norm","B_norm"]]
    .style
    .map(style_dominant, subset=["Dominant"])
    .format({
        "R_mean":"{:.1f}", "G_mean":"{:.1f}", "B_mean":"{:.1f}",
        "Brightness":"{:.1f}",
        "R_norm":"{:.4f}", "G_norm":"{:.4f}", "B_norm":"{:.4f}",
    })
)
st.dataframe(styled, use_container_width=True, height=min(400, 50+40*len(rows)))

# ── CSV download ───────────────────────────────────────────────────────────────
st.download_button(
    label="⬇️  Download full CSV",
    data=df_to_csv_bytes(df),
    file_name="rgb_results.csv",
    mime="text/csv",
)

st.divider()

# ── Per-image detail ───────────────────────────────────────────────────────────
st.subheader("Per-image detail")

for fname, img, box, res in rows:
    with st.expander(f"📷  {fname}  —  HEX {res['HEX']}  |  Dominant: {res['Dominant']}"):
        c1, c2, c3 = st.columns([2, 1.6, 1.4])

        with c1:
            display_img = draw_box(img, box) if show_box else img.convert("RGB")
            # cap display size
            max_w = 480
            if display_img.width > max_w:
                ratio = max_w / display_img.width
                display_img = display_img.resize(
                    (max_w, int(display_img.height * ratio)), Image.LANCZOS
                )
            st.image(display_img, caption=f"{img.width}×{img.height} px", use_container_width=True)

        with c2:
            st.markdown("**Mean values (0–255)**")
            st.metric("R", res["R_mean"])
            st.metric("G", res["G_mean"])
            st.metric("B", res["B_mean"])
            st.markdown("**Median values**")
            st.metric("R med", res["R_median"])
            st.metric("G med", res["G_median"])
            st.metric("B med", res["B_median"])

        with c3:
            st.markdown("**Colour swatch**")
            swatch = color_swatch(res["HEX"], size=80)
            st.image(swatch, width=80)
            st.code(res["HEX"], language=None)

            st.markdown("**Normalised (0–1)**")
            st.write(f"R: `{res['R_norm']}`")
            st.write(f"G: `{res['G_norm']}`")
            st.write(f"B: `{res['B_norm']}`")

            st.markdown("**Std dev**")
            st.write(f"R: `{res['R_std']}`  G: `{res['G_std']}`  B: `{res['B_std']}`")
            st.write(f"**Brightness:** `{res['Brightness']}`")
            st.write(f"**Dominant:** `{res['Dominant']}`")

        if show_channels:
            st.markdown("**Channel breakdown**")
            bar_df = pd.DataFrame({
                "Channel": ["R", "G", "B"],
                "Mean (0–255)": [res["R_mean"], res["G_mean"], res["B_mean"]],
            })
            bar_df = bar_df.set_index("Channel")
            st.bar_chart(bar_df, color=["#e74c3c"], height=200)
