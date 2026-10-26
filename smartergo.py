
import cv2, mediapipe as mp, math, time, threading
from collections import deque

try:
    import pyttsx3
    VOICE_OK=True
except ImportError:
    VOICE_OK=False
try:
    from pynput import mouse
    MOUSE_OK=True
except ImportError:
    MOUSE_OK=False

CAMERA_INDEX=0
BREAK_MINUTES=25         # general movement-break interval
SCREEN_BREAK_MINUTES=30    # screen-time reminder; not an eye-strain diagnosis
CLICK_ALERT_THRESHOLD=100  # high mouse-click activity reminder
CALIBRATION_SECONDS=10
BAD_SECONDS=5
VIS=.20
SHOULDER_DELTA=5.0
HEAD_DELTA=5.0
SHIFT_DELTA=.08
TORSO_DELTA=6.0
RAPID_CLICKS=12          # clicks in 10 sec
MOUSE_STREAK=60          # testing; increase later

mp_pose=mp.solutions.pose
mp_draw=mp.solutions.drawing_utils
PL=mp_pose.PoseLandmark

EXERCISES=[
    "SHOULDER ROLLS","CHIN RETRACTION","SIDE STRETCH",
    "WRIST & HAND RESET","STAND & MOVE","EYE & SCREEN BREAK"
]
DURATION={"SHOULDER ROLLS":20,"CHIN RETRACTION":20,"SIDE STRETCH":24,
          "WRIST & HAND RESET":22,"STAND & MOVE":30,"EYE & SCREEN BREAK":20}
SHORT={
"SHOULDER ROLLS":"Slowly roll shoulders backward.",
"CHIN RETRACTION":"Eyes level; gently draw chin backward.",
"SIDE STRETCH":"Reach upward and gently alternate sides.",
"WRIST & HAND RESET":"Relax grip; move fingers and wrists gently.",
"STAND & MOVE":"Stand if comfortable and change position.",
"EYE & SCREEN BREAK":"Look away from the screen; blink and relax your eyes."
}
VOICE={
"SHOULDER ROLLS":"Shoulder rolls. Sit or stand tall. Relax your arms. Slowly lift your shoulders, roll them backward, and lower them. Keep the movement comfortable.",
"CHIN RETRACTION":"Gentle chin retraction. Keep your eyes level. Without looking down, gently draw your chin straight backward. Relax and repeat slowly.",
"SIDE STRETCH":"Gentle side stretch. Sit or stand tall. Reach one arm upward and gently lean to the opposite side. Return to center and change sides.",
"WRIST & HAND RESET":"Wrist and hand reset. Relax your grip. Extend one arm comfortably. Open and close your hand, then gently move your wrist up and down and in small circles. Switch hands.",
"STAND & MOVE":"Movement break. If comfortable, stand up, change position, take a few easy steps, and relax your shoulders.",
"EYE & SCREEN BREAK":"Screen break. Look away from the screen toward something farther away. Blink naturally, relax your face, and give your eyes a short rest."
}

# ---------------- voice ----------------
sound_on=True
voice_lock=threading.Lock()
def _say(s):
    if not VOICE_OK:return
    with voice_lock:
        try:
            e=pyttsx3.init(); e.setProperty("rate",165); e.setProperty("volume",1.0)
            e.say(s); e.runAndWait(); e.stop()
        except Exception as ex: print("Voice warning:",ex)
def speak(s):
    if VOICE_OK and sound_on:
        threading.Thread(target=_say,args=(s,),daemon=True).start()

# ---------------- mouse interaction ----------------
mlock=threading.Lock()
m={"x":None,"y":None,"distance":0.0,"clicks":0,"last_activity":None,"streak_start":None}
click_times=deque(maxlen=100)
listener=None

def activity(now):
    last=m["last_activity"]
    if last is None or now-last>2.0: m["streak_start"]=now
    m["last_activity"]=now

def on_move(x,y):
    now=time.time()
    with mlock:
        if m["x"] is not None:
            d=math.hypot(x-m["x"],y-m["y"])
            if d<5000:m["distance"]+=d
        m["x"],m["y"]=x,y; activity(now)

def on_click(x,y,button,pressed):
    if not pressed:return
    now=time.time()
    with mlock:
        m["clicks"]+=1; click_times.append(now); activity(now)

def mouse_snapshot():
    now=time.time()
    with mlock:
        while click_times and now-click_times[0]>10:click_times.popleft()
        streak=0
        if m["last_activity"] and m["streak_start"] and now-m["last_activity"]<=2:
            streak=now-m["streak_start"]
        return dict(clicks=m["clicks"],recent=len(click_times),
                    distance=m["distance"],streak=streak)

def reset_mouse():
    with mlock:
        m["distance"]=0;m["clicks"]=0;m["streak_start"]=None
        click_times.clear()

if MOUSE_OK:
    try:
        listener=mouse.Listener(on_move=on_move,on_click=on_click)
        listener.daemon=True;listener.start()
    except Exception as ex: print("Mouse warning:",ex)

# ---------------- helpers ----------------
def txt(f,s,x,y,sc=.48,c=(255,255,255),t=1):
    cv2.putText(f,s,(x,y),cv2.FONT_HERSHEY_SIMPLEX,sc,c,t,cv2.LINE_AA)
def xy(lm,p,w,h):
    q=lm[p.value];return int(q.x*w),int(q.y*h)
def vis(lm,p):return lm[p.value].visibility>=VIS
def mid(a,b):return ((a[0]+b[0])//2,(a[1]+b[1])//2)
def hang(a,b):
    z=math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
    if z>90:z-=180
    if z<-90:z+=180
    return z
def vang(a,b):return math.degrees(math.atan2(b[0]-a[0],b[1]-a[1]))
def avg(v):return sum(v)/len(v) if v else 0
def inside(x,y,r):return r[0]<=x<=r[2] and r[1]<=y<=r[3]

def camera():
    for name,b in [("DirectShow",cv2.CAP_DSHOW),("Default",None),("MSMF",cv2.CAP_MSMF)]:
        print("Trying camera",CAMERA_INDEX,"with",name)
        c=cv2.VideoCapture(CAMERA_INDEX) if b is None else cv2.VideoCapture(CAMERA_INDEX,b)
        if not c.isOpened():c.release();continue
        c.set(cv2.CAP_PROP_FRAME_WIDTH,640);c.set(cv2.CAP_PROP_FRAME_HEIGHT,480);time.sleep(.8)
        for _ in range(25):
            ok,f=c.read()
            if ok and f is not None and f.mean()>1:
                print("Camera ready:",name);return c
            time.sleep(.03)
        c.release()
    return None

# ---------------- recommendation ----------------
def recommend(hist,ms,screen_due=False):
    if screen_due:
        return "EYE & SCREEN BREAK"
    if ms["clicks"]>=CLICK_ALERT_THRESHOLD or ms["recent"]>=RAPID_CLICKS or ms["streak"]>=MOUSE_STREAK:
        return "WRIST & HAND RESET"
    if not hist:return "STAND & MOVE"
    a=sum(x["s"] for x in hist);b=sum(x["h"] for x in hist);c=sum(x["t"] for x in hist)
    if a>=b and a>=c and a:return "SHOULDER ROLLS"
    if b>=c and b:return "CHIN RETRACTION"
    if c:return "SIDE STRETCH"
    return "STAND & MOVE"

# ---------------- exercise animation ----------------
def _limb(f,a,b,width=16,color=(80,180,255)):
    cv2.line(f,a,b,color,width,cv2.LINE_AA)
    cv2.circle(f,a,max(5,width//2),color,-1,cv2.LINE_AA)
    cv2.circle(f,b,max(5,width//2),color,-1,cv2.LINE_AA)

def _head(f,c):
    x,y=c
    cv2.circle(f,(x,y),32,(50,55,70),-1,cv2.LINE_AA)
    cv2.ellipse(f,(x,y+4),(27,29),0,0,360,(190,220,245),-1,cv2.LINE_AA)
    cv2.circle(f,(x-9,y),3,(35,40,50),-1,cv2.LINE_AA)
    cv2.circle(f,(x+9,y),3,(35,40,50),-1,cv2.LINE_AA)
    cv2.ellipse(f,(x,y+12),(9,5),0,10,170,(60,65,75),2,cv2.LINE_AA)

def _torso(f,shoulder,hip):
    import numpy as np
    sx,sy=shoulder;hx,hy=hip
    pts=np.array([(sx-40,sy),(sx+40,sy),(hx+30,hy),(hx-30,hy)],dtype="int32")
    cv2.fillConvexPoly(f,pts,(65,125,230),cv2.LINE_AA)
    cv2.polylines(f,[pts],True,(235,235,245),2,cv2.LINE_AA)

def _arrow(f,a,b):
    cv2.arrowedLine(f,a,b,(0,255,255),3,cv2.LINE_AA,tipLength=.22)

def animate(f,name,elapsed):
    h,w=f.shape[:2]
    dur=DURATION[name]
    phase=math.sin(elapsed*2.4)
    slow=math.sin(elapsed*1.35)

    # Dedicated exercise screen
    f[:]=(24,27,34)
    cv2.rectangle(f,(0,0),(w,103),(12,14,19),-1)

    txt(f,"SMARTERGO COACH",22,31,.68,(0,255,255),2)
    txt(f,name,22,62,.62,(255,255,255),2)
    txt(f,SHORT[name],22,88,.42,(190,220,235))

    progress=min(1.0,elapsed/max(dur,.001))
    cv2.rectangle(f,(22,112),(w-22,126),(75,80,90),-1)
    cv2.rectangle(f,(22,112),(22+int((w-44)*progress),126),(0,220,180),-1)

    cx=w//2
    base=h-73
    hip=(cx,base-92)
    shoulder=(cx,base-202)
    head=(cx,base-257)

    if name=="SIDE STRETCH":
        lean=int(27*slow)
        shoulder=(cx+lean,base-202)
        head=(cx+lean,base-257)

    if name=="STAND & MOVE":
        bounce=int(5*abs(phase))
        hip=(cx,base-92-bounce)
        shoulder=(cx,base-202-bounce)
        head=(cx,base-257-bounce)

    cv2.ellipse(f,(cx,base+7),(82,13),0,0,360,(12,14,18),-1,cv2.LINE_AA)

    lk=(cx-28,base-45)
    rk=(cx+28,base-45)
    lf=(cx-44,base)
    rf=(cx+44,base)

    _limb(f,hip,lk,18,(75,85,120))
    _limb(f,lk,lf,17,(75,85,120))
    _limb(f,hip,rk,18,(75,85,120))
    _limb(f,rk,rf,17,(75,85,120))

    _torso(f,shoulder,hip)

    sx,sy=shoulder
    ls=(sx-39,sy+4)
    rs=(sx+39,sy+4)

    if name=="SHOULDER ROLLS":
        lift=int(12*phase)
        l=(ls[0],ls[1]-lift)
        r=(rs[0],rs[1]-lift)
        le=(cx-72,sy+55)
        re=(cx+72,sy+55)
        _limb(f,l,le);_limb(f,le,(cx-61,sy+108),14)
        _limb(f,r,re);_limb(f,re,(cx+61,sy+108),14)
        cv2.ellipse(f,ls,(31,22),0,20,330,(0,255,255),3,cv2.LINE_AA)
        cv2.ellipse(f,rs,(31,22),0,20,330,(0,255,255),3,cv2.LINE_AA)

    elif name=="CHIN RETRACTION":
        _limb(f,ls,(cx-69,sy+52))
        _limb(f,(cx-69,sy+52),(cx-58,sy+105),14)
        _limb(f,rs,(cx+69,sy+52))
        _limb(f,(cx+69,sy+52),(cx+58,sy+105),14)
        shift=int(10*((phase+1)/2))
        head=(head[0]-shift,head[1])
        _arrow(f,(head[0]+65,head[1]+12),(head[0]+32,head[1]+12))

    elif name=="SIDE STRETCH":
        side=1 if slow>=0 else -1
        raised=rs if side>0 else ls
        down=ls if side>0 else rs
        e1=(raised[0]+side*25,sy-54)
        hand1=(raised[0]+side*42,sy-111)
        e2=(down[0]-side*31,sy+49)
        hand2=(down[0]-side*44,sy+91)
        _limb(f,raised,e1);_limb(f,e1,hand1,14)
        _limb(f,down,e2);_limb(f,e2,hand2,14)
        _arrow(f,(cx-side*90,sy-30),(cx-side*120,sy-30))

    elif name=="WRIST & HAND RESET":
        _limb(f,ls,(cx-66,sy+53))
        _limb(f,(cx-66,sy+53),(cx-55,sy+104),14)
        elbow=(cx+83,sy+12)
        wrist=(cx+145,sy+12+int(9*phase))
        _limb(f,rs,elbow)
        _limb(f,elbow,wrist,14)
        cv2.circle(f,wrist,11,(0,220,180),-1,cv2.LINE_AA)
        palm=(wrist[0]+17,wrist[1])
        cv2.circle(f,palm,13,(190,220,245),-1,cv2.LINE_AA)
        for dy in (-12,-6,0,6,12):
            cv2.line(f,(palm[0]+8,palm[1]),(palm[0]+25,palm[1]+dy),
                     (190,220,245),4,cv2.LINE_AA)
        _arrow(f,(wrist[0]+5,wrist[1]-34),(wrist[0]+5,wrist[1]+31))

    elif name=="EYE & SCREEN BREAK":
        # Calm seated/standing pose with visual "look far away" cue.
        le=(cx-67,sy+52); re=(cx+67,sy+52)
        _limb(f,ls,le); _limb(f,le,(cx-52,sy+102),14)
        _limb(f,rs,re); _limb(f,re,(cx+52,sy+102),14)
        # Far-away focus symbol and blinking cue.
        target=(cx+135,head[1]-5)
        cv2.circle(f,target,20,(0,220,180),3,cv2.LINE_AA)
        cv2.circle(f,target,7,(0,220,180),-1,cv2.LINE_AA)
        _arrow(f,(head[0]+32,head[1]),(target[0]-24,target[1]))
        if phase>0:
            cv2.line(f,(head[0]-14,head[1]),(head[0]-4,head[1]),(0,255,255),2,cv2.LINE_AA)
            cv2.line(f,(head[0]+4,head[1]),(head[0]+14,head[1]),(0,255,255),2,cv2.LINE_AA)

    else:
        swing=int(30*phase)
        le=(cx-72,sy+45+swing)
        re=(cx+72,sy+45-swing)
        _limb(f,ls,le);_limb(f,le,(cx-57,sy+98+swing),14)
        _limb(f,rs,re);_limb(f,re,(cx+57,sy+98-swing),14)

    _head(f,head)

    # Small SmartErgo badge
    cv2.circle(f,(head[0]+47,head[1]-15),12,(0,220,180),-1,cv2.LINE_AA)
    txt(f,"+",head[0]+42,head[1]-10,.42,(255,255,255),2)

    remaining=max(0,math.ceil(dur-elapsed))
    txt(f,f"{remaining} sec",w-105,61,.62,(0,255,255),2)
    txt(f,"Follow the coach using a comfortable range of movement.",22,h-39,.40,(220,225,230))
    txt(f,"SPACE = Finish exercise     Q = Quit",22,h-16,.37,(165,175,185))

    return elapsed>=dur

# ---------------- clickable exercise tab ----------------
tab_rect=(0,0,0,0);cards=[];menu=False;pending=None
sound_rect=(0,0,0,0)
def draw_tab(f):
    global tab_rect,sound_rect
    h,w=f.shape[:2]
    tab_rect=(w-158,10,w-12,46)
    sound_rect=(w-298,10,w-168,46)
    cv2.rectangle(f,(sound_rect[0],sound_rect[1]),(sound_rect[2],sound_rect[3]),(40,40,40),-1)
    cv2.rectangle(f,(sound_rect[0],sound_rect[1]),(sound_rect[2],sound_rect[3]),(0,220,180) if sound_on else (120,120,120),2)
    txt(f,"SOUND ON" if sound_on else "SOUND OFF",sound_rect[0]+12,34,.43,(0,255,200) if sound_on else (190,190,190),2)
    cv2.rectangle(f,(tab_rect[0],tab_rect[1]),(tab_rect[2],tab_rect[3]),(40,40,40),-1)
    cv2.rectangle(f,(tab_rect[0],tab_rect[1]),(tab_rect[2],tab_rect[3]),(0,255,255),2)
    txt(f,"EXERCISES",tab_rect[0]+20,34,.49,(0,255,255),2)

def draw_menu(f,rec,ms):
    global cards
    h,w=f.shape[:2];cards=[]
    dark=f.copy();dark[:]=(0,0,0);f[:]=cv2.addWeighted(f,.12,dark,.88,0)
    txt(f,"SMARTERGO EXERCISE LIBRARY",20,34,.64,(0,255,255),2)
    txt(f,"Click an exercise to see animation + hear instructions.",20,59,.41)
    txt(f,"Recommended: "+rec,20,83,.45,(0,255,0),2)
    y=96
    card_h=47
    gap=4
    for i,name in enumerate(EXERCISES):
        yy=y+i*(card_h+gap)
        r=(25,yy,w-25,yy+card_h);cards.append((*r,name))
        cv2.rectangle(f,(r[0],r[1]),(r[2],r[3]),(35,35,35),-1)
        cv2.rectangle(f,(r[0],r[1]),(r[2],r[3]),(0,255,0) if name==rec else (150,150,150),2)
        txt(f,f"{i+1}. {name}",r[0]+13,r[1]+19,.44,(255,255,255),2)
        txt(f,SHORT[name],r[0]+13,r[1]+38,.33,(210,210,210))
    txt(f,f"Mouse: {ms['clicks']} clicks | {ms['recent']} clicks/10s | active {ms['streak']:.0f}s",
        20,h-38,.37,(0,255,255))
    txt(f,"X or click EXERCISES to close",20,h-16,.37,(210,210,210))
    draw_tab(f)

def ui_mouse(event,x,y,flags,param):
    global menu,pending,sound_on
    if event!=cv2.EVENT_LBUTTONDOWN:return
    if inside(x,y,sound_rect):
        sound_on=not sound_on
        print("Sound","ON" if sound_on else "OFF")
        if sound_on:speak("Sound is on.")
        return
    if inside(x,y,tab_rect):menu=not menu;return
    if menu:
        for x1,y1,x2,y2,name in cards:
            if inside(x,y,(x1,y1,x2,y2)):
                pending=name;menu=False;return

# ---------------- startup ----------------
cap=camera()
if cap is None:
    raise SystemExit("ERROR: webcam is not providing a usable visible image.")

if not VOICE_OK:
    print(r"Install voice: C:\Users\sunda\smartergo_env\Scripts\python.exe -m pip install pyttsx3")
if not MOUSE_OK:
    print(r"Install mouse: C:\Users\sunda\smartergo_env\Scripts\python.exe -m pip install pynput")

WIN="SmartErgo"
cv2.namedWindow(WIN);cv2.setMouseCallback(WIN,ui_mouse)

calibrated=False;cal_start=time.time()
cs=[];ch=[];cshift=[];ct=[]
bs=bh=bshift=0.0;bt=None
work_start=None;screen_start=None;bad_start=None
hist=deque(maxlen=1800)
exercise=False;current=None;exercise_start=None
screen_alerted=False
click_alerted=False
alert_message=""
alert_until=0

def start_ex(name):
    global exercise,current,exercise_start
    current=name;exercise_start=time.time();exercise=True
    print("Exercise:",name);speak(VOICE[name])

def finish_ex():
    global exercise,work_start,screen_start,bad_start,screen_alerted,click_alerted
    exercise=False
    work_start=time.time()
    screen_start=time.time()
    bad_start=None
    screen_alerted=False
    click_alerted=False
    hist.clear()
    reset_mouse()
    speak("Great job. Your break is complete. Returning to SmartErgo monitoring.")

print("SmartErgo ready. Click EXERCISES for the exercise library. Click SOUND ON/OFF or press S to toggle voice.")

try:
    with mp_pose.Pose(static_image_mode=False,model_complexity=1,smooth_landmarks=True,
                      min_detection_confidence=.4,min_tracking_confidence=.4) as pose:
        while True:
            ok,f=cap.read()
            if not ok or f is None:continue
            if f.mean()<=1:
                f[:]=(0,0,0);txt(f,"CAMERA IMAGE IS BLACK",30,80,.75,(0,0,255),2)
                cv2.imshow(WIN,f)
                if cv2.waitKey(1)&0xff==ord("q"):break
                continue
            f=cv2.flip(f,1);h,w=f.shape[:2]

            if pending is not None:
                chosen=pending;pending=None
                if calibrated:start_ex(chosen)

            if exercise:
                done=animate(f,current,time.time()-exercise_start)
                cv2.imshow(WIN,f);k=cv2.waitKey(1)&0xff
                if k==ord("q"):break
                if k==32 or done:finish_ex()
                continue

            res=pose.process(cv2.cvtColor(f,cv2.COLOR_BGR2RGB))
            sa=ha=hs=ta=None;lv=rv=0
            if res.pose_landmarks:
                lm=res.pose_landmarks.landmark;mp_draw.draw_landmarks(f,res.pose_landmarks,mp_pose.POSE_CONNECTIONS)
                lv=lm[PL.LEFT_SHOULDER.value].visibility;rv=lm[PL.RIGHT_SHOULDER.value].visibility
                if vis(lm,PL.LEFT_SHOULDER) and vis(lm,PL.RIGHT_SHOULDER):
                    ls=xy(lm,PL.LEFT_SHOULDER,w,h);rs=xy(lm,PL.RIGHT_SHOULDER,w,h);sm=mid(ls,rs)
                    sa=hang(ls,rs);cv2.line(f,ls,rs,(0,255,0),3)
                    if vis(lm,PL.LEFT_EAR) and vis(lm,PL.RIGHT_EAR):
                        le=xy(lm,PL.LEFT_EAR,w,h);re=xy(lm,PL.RIGHT_EAR,w,h);ha=hang(le,re);cv2.line(f,le,re,(255,255,0),2)
                    if vis(lm,PL.NOSE):
                        nose=xy(lm,PL.NOSE,w,h);sw=abs(rs[0]-ls[0])
                        if sw>1:hs=(nose[0]-sm[0])/sw
                        cv2.line(f,nose,sm,(255,0,255),2)
                    if vis(lm,PL.LEFT_HIP) and vis(lm,PL.RIGHT_HIP):
                        hm=mid(xy(lm,PL.LEFT_HIP,w,h),xy(lm,PL.RIGHT_HIP,w,h));ta=vang(sm,hm);cv2.line(f,sm,hm,(0,165,255),3)

            if not calibrated:
                elapsed=time.time()-cal_start
                if sa is not None:cs.append(sa)
                if ha is not None:ch.append(ha)
                if hs is not None:cshift.append(hs)
                if ta is not None:ct.append(ta)
                cv2.rectangle(f,(8,8),(w-8,142),(0,0,0),-1)
                txt(f,"SMARTERGO CALIBRATION",18,34,.65,(0,255,255),2)
                txt(f,f"Sit comfortably and face forward: {max(0,CALIBRATION_SECONDS-elapsed):.1f} sec",18,63,.46)
                txt(f,"Keep head and both shoulders visible. Hips optional.",18,87,.41)
                txt(f,f"Shoulder visibility L {lv:.2f} | R {rv:.2f}",18,111,.41)
                txt(f,f"Valid frames: {len(cs)}",18,135,.41);draw_tab(f)
                if elapsed>=CALIBRATION_SECONDS:
                    if len(cs)>=20:
                        bs=avg(cs);bh=avg(ch);bshift=avg(cshift);bt=avg(ct) if ct else None
                        calibrated=True
                        work_start=time.time()
                        screen_start=time.time()
                        speak("Calibration complete. SmartErgo posture and mouse interaction monitoring has started.")
                    else:cal_start=time.time()
            else:
                sb=sa is not None and abs(sa-bs)>SHOULDER_DELTA
                hb=(ha is not None and abs(ha-bh)>HEAD_DELTA) or (hs is not None and abs(hs-bshift)>SHIFT_DELTA)
                tb=ta is not None and bt is not None and abs(ta-bt)>TORSO_DELTA
                hist.append({"s":sb,"h":hb,"t":tb});bad=sb or hb or tb
                if bad:
                    if bad_start is None:bad_start=time.time()
                    badfor=time.time()-bad_start
                else:bad_start=None;badfor=0
                ms=mouse_snapshot()
                now=time.time()
                screen_elapsed=now-screen_start
                screen_due=screen_elapsed>=SCREEN_BREAK_MINUTES*60

                if screen_due and not screen_alerted:
                    screen_alerted=True
                    alert_message="SCREEN-TIME REMINDER: 30 minutes reached - take a short eye/screen break."
                    alert_until=now+8
                    print(alert_message)
                    speak("Screen time reminder. You have been using the computer for 30 minutes. Please take a short eye and screen break.")

                if ms["clicks"]>=CLICK_ALERT_THRESHOLD and not click_alerted:
                    click_alerted=True
                    alert_message=f"HIGH MOUSE ACTIVITY: {CLICK_ALERT_THRESHOLD} clicks reached - relax your hand and wrist."
                    alert_until=now+8
                    print(alert_message)
                    speak(f"High mouse activity detected. You have reached {CLICK_ALERT_THRESHOLD} clicks. Consider a short wrist and hand reset.")

                rec=recommend(hist,ms,screen_due)
                if menu:draw_menu(f,rec,ms)
                else:
                    cv2.rectangle(f,(8,8),(w-8,108),(0,0,0),-1)
                    txt(f,"SMARTERGO LIVE COACH",18,34,.62,(0,255,255),2);draw_tab(f)
                    # User-friendly posture interpretation.
                    # We describe sustained changes relative to the user's own calibrated baseline
                    # rather than medically labeling posture as "poor".
                    shoulder_changed = (sa is not None and bs is not None and abs(sa-bs) > SHOULDER_DELTA)
                    head_angle_changed = (ha is not None and bh is not None and abs(ha-bh) > HEAD_DELTA)
                    head_shift_changed = (hs is not None and bshift is not None and abs(hs-bshift) > SHIFT_DELTA)
                    torso_changed = (ta is not None and bt is not None and abs(ta-bt) > TORSO_DELTA)

                    changed_count = sum([shoulder_changed, head_angle_changed, head_shift_changed, torso_changed])

                    if bad and badfor>=BAD_SECONDS:
                        if changed_count >= 2:
                            status="POSTURE: ADJUSTMENT SUGGESTED"
                            detail="Multiple sustained changes detected."
                        elif torso_changed:
                            status="POSTURE: LEANING DETECTED"
                            detail="Consider returning toward your calibrated position."
                        elif head_shift_changed or head_angle_changed:
                            status="POSTURE: HEAD POSITION CHANGED"
                            detail="Consider adjusting toward your calibrated head position."
                        elif shoulder_changed:
                            status="POSTURE: SHOULDER ALIGNMENT CHANGED"
                            detail="Consider relaxing and realigning your shoulders."
                        else:
                            status="POSTURE: CHANGE DETECTED"
                            detail="Consider returning toward your calibrated position."
                        txt(f,status,18,62,.45,(0,165,255),2)
                        txt(f,detail,18,88,.36,(235,235,235),1)
                    elif bad:
                        txt(f,"POSTURE: NORMAL MOVEMENT",18,62,.45,(0,255,255),2)
                        txt(f,"Checking whether the change is sustained...",18,88,.36,(235,235,235),1)
                    else:
                        txt(f,"POSTURE: GOOD",18,62,.49,(0,255,0),2)
                        txt(f,"Close to your calibrated position.",18,88,.36,(220,255,220),1)
                    y=135
                    if sa is not None:txt(f,f"Shoulder tilt: {sa:+.1f} deg",18,y,.42,(0,255,0));y+=21
                    if ha is not None:txt(f,f"Head tilt: {ha:+.1f} deg",18,y,.42,(255,255,0));y+=21
                    if hs is not None:txt(f,f"Head shift: {hs:+.2f}",18,y,.42,(255,0,255));y+=21
                    if ta is not None:txt(f,f"Torso lean*: {ta:+.1f} deg",18,y,.42,(0,165,255))
                    my=h-126;cv2.rectangle(f,(8,my-22),(w-8,h-61),(0,0,0),-1)
                    txt(f,"MOUSE INTERACTION",18,my,.46,(0,255,255),2)
                    txt(f,f"Clicks {ms['clicks']} | clicks/10s {ms['recent']} | movement {ms['distance']/1000:.1f}k px",18,my+22,.37)
                    txt(f,f"Continuous activity {ms['streak']:.0f}s",18,my+43,.37)
                    mouse_heavy=ms["clicks"]>=CLICK_ALERT_THRESHOLD or ms["recent"]>=RAPID_CLICKS or ms["streak"]>=MOUSE_STREAK
                    txt(f,"Mouse pattern: "+("high activity - hand/wrist break suggested" if mouse_heavy else "normal activity"),
                        18,my+64,.34,(0,165,255) if mouse_heavy else (0,255,0),2 if mouse_heavy else 1)

                    screen_rem=max(0,SCREEN_BREAK_MINUTES*60-screen_elapsed)
                    rem=BREAK_MINUTES*60-(time.time()-work_start)

                    if time.time()<alert_until:
                        cv2.rectangle(f,(8,h-184),(w-8,h-145),(0,80,180),-1)
                        txt(f,alert_message,18,h-158,.37,(255,255,255),2)

                    if rem<=0:
                        start_ex(rec);continue

                    txt(f,f"Eye/screen break {int(screen_rem//60):02d}:{int(screen_rem%60):02d} | Next movement break {int(rem//60):02d}:{int(rem%60):02d}",18,h-34,.35)
                    txt(f,f"Recommended: {rec} | S sound | X exercises | E start | Q quit",18,h-13,.33,(210,210,210))

            cv2.imshow(WIN,f);k=cv2.waitKey(1)&0xff
            if k==ord("q"):break
            if k==ord("x"):menu=not menu
            if k==ord("s"):
                sound_on=not sound_on
                print("Sound","ON" if sound_on else "OFF")
                if sound_on:speak("Sound is on.")
            if calibrated:
                if k==ord("e"):
                    due=(time.time()-screen_start)>=SCREEN_BREAK_MINUTES*60
                    start_ex(recommend(hist,mouse_snapshot(),due))
                elif k==ord("1"):start_ex(EXERCISES[0])
                elif k==ord("2"):start_ex(EXERCISES[1])
                elif k==ord("3"):start_ex(EXERCISES[2])
                elif k==ord("4"):start_ex(EXERCISES[3])
                elif k==ord("5"):start_ex(EXERCISES[4])
                elif k==ord("6"):start_ex(EXERCISES[5])
                elif k==ord("r"):
                    work_start=time.time();screen_start=time.time();bad_start=None
                    screen_alerted=False;click_alerted=False;hist.clear();reset_mouse()
finally:
    if listener:
        try:listener.stop()
        except:pass
    cap.release();cv2.destroyAllWindows()
    print("SmartErgo closed.")
