from pathlib import Path


def pdf_to_docx(input_path: Path, output_path: Path) -> None:
    from pdf2docx import Converter
    cv = Converter(str(input_path))
    cv.convert(str(output_path))
    cv.close()


def docx_to_pdf(input_path: Path, output_path: Path) -> None:
    import mammoth
    from xhtml2pdf import pisa

    with open(input_path, "rb") as f:
        result = mammoth.convert_to_html(f)

    html = f"""
    <html><head><meta charset="utf-8">
    <style>
      body {{ font-family: Arial, sans-serif; font-size: 12pt; margin: 40px; line-height: 1.5; }}
      h1, h2, h3 {{ margin-top: 16px; }} p {{ margin: 6px 0; }}
      table {{ border-collapse: collapse; width: 100%; }}
      td, th {{ border: 1px solid #ccc; padding: 6px; }}
    </style></head>
    <body>{result.value}</body></html>
    """

    with open(output_path, "wb") as f:
        pisa.CreatePDF(html, dest=f)
