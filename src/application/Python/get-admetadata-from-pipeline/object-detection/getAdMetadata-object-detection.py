## **
## Demo senario: 
## gst-launch-1.0 videotestsrc ! video/x-raw, format=BGR, width=320, height=240, framerate=30/1 ! admetadebuger type=1 id=187 class=boy prob=0.876 x1=0.1 y1=0.2 x2=0.3 y2=0.4 ! appsink

## This example only show how to get adlink metadata from appsink.
## So this example does not deal with any other detail concern about snchronize or other tasks.
## Only show how to retrieve the adlink metdata for user who is interested with them.
## **
import sys
import time
import numpy

# Required to import to get ADLINK inference metadata
import gst_admeta as admeta

import cv2
import gi
gi.require_version('Gst', '1.0')


from gi.repository import Gst, GObject


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
    
    # get image data and save as bmp file
    arr = extract_data(sample)
    cv2.imwrite("a.bmp", arr.copy())
    
    # get detection inference result
    buf = sample.get_buffer()
    boxes = admeta.get_detection_box(buf,0)
    
    with boxes as det_box :
        if det_box is not None :
            for box in det_box:                
                print('Detection result: prob={:.3f}, coordinate=({:.2f},{:.2f}) to ({:.2f},{:.2f})), Index = {}, Label = {}'.format(box.prob,box.x1,box.y1,box.x2, box.y2, box.obj_id, box.obj_label.decode("utf-8").strip()))
        else:
            print("None")
            
    time.sleep(0.01)
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


if __name__ == '__main__':
    print('Start establish pipeline.')
    # Initialize GStreamer
    Gst.init(sys.argv)
    
    # Create the elements
    ## element: videotesetsrc
    src = Gst.ElementFactory.make("videotestsrc", "src")
    
    ## element: capsfilter
    filtercaps = Gst.ElementFactory.make("capsfilter", "filtercaps")
    filtercaps.set_property("caps", Gst.Caps.from_string("video/x-raw, format=BGR, width=320, height=240"))
    
    ## element: videoconvert
    videoconvert = Gst.ElementFactory.make("videoconvert", "videoconvert")
    
    ## element: admetadebuger
    debuger = Gst.ElementFactory.make("admetadebuger", "debuger")
    debuger.set_property("type", 1)
    debuger.set_property("id", 187)
    debuger.set_property("class", "boy")
    debuger.set_property("prob", 0.876)
    debuger.set_property("x1", 0.1)
    debuger.set_property("y1", 0.2)
    debuger.set_property("x2", 0.3)
    debuger.set_property("y2", 0.4)
    
    ## element: appsink
    sink = Gst.ElementFactory.make("appsink", "sink")
    sink.set_property('emit-signals', True)
    sink.connect('new-sample', new_sample, None)
    
    # Create the empty pipeline
    pipeline = Gst.Pipeline().new("test-pipeline")
    
    # Build the pipeline
    pipeline_elements = [src, filtercaps, videoconvert, debuger, sink]
    establish_pipeline(pipeline, pipeline_elements)

    # Start pipeline
    pipeline.set_state(Gst.State.PLAYING)
    loop = GObject.MainLoop()
    
    # Wait until error or EOS
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", on_message, loop)

    try:
        print("Start to run the pipeline.\n")
        loop.run()
    except Exception:
        print("in exception")
        traceback.print_exc()
        loop.quit()

    # Stop Pipeline
    pipeline.set_state(Gst.State.NULL)
    del pipeline
    print('pipeline stopped.\n')
    

