import os
import re
import requests
from io import BytesIO  
from PIL import Image
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import html
from html2image import Html2Image
import tempfile
import base64
from reportlab.graphics.barcode import code128
from reportlab.graphics import renderPDF
from reportlab.lib.pagesizes import letter


# Conversion: 1 inch = 72 points

PAGE_WIDTH = 19 * 72  
PAGE_HEIGHT = 13 * 72  
Right_IMG_POS = 1.5 * 72
hti = Html2Image()


FONT_DIR = "./asset/font/"

def load_font_as_base64(font_path):
    with open(font_path, "rb") as font_file:
        return base64.b64encode(font_file.read()).decode('utf-8')

def insert_message_content(c, pos_x, pos_y, text_from, message, text_to, font_size, font_family, img_size=(400, 140)):
    # Escape any special HTML characters in the text
    if message is not None:
     escaped_text = html.escape(message)
    else:
        escaped_text = ""
    if text_from is None:
        text_from =""
    if text_to is None:
        text_to =""
        
    font_path = f'./asset/font/{font_family}/{font_family}.ttf'
    base64_font = load_font_as_base64(font_path)
    # Create the HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Emoji Text</title>
        <style>
            @font-face {{
                font-family: '{font_family}';
                src: url('data:font/truetype;charset=utf-8;base64,{base64_font}') format('truetype');
            }}
            body {{
                padding: 0px;
                margin: 0px;
            }}
            #message_content {{
                width: {img_size[0] * 10}px;
                font-size: {font_size * 10}px;
                height: {img_size[1] * 10}px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                font-family: '{font_family}';
                overflw:auto;
                padding:0px;
                margin:0px;
            }}
        </style>
    </head>
    <body>
      <div id="message_content">
        <span>{text_to}</span>
        <span>{escaped_text}</span>
        <span>{text_from}</span>
      </div>
    </body>
    </html>
    """
    
    # Create a temporary HTML file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_html_file:
        temp_html_file.write(html_content.encode('utf-8'))
        temp_html_file_path = temp_html_file.name
    
    # Initialize Html2Image
    hti = Html2Image()
    hti.output_path = './temp'  # Set the output directory

    # Create a temporary image file name
    image_filename = 'message.png'  # Just the filename
    image_file = os.path.join(hti.output_path, 'message.png')

    try:
        # Capture the image
        hti.screenshot(html_file=temp_html_file_path, save_as=image_filename, size=(img_size[0] * 10, img_size[1] * 10))
        # with Image.open(image_file) as img:
        #  original_width, original_height = img.size
        #  new_size = (original_width * 10, original_height * 10)
        #  img = img.resize(new_size, Image.LANCZOS)  # Use LANCZOS filter for high-quality resizing
        #  img.save(image_file, dpi=(720, 720))
        add_image_to_canvas(c,os.path.join(hti.output_path, image_filename), pos_x, pos_y, width=img_size[0], height=img_size[1])
        
    except Exception as e:
        print(f"Error occurred while creating the image: {e}")
    
    finally:
        # Clean up the temporary HTML file
        os.remove(temp_html_file_path)

        # Clean up the generated image file
        generated_image_path = os.path.join(hti.output_path, image_filename)
        if os.path.exists(generated_image_path):
            os.remove(generated_image_path)
    
    return

def draw_string_with_max_width(c, text, x, y, max_width, font_name='Helvetica', font_size=12, rotate=False):
    c.setFont(font_name, font_size)
    
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        # Check the width of the word alone
        if stringWidth(word, font_name, font_size) > max_width:
            # If the word is too long, split it
            while len(word) > 0:
                # Try to fit the word within max_width
                for i in range(len(word), 0, -1):
                    if stringWidth(word[:i], font_name, font_size) <= max_width:
                        lines.append(word[:i])  # Add the part that fits
                        word = word[i:]  # Reduce the word
                        break
        else:
            # Check the width with the new word
            line_width = stringWidth(current_line + word, font_name, font_size)

            if line_width <= max_width:
                # If it fits, add the word to the current line
                current_line += f"{word} "
            else:
                # If it doesn't fit, start a new line
                if current_line:
                    lines.append(current_line.strip())
                current_line = f"{word} "

    # Add the last line if it exists
    if current_line:
        lines.append(current_line.strip())
    if rotate:
        c.saveState()  # Save the current state
        c.translate(x, y)
        c.rotate(90)  # Rotate the canvas by 90 degrees
        for i, line in enumerate(lines):
            # Adjust x and y for drawing the rotated text
            c.drawString(0, -(font_size * i), line)
        c.restoreState()  # Restore the canvas to its or
    else:
        # Draw each line
        for i, line in enumerate(lines):
            c.drawString(x, y - (font_size * i), line)
            

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
    img_reader = ImageReader(img)
    c.drawImage(img_reader, x, y, width=width, height=height, mask='auto')

def create_pdf(gift_claim_code, gift_pin_code, gift_card_text, gift_card_img_url,gift_product_img_url,gift_product_title,gift_card_price,order_number,gift_card_title, output_filename, outer_image_path, inner_image_path, user_custom_image=["","",""], text_to="", text_description="", text_from="", font="Allura", addon_img_url = "", addon_title = ""):
    c = canvas.Canvas(output_filename, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    
    # --------- First Page (Outer Image) ---------
    if outer_image_path:
        add_image_to_canvas(c, outer_image_path, x=Right_IMG_POS, y=0, width=PAGE_WIDTH, height=PAGE_HEIGHT)

    draw_exact_registration_marks(c)  # Draw registration marks
    
    # gift card and insert card
    
    # c.setStrokeColor('white')
    # c.line(63, 379, 63, 155)   
    # c.line(63, 379, 224, 379)   
    # c.line(224, 155, 63, 155)   
    # c.line(224, 155, 224, 379)   
    # c.line(224, 352, 350, 352)   
    # c.line(350, 155, 350, 352)   
    # c.line(350, 155, 224, 155) 
    # c.setStrokeColor('black')
    # insert_front_img = Image.open(f"./asset/insertcard/front.jpg")
    # image_reader = ImageReader(insert_front_img)
    # c.drawImage(image_reader, 224, 155, width = 126, height = 197 )
    
    c.saveState()
    c.translate(340, 155)
    c.rotate(90)
    barcode = code128.Code128(order_number, barHeight=30, barWidth=2.5)
    barcode.drawOn(c, 0, 0)
    c.restoreState()
    
    if gift_card_img_url != "":
        c.saveState()
        c.translate(227, 158)
        c.rotate(90)
        # gift_card_img = fetch_image(gift_card_img_url)
        gift_card_img = ImageReader("./temp/gift_card.png")
        c.drawImage(ImageReader(gift_card_img), 0, 0, width = 223, height=161, mask="auto")
        c.restoreState()
        
    if gift_product_title != "":
        c.saveState()
        c.translate(223, 450)
        c.rotate(90)
        # gift_card_img = fetch_image(gift_card_img_url)
        # gift_product_img = ImageReader("./temp/gift_product_img.png")
        c.setFontSize(10)
        c.drawString(5, 170, f"Gift: {gift_product_title}")
        # c.drawImage(ImageReader(gift_product_img), 0, 0, width = 150, height=150, mask="auto")
        c.restoreState()
        
    if addon_title != "":
        c.saveState()
        c.translate(223, 650)
        c.rotate(90)
        # gift_card_img = fetch_image(gift_card_img_url)
        # gift_product_img = ImageReader("./temp/addon_img.png")
        c.setFontSize(10)
        c.drawString(5, 170, f"AddOn: {addon_title}")
        # c.drawImage(ImageReader(gift_product_img), 0, 0, width = 150, height=150, mask="auto")
        c.restoreState()
    
    c.showPage()  # New page
    
   
    # # --------- Second Page (Inner Image and Custom Images) ---------
    # draw_exact_registration_marks(c)  # Draw registration marks

    if inner_image_path:
        add_image_to_canvas(c, inner_image_path, x=-Right_IMG_POS, y=0, width=PAGE_WIDTH, height=PAGE_HEIGHT)

    column_x_positions = [440, 895, 440]
    row_y_positions = [597, 378, 150]   # Initial Y position (top margin)
    image_width = [189, 188, 189]
    image_height = [189, 178, 189]
    
    # -------- Custom Images --------
    for i in range(3):  # Up to 3 custom images
        if user_custom_image[i]:
            x = column_x_positions[i]
            y = row_y_positions[i]
            img_url = f"custom_{i}.png"
            if os.path.exists(f"./temp/{img_url}"):
                # custom_img = fetch_image(user_custom_image[i])
                with Image.open(f"./temp/custom_{i}.png") as custom_img:
                    original_width, original_height = custom_img.size
                    max_width = image_width[i]
                    max_height = image_height[i]
                    aspect_ratio = max_width / max_height
                    if (original_width / original_height) > aspect_ratio:
                        new_width = original_width
                        new_height = int(original_width * aspect_ratio)
                    else:
                        new_height = original_height
                        new_width = int(original_height / aspect_ratio)
                    final_img = Image.new("RGB", (new_width, new_height), (255, 255, 255))
                    paste_x = (new_width - original_width) // 2
                    paste_y = (new_height - original_height) // 2
                    final_img.paste(custom_img, (paste_x, paste_y))
                    c.drawImage(ImageReader(final_img.convert('RGB')), x - Right_IMG_POS, y, width=max_width, height=max_height)

    
    insert_message_content(c, column_x_positions[0] - Right_IMG_POS, row_y_positions[1], text_from, text_description, text_to, 18, font, img_size=(428, 188))
    # gift card and insert card
    # c.setStrokeColor('black')
    # c.line(PAGE_WIDTH - 63, 379, PAGE_WIDTH - 63, 155)   
    # c.line(PAGE_WIDTH - 63, 379, PAGE_WIDTH - 224, 379)   
    # c.line(PAGE_WIDTH - 224, 155, PAGE_WIDTH - 63, 155)   
    # c.line(PAGE_WIDTH - 224, 155, PAGE_WIDTH - 224, 379)   
    # c.line(PAGE_WIDTH - 224, 352, PAGE_WIDTH - 350, 352)   
    # c.line(PAGE_WIDTH - 350, 155, PAGE_WIDTH - 350, 352)   
    # c.line(PAGE_WIDTH - 350, 155, PAGE_WIDTH - 224, 155)  
    # c.setStrokeColor('black')
    
    # c.drawString(PAGE_WIDTH - 345, 335, f"order number: {order_number}")
    # draw_string_with_max_width(c,  f"order number: {order_number}",PAGE_WIDTH - 336, 190, 155, rotate=True)
    insert_back_img = Image.open(f"./asset/insertcard/back.jpg")
    image_reader = ImageReader(insert_back_img)
    c.drawImage(image_reader, PAGE_WIDTH - 350, 155, width = 126, height = 197 )
    if gift_claim_code != "":
        c.line(PAGE_WIDTH-63, 158, PAGE_WIDTH-224, 158)
        gift_card_price =  "$" + f"{round(float(gift_card_price))}" 
        gift_claim_code = "Claim: " + gift_claim_code
        if gift_pin_code != "":
            gift_pin_code = "PIN: " + gift_pin_code
        draw_string_with_max_width(c, gift_card_title, PAGE_WIDTH -205, 165,font_size=15, max_width=160, rotate=True)
        draw_string_with_max_width(c, gift_card_price, PAGE_WIDTH -205, 330,font_size=14, max_width=160, font_name="Helvetica-Bold", rotate=True)
        draw_string_with_max_width(c, gift_claim_code, PAGE_WIDTH -188, 165,font_size=8, max_width=160, rotate=True)
        draw_string_with_max_width(c, gift_pin_code, PAGE_WIDTH -188, 295,font_size=8, max_width=160, rotate=True)
        draw_string_with_max_width(c, gift_card_text, PAGE_WIDTH -170, 165, max_width=210, font_size=8, rotate=True)
        
    # draw_string_with_max_width(c, gift_claim_code, PAGE_WIDTH -80, 155, max_width=160, rotate=True)
    # draw_string_with_max_width(c, gift_pin_code, PAGE_WIDTH -100, 155, max_width=160, rotate=True)
    # draw_string_with_max_width(c, gift_card_price, PAGE_WIDTH -120, 155, max_width=160, rotate=True)
    # draw_string_with_max_width(c, gift_card_text, PAGE_WIDTH -150, 155, max_width=160, rotate=True)
    # c.saveState()
    # c.translate(PAGE_WIDTH - 295, 180)
    # c.rotate(90)
    # barcode = code128.Code128(order_number, barHeight=30, barWidth=1.5)
    # barcode.drawOn(c, 0, 0)
    # c.restoreState()
    
    # draw_string_with_max_width(c,  f"Gift:",PAGE_WIDTH - 275, 230, 155, rotate=True)
    # draw_string_with_max_width(c,  f"{gift}",PAGE_WIDTH - 255, 180, 155, rotate=True)
    
    c.showPage()
    c.save()