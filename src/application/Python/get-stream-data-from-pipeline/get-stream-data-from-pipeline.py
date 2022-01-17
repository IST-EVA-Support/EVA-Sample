# **
# Demo senario: appsrc ! clockoverlay ! videoconvert ! appsink
# This example only show how to feed frame data to appsrc and get the frame data from appsink.
# So this example does not deal with any other detail concern about snchronize or other tasks.
# Only show how to use the appsink and appsrc for user who is interested with them.
# **

import sys
import time
import traceback
import threading
from queue import Queue
import numpy
import cv2
import gi
gi.require_version('Gst', '1.0')


from gi.repository import Gst, GObject, GLib

grabVec = Queue()
pipeLineOutputVec = Queue()
num_frames = 0

def need_data(src, length) -> Gst.FlowReturn:
    # wait for image data vector, grabVec, is not full
    while True:
        time.sleep(0.001)
        if grabVec.qsize() > 0:
            break
    
    global num_frames
    if grabVec.qsize() > 0:
        # get image data from vector
        buf = Gst.Buffer.new_allocate(None, length, None)
        buf.fill(0, grabVec.get().tostring())
        
        # set buffer timestamp
        buf.duration = 1/ 30 * Gst.SECOND
        buf.pts = buf.dts = int(num_frames * buf.duration)
        buf.offset = num_frames * buf.duration
        num_frames += 1
        
        # push buffer to sppsrc
        retval = src.emit('push-buffer', buf)
        if retval != Gst.FlowReturn.OK:
            print("retval = ", retval)
            
        time.sleep(0.01)


def enough_data(src, size, length) -> Gst.FlowReturn:
    return Gst.FlowReturn.OK


def extract_data(sample):
    buf = sample.get_buffer()
    caps = sample.get_caps()
    
    # ref: get some basic information
    #print(caps.get_structure(0).get_value('format'))
    #print(caps.get_structure(0).get_value('height'))
    #print(caps.get_structure(0).get_value('width'))
    #print(buf.get_size())

    arr = numpy.ndarray(
        (caps.get_structure(0).get_value('height'),
         caps.get_structure(0).get_value('width'),
         3),
        buffer=buf.extract_dup(0, buf.get_size()),
        dtype=numpy.uint8)
    return arr

def new_sample(sink, data) -> Gst.FlowReturn:
    sample = sink.emit('pull-sample')
    arr = extract_data(sample)
    pipeLineOutputVec.put(arr.copy())
    time.sleep(0.01)
    return Gst.FlowReturn.OK


def on_message(bus: Gst.Bus, message: Gst.Message, loop: GObject.MainLoop):
    mtype = message.type

    if mtype == Gst.MessageType.EOS:
        print("End of stream")
        loop.quit()

    elif mtype == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print(err, debug)
        loop.quit()
    elif mtype == Gst.MessageType.WARNING:
        err, debug = message.parse_warning()
        print(err, debug)

    return True


def establish_thread_pipeline():
    print('Start establish pipeline in thread.')
    # GStreamer init and declare the pipeline
    Gst.init(sys.argv)
    pipeline = Gst.Pipeline().new("example-pipeline")

    # Start to declare the elements
    ## element: appsrc
    src = Gst.ElementFactory.make("appsrc", "src")
    caps = Gst.caps_from_string("video/x-raw,format=BGR,width=640,height=480,framerate=30/1")
    src.set_property('caps', caps)
    src.set_property('blocksize', 640*480*3)
    src.connect('need-data', need_data)
    src.connect('enough-data', enough_data)
    ## element: clockoverlay
    clockoverlay = Gst.ElementFactory.make("clockoverlay", "clockoverlay")
    ## element: videoconvert
    videoconvert = Gst.ElementFactory.make("videoconvert", "videoconvert")
    ## element: appsink
    sink = Gst.ElementFactory.make("appsink", "sink")
    sink.set_property('emit-signals', True)
    sink.connect('new-sample', new_sample, None)
    ### elements
    pipeline_elements = [src, clockoverlay, videoconvert, sink]

    establish_pipeline(pipeline, pipeline_elements)

    bus = pipeline.get_bus()

    # allow bus to emit messages to main thread
    bus.add_signal_watch()

    # Start pipeline
    pipeline.set_state(Gst.State.PLAYING)

    loop = GLib.MainLoop()

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


def establish_pipeline(pipeline, pipeline_elements):
    ## Add elements in pipeline.
    for element in pipeline_elements:
        pipeline.add(element)
    ## Link element one by one.
    for i in range(len(pipeline_elements) - 1):
        pipeline_elements[i].link(pipeline_elements[i + 1])


if __name__ == '__main__':
    pipthread = threading.Thread(target=establish_thread_pipeline)
    pipthread.daemon = True
    pipthread.start()
    
    print("run pipeline in opencv in main")

    if sys.platform == 'win32':
        cap = cv2.VideoCapture("ksvideosrc ! videoscale ! video/x-raw, width=1024, height=768 ! videoconvert ! appsink", cv2.CAP_GSTREAMER)
    elif sys.platform == 'linux':
        cap = cv2.VideoCapture("v4l2src ! videoscale ! video/x-raw, width=1024, height=768 ! videoconvert ! appsink", cv2.CAP_GSTREAMER)
    else:
        print("[VideoCapture] Do not support this system platform.")
        sys.exit()

    if cap.isOpened() == False:
        print("ERROR! Unable to open camera")
        sys.exit()

    if sys.platform == 'win32':
        writer = cv2.VideoWriter("appsrc ! videoconvert ! video/x-raw, format=BGR, width=640, height=480, framerate=30/1 ! videoconvert ! d3dvideosink sync=false", cv2.CAP_GSTREAMER, 0, 30, (640, 480), True)
    elif sys.platform == 'linux':
        writer = cv2.VideoWriter("appsrc ! videoconvert ! video/x-raw, format=BGR, width=640, height=480, framerate=30/1 ! videoconvert ! ximagesink sync=false", cv2.CAP_GSTREAMER, 0, 30,(640, 480), True)
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
        
        # you can do your logic here. Assume you are going to resize the image.
        resize_frame = cv2.resize(frame,(640, 480))
        
        # write back to pipeline through OpenCV to display
        writer.write(resize_frame)
        
        # push the image data to vector for the pipeline created in thread as a data provider
        grabVec.put(resize_frame)
        
        # Save image data queued in pipeLineOutputVec from the pipeline created in thread
        if pipeLineOutputVec.qsize() > 0:
            cv2.imwrite("a.bmp", pipeLineOutputVec.get())
                
        time.sleep(0.01)

    cap.release()
    cv2.destroyAllWindows()
    
    pipthread.join()
    print('main thread end.\n')

