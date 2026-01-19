import cv2
import numpy as np
from PIL import Image

def calculate_group_size(uploaded_image, target_width_mm=210.0, sensitivity=128, min_area_px=10):
    """
    Analyzes an image to detect bullet holes and calculate group size metrics.
    Uses user-adjustable thresholding for better control over lighting conditions.

    Args:
        uploaded_image: StreamlitUploadedFile or PIL Image
        target_width_mm: The physical width of the image area in mm
        sensitivity: Threshold value (0-255). Lower = strictly dark holes. Higher = more permissive.
        min_area_px: Minimum area of a blob to be considered a hole.
        
    Returns:
        dict: containing 'group_size_mm', 'mean_radius_mm', 'shot_count', 'annotated_image', 'debug_binary'
    """
    try:
        # Convert PIL to openCV
        if isinstance(uploaded_image, Image.Image):
            image = uploaded_image
        else:
            image = Image.open(uploaded_image)
            
        img_np = np.array(image)
        
        # Convert RGB to BGR
        if len(img_np.shape) == 3:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        else:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)
            
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # 1. Image Preprocessing
        # Stronger Gaussian Blur to remove paper texture noise
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # Global Thresholding (User Controlled)
        # Inverted: Holes (dark) become White (255), Paper (light) becomes Black (0)
        # Sensitivity is the threshold value. Pixels darker than 'sensitivity' become white.
        _, thresh = cv2.threshold(blurred, sensitivity, 255, cv2.THRESH_BINARY_INV)
        
        # Morphological Opening (Erosion followed by Dilation)
        # This removes small white noise (specks) without affecting larger blobs (holes)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
        
        # 2. Contour Detection
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detected_shots = []
        
        annotated_img = img_np.copy()
        
        # 3. Filter Contours (Bullet Hole Heuristics)
        img_area = img_np.shape[0] * img_np.shape[1]
        
        # Safety clamp for min_area to avoid 0
        current_min_area = max(min_area_px, 5) 
        max_valid_area = img_area * 0.02 # Max single hole size 2% of image (prevent detecting the whole target frame)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            
            if current_min_area < area < max_valid_area:
                # Circularity check to differentiate holes from random squiggles or lines
                perimeter = cv2.arcLength(cnt, True)
                if perimeter == 0: continue
                circularity = 4 * np.pi * (area / (perimeter * perimeter))
                
                # Convex Hull solidity check (another way to check for blob-ness)
                hull = cv2.convexHull(cnt)
                hull_area = cv2.contourArea(hull)
                if hull_area == 0: continue
                solidity = float(area)/hull_area

                # Bullet holes should be somewhat circular (>0.5) and solid (>0.7)
                if circularity > 0.5 and solidity > 0.7:
                    # Get center
                    M = cv2.moments(cnt)
                    if M["m00"] != 0:
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])
                        detected_shots.append((cX, cY))
                        # Draw contour on debug to show exactly what was detected
                        cv2.drawContours(annotated_img, [cnt], -1, (0, 165, 255), 1) # Orange contour

        # Pixel to mm conversion
        height, width = img_np.shape[:2]
        pixel_per_mm = width / target_width_mm
        
        stats = {
            "group_size_mm": 0.0,
            "mean_radius_mm": 0.0,
            "shot_count": len(detected_shots),
            "annotated_image": annotated_img,
            "debug_binary": thresh,
            "detected_shots": detected_shots
        }

        if len(detected_shots) > 0:
            # --- Draw Shots ---
            for (x, y) in detected_shots:
                # Draw crosshair
                cv2.drawMarker(annotated_img, (x, y), (0, 0, 255), markerType=cv2.MARKER_CROSS, markerSize=20, thickness=2)
                # Draw circle
                cv2.circle(annotated_img, (x, y), 12, (0, 255, 0), 2)
            
            # --- Calculate Group Center (MPI) ---
            avg_x = sum([p[0] for p in detected_shots]) / len(detected_shots)
            avg_y = sum([p[1] for p in detected_shots]) / len(detected_shots)
            center_pt = (int(avg_x), int(avg_y))
            
            # Draw MPI
            cv2.drawMarker(annotated_img, center_pt, (255, 0, 0), markerType=cv2.MARKER_DIAMOND, markerSize=25, thickness=2)
            cv2.putText(annotated_img, "MPI", (center_pt[0]+15, center_pt[1]-15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

            # --- Calculate Metrics ---
            
            # Mean Radius (Avg dist from MPI)
            total_dist_from_center = 0
            for (x, y) in detected_shots:
                dist = np.sqrt((x - avg_x)**2 + (y - avg_y)**2)
                total_dist_from_center += dist
            
            mean_radius_px = total_dist_from_center / len(detected_shots)
            stats["mean_radius_mm"] = mean_radius_px / pixel_per_mm

            # Group Size (Max Distance)
            max_dist_px = 0
            p1, p2 = None, None
            
            if len(detected_shots) >= 2:
                for i in range(len(detected_shots)):
                    for j in range(i + 1, len(detected_shots)):
                        x1, y1 = detected_shots[i]
                        x2, y2 = detected_shots[j]
                        dist = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                        if dist > max_dist_px:
                            max_dist_px = dist
                            p1 = (x1, y1)
                            p2 = (x2, y2)
            
                stats["group_size_mm"] = max_dist_px / pixel_per_mm
                
                # Draw Max Spread Line
                if p1 and p2:
                    cv2.line(annotated_img, p1, p2, (255, 0, 255), 3) # Magenta line
                    mid_line_x = int((p1[0] + p2[0]) / 2)
                    mid_line_y = int((p1[1] + p2[1]) / 2)
                    label = f"{stats['group_size_mm']:.1f} mm"
                    # Add background to text for readability
                    (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                    cv2.rectangle(annotated_img, (mid_line_x - 2, mid_line_y - 25), (mid_line_x + w + 2, mid_line_y + 5), (255, 255, 255), -1)
                    cv2.putText(annotated_img, label, (mid_line_x, mid_line_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)

        return stats

    except Exception as e:
        print(f"Error in CV: {e}")
        # Convert fallback grayscale back to BGR for consistency
        placeholder = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        return {"group_size_mm": 0.0, "mean_radius_mm": 0.0, "shot_count": 0, "annotated_image": placeholder, "debug_binary": None}
