import cv2
import numpy as np
from PIL import Image

def detect_reference_object(img_bgr, ref_type="coin_br_1"):
    """
    Attempts to detect a reference object (like a coin) to calibrate pixels to mm.
    ref_type: "coin_br_1" (27mm), "coin_br_050" (23mm), etc.
    Returns: pixel_per_mm or None
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)
    
    # Use HoughCircles to detect the coin
    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=100,
        param1=50, param2=30, minRadius=20, maxRadius=100
    )
    
    if circles is not None:
        circles = np.uint16(np.around(circles))
        # Take the most prominent circle
        coin = circles[0, 0] # [x, y, radius]
        diameter_px = coin[2] * 2
        
        # Reference diameters in mm
        refs = {
            "coin_br_1": 27.0,
            "coin_br_050": 23.0,
            "coin_br_025": 25.0,
            "coin_br_010": 20.0
        }
        
        ref_mm = refs.get(ref_type, 27.0)
        return diameter_px / ref_mm, coin # px/mm, coin_geom
    
    return None, None

def group_shots(shots, dist_threshold_px=150):
    """
    Groups shots into clusters based on distance.
    Simple implementation of Density-Based clustering without sklearn.
    """
    if not shots: return []
    
    n = len(shots)
    groups = []
    visited = [False] * n
    
    def get_neighbors(idx):
        neighbors = []
        for j in range(n):
            d = np.sqrt((shots[idx][0] - shots[j][0])**2 + (shots[idx][1] - shots[j][1])**2)
            if d < dist_threshold_px:
                neighbors.append(j)
        return neighbors

    for i in range(n):
        if not visited[i]:
            visited[i] = True
            cluster = [shots[i]]
            queue = get_neighbors(i)
            
            idx = 0
            while idx < len(queue):
                neighbor_idx = queue[idx]
                if not visited[neighbor_idx]:
                    visited[neighbor_idx] = True
                    cluster.append(shots[neighbor_idx])
                    new_neighbors = get_neighbors(neighbor_idx)
                    for nn in new_neighbors:
                        if nn not in queue:
                            queue.append(nn)
                idx += 1
            groups.append(cluster)
            
    return groups

def calculate_group_size_v2(uploaded_image, target_width_mm=210.0, sensitivity=155, min_area_px=50, center_point=None, use_auto_calib=False):
    """
    Improved CV Analysis with Multi-Group support and POI calculation.
    """
    try:
        if isinstance(uploaded_image, Image.Image):
            image = uploaded_image
        else:
            image = Image.open(uploaded_image)
        img_np = np.array(image)
        
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR) if len(img_np.shape) == 3 else cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # --- 1. Calibration ---
        pixel_per_mm = img_np.shape[1] / target_width_mm
        auto_calib_marker = None
        
        if use_auto_calib:
            calib_px_mm, coin_data = detect_reference_object(img_bgr)
            if calib_px_mm:
                pixel_per_mm = calib_px_mm
                auto_calib_marker = coin_data

        # --- 2. Hole Detection (strict filtering to avoid false positives) ---
        # Bullet holes are dark, roughly circular, and have distinct edges
        _, thresh = cv2.threshold(blurred, sensitivity, 255, cv2.THRESH_BINARY_INV)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_shots = []
        annotated_img = img_np.copy()
        
        img_h, img_w = img_np.shape[:2]
        img_area = img_h * img_w
        max_valid_area = img_area * 0.03  # Max 3% of image (was 5%)
        min_valid_area = max(min_area_px, 80)  # Minimum area to avoid noise
        edge_margin = int(min(img_h, img_w) * 0.02)  # 2% margin from edges

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_valid_area or area > max_valid_area:
                continue

            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue

            # Shape metrics (stricter for impact points)
            circularity = 4 * np.pi * (area / (perimeter * perimeter))
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            solidity = float(area) / hull_area if hull_area > 0 else 0

            # Bounding box aspect ratio (bullet holes are extremely close to 1:1)
            x_r, y_r, w_r, h_r = cv2.boundingRect(cnt)
            aspect_ratio = float(w_r) / h_r if h_r > 0 else 0

            # FILTER 1: Shape must be circular-ish (real impact points are very circular)
            if circularity < 0.75 or solidity < 0.88:
                continue

            # FILTER 2: Aspect ratio must be very close to 1:1
            if aspect_ratio < 0.8 or aspect_ratio > 1.25:
                continue

            # FILTER 3: Reject detections too close to image edges
            M = cv2.moments(cnt)
            if M["m00"] == 0:
                continue
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])

            if cX < edge_margin or cX > (img_w - edge_margin):
                continue
            if cY < edge_margin or cY > (img_h - edge_margin):
                continue

            # FILTER 4: Intensity Gradient Validation
            # Bullet holes in paper have a dark interior and often a "lead smear" ring.
            mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.drawContours(mask, [cnt], -1, 255, -1)
            
            # Sample interior
            mean_intensity = cv2.mean(gray, mask=mask)[0]
            
            # Sample exterior ring
            dilated_mask = cv2.dilate(mask, kernel, iterations=3)
            ring_mask = cv2.subtract(dilated_mask, mask)
            surround_intensity = cv2.mean(gray, mask=ring_mask)[0] if cv2.countNonZero(ring_mask) > 0 else 255

            # A real hole should be MUCH darker than its immediate surroundings
            # AND it shouldn't be just a dark spot in a dark area (contrast check)
            if (surround_intensity - mean_intensity) < 35:
                continue

            # Passed all filters — this is likely a real bullet hole
            detected_shots.append((cX, cY))
            cv2.drawContours(annotated_img, [cnt], -1, (255, 165, 0), 2)

        # --- 3. Multi-Group Logic ---
        shot_groups = group_shots(detected_shots, dist_threshold_px=pixel_per_mm * 100) # 10cm threshold
        results_groups = []

        for idx, group in enumerate(shot_groups):
            # Calculate metrics for this specific group
            avg_x = sum([p[0] for p in group]) / len(group)
            avg_y = sum([p[1] for p in group]) / len(group)
            
            # Max Spread
            max_dist_px = 0
            if len(group) >= 2:
                for i in range(len(group)):
                    for j in range(i+1, len(group)):
                        dist = np.sqrt((group[i][0]-group[j][0])**2 + (group[i][1]-group[j][1])**2)
                        if dist > max_dist_px: max_dist_px = dist
            
            group_mm = max_dist_px / pixel_per_mm
            poi_x, poi_y = 0.0, 0.0
            if center_point:
                poi_x = (avg_x - center_point[0]) / pixel_per_mm
                poi_y = (center_point[1] - avg_y) / pixel_per_mm # Inverted Y for ballistic coordinate

            results_groups.append({
                "id": idx + 1,
                "shots": group,
                "mpi": (avg_x, avg_y),
                "group_size_mm": group_mm,
                "poi_mm": (poi_x, poi_y)
            })

            # Visuals for group
            color = (0, 255, 0) if idx == 0 else (255, 255, 0)
            for (sx, sy) in group:
                cv2.circle(annotated_img, (sx, sy), 10, color, 2)
                cv2.drawMarker(annotated_img, (sx, sy), color, cv2.MARKER_CROSS, 15)
            
            cv2.drawMarker(annotated_img, (int(avg_x), int(avg_y)), (0, 0, 255), cv2.MARKER_STAR, 20)
            cv2.putText(annotated_img, f"G{idx+1}: {group_mm:.1f}mm", (int(avg_x), int(avg_y)-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Highlight auto-calib coin
        if auto_calib_marker is not None:
            x, y, r = auto_calib_marker
            cv2.circle(annotated_img, (x, y), r, (255, 0, 255), 3)
            cv2.putText(annotated_img, "REF CALIB", (x-r, y-r-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

        return {
            "groups": results_groups,
            "annotated_image": annotated_img,
            "pixel_per_mm": pixel_per_mm,
            "shot_count": len(detected_shots)
        }

    except Exception as e:
        print(f"CV Error: {e}")
        return {"groups": [], "annotated_image": np.array(image), "pixel_per_mm": 1.0, "shot_count": 0}
