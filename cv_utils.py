import cv2
import numpy as np
from PIL import Image

def calculate_group_size(uploaded_image, target_width_mm=210.0):
    """
    Simulates group size calculation. In a real scenario, this would involve intricate computer vision.
    For this prototype/version, we will process the image to find the 'hottest' spots or simply return
    mock data if complex CV fails, but let's try a simple blob detection.
    
    Args:
        uploaded_image: StreamlitUploadedFile or PIL Image
        target_width_mm: The physical width of the image area in mm (default A4 width)
        
    Returns:
        float: Estimated group size in mm
        image: Processed image with annotations
    """
    try:
        # Convert PIL to openCV
        image = Image.open(uploaded_image)
        img_np = np.array(image)
        
        # Convert RGB to BGR
        if len(img_np.shape) == 3:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        else:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)
            
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Blur to reduce noise
        gray_blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # Use Hough Circles to detect bullet holes (approximated as circles)
        # These params are tuned for typical black bullet holes on white paper
        circles = cv2.HoughCircles(
            gray_blurred, 
            cv2.HOUGH_GRADIENT, 
            dp=1, 
            minDist=20,
            param1=50, 
            param2=30, 
            minRadius=3, 
            maxRadius=30
        )
        
        annotated_img = img_np.copy()
        max_dist_px = 0
        p1, p2 = None, None
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            
            # Draw all circles
            for (x, y, r) in circles:
                cv2.circle(annotated_img, (x, y), r, (0, 255, 0), 2)
                cv2.circle(annotated_img, (x, y), 2, (0, 0, 255), 3)
            
            # Find max distance between any two holes (Group Size)
            if len(circles) >= 2:
                for i in range(len(circles)):
                    for j in range(i + 1, len(circles)):
                        x1, y1, _ = circles[i]
                        x2, y2, _ = circles[j]
                        dist = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                        if dist > max_dist_px:
                            max_dist_px = dist
                            p1 = (x1, y1)
                            p2 = (x2, y2)
                
                # Draw the group size line
                if p1 and p2:
                    cv2.line(annotated_img, p1, p2, (255, 0, 0), 2)
        
        # Pixel to mm conversion
        height, width = img_np.shape[:2]
        pixel_per_mm = width / target_width_mm
        
        group_size_mm = max_dist_px / pixel_per_mm
        
        if group_size_mm == 0:
            return 0.0, img_np
            
        return group_size_mm, annotated_img

    except Exception as e:
        print(f"Error in CV: {e}")
        return 0.0, None
