# SmartErgo

### AI-Assisted Ergonomic Coach for Healthier Computer-Use Habits

SmartErgo is an AI-assisted ergonomic wellness application designed for students, professionals, programmers, gamers, and other computer users. It uses real-time posture monitoring and mouse-interaction tracking to increase awareness of computer-use habits and encourage movement breaks and simple exercises.

## Features

- **Real-Time Posture Monitoring** — Uses a webcam with MediaPipe and OpenCV to track body landmarks and monitor posture changes.
- **Personalized Calibration** — Performs a 10-second calibration and compares posture with the user's own starting position.
- **Mouse Activity Monitoring** — Tracks clicks, mouse movement, and continuous activity.
- **Movement & Screen-Break Reminders** — Encourages breaks during extended computer use.
- **Voice Feedback** — Provides optional spoken reminders and exercise instructions.
- **Interactive Exercise Coach** — Includes animated guidance for Shoulder Rolls, Chin Retraction, Side Stretch, Wrist & Hand Reset, Stand & Move, and Eye & Screen Break.

## How It Works

**Webcam → Body Landmark Detection → Calibration → Posture Analysis → Feedback → Exercise Recommendation**

SmartErgo uses MediaPipe Pose to detect body landmarks from webcam video. After calibration, the application compares the user's current shoulder, head, and torso positions with their personalized baseline.

Mouse activity is monitored at the same time. Based on posture changes, mouse activity, and computer-use duration, SmartErgo can provide feedback and recommend an appropriate movement or exercise.

## Technologies Used

- **Python**
- **MediaPipe Pose** — Body landmark detection
- **OpenCV** — Webcam processing, interface, and exercise animations
- **NumPy** — Numerical operations
- **pynput** — Mouse activity monitoring
- **pyttsx3** — Voice feedback

## Installation

### 1. Clone the repository

```bash id="tcnz6p"
git clone https://github.com/YOUR-USERNAME/SmartErgo.git
cd SmartErgo
```

### 2. Create a virtual environment

```bash id="b6z91a"
python -m venv smartergo_env
```

### 3. Activate the environment

**Windows**

```bash id="xgr0bv"
smartergo_env\Scripts\activate
```

**macOS/Linux**

```bash id="8frypi"
source smartergo_env/bin/activate
```

### 4. Install dependencies

```bash id="k88wyh"
pip install -r requirements.txt
```

## Run SmartErgo

```bash id="9m2ngv"
python smartergo.py
```

Allow webcam access when requested.

SmartErgo will begin with a **10-second calibration**. Sit comfortably, face forward, and keep your head and both shoulders visible.

After calibration, SmartErgo begins posture and mouse-interaction monitoring.

## Using the Exercise Coach

Click **EXERCISES** to open the exercise library and select an exercise.

SmartErgo can also recommend an exercise based on the activity detected during the session.

### Keyboard Controls

| Key | Action |
|---|---|
| **S** | Voice ON/OFF |
| **X** | Open/close exercises |
| **E** | Start recommended exercise |
| **1–6** | Select an exercise |
| **Space** | Finish exercise |
| **R** | Reset session |
| **Q** | Quit SmartErgo |

## AI Use

SmartErgo uses MediaPipe Pose for computer-vision-based body landmark detection. ChatGPT was also used as a learning and troubleshooting resource during development. AI suggestions were reviewed, modified, tested, and integrated as appropriate by the developer.

## Developer

**Harsith Sundara Pandiyan**  
Grade 11  
Solon High School, Solon, Ohio

## Disclaimer

SmartErgo is an educational wellness-awareness project and is not a medical device. It is not intended to diagnose, treat, prevent, or provide medical advice regarding any health condition.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
