import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject


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


if __name__ == '__main__':
    # Initialize GStreamer
    Gst.init(sys.argv)
    
    # Define gstreamer command pipeline
    pipeline_command = "videotestsrc pattern=18 ! autovideosink"
    
    # Create pipeline via parse_launch
    pipeline = Gst.parse_launch(pipeline_command)
    
    # Allow bus to emit messages to main thread
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    
    
    # Start pipeline
    pipeline.set_state(Gst.State.PLAYING)
    loop = GObject.MainLoop()
    
    # Add handler to specific signal
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
    
