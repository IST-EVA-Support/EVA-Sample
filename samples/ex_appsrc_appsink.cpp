#include "opencv2/opencv.hpp"
#include <iostream>
#include <stdio.h>
#include <thread>
#include <chrono>

using namespace cv;
using namespace std;
int main(int, char**)
{
	Mat frame;
	Mat resize_frame;

#ifdef _WIN32
	VideoCapture cap("ksvideosrc ! videoscale ! video/x-raw, width=1024, height=768 ! videoconvert ! appsink", CAP_GSTREAMER);
#else
	VideoCapture cap("v4l2src ! videoscale ! video/x-raw, width=1024, height=768 ! videoconvert ! appsink", CAP_GSTREAMER);
#endif

	if (!cap.isOpened())
	{
		cerr << "ERROR! Unable to open camera\n";
		return -1;
	}

	cv::VideoWriter writer;
#ifdef _WIN32
	writer.open("appsrc ! videoconvert ! video/x-raw, width=640, height=480, framerate=30/1 ! clockoverlay ! videoconvert ! d3dvideosink sync=false", CAP_GSTREAMER, 0, 30, cv::Size(640, 480), true);
#else
	writer.open("appsrc ! videoconvert ! video/x-raw, width=640, height=480, framerate=30/1 ! clockoverlay ! videoconvert ! ximagesink sync=false", CAP_GSTREAMER, 0, 30, cv::Size(640, 480), true);
#endif
	if (!writer.isOpened())
	{
		printf("=ERR= can't create writer\n");
		return -1;
	}

	//--- GRAB AND WRITE LOOP
	cout << "Start grabbing" << endl;

	for (;;)
	{
		cap.read(frame);
		if (frame.empty())
		{
			cerr << "ERROR! blank frame grabbed\n";
			break;
		}
		cv::resize(frame, resize_frame, Size(640, 480));
		writer.write(resize_frame);
		imshow("OpenCV Live", frame);
		if (waitKey(5) >= 0)
			break;

		this_thread::sleep_for(chrono::milliseconds(10));
	}
	cap.release();
	frame.release();
	resize_frame.release();
	return 0;
}