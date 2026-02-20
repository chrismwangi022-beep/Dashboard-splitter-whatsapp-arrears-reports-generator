import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime
import time

# --- CONFIGURATION ---
WORKING_DIR = r'C:\Users\ADMIN\Desktop\Christopher\Dashboard\Splitter'
HEADER_NAME = "header.jpeg"
OUTPUT_DIR = os.path.join(WORKING_DIR, "Final_WhatsApp_Reports")

# Blue Sub-total Bar Detection (Standard range)
BAR_BLUE_LOWER = np.array([85, 40, 40]) 
BAR_BLUE_UPPER = np.array([135, 255, 255])

def draw_date_left_edge(image, date_str, bar_y_bottom, has_blue_bar=True):
    """Adds the date to the blue bar in BLACK text."""
    if not has_blue_bar: return image
    draw = ImageDraw.Draw(image)
    try:
        # Using bold arial if available, otherwise default
        font = ImageFont.truetype("arialbd.ttf", 18)
    except:
        font = ImageFont.load_default()
    
    # Black text for maximum clarity on the blue bar
    draw.text((8, bar_y_bottom - 22), date_str, fill="black", font=font)
    return image

def process_everything():
    print("--- 🏁 STARTING FINAL SEQUENTIAL SPLITTER (NO OCR) ---")
    today_date = datetime.now().strftime("%d-%m-%Y")
    
    # This counter will name branches 1, 2, 3... across all images
    global_branch_count = 1
    
    if not os.path.exists(WORKING_DIR):
        print(f"❌ Path Error: {WORKING_DIR} not found.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    header_path = os.path.join(WORKING_DIR, HEADER_NAME)
    if not os.path.exists(header_path):
        print(f"❌ Header Missing: Ensure {HEADER_NAME} is in the folder.")
        return
    header = Image.open(header_path).convert("RGB")

    valid_ext = ('.png', '.jpg', '.jpeg')
    # Get all screenshots except the header file
    screenshots = sorted([f for f in os.listdir(WORKING_DIR) if f.lower().endswith(valid_ext) and f.lower() != HEADER_NAME.lower()])
    
    for screenshot_name in screenshots:
        try:
            print(f"📸 Processing: {screenshot_name}")
            img_path = os.path.join(WORKING_DIR, screenshot_name)
            img_cv = cv2.imread(img_path)
            height, width, _ = img_cv.shape
            
            hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, BAR_BLUE_LOWER, BAR_BLUE_UPPER)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Identify blue bars for cutting, ignoring the top 5% (header guard)
            y_points = []
            for c in contours:
                x, y, w_cont, h_cont = cv2.boundingRect(c)
                if w_cont > (width * 0.4) and y > (height * 0.05):
                    y_points.append(y + h_cont)
            
            y_points = sorted(list(set(y_points)))
            full_cuts = [0] + y_points
            
            # Ensure the last section of the image is included
            if not y_points or full_cuts[-1] < height - 10:
                full_cuts.append(height)

            pil_img = Image.open(img_path).convert("RGB")

            for i in range(len(full_cuts) - 1):
                top, bottom = full_cuts[i], full_cuts[i+1]
                # Skip tiny noise segments
                if (bottom - top) < 100: continue 

                branch_crop = pil_img.crop((0, top, width, bottom))
                
                # Apply date only if it ends on a blue "Sub Total" bar
                is_subtotal = any(abs(bottom - yp) < 10 for yp in y_points)
                branch_crop = draw_date_left_edge(branch_crop, today_date, (bottom - top), has_blue_bar=is_subtotal)

                # Resize header to match the width of the crop
                h_ratio = width / float(header.width)
                resized_h = header.resize((width, int(header.height * h_ratio)), Image.Resampling.LANCZOS)
                
                # Stitch header and branch content together
                final_report = Image.new('RGB', (width, resized_h.height + branch_crop.height))
                final_report.paste(resized_h, (0, 0))
                final_report.paste(branch_crop, (0, resized_h.height))

                # Save with sequential name: Branch 1, Branch 2, etc.
                save_fn = f"Branch {global_branch_count}.jpeg"
                final_report.save(os.path.join(OUTPUT_DIR, save_fn), quality=95)
                
                print(f"   💾 Saved: {save_fn}")
                global_branch_count += 1
            
        except Exception as e:
            print(f"   ❌ Error on {screenshot_name}: {e}")

    print(f"\n🏁 BATCH COMPLETE. Processed {global_branch_count - 1} total reports.")
    time.sleep(2)

if __name__ == "__main__":
    process_everything()