from PIL import Image, ImageDraw
import os

def process_image(input_path, output_path, frame_width=20, frame_color=(255, 255, 255)):
    """
    Process an image: convert JPG to PNG, crop to square using height, center, and add frame
    
    Args:
        input_path (str): Path to input JPG image
        output_path (str): Path to output PNG image
        frame_width (int): Width of the frame in pixels
        frame_color (tuple): RGB color of the frame
    """
    try:
        # Open the image
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (in case of RGBA or other modes)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get dimensions
            width, height = img.size
            print(f"Original image size: {width}x{height}")
            
            # Calculate square crop size (use height as the dimension)
            crop_size = height
            
            # Calculate crop coordinates to center the image
            left = (width - crop_size) // 2
            top = 0
            right = left + crop_size
            bottom = height
            
            # Crop to square
            cropped_img = img.crop((left, top, right, bottom))
            print(f"Cropped to square: {crop_size}x{crop_size}")
            
            # Add frame
            frame_size = crop_size + (2 * frame_width)
            framed_img = Image.new('RGB', (frame_size, frame_size), frame_color)
            
            # Paste the cropped image in the center of the frame
            paste_x = frame_width
            paste_y = frame_width
            framed_img.paste(cropped_img, (paste_x, paste_y))
            
            print(f"Added frame: {frame_size}x{frame_size}")
            
            # Save as PNG
            framed_img.save(output_path, 'PNG')
            print(f"Saved as: {output_path}")
            
            return True
            
    except Exception as e:
        print(f"Error processing image: {e}")
        return False

def main():
    # Input and output paths
    input_file = "src/Dry Run/test.jpg"
    output_file = "src/Dry Run/test_processed.png"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        return
    
    # Process the image
    print("Processing image...")
    success = process_image(
        input_path=input_file,
        output_path=output_file,
        frame_width=30,  # 30 pixel frame
        frame_color=(200, 200, 200)  # Light gray frame
    )
    
    if success:
        print("Image processing completed successfully!")
    else:
        print("Image processing failed!")

if __name__ == "__main__":
    main() 