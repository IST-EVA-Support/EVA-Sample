"""
		This is a sample python plugin with ADLINK
		In this sample, we will guide you by comment on the section with !!!ADLINK!!!
		The main task of this sample is :
		- Read inference result ( Boxes ) from adlink metadata
		- Draw the box inference result in image.
"""

import ctypes
import numpy as np

import cv2
import gst_helper
import gst_cv_helper
import gst_admeta as admeta

from gi.repository import Gst, GObject, GLib, GstVideo
#!!!ADLINK!!!
# function to draw boxes on buffer and display by ximagesink
# 	Below is the metadata structure for detection box ( can contain both box and pose , diffrentiate by 'meta' ; 'meta' is None mean box, 'pose' mean pose)
#  'obj_id' 
#  'obj_label'
#  'class_id'
#  'class_label'
#  'x1'
#  'y1'
#  'x2'
#  'y2'
#  'prob'
#  'meta'
def draw_boxs(img, boxs):
	h, w, c = img.shape
	face = cv2.FONT_HERSHEY_COMPLEX
	scale = 1.5
	thickness = 2
	baseline = 0
	for each in boxs:
		l =  each.obj_label.decode("utf-8").strip() if each.obj_label.decode("utf-8").strip() != '' else str(each.class_id)
		size = cv2.getTextSize(l, face, scale, thickness+1)
		x1, x2, y1, y2 = int(each.x1*w), int(each.x2*w), int(each.y1*h), int(each.y2*h)
		cv2.rectangle(img, (x1, y1), (x2, y2), (255, 255, 0), thickness)
		cv2.rectangle(img, (x1, y1), (x1+size[0][0], y1+size[0][1]+size[1]), (255, 255, 255), -1)
		cv2.putText(img, l, (x1, y1 + size[0][1]), face, scale, (0, 0, 255), thickness+1)

def gst_video_caps_make(fmt):
	return  "video/x-raw, "\
		"format = (string) " + fmt + " , "\
		"width = " + GstVideo.VIDEO_SIZE_RANGE + ", "\
		"height = " + GstVideo.VIDEO_SIZE_RANGE + ", "\
		"framerate = " + GstVideo.VIDEO_FPS_RANGE


class AdlinkSamplePy(Gst.Element):

		# !!!ADLINK !!!!
		# Change name of your plugin here, this name will be used when you run gst-inspect
		GST_PLUGIN_NAME = 'adlink_plugin_sample'
		# !!!ADLINK !!!!
		# Change info of your plugin her, it will show when you run gst-inspect		
		__gstmetadata__ = ("Name",
											 "Transform",
											 "Description",
											 "Author")

		__gsttemplates__ = (Gst.PadTemplate.new("src",
																						Gst.PadDirection.SRC,
																						Gst.PadPresence.ALWAYS,
																						Gst.Caps.from_string(gst_video_caps_make("{ BGR }"))),
												Gst.PadTemplate.new("sink",
																						Gst.PadDirection.SINK,
																						Gst.PadPresence.ALWAYS,
																						Gst.Caps.from_string(gst_video_caps_make("{ BGR }"))))
		
		_sinkpadtemplate = __gsttemplates__[1]
		_srcpadtemplate = __gsttemplates__[0]
		
		# MODIFIED - Gstreamer plugin properties
		# !!!ADLINK!!!
		# Here you can define your parameter which can be pass from pipeline to your plugin function.
		# I put here 1 integer parameter and 1 string parameter
		__gproperties__ = {
			"num": (int,  # type
									"num",  # nick
									"number",  # blurb
									1, 65536, 1, # min,max, default
									GObject.ParamFlags.READWRITE  ),# flags 
			"file-name": (str, "file-name", "File name",
									"", GObject.ParamFlags.READWRITE),
		}

		def __init__(self):
			# !!!ADLINK!!!
			# Init the internal value to store the num and file-name parameter
			self.num = 1
			self.file_name = ""
			super(AdlinkSamplePy, self).__init__()

			self.sinkpad = Gst.Pad.new_from_template(self._sinkpadtemplate, 'sink')

			self.sinkpad.set_chain_function_full(self.chainfunc, None)

			self.sinkpad.set_chain_list_function_full(self.chainlistfunc, None)

			self.sinkpad.set_event_function_full(self.eventfunc, None)
			self.add_pad(self.sinkpad)

			self.srcpad = Gst.Pad.new_from_template(self._srcpadtemplate, 'src')

			self.srcpad.set_event_function_full(self.srceventfunc, None)

			self.srcpad.set_query_function_full(self.srcqueryfunc, None)
			self.add_pad(self.srcpad)

		# !!!ADLINK!!!
		# Get the prarameter ( property is the name of parameter in gstreamer api )
		def do_get_property(self, prop: GObject.GParamSpec):
			if prop.name == 'num':
				return self.num
			elif prop.name == 'file-name':
				return self.file_name
			else:
				raise AttributeError('unknown property %s' % prop.name)

		# !!!ADLINK!!!
		# Set the prarameter to the value from pipeline
		def do_set_property(self, prop: GObject.GParamSpec, value):
			if prop.name == 'num':
				self.num = int(value)		
			elif prop.name == 'file-name':
				self.file_name = str(value)
			else :
				raise AttributeError('unknown property %s' % prop.name)

		# !!!ADLINK!!!
		# Main function to get image buffer and adlink metadata 
		def chainfunc(self, pad: Gst.Pad, parent, buff: Gst.Buffer) -> Gst.FlowReturn:
			# !!!ADLINK !!!!		
			# frame id used to identify frame in a batched input, we have 1 stream so always set to 0
			frame_idx =0
			# !!!ADLINK !!!!		
			# This function will get inference result data from buffer
			boxes = admeta.get_detection_box(buff, 0)
			# !!!ADLINK !!!!
			# This function will get image buffer to a numpy array img to allow drawing to it
			img = gst_cv_helper.pad_and_buffer_to_numpy(pad, buff, ro=False)
			draw_box = []
			with boxes as det_box :
				if det_box is not None :
					for box in det_box:
						# Check if this is pose result or not
						if box.meta == b'pose' :
							continue
						else :
							draw_box.append(box)
			# !!!ADLINK !!!!
			# This function will draw detection box result to image buffer 
			draw_boxs	(img,draw_box)
			return self.srcpad.push(buff)

		def chainlistfunc(self, pad: Gst.Pad, parent, list: Gst.BufferList) -> Gst.FlowReturn:
			return self.srcpad.push(list.get(0))

		def eventfunc(self, pad: Gst.Pad, parent, event: Gst.Event) -> bool:
			return self.srcpad.push_event(event)

		def srcqueryfunc(self, pad: Gst.Pad, parent, query: Gst.Query) -> bool:
			return self.sinkpad.query(query)

		def srceventfunc(self, pad: Gst.Pad, parent, event: Gst.Event) -> bool:
			return self.sinkpad.push_event(event)	

# Register plugin to use it from command line
GObject.type_register(AdlinkSamplePy)
__gstelementfactory__ = (AdlinkSamplePy.GST_PLUGIN_NAME,
												 Gst.Rank.NONE, AdlinkSamplePy)

