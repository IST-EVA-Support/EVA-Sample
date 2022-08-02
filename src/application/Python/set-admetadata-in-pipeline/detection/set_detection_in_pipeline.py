## **
## Demo senario: appsrc ! drawer ! videoconvert ! ximagesink
## 
## This example only show how to feed frame data to appsrc and set object detections to adlink metadata.
## So this example does not deal with any other detail concern about snchronize or other tasks.
## Only show how to set the adlink metdata through appsrc for user who is interested with them.
## **
import sys
import time
import numpy
import random
import threading

# Required to import to set ADLINK inference metadata
import gst_admeta as admeta

import cv2
import gi
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GObject, GLib
from queue import Queue

grabBuffer = Queue()
num_frames = 0

def need_data(src, length) -> Gst.FlowReturn:
    # wait for image data vector, grabVec, is not full
    while True:
        time.sleep(0.001)
        if grabBuffer.qsize() > 0:
            break
    
    global num_frames
    if grabBuffer.qsize() > 0:
        # get image data from vector
        buf = Gst.Buffer.new_allocate(None, length, None)
        buf.fill(0, grabBuffer.get().tostring())
        
        # set buffer timestamp
        buf.duration = 1/ 30 * Gst.SECOND
        buf.pts = buf.dts = int(num_frames * buf.duration)
        buf.offset = num_frames * buf.duration
        num_frames += 1

        # create random object detection
        random_box = []
        labels = ['water bottle', 'camera', 'chair', 'person', 'slipper']
        i = random.randrange(0, 5)
        obj_id = i
        obj_label = labels[i]
        prob = random.uniform(0, 1)
        x1 = random.randrange(1, 4)/10	# 0.1~0.3
        x2 = random.randrange(7, 10)/10	# 0.7~0.9
        y1 = random.randrange(1, 4)/10	# 0.1~0.3
        y2 = random.randrange(7, 10)/10	# 0.7~0.9
        random_box.append(admeta._DetectionBox(obj_id, obj_label, 0, '', x1, y1, x2, y2, prob, ''))

        pad_list = src.get_pad_template_list()
        pad = Gst.Element.get_static_pad(src, pad_list[0].name_template)
        admeta.set_detection_box(buf, pad, random_box)

        # push buffer to appsrc
        retval = src.emit('push-buffer', buf)

        if retval != Gst.FlowReturn.OK:
            print("retval = ", retval)

        time.sleep(0.01)

def enough_data(src, size, length) -> Gst.FlowReturn:
    return Gst.FlowReturn.OK

def on_message(bus: Gst.Bus, message: Gst.Message, loop: GObject.MainLoop):
    mtype = message.type
    
    if mtype == Gst.MessageType.EOS:
        print("End of stream")
        loop.quit()
    elif mtype == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print("Gst.MessageType.ERROR catched in on_message:")
        print(err, debug)
        loop.quit()
    elif mtype == Gst.MessageType.ANY:
        err, debug = message.parse_warning()
        print(err, debug)

    return True

def establish_pipeline(pipeline, pipeline_elements):
    ## Add elements in pipeline.
    for element in pipeline_elements:
        pipeline.add(element)
    ## Link element one by one.
    for i in range(len(pipeline_elements) - 1):
        pipeline_elements[i].link(pipeline_elements[i + 1])

def establish_thread_pipeline():

    print('Start establish thread pipeline.')

    # Initialize GStreamer
    Gst.init(sys.argv)

    # Create the elements
    ## element: appsrc
    src = Gst.ElementFactory.make("appsrc", "src")
    caps = Gst.caps_from_string("video/x-raw,format=BGR,width=640,height=480,framerate=30/1")
    src.set_property('caps', caps)
    src.set_property('blocksize', 640*480*3)
    src.set_property('emit-signals', True)
    src.connect('need-data', need_data)
    src.connect('enough-data', enough_data)
    
    ## element: admetadrawer
    drawer = Gst.ElementFactory.make("admetadrawer", "drawer")

    ## element: videoconvert
    videoconvert = Gst.ElementFactory.make("videoconvert", "videoconvert")

    ## element: ximagesink
    sink = Gst.ElementFactory.make("ximagesink", "sink")
    
    # Create the empty pipeline
    pipeline = Gst.Pipeline().new("test-pipeline")
    
    # Build the pipeline
    pipeline_elements = [src, drawer, videoconvert, sink]
    establish_pipeline(pipeline, pipeline_elements)

    # Start pipeline
    pipeline.set_state(Gst.State.PLAYING)
    loop = GLib.MainLoop()

    # Wait until error or EOS
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", on_message, loop)

    try:
        print("Start to run the pipeline in thread.\n")
        loop.run()
    except Exception:
        traceback.print_exc()
        loop.quit()

    # Stop Pipeline
    pipeline.set_state(Gst.State.NULL)
    del pipeline
    print('pipeline stopped.\n')

if __name__ == '__main__':

    pipthread = threading.Thread(target=establish_thread_pipeline)
    pipthread.daemon = True

    if sys.platform == 'win32' or sys.platform == 'linux':
        cap = cv2.VideoCapture("videotestsrc ! video/x-raw, width=640, height=480, framerate=30/1 ! videoconvert ! appsink", cv2.CAP_GSTREAMER)
    else:
        print("[VideoCapture] Do not support this system platform.")
        sys.exit()

    if cap.isOpened() == False:
        print("ERROR! Unable to open camera")
        sys.exit()
      
    pipthread.start()
    while(True):
        ret, frame = cap.read()
        
        # push the image data to vector for the pipeline created in thread as a data provider
        grabBuffer.put(frame)
        
        time.sleep(0.05)

    cap.release()
    cv2.destroyAllWindows()

    pipthread.join()
    print('main thread end.\n')

