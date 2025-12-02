import cv2
import numpy as np
import time
import threading
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not installed. Running in silent mode (no sound).")
    print("To enable sound: pip install pygame")

from pynput import keyboard

class PianoKey:
    """Represents a single piano key."""
    
    def __init__(self, x, y, width, height, note, frequency, keyboard_key, is_black=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.note = note
        self.frequency = frequency
        self.keyboard_key = keyboard_key  # Display label (e.g., "1", "Shift+1")
        self.is_black = is_black
        self.is_pressed = False
        self.cooldown = 0
        
    def draw(self, frame):
        """Draw the key on the frame."""
        if not self.is_black:
            # White key with 3D effect
            if self.is_pressed:
                # Pressed state - darker gradient
                top_color = (200, 200, 200)
                bottom_color = (160, 160, 160)
            else:
                # Normal state - light gradient
                top_color = (255, 255, 255)
                bottom_color = (220, 220, 220)
            
            # Create gradient effect for white keys
            for i in range(self.height):
                ratio = i / self.height
                r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
                g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
                b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
                cv2.line(frame, 
                        (self.x, self.y + i), 
                        (self.x + self.width, self.y + i), 
                        (b, g, r), 1)
            
            # Add shadow on the right edge
            shadow_width = 6
            for i in range(shadow_width):
                alpha = (shadow_width - i) / shadow_width * 0.3
                shadow_color = int(150 * (1 - alpha))
                cv2.line(frame,
                        (self.x + self.width - i - 1, self.y),
                        (self.x + self.width - i - 1, self.y + self.height),
                        (shadow_color, shadow_color, shadow_color), 1)
            
            # Dark border
            cv2.rectangle(frame, (self.x, self.y), 
                         (self.x + self.width, self.y + self.height),
                         (40, 40, 40), 3)
        
        else:
            # Black key with 3D raised effect
            y_offset = 2 if self.is_pressed else 0
            actual_y = self.y + y_offset
            
            if self.is_pressed:
                # Pressed - lighter gray
                top_color = (80, 80, 80)
                bottom_color = (60, 60, 60)
            else:
                # Normal - dark gradient
                top_color = (60, 60, 60)
                bottom_color = (20, 20, 20)
            
            # Create gradient for black keys
            for i in range(self.height - y_offset):
                ratio = i / (self.height - y_offset)
                r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
                g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
                b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
                cv2.line(frame,
                        (self.x, actual_y + i),
                        (self.x + self.width, actual_y + i),
                        (b, g, r), 1)
            
            # Highlight on top edge (3D effect)
            if not self.is_pressed:
                cv2.rectangle(frame, (self.x + 2, actual_y + 2),
                            (self.x + self.width - 2, actual_y + 8),
                            (90, 90, 90), -1)
            
            # Black border
            cv2.rectangle(frame, (self.x, actual_y),
                         (self.x + self.width, actual_y + self.height - y_offset),
                         (0, 0, 0), 2)
        
        # Draw labels based on key type
        y_offset = 2 if (self.is_black and self.is_pressed) else 0
        
        # Draw note label
        label_color = (0, 0, 0) if not self.is_black else (255, 255, 255)
        text_size = cv2.getTextSize(self.note, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        text_x = self.x + (self.width - text_size[0]) // 2
        text_y = self.y + y_offset + self.height - 45
        
        cv2.putText(
            frame,
            self.note,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            label_color,
            1
        )
        
        # Draw keyboard key label
        if not self.is_black:
            # White keys show just the number
            kb_label_color = (255, 0, 0)  # Red labels
            display_key = self.keyboard_key
            kb_text_size = cv2.getTextSize(display_key, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            kb_text_x = self.x + (self.width - kb_text_size[0]) // 2
            kb_text_y = self.y + self.height - 15
            
            cv2.putText(
                frame,
                display_key,
                (kb_text_x, kb_text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                kb_label_color,
                2
            )
        else:
            # Black keys show shift arrow + number
            kb_label_color = (200, 200, 255)  # Light blue/white for black keys
            # Extract the number from keyboard_key (e.g., "Shift+1" -> "1")
            display_key = "^" + self.keyboard_key.split("+")[1]
            kb_text_size = cv2.getTextSize(display_key, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            kb_text_x = self.x + (self.width - kb_text_size[0]) // 2
            kb_text_y = self.y + y_offset + self.height - 15
            
            cv2.putText(
                frame,
                display_key,
                (kb_text_x, kb_text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                kb_label_color,
                2
            )


class KeyboardPiano:
    """Piano controlled by computer keyboard."""
    
    def __init__(self, frame_width, frame_height):
        self.frame_w = frame_width
        self.frame_h = frame_height
        self.keys = []
        self.key_map = {}  # Maps input characters to piano keys
        self.setup_piano()
        
        # Initialize pygame for sound
        self.sound_enabled = PYGAME_AVAILABLE
        if self.sound_enabled:
            # Increased channels to 32 to prevent sound clipping when playing many notes
            # Using 44.1kHz for better quality
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(32)
            self.sounds = {}
            self.generate_sounds()

        # Input handling with pynput
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.listener.start()

    def setup_piano(self):
        """Create piano keys layout with keyboard mapping."""
        # Key mapping following Option A (chromatic scale with natural sharps)
        # Format: (note_name, frequency, display_label, input_chars, is_black)
        # input_chars is a list of characters that trigger this note (e.g. '1' for C4, '!' for C#4)
        
        notes_data = [
            # Natural notes (white keys)
            ("C4", 261.63, "1", ['1'], False),
            ("D4", 293.66, "2", ['2'], False),
            ("E4", 329.63, "3", ['3'], False),
            ("F4", 349.23, "4", ['4'], False),
            ("G4", 392.00, "5", ['5'], False),
            ("A4", 440.00, "6", ['6'], False),
            ("B4", 493.88, "7", ['7'], False),
            ("C5", 523.25, "8", ['8'], False),
            ("D5", 587.33, "9", ['9'], False),
            ("E5", 659.25, "0", ['0'], False),
            
            # Sharp notes (black keys)
            ("C#4", 277.18, "Shift+1", ['!'], True),
            ("D#4", 311.13, "Shift+2", ['@'], True),
            ("F#4", 369.99, "Shift+4", ['$'], True),
            ("G#4", 415.30, "Shift+5", ['%'], True),
            ("A#4", 466.16, "Shift+6", ['^'], True),
            ("C#5", 554.37, "Shift+8", ['*'], True),
            ("D#5", 622.25, "Shift+9", ['('], True),
        ]
        
        # Calculate key dimensions
        key_start_y = 200
        white_key_width = 90
        white_key_height = 250
        black_key_width = 60
        black_key_height = 160
        
        # Create white keys first
        white_keys = [n for n in notes_data if not n[4]]
        x_offset = 50
        
        for note, freq, label, chars, is_black in white_keys:
            key = PianoKey(
                x_offset, key_start_y,
                white_key_width, white_key_height,
                note, freq, label, False
            )
            self.keys.append(key)
            for char in chars:
                self.key_map[char] = key
            x_offset += white_key_width
        
        # Create black keys on top
        black_positions = {
            "Shift+1": 0, "Shift+2": 1,
            "Shift+4": 3, "Shift+5": 4, "Shift+6": 5,
            "Shift+8": 7, "Shift+9": 8,
        }
        
        black_keys = [n for n in notes_data if n[4]]
        
        for note, freq, label, chars, is_black in black_keys:
            if label in black_positions:
                white_key_pos = black_positions[label]
                white_key_x = 50 + white_key_pos * white_key_width
                black_key_x = white_key_x + white_key_width - black_key_width // 2
                
                key = PianoKey(
                    black_key_x, key_start_y,
                    black_key_width, black_key_height,
                    note, freq, label, True
                )
                self.keys.append(key)
                for char in chars:
                    self.key_map[char] = key
    
    def add_reverb(self, wave, sample_rate, delay_ms=80, decay=0.45, num_echoes=7, wet=0.25):
        """Add realistic reverb effect using FIR-style echo convolution."""
        delay_samples = int(sample_rate * delay_ms / 1000)
        output = np.copy(wave)
        
        # Create delayed echoes
        for i in range(1, num_echoes + 1):
            delay = delay_samples * i
            if delay < len(wave):
                echo_gain = decay ** i
                # Add delayed and attenuated version
                output[delay:] += wave[:-delay] * echo_gain
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(output))
        if max_val > 0:
            output = output / max_val
        
        # Mix dry and wet signals
        result = (1 - wet) * wave + wet * output
        
        return result
    
    def generate_sounds(self):
        """Generate professionally tuned piano sounds."""
        sample_rate = 44100
        duration = 3.5
        
        for key in self.keys:
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples)
            fundamental = key.frequency
            
            wave = np.zeros(samples)
            
            # Rich Piano Harmonic Profile (restored from original)
            # This profile gives the warm, rich piano sound
            harmonics_data = [
                (1.0, 1.0),      # Fundamental
                (2.0, 0.5),      # 2nd harmonic
                (3.0, 0.3),      # 3rd harmonic
                (4.0, 0.2),      # 4th harmonic
                (5.0, 0.15),     # 5th harmonic
                (6.0, 0.1),      # 6th harmonic
                (7.0, 0.08),     # 7th harmonic
                (8.0, 0.05),     # 8th harmonic
            ]
            
            for h_num, amp in harmonics_data:
                freq = fundamental * h_num
                wave += amp * np.sin(2 * np.pi * freq * t)
            
            # Very subtle hammer attack (much less than before to avoid hiss)
            hammer_noise = np.random.normal(0, 0.01, samples)  # Reduced from 0.05
            hammer_envelope = np.exp(-t * 60)  # Faster decay (was 40)
            wave += hammer_noise * hammer_envelope
            
            # Normalize
            max_val = np.max(np.abs(wave))
            if max_val > 0:
                wave = wave / max_val
            
            # ADSR Envelope (restored from original with slight improvements)
            attack_t = 0.01
            decay_t = 0.1
            
            attack_samples = int(sample_rate * attack_t)
            decay_samples = int(sample_rate * decay_t)
            sustain_samples = samples - attack_samples - decay_samples
            
            # Attack
            attack_env = np.linspace(0, 1, attack_samples)
            
            # Decay
            decay_env = np.linspace(1, 0.7, decay_samples)
            
            # Sustain with exponential decay
            sustain_t = np.linspace(0, 1, sustain_samples)
            sustain_env = 0.7 * np.exp(-2.2 * sustain_t)
            
            envelope = np.concatenate([attack_env, decay_env, sustain_env])
            wave = wave * envelope
            
            # Add reverb effect
            wave = self.add_reverb(wave, sample_rate, delay_ms=80, decay=0.45, num_echoes=7, wet=0.25)
            
            # Convert to 16-bit stereo
            wave = (wave * 32767 * 0.95).astype(np.int16)
            stereo_wave = np.column_stack((wave, wave))
            
            self.sounds[key.note] = pygame.mixer.Sound(stereo_wave)
    
    def play_note(self, note):
        """Start playing the note."""
        if self.sound_enabled and note in self.sounds:
            self.sounds[note].stop()
            self.sounds[note].play()
    
    def stop_note(self, note):
        """Fade out the note."""
        if self.sound_enabled and note in self.sounds:
            self.sounds[note].fadeout(300)  # 300ms fadeout mimics damper

    def on_press(self, key):
        try:
            char = None
            if hasattr(key, 'char') and key.char:
                char = key.char
            
            if char and char in self.key_map:
                piano_key = self.key_map[char]
                if not piano_key.is_pressed:
                    piano_key.is_pressed = True
                    self.play_note(piano_key.note)
        except Exception as e:
            print(f"Error in on_press: {e}")

    def on_release(self, key):
        try:
            char = None
            if hasattr(key, 'char') and key.char:
                char = key.char
            
            if char and char in self.key_map:
                piano_key = self.key_map[char]
                if piano_key.is_pressed:
                    piano_key.is_pressed = False
                    self.stop_note(piano_key.note)
        except Exception as e:
            print(f"Error in on_release: {e}")
            
    def draw_decorative_dials(self, frame):
        """Draw decorative control dials below the piano."""
        dial_y = 550  # Move to bottom
        dial_radius = 38  # Increased by 50%
        dial_spacing = 180  # Adjusted spacing for larger dials
        start_x = 200
        
        dial_labels = ["MODULATOR", "PITCH", "TREMOLO", "REVERB"]
        
        for i, label in enumerate(dial_labels):
            dial_x = start_x + i * dial_spacing
            
            # Draw dial outer circle (dark metallic)
            cv2.circle(frame, (dial_x, dial_y), dial_radius, (60, 60, 65), -1)
            cv2.circle(frame, (dial_x, dial_y), dial_radius, (40, 40, 45), 2)
            
            # Draw dial inner circle (darker)
            cv2.circle(frame, (dial_x, dial_y), dial_radius - 5, (35, 35, 40), -1)
            
            # Draw indicator line
            angle = -135 + (i * 30)  # Varying positions
            rad = np.radians(angle)
            line_length = dial_radius - 8
            end_x = int(dial_x + line_length * np.cos(rad))
            end_y = int(dial_y + line_length * np.sin(rad))
            cv2.line(frame, (dial_x, dial_y), (end_x, end_y), (180, 180, 200), 3)
            
            # Draw center dot
            cv2.circle(frame, (dial_x, dial_y), 4, (200, 200, 220), -1)
            
            # Draw label below dial
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)[0]
            text_x = dial_x - text_size[0] // 2
            text_y = dial_y + dial_radius + 20
            cv2.putText(frame, label, (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.35, (140, 140, 150), 1)
    
    def draw(self, frame):
        """Draw the piano on the frame."""
        # Darker background for professional look
        frame[:] = (25, 25, 25)
        
        # Draw decorative dials
        self.draw_decorative_dials(frame)
        
        # Draw white keys
        for key in self.keys:
            if not key.is_black:
                key.draw(frame)
        
        # Draw black keys
        for key in self.keys:
            if key.is_black:
                key.draw(frame)
        
        # UI Text
        cv2.putText(frame, "Keyboard Piano", (50, 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        
        instructions = [
            "Press and HOLD keys 1-0 to play",
            "Use Shift + number for sharp notes (#)",
            "Press 'Q' or ESC to quit"
        ]
        
        for i, text in enumerate(instructions):
            cv2.putText(frame, text, (50, 120 + i * 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
                       
        return frame

def main():
    print("Starting Keyboard Piano...")
    print("Controls:")
    print("  - Press keys 1-0 for white keys")
    print("  - Shift + 1-9 for black keys")
    print("  - Q or ESC to quit")
    
    window_width = 1000
    window_height = 700
    
    piano = KeyboardPiano(window_width, window_height)
    frame = np.zeros((window_height, window_width, 3), dtype=np.uint8)
    
    running = True
    while running:
        # We still need waitKey for the OpenCV window to update and handle window events
        # But we don't use it for piano input anymore
        key = cv2.waitKey(10) & 0xFF
        
        if key == ord('q') or key == ord('Q') or key == 27:
            running = False
            
        frame = piano.draw(frame)
        cv2.imshow("Keyboard Piano", frame)
    
    # Cleanup
    piano.listener.stop()
    cv2.destroyAllWindows()
    if PYGAME_AVAILABLE:
        pygame.mixer.quit()
    print("Keyboard Piano ended.")

if __name__ == "__main__":
    main()
