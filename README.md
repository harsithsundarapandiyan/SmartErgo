# SmartErgo

**AI-Assisted Ergonomic Wellness App for Healthier Computer-Use Habits**

SmartErgo is an AI-assisted ergonomic coach designed for students, professionals, programmers, gamers, and other computer users. It helps users become more aware of their posture and computer-use patterns, encourages timely movement breaks, and provides simple guided exercises to promote healthier screen-time habits.

## Features

### Real-Time Posture Monitoring
SmartErgo uses the computer's webcam to monitor posture in real time. MediaPipe detects body landmarks, and the application uses these landmarks to evaluate posture and identify patterns such as slouching.

### Posture Feedback
The application provides real-time feedback when it detects posture that may need correction, helping users become more aware of how they sit while using a computer.

### Mouse Activity Monitoring
SmartErgo monitors mouse interaction as an additional measure of computer activity. This helps the application recognize periods of continuous computer use.

### Movement Break Reminders
The application encourages users to take short movement breaks during extended computer sessions.

### Voice Feedback
SmartErgo provides optional voice alerts and reminders so that users can receive feedback without continuously watching the application screen.

### Interactive Exercise Coach
The built-in exercise coach guides users through simple stretches and movements designed for breaks during computer use.

## How It Works

SmartErgo combines webcam-based posture monitoring with computer-interaction tracking.

The basic workflow is:

**Webcam → Body Landmark Detection → Posture Analysis → Feedback**

1. The webcam captures the user's posture.
2. MediaPipe detects body landmarks in real time.
3. SmartErgo calculates posture-related measurements using the detected landmarks.
4. The application evaluates these measurements using its posture-analysis logic.
5. Mouse activity is monitored to provide additional information about computer interaction.
6. SmartErgo provides visual and/or voice feedback when appropriate.
7. The exercise coach provides guided movements and stretches during breaks.

## Technologies Used

- **Python** — Core application development
- **MediaPipe** — Body landmark detection
- **OpenCV** — Webcam capture and image processing
- **Streamlit** — Application interface
- **pynput** — Mouse activity monitoring
- **Text-to-Speech** — Voice feedback and reminders

## Requirements

SmartErgo requires:

- Python
- A computer with a webcam
- Webcam permission enabled
- Required Python packages listed in `requirements.txt`

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/SmartErgo.git
cd SmartErgo
```

### 2. Create a Virtual Environment

```bash
python -m venv smartergo_env
```

### 3. Activate the Virtual Environment

**Windows**

```bash
smartergo_env\Scripts\activate
```

**macOS/Linux**

```bash
source smartergo_env/bin/activate
```

### 4. Install Required Packages

```bash
pip install -r requirements.txt
```

## Running SmartErgo

Run the application with:

```bash
streamlit run smartergo.py
```

Replace `smartergo.py` with the actual name of the main SmartErgo Python file if it is different.

When the application opens:

1. Allow webcam access when requested.
2. Position yourself so that your upper body is visible to the webcam.
3. Start posture monitoring.
4. SmartErgo will analyze posture and display feedback.
5. Enable voice feedback if desired.
6. Use the exercise coach to follow guided movements and stretches.
7. Monitor computer-use and mouse-activity feedback during the session.

## Privacy

SmartErgo uses webcam input for real-time posture analysis. It is designed to process posture information during use rather than function as a video-recording application.

Users should enable the appropriate webcam and system permissions before starting SmartErgo.

## AI Use

ChatGPT was used as a learning and troubleshooting resource during development, including assistance with understanding programming errors, library compatibility, and debugging. AI-generated suggestions were reviewed, modified, tested, and integrated as appropriate by the developer.

SmartErgo uses MediaPipe for real-time body landmark detection. The application's posture evaluation, feature integration, interface, mouse monitoring, feedback system, and exercise-coach workflow were implemented and tested as part of the SmartErgo project.

## Developer

**Harsith Sundara Pandiyan**  
Grade 11  
Solon High School  
Solon, Ohio

## Disclaimer

SmartErgo is an educational wellness-awareness application. It is not a medical device and is not intended to diagnose, treat, or prevent any medical condition or replace professional medical advice.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
