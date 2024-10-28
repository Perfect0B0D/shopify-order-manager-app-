import os
import requests
from PIL import Image
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.colors import red, black, white

# Conversion: 1 inch = 72 points
# Custom page size in points: 19.5 inches by 13.5 inches
PAGE_WIDTH = 19 * 72  # 19.5 inches converted to points
PAGE_HEIGHT = 13 * 72  # 13.5 inches converted to points

FONT_DIR = "./asset/font/"

def download_and_register_font(font_name, font_url, font_path):
    """Download and register a font if it doesn't exist."""
    if not os.path.exists(font_path):
        os.makedirs(os.path.dirname(font_path), exist_ok=True)
        response = requests.get(font_url)
        with open(font_path, 'wb') as f:
            f.write(response.content)
    
    # Register the downloaded font
    pdfmetrics.registerFont(TTFont(font_name, font_path))

def ensure_font_available(font_name):
    """Check if a font is registered locally or download and register it."""
    try:
        pdfmetrics.getFont(font_name)
    except KeyError:
        font_path = os.path.join(FONT_DIR, f"{font_name}/{font_name}.ttf")
        font_url = f"https://github.com/google/fonts/raw/main/ufl/{font_name}/{font_name}-Regular.ttf"  # Change URL if needed
        
        if not os.path.exists(font_path):
            download_and_register_font(font_name, font_url, font_path)
        else:
            pdfmetrics.registerFont(TTFont(font_name, font_path))

def draw_exact_registration_marks(c, padding=35, line_length=24, circle_radius=7):
    """Draw registration marks with filled black circles and red lines in the four corners."""
    mark_positions = [
        (padding, PAGE_HEIGHT - padding),  # Top-left corner
        (PAGE_WIDTH - padding, PAGE_HEIGHT - padding),  # Top-right corner
        (padding, padding),  # Bottom-left corner
        (PAGE_WIDTH - padding, padding),  # Bottom-right corner
    ]

    for x, y in mark_positions:
        c.setStrokeColor(black)
        c.setFillColor(black)
        c.circle(x, y, circle_radius, fill=1)
        c.setStrokeColor(red)
        if y > padding and x == padding:
            c.line(x - padding, y-line_length, x + line_length, y-line_length)
            c.line(x+line_length, y + padding, x+line_length, y - line_length)
        if y > padding and x > padding:
            c.line(x + padding, y-line_length, x - line_length, y-line_length)
            c.line(x-line_length, y + padding, x-line_length, y - line_length)
        if y == padding and x == padding:
            c.line(x - padding, y+line_length, x + line_length, y+line_length)
            c.line(x+line_length, y + line_length, x+line_length, y - padding)
        if y == padding and x > padding:
            c.line(x -  line_length, y+line_length, x + padding, y+line_length)
            c.line(x-line_length, y - padding, x-line_length, y + line_length)

def fetch_image(url):
    """Fetch image from URL and return a PIL Image object."""
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return img

def add_image_to_canvas(c, img_path, x, y, width, height, target_dpi=300):
    """Add an image to the canvas, rescaling it to a higher DPI for better quality."""
    img = Image.open(img_path)

    # Get the original DPI of the image
    img_dpi = img.info.get('dpi', (72, 72))[0]  # Default to 72 DPI if not provided

    # Scale the image based on target DPI
    dpi_scale_factor = target_dpi / img_dpi
    new_width = int(img.width * dpi_scale_factor)
    new_height = int(img.height * dpi_scale_factor)

    # Resize image based on the new DPI scale factor
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Embed the higher-resolution image into the PDF
    img_reader = ImageReader(img)
    c.drawImage(img_reader, x, y, width=width, height=height, mask='auto')    

def create_pdf(output_filename, outer_image_path, inner_image_path, user_custom_image,text_to="", text_description ="", text_from="", font="Helvetica", font_size=23):
    ensure_font_available(font)
    c = canvas.Canvas(output_filename, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    
    # --------- First Page (Outer Image) ---------
    if outer_image_path:
        add_image_to_canvas(c, outer_image_path, x=0, y=0, width=PAGE_WIDTH, height=PAGE_HEIGHT)

    draw_exact_registration_marks(c)  # Draw registration marks
    
    c.showPage()  # New page

    # --------- Second Page (Inner Image and Custom Images) ---------
    draw_exact_registration_marks(c)  # Draw registration marks

    if inner_image_path:
        add_image_to_canvas(c, inner_image_path, x=0, y=0, width=PAGE_WIDTH, height=PAGE_HEIGHT)

    column_x_positions = [440, 895, 440]
    row_y_positions = [597, 378, 150]   # Initial Y position (top margin)
    image_width = [189, 188, 189]
    image_height = [189, 178, 189]

    # -------- Custom Images --------
    for i in range(3):  # Up to 3 custom images
        if user_custom_image[i]:
            x = column_x_positions[i]
            y = row_y_positions[i]
            
            custom_img = fetch_image(user_custom_image[i])
            original_width, original_height = custom_img.size
            max_width = image_width[i]
            max_height = image_height[i]
            aspect_ratio = original_width / original_height
            if (original_width / max_width) > (original_height / max_height):
                new_width = max_width
                new_height = int(new_width / aspect_ratio)
            else:
                new_height = max_height
                new_width = int(new_height * aspect_ratio)
            resized_img = custom_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            final_img = Image.new("RGB", (max_width, max_height), (255, 255, 255))
            paste_x = (max_width - new_width) // 2
            paste_y = (max_height - new_height) // 2
            final_img.paste(resized_img, (paste_x, paste_y))
            c.drawImage(ImageReader(final_img), x, y, width=max_width, height=max_height)

    # -------- Text between columns --------
    text_x = column_x_positions[0]
    text_y = row_y_positions[1]
    text_max_width = 430
    styles = getSampleStyleSheet()
    style = styles["BodyText"]
    style.fontName = font
    style.fontSize = font_size
    if text_to:
        c.setFont(font, font_size)
        c.drawString(text_x, text_y + 155, text_to)

    # Render 'text_description' in the center
    if text_description:
        paragraph = Paragraph(text_description, style)
        width, height = paragraph.wrap(text_max_width, image_height[1])
        paragraph.drawOn(c, text_x, text_y + 120)

    # Render 'text_from' at the bottom
    if text_from:
        c.setFont(font, font_size)
        c.drawString(text_x, text_y + 20, text_from)

    draw_exact_registration_marks(c)
    c.save()
