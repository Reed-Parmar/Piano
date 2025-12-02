import cv2
import numpy as np
import argparse
from hand_tracker import HandTracker
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not installed. Running in silent mode (no sound).")
    print("To enable sound: pip install pygame")


class PianoKey:
    """Represents a single piano key."""
    
    def __init__(self, x, y, width, height, note, frequency, is_black=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.note = note
        self.frequency = frequency
        self.is_black = is_black
        self.is_pressed = False
        self.cooldown = 0
        
    def contains_point(self, x, y):
        """Check if point (x, y) is inside this key."""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)
    
    def draw(self, frame):
        """Draw the key on the frame."""
        # Color based on key type and state
        if self.is_pressed and self.cooldown > 0:
            color = (100, 200, 255) if not self.is_black else (150, 150, 255)
        else:
            color = (255, 255, 255) if not self.is_black else (50, 50, 50)
        
        # Draw key rectangle
        cv2.rectangle(
            frame,
            (self.x, self.y),
            (self.x + self.width, self.y + self.height),
            color,
            -1  # Filled
        )
        
        # Draw key border
        border_color = (0, 0, 0)
        cv2.rectangle(
            frame,
            (self.x, self.y),
            (self.x + self.width, self.y + self.height),
            border_color,
            2
        )
        
        # Draw note label
        label_color = (0, 0, 0) if not self.is_black else (255, 255, 255)
        text_size = cv2.getTextSize(self.note, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        text_x = self.x + (self.width - text_size[0]) // 2
        text_y = self.y + self.height - 10
        
        cv2.putText(
            frame,
            self.note,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            label_color,
            1
        )


class AirPiano:
    """Air Piano using hand tracking."""
    
    def __init__(self, frame_width, frame_height):
        self.frame_w = frame_width
        self.frame_h = frame_height
        self.keys = []
        self.setup_piano()
        
        # Initialize pygame for sound
        self.sound_enabled = PYGAME_AVAILABLE
        if self.sound_enabled:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.sounds = {}
            self.generate_sounds()
    
    def setup_piano(self):
        """Create piano keys layout."""
        # Piano keyboard layout (2 octaves, C4 to C6)
        # Notes and their frequencies
        notes_data = [
            # Octave 4
            ("C4", 261.63, False),
            ("C#4", 277.18, True),
            ("D4", 293.66, False),
            ("D#4", 311.13, True),
            ("E4", 329.63, False),
            ("F4", 349.23, False),
            ("F#4", 369.99, True),
            ("G4", 392.00, False),
            ("G#4", 415.30, True),
            ("A4", 440.00, False),
            ("A#4", 466.16, True),
            ("B4", 493.88, False),
            # Octave 5
            ("C5", 523.25, False),
            ("C#5", 554.37, True),
            ("D5", 587.33, False),
            ("D#5", 622.25, True),
            ("E5", 659.25, False),
            ("F5", 698.46, False),
        ]
        
        # Calculate key dimensions
        # Position piano in upper-middle area for easier reach
        key_start_y = 150  # Moved up from bottom (was: self.frame_h - 250)
        white_key_width = 70
        white_key_height = 200
        black_key_width = 45
        black_key_height = 130
        
        # Create white keys first
        white_keys = [n for n in notes_data if not n[2]]
        x_offset = 50
        
        for note, freq, is_black in white_keys:
            key = PianoKey(
                x_offset, key_start_y,
                white_key_width, white_key_height,
                note, freq, False
            )
            self.keys.append(key)
            x_offset += white_key_width
        
        # Create black keys on top
        black_positions = [0, 1, 3, 4, 5, 7, 8, 10]  # Positions where black keys appear
        black_keys = [n for n in notes_data if n[2]]
        
        for i, (note, freq, is_black) in enumerate(black_keys):
            if i < len(black_positions):
                white_key_x = 50 + black_positions[i] * white_key_width
                black_key_x = white_key_x + white_key_width - black_key_width // 2
                
                key = PianoKey(
                    black_key_x, key_start_y,
                    black_key_width, black_key_height,
                    note, freq, True
                )
                self.keys.append(key)
    
    def generate_sounds(self):
        """Generate sine wave sounds for each note."""
        sample_rate = 22050
        duration = 0.3  # seconds
        
        for key in self.keys:
            # Generate sine wave
            samples = int(sample_rate * duration)
            wave = np.array([
                int(4096 * np.sin(2 * np.pi * key.frequency * i / sample_rate))
                for i in range(samples)
            ])
            
            # Apply fade out to avoid clicking
            fade_samples = int(sample_rate * 0.05)
            for i in range(fade_samples):
                wave[-(i+1)] = int(wave[-(i+1)] * (i / fade_samples))
            
            # Convert to stereo
            stereo_wave = np.column_stack((wave, wave))
            
            # Create pygame sound
            sound = pygame.sndarray.make_sound(stereo_wave.astype(np.int16))
            self.sounds[key.note] = sound
    
    def play_note(self, note):
        """Play the sound for a given note."""
        if self.sound_enabled and note in self.sounds:
            self.sounds[note].play(maxtime=300)
    
    def update(self, hands):
        """Update piano state based on detected hands."""
        # Decrease cooldown for all keys
        for key in self.keys:
            if key.cooldown > 0:
                key.cooldown -= 1
            if key.cooldown == 0:
                key.is_pressed = False
        
        if not hands:
            return
        
        # Check all fingertips for both hands
        for hand in hands:
            landmarks = hand['landmarks']
            h, w = self.frame_h, self.frame_w
            
            # Fingertip landmark IDs: thumb=4, index=8, middle=12, ring=16, pinky=20
            fingertip_ids = [4, 8, 12, 16, 20]
            
            for tip_id in fingertip_ids:
                lm = landmarks.landmark[tip_id]
                x, y = int(lm.x * w), int(lm.y * h)
                
                # Check if fingertip touches any key (check black keys first)
                for key in sorted(self.keys, key=lambda k: k.is_black, reverse=True):
                    if key.contains_point(x, y) and key.cooldown == 0:
                        key.is_pressed = True
                        key.cooldown = 15  # Prevent rapid re-triggering
                        self.play_note(key.note)
                        break
    
    def draw(self, frame):
        """Draw the piano on the frame."""
        # Draw white keys first
        for key in self.keys:
            if not key.is_black:
                key.draw(frame)
        
        # Draw black keys on top
        for key in self.keys:
            if key.is_black:
                key.draw(frame)
        
        # Draw title
        cv2.putText(
            frame,
            "Air Piano - Touch keys with your fingertips!",
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )
        
        # Draw instructions
        cv2.putText(
            frame,
            "Press 'q' to quit",
            (10, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2
        )
        
        return frame


def main(camera_index=1):
    """Main function to run the air piano."""
    print("Starting Air Piano...")
    print("Controls:")
    print("  - Touch piano keys with your fingertips to play notes")
    print("  - Press 'q' to quit")
    print()
    
    # Initialize camera
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"Error: Could not open camera at index {camera_index}")
        print("Try running with a different camera index:")
        print("  python air_piano.py --camera 0")
        print("  python air_piano.py --camera 2")
        return
    
    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Initialize hand tracker (both hands)
    tracker = HandTracker(max_num_hands=2)
    
    # Read one frame to get dimensions
    success, frame = cap.read()
    if not success:
        print("Error: Could not read from camera")
        cap.release()
        return
    
    frame_h, frame_w, _ = frame.shape
    
    # Initialize air piano
    piano = AirPiano(frame_w, frame_h)
    
    print("Air Piano started! Show your hands to the camera.")
    if not PYGAME_AVAILABLE:
        print("Note: Running in silent mode. Install pygame for sound:")
        print("  pip install pygame")
    print()
    
    while True:
        success, frame = cap.read()
        if not success:
            print("Failed to read from camera")
            break
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Get detected hands
        hands = tracker.get_all_hands(frame, draw=True)
        
        # Update piano with hand positions
        piano.update(hands)
        
        # Draw piano
        frame = piano.draw(frame)
        
        # Display frame
        cv2.imshow("Air Piano", frame)
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    if PYGAME_AVAILABLE:
        pygame.mixer.quit()
    print("Air Piano ended.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Air Piano with Hand Tracking")
    parser.add_argument(
        '--camera',
        type=int,
        default=1,
        help='Camera index to use (default: 1 for integrated webcam)'
    )
    args = parser.parse_args()
    
    main(camera_index=args.camera)
