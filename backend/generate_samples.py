"""
Generate realistic-looking sample documents for the Compass demo.
Creates PNG images of a pay stub and utility bill so judges can
test Nova Lite vision + Nova Multimodal Embeddings without needing
their own documents.

Called once at server startup if the sample files don't already exist.
"""

import os
from pathlib import Path


def generate_samples(output_dir: Path) -> None:
    """Generate sample document images if they don't exist."""
    output_dir.mkdir(parents=True, exist_ok=True)

    pay_stub_path = output_dir / "sample_pay_stub.png"
    utility_bill_path = output_dir / "sample_utility_bill.png"

    if not pay_stub_path.exists():
        _generate_pay_stub(pay_stub_path)

    if not utility_bill_path.exists():
        _generate_utility_bill(utility_bill_path)


def _generate_pay_stub(path: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
        _generate_pay_stub_pil(path)
    except ImportError:
        _generate_pay_stub_fallback(path)


def _generate_utility_bill(path: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
        _generate_utility_bill_pil(path)
    except ImportError:
        _generate_utility_bill_fallback(path)


def _get_font(size: int):
    """Try to load a system font, fall back to PIL default."""
    from PIL import ImageFont
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "/Windows/Fonts/arial.ttf",  # Windows
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _generate_pay_stub_pil(path: Path) -> None:
    from PIL import Image, ImageDraw

    W, H = 700, 480
    img = Image.new("RGB", (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Header background
    draw.rectangle([0, 0, W, 80], fill=(30, 64, 175))

    font_lg = _get_font(22)
    font_md = _get_font(16)
    font_sm = _get_font(13)
    font_bold = _get_font(18)

    # Company name
    draw.text((20, 15), "METRO TRANSIT AUTHORITY", font=font_lg, fill=(255, 255, 255))
    draw.text((20, 48), "Payroll Division  |  1 Transit Plaza, Oakland CA 94607", font=font_sm, fill=(186, 213, 255))

    # PAY STUB title
    draw.rectangle([0, 80, W, 110], fill=(241, 245, 249))
    draw.text((20, 88), "EARNINGS STATEMENT", font=font_bold, fill=(30, 64, 175))
    draw.text((W - 220, 88), "PAY PERIOD: Jan 1–15, 2025", font=font_sm, fill=(100, 116, 139))

    # Employee info
    y = 125
    draw.text((20, y), "Employee:", font=font_sm, fill=(100, 116, 139))
    draw.text((120, y), "Maria Elena Reyes", font=font_md, fill=(15, 23, 42))
    draw.text((20, y + 22), "Employee ID:", font=font_sm, fill=(100, 116, 139))
    draw.text((120, y + 22), "EMP-48821", font=font_md, fill=(15, 23, 42))
    draw.text((20, y + 44), "Department:", font=font_sm, fill=(100, 116, 139))
    draw.text((120, y + 44), "Bus Operations", font=font_md, fill=(15, 23, 42))

    draw.text((380, y), "Pay Date:", font=font_sm, fill=(100, 116, 139))
    draw.text((460, y), "Jan 17, 2025", font=font_md, fill=(15, 23, 42))
    draw.text((380, y + 22), "Status:", font=font_sm, fill=(100, 116, 139))
    draw.text((460, y + 22), "Terminated", font=font_md, fill=(185, 28, 28))
    draw.text((380, y + 44), "Last Day:", font=font_sm, fill=(100, 116, 139))
    draw.text((460, y + 44), "Dec 15, 2024", font=font_md, fill=(15, 23, 42))

    # Divider
    draw.line([(20, 215), (W - 20, 215)], fill=(226, 232, 240), width=1)

    # Earnings table header
    y = 228
    draw.rectangle([20, y, W - 20, y + 28], fill=(248, 250, 252))
    draw.text((30, y + 7), "EARNINGS", font=font_sm, fill=(71, 85, 105))
    draw.text((300, y + 7), "HOURS", font=font_sm, fill=(71, 85, 105))
    draw.text((400, y + 7), "RATE", font=font_sm, fill=(71, 85, 105))
    draw.text((530, y + 7), "AMOUNT", font=font_sm, fill=(71, 85, 105))

    # Earnings rows
    rows = [
        ("Regular Pay", "80.0", "$15.63/hr", "$1,250.40"),
        ("Overtime", "0.0", "$23.44/hr", "$0.00"),
        ("Final PTO Payout", "--", "--", "$312.50"),
    ]
    y += 32
    for desc, hrs, rate, amt in rows:
        draw.text((30, y), desc, font=font_sm, fill=(15, 23, 42))
        draw.text((300, y), hrs, font=font_sm, fill=(15, 23, 42))
        draw.text((400, y), rate, font=font_sm, fill=(15, 23, 42))
        draw.text((530, y), amt, font=font_sm, fill=(15, 23, 42))
        y += 22

    draw.line([(20, y + 5), (W - 20, y + 5)], fill=(226, 232, 240), width=1)
    y += 14

    # Gross / Net totals
    draw.text((400, y), "GROSS PAY:", font=font_bold, fill=(15, 23, 42))
    draw.text((530, y), "$1,562.90", font=font_bold, fill=(15, 23, 42))
    y += 26
    draw.text((400, y), "Total Deductions:", font=font_sm, fill=(100, 116, 139))
    draw.text((530, y), "($320.47)", font=font_sm, fill=(185, 28, 28))
    y += 26

    # Net pay highlight
    draw.rectangle([390, y, W - 20, y + 34], fill=(30, 64, 175))
    draw.text((400, y + 8), "NET PAY:", font=font_bold, fill=(255, 255, 255))
    draw.text((530, y + 8), "$1,242.43", font=font_bold, fill=(255, 255, 255))

    # Footer
    draw.rectangle([0, H - 32, W, H], fill=(241, 245, 249))
    draw.text((20, H - 24), "This is your final paycheck. Questions? Call HR: (510) 555-0192", font=font_sm, fill=(100, 116, 139))

    img.save(str(path), "PNG")


def _generate_utility_bill_pil(path: Path) -> None:
    from PIL import Image, ImageDraw

    W, H = 680, 460
    img = Image.new("RGB", (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([0, 0, W, 90], fill=(22, 101, 52))
    font_lg = _get_font(24)
    font_md = _get_font(16)
    font_sm = _get_font(13)
    font_bold = _get_font(18)

    draw.text((20, 16), "Pacific Gas & Electric", font=font_lg, fill=(255, 255, 255))
    draw.text((20, 52), "Customer Account Statement", font=font_sm, fill=(187, 247, 208))
    draw.text((W - 200, 52), "pg&e.com  |  1-800-743-5000", font=font_sm, fill=(187, 247, 208))

    # Account info box
    y = 105
    draw.rectangle([20, y, 340, y + 100], fill=(240, 253, 244), outline=(187, 247, 208))
    draw.text((30, y + 10), "Account Holder:", font=font_sm, fill=(71, 85, 105))
    draw.text((150, y + 10), "Maria E. Reyes", font=font_md, fill=(15, 23, 42))
    draw.text((30, y + 33), "Account #:", font=font_sm, fill=(71, 85, 105))
    draw.text((150, y + 33), "4521-XXXX-XXXX", font=font_md, fill=(15, 23, 42))
    draw.text((30, y + 56), "Service Address:", font=font_sm, fill=(71, 85, 105))
    draw.text((150, y + 56), "412 Oak St, Apt 3B", font=font_md, fill=(15, 23, 42))
    draw.text((150, y + 76), "Oakland, CA 94601", font=font_sm, fill=(15, 23, 42))

    # Amount due box
    draw.rectangle([370, y, W - 20, y + 100], fill=(254, 242, 242), outline=(254, 202, 202))
    draw.text((385, y + 10), "Bill Date:", font=font_sm, fill=(71, 85, 105))
    draw.text((490, y + 10), "Jan 15, 2025", font=font_md, fill=(15, 23, 42))
    draw.text((385, y + 33), "Due Date:", font=font_sm, fill=(71, 85, 105))
    draw.text((490, y + 33), "Feb 5, 2025", font=font_md, fill=(185, 28, 28))
    draw.text((385, y + 56), "AMOUNT DUE:", font=font_bold, fill=(185, 28, 28))
    draw.text((490, y + 56), "$187.43", font=font_bold, fill=(185, 28, 28))

    # Usage chart section
    y = 220
    draw.line([(20, y), (W - 20, y)], fill=(226, 232, 240), width=1)
    y += 14
    draw.text((20, y), "SERVICE PERIOD: Dec 15, 2024 – Jan 15, 2025", font=font_bold, fill=(22, 101, 52))
    y += 28

    charges = [
        ("Electricity Supply Charge", "487 kWh × $0.24/kWh", "$116.88"),
        ("Distribution Charge", "487 kWh × $0.08/kWh", "$38.96"),
        ("Baseline Credit", "", "($12.40)"),
        ("Gas Charge", "18 therms × $2.22/therm", "$39.96"),
        ("Taxes & Fees", "", "$4.03"),
    ]
    for label, detail, amount in charges:
        draw.text((30, y), label, font=font_sm, fill=(15, 23, 42))
        draw.text((310, y), detail, font=font_sm, fill=(100, 116, 139))
        draw.text((560, y), amount, font=font_sm, fill=(15, 23, 42))
        y += 22

    draw.line([(20, y + 4), (W - 20, y + 4)], fill=(226, 232, 240), width=1)
    y += 18
    draw.text((30, y), "Total Current Charges:", font=font_bold, fill=(15, 23, 42))
    draw.text((560, y), "$187.43", font=font_bold, fill=(15, 23, 42))

    # CARE program notice
    y += 40
    draw.rectangle([20, y, W - 20, y + 60], fill=(254, 249, 195), outline=(253, 224, 71))
    draw.text((30, y + 8), "CARE Program Available:", font=font_bold, fill=(133, 77, 14))
    draw.text((30, y + 30), "You may qualify for 20% discount through California's CARE energy assistance program.", font=font_sm, fill=(92, 60, 14))

    # Footer
    draw.rectangle([0, H - 30, W, H], fill=(240, 253, 244))
    draw.text((20, H - 22), "To set up payment arrangements or apply for CARE/FERA, call 1-800-743-5000", font=font_sm, fill=(22, 101, 52))

    img.save(str(path), "PNG")


def _generate_pay_stub_fallback(path: Path) -> None:
    """Create a minimal SVG-as-PNG if Pillow is unavailable."""
    # Write a simple 1x1 white pixel PNG as absolute fallback
    import struct, zlib
    def _png(w, h, data):
        def chunk(name, data):
            c = zlib.crc32(name + data) & 0xffffffff
            return struct.pack('>I', len(data)) + name + data + struct.pack('>I', c)
        raw = b''.join(b'\x00' + bytes([255] * w * 3) for _ in range(h))
        compressed = zlib.compress(raw)
        return (b'\x89PNG\r\n\x1a\n'
                + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                + chunk(b'IDAT', compressed)
                + chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(_png(700, 480, None))


def _generate_utility_bill_fallback(path: Path) -> None:
    _generate_pay_stub_fallback(path)  # same minimal PNG


if __name__ == "__main__":
    out = Path("frontend/static/samples")
    generate_samples(out)
    print(f"Samples generated in {out}")
