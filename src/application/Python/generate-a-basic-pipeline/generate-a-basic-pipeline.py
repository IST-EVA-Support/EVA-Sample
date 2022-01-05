import sys
import traceback
import threading
from queue import Queue
import numpy
import cv2
import gi
gi.require_version('Gst', '1.0')


from gi.repository import Gst, GObject, GLib


pipelineOutputQueue = Queue()


def extract_data(sample):
    buf = sample.get_buffer()
    caps = sample.get_caps()
    
    # ref: get some basic information
    # print(caps.get_structure(0).get_value('format'))
    # print(caps.get_structure(0).get_value('height'))
    # print(caps.get_structure(0).get_value('width'))
    # print(buf.get_size())

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
    pipelineOutputQueue.put(arr.copy())
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
    
    ## element: autovideosink
    sink = Gst.ElementFactory.make("autovideosink", "sink")
    
    # Create the empty pipeline
    pipeline = Gst.Pipeline().new("test-pipeline")
    
    # Build the pipeline
    pipeline_elements = [src, sink]
    establish_pipeline(pipeline, pipeline_elements)

    # Modify the source's properties
    src.set_property("pattern", 18)

    # Start pipeline
    pipeline.set_state(Gst.State.PLAYING)
    loop = GLib.MainLoop()
    
    # Wait until error or EOS
    bus = pipeline.get_bus()
    bus.connect("message", on_message, loop)

    try:
        print("Start to run the pipeline.\n")
        loop.run()
    except Exception:
        traceback.print_exc()
        loop.quit()

    # Stop Pipeline
    pipeline.set_state(Gst.State.NULL)
    del pipeline
    print('pipeline stopped.\n')
    

