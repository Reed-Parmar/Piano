# 🎹 Keyboard Piano

A virtual piano application that lets you play music using your computer keyboard. Features realistic piano sound synthesis with reverb effects and a beautiful 3D graphical interface.

## ✨ Features

- **🎵 Realistic Piano Sound** - Professionally synthesized piano tones with harmonic overtones and reverb
- **⌨️ Keyboard Control** - Play using number keys 1-0 for natural notes and Shift+number for sharps
- **🎨 Beautiful 3D Interface** - Gradient keys with realistic pressed effects and decorative control dials
- **🔊 High Quality Audio** - 44.1kHz sample rate with 32-channel polyphony
- **📊 Real-time Visual Feedback** - Keys light up as you play them

## 🎮 How to Play

### White Keys (Natural Notes)
- Press keys **1-0** to play C4 through E5
- Hold the key down to sustain the note

### Black Keys (Sharp Notes)
- Press **Shift + number** for sharp notes (e.g., Shift+1 for C#4)
- Available sharps: Shift+1, Shift+2, Shift+4, Shift+5, Shift+6, Shift+8, Shift+9

### Keyboard Layout
```
Black Keys:  ^1  ^2      ^4  ^5  ^6      ^8  ^9
             C#  D#      F#  G#  A#      C#  D#

White Keys:   1   2   3   4   5   6   7   8   9   0
              C   D   E   F   G   A   B   C   D   E
             (C4 through E5)
```

### Controls
- **Q** or **ESC** - Quit the application

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/keyboard-piano.git
   cd keyboard-piano
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**
   - **Windows (PowerShell):**
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD):**
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - **macOS/Linux:**
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 📦 Dependencies

- **opencv-python** (cv2) - GUI rendering and display
- **numpy** - Audio waveform generation and numerical operations
- **pygame** - Sound synthesis and playback
- **pynput** - Keyboard input handling

## 🎯 Usage

Run the application:
```bash
python keyboard_piano.py
```

The piano window will open with:
- Visual piano keyboard display
- On-screen key labels
- Decorative control dials
- Real-time key press feedback

## 🛠️ Technical Details

### Audio Synthesis
- **Sample Rate:** 44.1 kHz
- **Bit Depth:** 16-bit stereo
- **Polyphony:** 32 simultaneous notes
- **Harmonics:** 8 harmonic overtones for realistic piano timbre
- **Effects:** Custom reverb with 7 echoes and exponential decay
- **ADSR Envelope:** Attack (10ms), Decay (100ms), Sustain with exponential release

### Visual Features
- 3D gradient rendering for realistic key appearance
- Pressed state animations with depth effects
- Shadow effects on white keys
- Highlight effects on black keys
- Professional dark theme interface

## 📁 Project Structure

```
keyboard-piano/
├── keyboard_piano.py       # Main application file
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── .venv/                # Virtual environment (created on setup)
└── [song files].md       # Practice song collections
```

## 🎼 Song Collections

Check out the included song collections for practice:
- `easy_songs.md` - Beginner-friendly melodies
- `copilot_songs.md` - Popular songs adapted for keyboard piano
- `PIANO_PRACTICE_SONGS.md` - Additional practice pieces

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Add new songs to the collections

## 🐛 Troubleshooting

### No Sound?
If you see "Running in silent mode", install pygame:
```bash
pip install pygame
```

### Keys Not Responding?
- Make sure the OpenCV window is in focus
- Try clicking on the piano window
- Check that pynput is installed correctly

### High CPU Usage?
- This is normal due to real-time audio synthesis
- Close other applications if needed

## 🎨 Customization

You can customize the piano by modifying `keyboard_piano.py`:
- **Change key colors** - Edit the RGB values in `PianoKey.draw()`
- **Adjust reverb** - Modify parameters in `add_reverb()`
- **Add more notes** - Extend the `notes_data` list in `setup_piano()`
- **Customize sound** - Adjust harmonics in `generate_sounds()`

## 🙏 Acknowledgments

- Piano sound synthesis inspired by physical modeling techniques
- Reverb algorithm based on FIR filter principles
- Built with Python and open-source libraries

---

**Enjoy playing! 🎹🎵**
