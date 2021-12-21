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
    elif mtype == Gst.MessageType.WARNING:
        err, debug = message.parse_warning()
        print(err, debug)

    return True


def demuxer_dynamic_callback(src, pad, dst):
    if pad.get_property("template").name_template == "video_%u":
        dst_video_pad = dst.get_static_pad("sink")
        pad.link(dst_video_pad)
            

def construct_pipeline():
    print('Start establish pipeline.')
    # GStreamer init and declare the pipeline
    Gst.init(sys.argv)
    pipeline = Gst.Pipeline().new("example-pipeline")

    # Start to declare the elements - example1(line:43 to 78)
    #gst-launch-1.0 filesrc location=./face.mp4 ! qtdemux ! queue ! avdec_h264 ! videoconvert ! adrt model=facemask_tx2.engine scale=0.0039 mean="0 0 0" device=0 batch=1 ! adtranslator topology=yolov3 dims=1,24,13,13,1,24,26,26,1,24,52,52 input_width=416 label=mask.txt engine-type=2 ! adlink_plugin_sample ! videoconvert ! ximagesink
    ## element: filesrc
    src = Gst.ElementFactory.make("filesrc", "src")
    src.set_property("location", "./face.mp4")
    ## element: qtdemux
    demux = Gst.ElementFactory.make("qtdemux", "demux")
    ## element: queue
    queue = Gst.ElementFactory.make("queue", "queue")
    ## element: avdec_h265
    decoder = Gst.ElementFactory.make("avdec_h264", "decoder")
    ## element: videoconvert
    convert1 = Gst.ElementFactory.make("videoconvert", "convert1")
    ## element: adrt
    adrt = Gst.ElementFactory.make("adrt", "adrt")
    adrt.set_property("model", "facemask_tx2.engine")
    adrt.set_property("scale", 0.0039)
    adrt.set_property("mean", "0 0 0")
    adrt.set_property("device", 0)
    adrt.set_property("batch", 1)
    ## element: adtranslator
    translator = Gst.ElementFactory.make("adtranslator", "translator")
    translator.set_property("topology", "yolov3")
    translator.set_property("dims", "1,24,13,13,1,24,26,26,1,24,52,52")
    translator.set_property("input_width", 416)
    translator.set_property("label", "mask.txt")
    translator.set_property("engine-type", 2)
    ## element: adlink_plugin_sample
    drawer = Gst.ElementFactory.make("adlink_plugin_sample", "drawer")
    ## element: videoconvert
    convert2 = Gst.ElementFactory.make("videoconvert", "convert2")
    ## element: ximagesink
    sink = Gst.ElementFactory.make("ximagesink", "sink")
    
    ### elements
    pipeline_elements = [src, demux, queue, decoder, convert1, adrt, translator, drawer, convert2, sink]
    
    ## Start to declare the elements - example 2(line:80 to 111)
    ##gst-launch-1.0 v4l2src ! videoconvert ! video/x-raw, width=640, height=480, format=BGR ! adrt model=facemask_tx2.engine scale=0.0039 mean="0 0 0" device=0 batch=1 ! adtranslator topology=yolov3 dims=1,24,13,13,1,24,26,26,1,24,52,52 input_width=416 label=mask.txt engine-type=2 ! adlink_plugin_sample ! videoconvert ! ximagesink
    ### element: v4l2src
    #src = Gst.ElementFactory.make("v4l2src", "src")
    ### element: videoconvert
    #convert1 = Gst.ElementFactory.make("videoconvert", "convert1")
    ### element: capsfilter
    #filtercaps = Gst.ElementFactory.make("capsfilter", "filtercaps")
    #filtercaps.set_property("caps", Gst.Caps.from_string("video/x-raw, format=BGR, width=640, height=480"))
    ### element: adrt
    #adrt = Gst.ElementFactory.make("adrt", "adrt")
    #adrt.set_property("model", "facemask_tx2.engine")
    #adrt.set_property("scale", 0.0039)
    #adrt.set_property("mean", "0 0 0")
    #adrt.set_property("device", 0)
    #adrt.set_property("batch", 1)
    ### element: adtranslator
    #translator = Gst.ElementFactory.make("adtranslator", "translator")
    #translator.set_property("topology", "yolov3")
    #translator.set_property("dims", "1,24,13,13,1,24,26,26,1,24,52,52")
    #translator.set_property("input_width", 416)
    #translator.set_property("label", "mask.txt")
    #translator.set_property("engine-type", 2)
    ### element: adlink_plugin_sample
    #drawer = Gst.ElementFactory.make("adlink_plugin_sample", "drawer")
    ### element: videoconvert
    #convert2 = Gst.ElementFactory.make("videoconvert", "convert2")
    ### element: ximagesink
    #sink = Gst.ElementFactory.make("ximagesink", "sink")
    
    #### elements
    #pipeline_elements = [src, convert1, filtercaps, adrt, translator, drawer, convert2, sink]

    add_pipeline(pipeline, pipeline_elements)
    link_element(pipeline, pipeline_elements)

    bus = pipeline.get_bus()

    # allow bus to emit messages to main thread
    bus.add_signal_watch()

    # Start pipeline
    pipeline.set_state(Gst.State.PLAYING)

    loop = GLib.MainLoop()

    bus.connect("message", on_message, loop)

    try:
        print("Start to run the pipeline.")
        loop.run()
    except Exception:
        traceback.print_exc()
        loop.quit()

    # Stop Pipeline
    pipeline.set_state(Gst.State.NULL)
    del pipeline
    print('pipeline stopped.')


def add_pipeline(pipeline, pipeline_elements):
    ## Add elements in pipeline.
    for element in pipeline_elements:
        pipeline.add(element)


def link_element(pipeline, pipeline_elements):
    ## Link element one by one.
    for i in range(len(pipeline_elements) - 1):
        if pipeline_elements[i].name != "demux":
            pipeline_elements[i].link(pipeline_elements[i + 1])
        else:
            if i+1 < len(pipeline_elements) - 1:
                pipeline_elements[i].connect("pad-added", demuxer_dynamic_callback, pipeline_elements[i+1])


if __name__ == '__main__':
    construct_pipeline()

