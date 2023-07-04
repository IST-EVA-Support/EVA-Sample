## **
## Demo senario: 
## gst-launch-1.0 videotestsrc ! video/x-raw, format=BGR, width=320, height=240, framerate=30/1 ! videoconvert ! detection_sample ! appsink

## This example only show how to get adlink metadata from appsink.
## So this example does not deal with any other detail concern about snchronize or other tasks.
## Only show how to retrieve the adlink metdata for user who is interested with them.
## **
import sys
import time
import numpy

# Required to import to get ADLINK inference metadata
import adroi

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
    #cv2.imwrite("a.bmp", arr.copy())
    
    # get detection inference result
    qrs = adroi.gst_buffer_adroi_query(hash(sample.get_buffer()), '//sample-engine')
    if qrs is None or len(qrs) == 0:
        print("query is empty from frame meta in get classification.")
        return self.srcpad.push(buff)
    
    for roi in qrs[0].rois:
        if roi.category == 'box':
            box = roi.to_box()
            x1, y1, x2, y2 = box.x1, box.y1, box.x2, box.y2
            labelInfo = box.datas[0].to_classification()
            print('Detection result: prob={:.3f}, coordinate=({:.2f},{:.2f}) to ({:.2f},{:.2f})), Index = {}, Label = {}'.format(labelInfo.confidence, x1, y1, x2, y2, labelInfo.label_id, labelInfo.label))
            
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
    
    ## element: detection_sample
    set_object = Gst.ElementFactory.make("detection_sample", "detection_sample")
    
    ## element: appsink
    sink = Gst.ElementFactory.make("appsink", "sink")
    sink.set_property('emit-signals', True)
    sink.connect('new-sample', new_sample, None)
    
    # Create the empty pipeline
    pipeline = Gst.Pipeline().new("test-pipeline")
    
    # Build the pipeline
    pipeline_elements = [src, filtercaps, videoconvert, set_object, sink]
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
    

