import sys
import traceback
import threading
from queue import Queue
import numpy
import cv2
import gi
gi.require_version('Gst', '1.0')


from gi.repository import Gst, GObject, GLib


def on_message(bus: Gst.Bus, message: Gst.Message, loop: GObject.MainLoop):
    mtype = message.type
    
    if mtype == Gst.MessageType.EOS:
        print("End of stream")
        loop.quit()

    elif mtype == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
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
        print("in exception")
        traceback.print_exc()
        loop.quit()

    # Stop Pipeline
    pipeline.set_state(Gst.State.NULL)
    del pipeline
    print('pipeline stopped.\n')
    

