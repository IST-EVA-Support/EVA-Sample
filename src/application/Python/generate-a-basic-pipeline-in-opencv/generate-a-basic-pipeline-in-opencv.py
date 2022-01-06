#*******************************************************************************************************************************
#Required know in advance gstreamer plugin: appsink/appsrc
#This sample shows how to generate a simple pipeline using OpenCV Wrapper:VideoCapture and retrieve the video data in application.
#After retrieve the video data, use OpenCV Wrapper:VideoWriter to push the video data back to another pipeline.
#This sample illustrates the appsink with VideoCapture and appsrc with VideoWriter.
#OpenCV provide this Wrapper for gstreamer user to quick establish the pipeline, but this build feature is disabled when build the
#OpenCV. If user is going to use OpenCV wrapper for gstreamer, this build feature is required enabled in configuring before the 
#OpenCV library is build.
#*******************************************************************************************************************************

import sys
import time
import cv2

if __name__ == '__main__':
    if sys.platform == 'win32':
        cap = cv2.VideoCapture("ksvideosrc ! videoscale ! video/x-raw, width=1024, height=768 ! videoconvert ! appsink", cv2.CAP_GSTREAMER)
    elif sys.platform == 'linux':
        cap = cv2.VideoCapture("v4l2src ! videoscale ! video/x-raw, width=1024, height=768 ! videoconvert ! appsink", cv2.CAP_GSTREAMER)
    else:
        print("[VideoCapture] Do not support this system platform.");
        sys.exit()

    if cap.isOpened() == False:
        print("ERROR! Unable to open camera")
        sys.exit()

    if sys.platform == 'win32':
        writer = cv2.VideoWriter("appsrc ! videoconvert ! video/x-raw, width=640, height=480, framerate=30/1 ! clockoverlay ! videoconvert ! d3dvideosink sync=false", cv2.CAP_GSTREAMER, 0, 30, (640, 480), True)
    elif sys.platform == 'linux':
        writer = cv2.VideoWriter("appsrc ! videoconvert ! video/x-raw, width=640, height=480, framerate=30/1 ! clockoverlay ! videoconvert ! ximagesink sync=false", cv2.CAP_GSTREAMER, 0, 30, (640, 480), True)
    else:
        print("[VideoWriter] Do not support this system platform.")
        sys.exit()
        
    if writer.isOpened() == False:
        print("=ERR= can't create writer")
        sys.exit()


    while(True):
        ret, frame = cap.read()
        
        if ret == False:
            print("ERROR! blank frame grabbed")
            break
        
        resize_frame = cv2.resize(frame,(640, 480));
        writer.write(resize_frame);
        cv2.imshow('OpenCV Live in Python', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        time.sleep(0.01)

    cap.release()
    cv2.destroyAllWindows()
    

