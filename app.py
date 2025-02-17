import cv2 
from flask import Flask, render_template, Response
from scipy.spatial import distance as dist
from imutils import face_utils
import numpy as np
import imutils
import dlib

app = Flask(__name__)

@app.route("/")
def index():
    """Video streaming home page."""
    return render_template("index.html")    





def gen(): 
    def eye_aspect_ratio(eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
    
        C = dist.euclidean(eye[0], eye[3])
    
        ear = (A + B) / (2.0 * C)
    
        return ear

    def final_ear(shape):
        (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
    
        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]
    
        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)
    
        ear = (leftEAR + rightEAR) / 2.0
        return (ear, leftEye, rightEye)
    
    def lip_distance(shape):
        top_lip = shape[50:53]
        top_lip = np.concatenate((top_lip, shape[61:64]))
    
        low_lip = shape[56:59]
        low_lip = np.concatenate((low_lip, shape[65:68]))
    
        top_mean = np.mean(top_lip, axis=0)
        low_mean = np.mean(low_lip, axis=0)
    
        distance = abs(top_mean[1] - low_mean[1])
        return distance

    
    EYE_AR_THRESH = 0.3
    EYE_AR_CONSEC_FRAMES = 30
    YAWN_THRESH = 20
   # alarm_status = False
    #alarm_status2 = False
    #saying = False
    COUNTER = 0
    
    print("-> Loading the predictor and detector...")
    #detector = dlib.get_frontal_face_detector()
    detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")    #Faster but less accurate
    predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
    camera = cv2.VideoCapture(0+ cv2.CAP_DSHOW)
    camera.set( cv2.CAP_PROP_FRAME_HEIGHT, 10000 )
    camera.set( cv2.CAP_PROP_FRAME_WIDTH, 10000 )

    
    while True:
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            buffer = cv2.resize(frame,(0,0),None , 1,1)
            #buffer = imutils.resize(buffer, width=450)
            gray = cv2.cvtColor(buffer, cv2.COLOR_BGR2GRAY)
        
            #rects = detector(gray, 0)
            rects = detector.detectMultiScale(gray, scaleFactor=1.1, 
        		minNeighbors=5, minSize=(30, 30),
        		flags=cv2.CASCADE_SCALE_IMAGE)
        
            #for rect in rects:
            for (x, y, w, h) in rects:
                rect = dlib.rectangle(int(x), int(y), int(x + w),int(y + h))
                
                shape = predictor(gray, rect)
                shape = face_utils.shape_to_np(shape)
        
                eye = final_ear(shape)
                ear = eye[0]
                leftEye = eye [1]
                rightEye = eye[2]
        
                distance = lip_distance(shape)
        
                leftEyeHull = cv2.convexHull(leftEye)
                rightEyeHull = cv2.convexHull(rightEye)
                cv2.drawContours(buffer, [leftEyeHull], -1, (0, 255, 0), 1)
                cv2.drawContours(buffer, [rightEyeHull], -1, (0, 255, 0), 1)
        
                lip = shape[48:60]
                cv2.drawContours(buffer, [lip], -1, (0, 255, 0), 1)
        
                if ear < EYE_AR_THRESH:
                    COUNTER += 1
        
                    if COUNTER >= EYE_AR_CONSEC_FRAMES:
                        ##if alarm_status == False:
                          #  alarm_status = True
                          #  t = Thread(target=alarm, args=('wake up sir',))
                           # t.deamon = True
                           # t.start()
        
                        cv2.putText(buffer, "DROWSINESS ALERT!", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
                else:
                    COUNTER = 0
                    #alarm_status = False
        
                if (distance > YAWN_THRESH):
                        cv2.putText(buffer, "Yawn Alert", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        #if alarm_status2 == False and saying == False:
                            #alarm_status2 = True
                           # t = Thread(target=alarm, args=('take some fresh air sir',))
                           # t.deamon = True
                           # t.start()
                else:
                    continue
                    #alarm_status2 = False
        
                cv2.putText(buffer, "EAR: {:.2f}".format(ear), (300, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(buffer, "YAWN: {:.2f}".format(distance), (300, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            frame = cv2.imencode(".jpg",buffer)[1].tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            key = cv2.waitKey(20)

            if key == 27:
                break
            
  

@app.route('/video_feed' , methods = ['GET' , 'POST'])
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
    
if __name__ == "__main__":
    app.run(debug=True)
