"""
Generates sample 'messy' images for the Extraction Agent to practice on:
 - ledger_XX_<Persona>.jpg  -> a notebook-style ledger page with several transactions
 - upi_XX_<Persona>.jpg     -> a UPI payment confirmation screenshot style image

Reads directly from synthetic_transaction_ground_truth.json so the images
match your real ground-truth data exactly.
"""

import json
import os
import random
from PIL import Image, ImageDraw, ImageFont

random.seed(42)  # reproducible output

OUTPUT_DIR = "sample_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open("synthetic_transaction_ground_truth.json") as f:
    data = json.load(f)

transactions = data["transactions"]

personas = ["Asha", "Meena", "Radha", "Sunita"]

# Group transactions by persona
by_persona = {p: [t for t in transactions if t["persona"] == p] for p in personas}


def get_font(size, bold=False):
    """Try a few common Windows fonts, fall back to default if unavailable."""
    candidates = (
        ["arialbd.ttf", "calibrib.ttf"] if bold else ["arial.ttf", "calibri.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


# ---------- LEDGER PAGE STYLE ----------
def make_ledger_image(persona, txns, filename):
    W, H = 900, 1100
    img = Image.new("RGB", (W, H), color=(250, 247, 235))  # notebook cream
    draw = ImageDraw.Draw(img)

    # ruled lines
    for y in range(120, H - 40, 45):
        draw.line([(40, y), (W - 40, y)], fill=(200, 195, 170), width=1)
    # margin line
    draw.line([(90, 20), (90, H - 20)], fill=(220, 130, 130), width=2)

    title_font = get_font(34, bold=True)
    header_font = get_font(22, bold=True)
    text_font = get_font(24)

    draw.text((110, 30), f"Income & Expense Register - {persona}", font=title_font, fill=(30, 30, 30))
    draw.text((110, 75), f"{persona}'s {txns[0]['occupation']}", font=header_font, fill=(80, 80, 80))

    y = 140
    for t in txns:
        sign = "+" if t["transaction_type"] == "income" else "-"
        line = f"{t['date']}   {t['description'][:28]:<28}  {sign}Rs.{int(t['amount_inr'])}  ({t['payment_method']})"
        x_jitter = random.randint(-3, 6)
        draw.text((105 + x_jitter, y), line, font=text_font, fill=(20, 20, 60))
        y += 45
        if y > H - 60:
            break

    img.save(os.path.join(OUTPUT_DIR, filename), quality=90)


# ---------- UPI SCREENSHOT STYLE ----------
def make_upi_image(persona, txn, filename):
    W, H = 720, 1000
    img = Image.new("RGB", (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw.rectangle([(0, 0), (W, 90)], fill=(76, 47, 143))
    top_font = get_font(30, bold=True)
    draw.text((30, 25), "Payment Successful", font=top_font, fill=(255, 255, 255))

    draw.ellipse([(W // 2 - 60, 130), (W // 2 + 60, 250)], outline=(50, 160, 90), width=6)
    check_font = get_font(60, bold=True)
    draw.text((W // 2 - 22, 150), "OK", font=check_font, fill=(50, 160, 90))

    amt_font = get_font(48, bold=True)
    label_font = get_font(24)
    value_font = get_font(26, bold=True)

    is_income = txn["transaction_type"] == "income"
    amount_color = (30, 130, 60) if is_income else (180, 40, 40)
    prefix = "+" if is_income else "-"

    draw.text((W // 2 - 100, 280), f"{prefix} Rs.{int(txn['amount_inr'])}", font=amt_font, fill=amount_color)

    rows = [
        ("To / From", persona),
        ("For", txn["description"]),
        ("Date", txn["date"]),
        ("Mode", txn["payment_method"]),
        ("Txn ID", txn["transaction_id"]),
        ("Category", txn["category"]),
    ]

    y = 400
    for label, value in rows:
        draw.text((60, y), label, font=label_font, fill=(120, 120, 120))
        draw.text((60, y + 32), str(value), font=value_font, fill=(20, 20, 20))
        draw.line([(60, y + 70), (W - 60, y + 70)], fill=(230, 230, 230), width=1)
        y += 95

    img.save(os.path.join(OUTPUT_DIR, filename), quality=90)


# ---------- GENERATE ALL 32 IMAGES, MATCHING THE MANIFEST NAMING ----------
ledger_counter = 1
upi_counter = 1

for persona in personas:
    txns = by_persona[persona]
    random.shuffle(txns)

    for i in range(4):
        batch = txns[i * 5:(i + 1) * 5]
        if not batch:
            batch = txns[:5]
        fname = f"ledger_{ledger_counter:02d}_{persona}.jpg"
        make_ledger_image(persona, batch, fname)
        print("Created", fname)
        ledger_counter += 1

    upi_txns = random.sample(txns, 4)
    for t in upi_txns:
        fname = f"upi_{upi_counter:02d}_{persona}.jpg"
        make_upi_image(persona, t, fname)
        print("Created", fname)
        upi_counter += 1

print(f"\nDone. {ledger_counter - 1} ledger images + {upi_counter - 1} UPI images saved to '{OUTPUT_DIR}/'")