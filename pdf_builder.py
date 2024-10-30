import os
import re
import requests
from io import BytesIO  
from PIL import Image, ImageFont
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import ImageReader
from emojipy import Emoji

# Conversion: 1 inch = 72 points

PAGE_WIDTH = 19 * 72  
PAGE_HEIGHT = 13 * 72  
Right_IMG_POS = 1.5 * 72

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
    
def replace_with_emoji_pdf(text, size):
    # Convert text to image HTML for emojis
    text = Emoji.to_image(text)

    # Remove unsupported attributes: class, style, and alt
    text = re.sub(r'\s*class="[^"]*"', '', text)  # Remove class attributes
    text = re.sub(r'\s*style="[^"]*"', '', text)  # Remove style attributes
    text = re.sub(r'\s*alt="[^"]*"', '', text)    # Remove alt attributes
    
    # Replace the remaining attributes with height and width
    text = re.sub(r'<img', f'<img height="{size}" width="{size}"', text)
    
    return text

def draw_mixed_text(c, text, x, y, font, font_size, max_width):
    """Draw text and emojis with line wrapping, including handling line breaks."""
    # Split text into segments of text and emojis, including line breaks
    segments = re.split(r'([\U0001F600-\U0001F64F]|[\r\n])', text)  # Regex to match emoji range and line breaks
    current_x = x
    current_y = y
    line_height = font_size + 2  # Adjust line height for better spacing
    line = ""  # Current line being constructed

    for segment in segments:
        if segment:  # Non-empty segment
            if segment in ['\r', '\n']:  # Handle line breaks
                # Draw the current line if there's any text to draw
                if line:
                    c.setFont(font, font_size)
                    c.drawString(x + Right_IMG_POS, current_y, line)  # Draw the current line
                    current_y -= line_height  # Move down for the next line
                    line = ""  # Reset the current line
                continue  # Move to the next segment

            if re.match(r'[\U0001F600-\U0001F64F]', segment):  # If it's an emoji
                emoji_width = font_size  # Width of the emoji

                # Check if adding the emoji exceeds the max width
                if stringWidth(line + segment + " ", font, font_size) > max_width:
                    # Draw the current line and start a new one
                    c.setFont(font, font_size)
                    c.drawString(x + Right_IMG_POS, current_y, line)  # Draw the current line
                    current_y -= line_height  # Move down for the next line
                    line = ""  # Reset the current line

                # Fetch and draw the emoji image
                emoji_image_html = replace_with_emoji_pdf(segment, 64)
                img_src = re.search(r'src="([^"]+)"', emoji_image_html)
                if img_src:
                    emoji_url = img_src.group(1)
                    emoji_img = fetch_image(emoji_url)  # Fetch the emoji image
                    if emoji_img.mode != 'RGBA':
                        emoji_img = emoji_img.convert('RGBA')
                    emoji_img = emoji_img.resize((font_size, font_size), Image.Resampling.LANCZOS)
                    
                    img_reader = ImageReader(emoji_img)
                    emoji_y_position = current_y - (font_size * 0.15)  # Adjust for vertical alignment
                    c.drawImage(img_reader, current_x + Right_IMG_POS, emoji_y_position, width=font_size, height=font_size, mask='auto')
                    current_x += emoji_width  # Move x position for the next emoji

            else:
                # Check if adding the new segment exceeds the width
                test_line = line + segment + " "
                if stringWidth(test_line, font, font_size) <= max_width:
                    line = test_line  # Add to the current line
                else:
                    # Draw the current line and start a new one
                    c.setFont(font, font_size)
                    c.drawString(x + Right_IMG_POS, current_y, line)  # Draw the current line
                    current_y -= line_height  # Move down for the next line
                    line = segment + " "  # Start a new line with the current segment

                    # Check if the new segment alone is wider than max_width
                    if stringWidth(line, font, font_size) > max_width:
                        # If the segment itself exceeds max_width, draw it separately
                        while len(line) > 0:
                            current_segment = line
                            while stringWidth(current_segment, font, font_size) > max_width:
                                current_segment = current_segment[:-1]  # Trim one character
                            c.setFont(font, font_size)
                            c.drawString(x + Right_IMG_POS, current_y, current_segment)  # Draw the trimmed segment
                            current_y -= line_height  # Move down for the next line
                            line = line[len(current_segment):]  # Remove drawn segment from the line

                current_x += stringWidth(segment + " ", font, font_size)  # Update current_x for text

    # Draw the last line if there's any remaining text
    if line:
        c.setFont(font, font_size)
        c.drawString(x + Right_IMG_POS, current_y, line)


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
        c.setStrokeColor('black')
        c.setFillColor('black')
        c.circle(x, y, circle_radius, fill=1)
        c.setStrokeColor('red')
        if y > padding and x == padding:
            c.line(x - padding, y-line_length, x + line_length, y-line_length)
            c.line(x + line_length, y + padding, x + line_length, y - line_length)
        if y > padding and x > padding:
            c.line(x + padding, y-line_length, x - line_length, y-line_length)
            c.line(x-line_length, y + padding, x-line_length, y - line_length)
        if y == padding and x == padding:
            c.line(x - padding, y + line_length, x + line_length, y + line_length)
            c.line(x + line_length, y + line_length, x + line_length, y - padding)
        if y == padding and x > padding:
            c.line(x - line_length, y + line_length, x + padding, y + line_length)
            c.line(x - line_length, y - padding, x - line_length, y + line_length)

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
    c.drawImage(img_reader, x + Right_IMG_POS, y, width=width, height=height, mask='auto')

def create_pdf(output_filename, outer_image_path, inner_image_path, user_custom_image, text_to="", text_description="", text_from="", font="Helvetica", font_size=18):
    ensure_font_available(font)
    ensure_font_available("Symbola")
    c = canvas.Canvas(output_filename, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    
    # --------- First Page (Outer Image) ---------
    if outer_image_path:
        add_image_to_canvas(c, outer_image_path, x=0, y=0, width=PAGE_WIDTH, height=PAGE_HEIGHT)

    draw_exact_registration_marks(c)  # Draw registration marks
    
    c.showPage()  # New page

    # # --------- Second Page (Inner Image and Custom Images) ---------
    # draw_exact_registration_marks(c)  # Draw registration marks

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
            c.drawImage(ImageReader(final_img), x + Right_IMG_POS, y, width=max_width, height=max_height)

    # -------- Text between columns --------
    text_x = column_x_positions[0]
    text_y = row_y_positions[1]
    text_max_width = 420

    if text_to:
        draw_mixed_text(c, text_to, text_x, text_y + 168, font, font_size, text_max_width)
    if text_description:
        draw_mixed_text(c, text_description, text_x, text_y + 145, font, font_size, text_max_width)
    if text_from:
        draw_mixed_text(c, text_from, text_x, text_y + 5, font, font_size, text_max_width)

    c.showPage()
    c.save()