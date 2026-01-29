import os
import io
from flask import Flask, request, send_file, render_template
from flask_cors import CORS
from PIL import Image
from rembg import remove
import numpy as np

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Ensure folders exist
os.makedirs('static/css', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('uploads', exist_ok=True)

FRAME_PATH = 'images/frame.png'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/images/<path:filename>')
def serve_images(filename):
    # This matches the /images/frame.png path in the HTML
    return send_file(os.path.join('images', filename))

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return "No image uploaded", 400
    
    file = request.files['image']
    input_image = Image.open(file.stream)
    
    # 1. Remove background
    # Convert to bytes for rembg
    img_byte_arr = io.BytesIO()
    input_image.save(img_byte_arr, format='PNG')
    img_data = img_byte_arr.getvalue()
    
    # Process with rembg
    output_data = remove(img_data)
    foreground = Image.open(io.BytesIO(output_data)).convert("RGBA")
    
    # 2. Open frame
    frame = Image.open(FRAME_PATH).convert("RGBA")
    frame_w, frame_h = frame.size
    
    # 3. Process foreground placement
    # We want it to be "at the bottom center"
    # Let's scale the foreground so it doesn't exceed 80% of the frame width or 70% of frame height
    fg_w, fg_h = foreground.size
    
    max_fg_w = int(frame_w * 0.6)  # 60% of frame width
    max_fg_h = int(frame_h * 0.5)  # 50% of frame height
    
    ratio = min(max_fg_w / fg_w, max_fg_h / fg_h)
    new_fg_w = int(fg_w * ratio)
    new_fg_h = int(fg_h * ratio)
    
    foreground = foreground.resize((new_fg_w, new_fg_h), Image.Resampling.LANCZOS)
    
    # Calculate position (Bottom Center)
    x = (frame_w - new_fg_w) // 2
    y = frame_h - new_fg_h # Flush to bottom
    
    # 4. Composite
    # Create a copy of the frame to draw on
    combined = frame.copy()
    combined.alpha_composite(foreground, (x, y))
    
    # Return result
    result_bytes = io.BytesIO()
    combined.save(result_bytes, format='PNG')
    result_bytes.seek(0)
    
    return send_file(result_bytes, mimetype='image/png')

if __name__ == '__main__':
    # Using 0.0.0.0 to be accessible if needed, default port 5000
    app.run(debug=True, port=5000)
