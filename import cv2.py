import cv2
import numpy as np

# Global variables to store manually selected points
manual_landmarks = []

def load_image(image_path):
    """Load an image from the given path."""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Image not found or unable to load.")
    return image

def select_landmarks(event, x, y, flags, param):
    """Mouse callback function to manually select landmarks."""
    global manual_landmarks
    if event == cv2.EVENT_LBUTTONDOWN:
        manual_landmarks.append((x, y))
        cv2.circle(param, (x, y), 2, (0, 255, 0), -1)
        cv2.imshow("Select Landmarks", param)

def calculate_symmetry(landmarks):
    """Calculate basic symmetry metrics."""
    # Midline landmarks (assume first 6 points are midline)
    midline_points = landmarks[:6]
    midline_x = np.mean([p[0] for p in midline_points])
    deviations = [abs(p[0] - midline_x) for p in midline_points]
    avg_midline_deviation = np.mean(deviations)

    # Bilateral landmarks (assume next 4 points are paired: left eye, right eye, left mouth, right mouth)
    left_eye = landmarks[6]
    right_eye = landmarks[7]
    left_mouth = landmarks[8]
    right_mouth = landmarks[9]

    # Calculate horizontal symmetry (eye and mouth alignment)
    eye_horiz_diff = abs(left_eye[1] - right_eye[1])
    mouth_horiz_diff = abs(left_mouth[1] - right_mouth[1])

    return {
        "avg_midline_deviation": avg_midline_deviation,
        "eye_horizontal_difference": eye_horiz_diff,
        "mouth_horizontal_difference": mouth_horiz_diff
    }

def main(image_path):
    """Main function to analyze facial symmetry."""
    global manual_landmarks
    image = load_image(image_path)

    # Display the image and allow manual landmark selection
    cv2.imshow("Select Landmarks", image)
    cv2.setMouseCallback("Select Landmarks", select_landmarks, image)

    print("Select landmarks in the following order:")
    print("1. Nasion (between eyes)")
    print("2. Pronasale (tip of the nose)")
    print("3. Subnasale (below nose)")
    print("4. Labiale Superius (upper lip)")
    print("5. Labiale Inferius (lower lip)")
    print("6. Gnathion (chin)")
    print("7. Left Eye Corner")
    print("8. Right Eye Corner")
    print("9. Left Mouth Corner")
    print("10. Right Mouth Corner")

    # Wait until 10 landmarks are selected
    while len(manual_landmarks) < 10:
        cv2.waitKey(1)

    cv2.destroyAllWindows()

    # Calculate symmetry metrics
    symmetry_metrics = calculate_symmetry(manual_landmarks)

    print("\nFacial Symmetry Metrics:")
    print(f"Average Midline Deviation: {symmetry_metrics['avg_midline_deviation']:.2f} pixels")
    print(f"Eye Horizontal Difference: {symmetry_metrics['eye_horizontal_difference']:.2f} pixels")
    print(f"Mouth Horizontal Difference: {symmetry_metrics['mouth_horizontal_difference']:.2f} pixels")

    # Visualize landmarks
    for (x, y) in manual_landmarks:
        cv2.circle(image, (x, y), 2, (0, 255, 0), -1)
    cv2.imshow("Facial Landmarks", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Run the script
if __name__ == "__main__":
    image_path = "path_to_your_image.jpg"  # Replace with your image path
    main(image_path)