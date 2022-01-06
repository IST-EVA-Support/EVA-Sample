#import sys
#import traceback
#import threading
#from queue import Queue
#import numpy
import cv2
#import gi
#gi.require_version('Gst', '1.0')


#from gi.repository import Gst, GObject


# def on_message(bus: Gst.Bus, message: Gst.Message, loop: GObject.MainLoop):
    # mtype = message.type
    
    # if mtype == Gst.MessageType.EOS:
        # print("End of stream")
        # loop.quit()
    # elif mtype == Gst.MessageType.ERROR:
        # err, debug = message.parse_error()
        # print("Gst.MessageType.ERROR catched in on_message:")
        # print(err, debug)
        # loop.quit()
    # elif mtype == Gst.MessageType.ANY:
        # err, debug = message.parse_warning()
        # print(err, debug)

    # return True

# def establish_pipeline(pipeline, pipeline_elements):
    # ## Add elements in pipeline.
    # for element in pipeline_elements:
        # pipeline.add(element)
    # ## Link element one by one.
    # for i in range(len(pipeline_elements) - 1):
        # pipeline_elements[i].link(pipeline_elements[i + 1])


if __name__ == '__main__':
    print(cv2.getBuildInformation())
    # cap = cv2.VideoCapture(0)
    
    # while(True):
        # ret, frame = cap.read()

        # cv2.imshow('frame', frame)

        # if cv2.waitKey(1) & 0xFF == ord('q'):
            # break

    # cap.release()

    # cv2.destroyAllWindows()
    

