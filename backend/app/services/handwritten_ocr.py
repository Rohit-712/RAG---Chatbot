"""
Handwritten PDF OCR service.

Pipeline:

PDF
 -> page image
 -> preprocessing
 -> handwriting line detection
 -> TrOCR per line
 -> combined text
"""

from functools import lru_cache
from pathlib import Path

import pymupdf
import cv2
import numpy as np
import torch

from PIL import Image
from transformers import (
    TrOCRProcessor,
    VisionEncoderDecoderModel,
)


MODEL_NAME = "microsoft/trocr-base-handwritten"


# ============================================================
# LOAD MODEL
# ============================================================

@lru_cache(maxsize=1)
def get_ocr_model():

    print("Loading handwritten OCR model...")

    processor = TrOCRProcessor.from_pretrained(
        MODEL_NAME
    )

    model = VisionEncoderDecoderModel.from_pretrained(
        MODEL_NAME
    )

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    model.to(device)
    model.eval()

    print(
        f"Handwritten OCR loaded on {device}"
    )

    return processor, model, device


# ============================================================
# OCR ONE LINE
# ============================================================

def ocr_line(
    image: Image.Image,
) -> str:

    processor, model, device = get_ocr_model()

    # --------------------------------------------------
    # PIL -> OpenCV
    # --------------------------------------------------

    img = np.array(image)

    gray = cv2.cvtColor(
        img,
        cv2.COLOR_RGB2GRAY,
    )

    # --------------------------------------------------
    # Improve contrast
    # --------------------------------------------------

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    gray = clahe.apply(gray)

    # --------------------------------------------------
    # Remove noise
    # --------------------------------------------------

    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0,
    )

    # --------------------------------------------------
    # Adaptive threshold
    # --------------------------------------------------

    processed = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )

    # --------------------------------------------------
    # Convert back to PIL
    # --------------------------------------------------

    image = Image.fromarray(
        processed
    ).convert("RGB")

    # --------------------------------------------------
    # TrOCR
    # --------------------------------------------------

    pixel_values = processor(
        images=image,
        return_tensors="pt",
    ).pixel_values

    pixel_values = pixel_values.to(
        device
    )

    with torch.no_grad():

        generated_ids = model.generate(
            pixel_values,
            max_new_tokens=128,
            num_beams=4,
        )

    text = processor.batch_decode(
        generated_ids,
        skip_special_tokens=True,
    )[0]

    return text.strip()
# ============================================================
# PDF → PAGE IMAGES
# ============================================================

def pdf_to_images(
    file_path: str | Path,
    dpi: int = 200,
)-> list[Image.Image]:

    document = pymupdf.open(
        str(file_path)
    )

    images = []

    zoom = dpi / 72

    matrix = pymupdf.Matrix(
        zoom,
        zoom,
    )

    for page in document:

        pixmap = page.get_pixmap(
            matrix=matrix,
            alpha=False,
        )

        image = Image.frombytes(
            "RGB",
            (
                pixmap.width,
                pixmap.height,
            ),
            pixmap.samples,
        )

        images.append(image)

    document.close()

    return images


# ============================================================
# DETECT HANDWRITING LINES
# ============================================================

def detect_text_lines(
    image: Image.Image,
) -> list[Image.Image]:

    # PIL → OpenCV
    img = np.array(image)

    gray = cv2.cvtColor(
        img,
        cv2.COLOR_RGB2GRAY,
    )

    # Remove light background
    binary = cv2.threshold(
        gray,
        200,
        255,
        cv2.THRESH_BINARY_INV,
    )[1]

    # Horizontal morphology
    kernel_width = max(
        30,
        img.shape[1] // 30,
    )

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (kernel_width, 3),
    )

    horizontal = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        kernel,
    )

    # Find connected regions
    contours, _ = cv2.findContours(
        horizontal,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    boxes = []

    for contour in contours:

        x, y, w, h = cv2.boundingRect(
            contour
        )

        # Ignore tiny regions
        if w < 80:
            continue

        if h < 5:
            continue

        if h > img.shape[0] * 0.20:
            continue

        boxes.append(
            (x, y, w, h)
        )

    # Sort top → bottom
    boxes.sort(
        key=lambda box: box[1]
    )

    line_images = []

    for x, y, w, h in boxes:

        padding_x = 15
        padding_y = 15

        x1 = max(
            0,
            x - padding_x,
        )

        y1 = max(
            0,
            y - padding_y,
        )

        x2 = min(
            img.shape[1],
            x + w + padding_x,
        )

        y2 = min(
            img.shape[0],
            y + h + padding_y,
        )

        crop = img[
            y1:y2,
            x1:x2,
        ]

        if crop.size == 0:
            continue

        line_image = Image.fromarray(
            crop
        )

        line_images.append(
            line_image
        )

    return line_images


# ============================================================
# FALLBACK
# ============================================================

def fallback_full_page_ocr(
    image: Image.Image,
) -> str:

    print(
        "No handwriting lines detected. "
        "Trying full-page OCR..."
    )

    return ocr_line(image)


# ============================================================
# HANDWRITTEN PDF → TEXT
# ============================================================

def handwritten_pdf_to_text(
    file_path: str | Path,
) -> str:

    pages = pdf_to_images(
        file_path,
        dpi=150,
    )

    extracted_pages = []

    for page_number, image in enumerate(
        pages,
        start=1,
    ):

        print(
            f"OCR processing page "
            f"{page_number}/{len(pages)}..."
        )

        lines = detect_text_lines(
            image
        )

        print(
            f"Detected {len(lines)} "
            f"possible text lines."
        )

        page_text = []

        if lines:

            for line_number, line_image in enumerate(
                lines,
                start=1,
            ):

                print(
                    f"  OCR line "
                    f"{line_number}/{len(lines)}..."
                )

                text = ocr_line(
                    line_image
                )

                if text:

                    page_text.append(
                        text
                    )

        else:

            text = fallback_full_page_ocr(
                image
            )

            if text:
                page_text.append(
                    text
                )

        if page_text:

            extracted_pages.append(
                f"Page {page_number}\n"
                + "\n".join(page_text)
            )

    return "\n\n".join(
        extracted_pages
    ).strip()