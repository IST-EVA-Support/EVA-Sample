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


def establish_thread_pipeline():
    print('Start establish pipeline.')
    # GStreamer init and declare the pipeline
    Gst.init(sys.argv)
    pipeline = Gst.Pipeline().new("example-pipeline")

    # Start to declare the elements
    ## element: videotesetsrc
    src = Gst.ElementFactory.make("videotestsrc", "src")
    src.set_property("pattern", 18)
    ## element: capsfilter
    filtercaps = Gst.ElementFactory.make("capsfilter", "filtercaps")
    filtercaps.set_property("caps", Gst.Caps.from_string("video/x-raw, format=BGR, width=640, height=480"))
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
    ## element: appsink - for console out to verify debuger
    dumper = Gst.ElementFactory.make("admetadumper", "dumper")
    ## element: videoconvert - for console out to verify debuger
    videoconvert = Gst.ElementFactory.make("videoconvert", "videoconvert")
    ## element: appsink
    sink = Gst.ElementFactory.make("appsink", "sink")
    sink.set_property('emit-signals', True)
    sink.connect('new-sample', new_sample, None)
    ### elements
    pipeline_elements = [src, filtercaps, debuger, dumper, videoconvert, sink]

    establish_pipeline(pipeline, pipeline_elements)

    bus = pipeline.get_bus()

    # allow bus to emit messages to main thread
    bus.add_signal_watch()

    # Start pipeline
    pipeline.set_state(Gst.State.PLAYING)

    loop = GLib.MainLoop()

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


def establish_pipeline(pipeline, pipeline_elements):
    ## Add elements in pipeline.
    for element in pipeline_elements:
        pipeline.add(element)
    ## Link element one by one.
    for i in range(len(pipeline_elements) - 1):
        pipeline_elements[i].link(pipeline_elements[i + 1])


if __name__ == '__main__':
    pipthread = threading.Thread(target=establish_thread_pipeline)
    pipthread.start()

    while True:
        if pipelineOutputQueue.qsize() > 0:
            frame = pipelineOutputQueue.get()
            cv2.imwrite("a.bmp", frame)
            
    pipthread.join()
    print('main thread end.\n')

