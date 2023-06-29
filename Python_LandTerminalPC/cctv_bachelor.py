# Kilde: https://colab.research.google.com/github/roboflow-ai/notebooks/blob/main/notebooks/how-to-track-and-count-vehicles-with-yolov8.ipynb
# Kilde: https://github.com/roboflow/supervision
# Kilde: https://blog.roboflow.com/yolov8-tracking-and-counting/



import cv2
import argparse
import serial
import time
import supervision as sv
from ultralytics import YOLO
import numpy as np



# Testing serial communication over Advantech USB-5830
import sys
sys.path.append('..')
#from CommonUtils import kbhit


#from Automation.BDaq import *
#from Automation.BDaq.InstantDiCtrl import InstantDiCtrl
#from Automation.BDaq.InstantDoCtrl import InstantDoCtrl
#from Automation.BDaq.BDaqApi import AdxEnumToString, BioFailed

device = "USB-5830,BID#0"
profilePath = u"../../profile/DemoDevice.xml"

startPort = 0
portCount = 2

inputList = ['0x1', '0x2', '0x4', '0x8', '0x10', '0x20', '0x40', '0x80']
outputList = ['0x1', '0x2', '0x4', '0x8', '0x10', '0x20', '0x40', '0x80']



YOLOMODEL = "yolov8m.pt"

# Video is in the following format:
    #Width = 1920
    #Heigth = 1080

#sv.VideoInfo.from_video_path(pathVideo)
# We use that to shape a square in numpy by the following method.
#square = np.array([[0, 0], 
#                   [1920 // 2, 0], 
#                   [1920 // 2, 1080], 
#                   [0, 1080]])

square = np.array([[420, 200],
                  [1080, 200],
                  [1080, 1000],
                  [420, 1000 ]])

position_text = np.array([50, 50])


# Serial communication:
#comSer = serial.Serial("COM3", 115200)
#time.sleep(2)



def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description = "YOLOv8 Demo")
    parser.add_argument("--webcam-resolution",
                        default = [1280, 720],
                        nargs = 2,
                        type = int)
    args = parser.parse_args()
    return args

def counting_line():
    pathVideo = "cctv_test.3gp"
    
    video_info = VideoInfo.from_video_path(pathVideo)
    generator = get_video_frames_generator(pathVideo)
    
    with VideoSink(pathVideo, video_info) as sink:
        for frame in tqdm(generator, total = video_info.total_frames):
            frame = ...
            sink.write_frame(frame)


def detection_area():
    
    global argumentvalue
    
    args = parse_arguments()
    frame_width, frame_height = args.webcam_resolution
    
    
    pathVideo = "cctv_test.3gp"
    vc = cv2.VideoCapture(pathVideo)
    vc.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    vc.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    
    
    model = YOLO(YOLOMODEL)
    
    # Settings for box-annotation
    
    
    zone = sv.PolygonZone(polygon=square, frame_resolution_wh=tuple(args.webcam_resolution))
    zone_annotator = sv.PolygonZoneAnnotator(zone = zone, 
                                             color = sv.Color.green(),
                                             thickness = 1,
                                             text_color = sv.Color.white(),
                                             text_padding = 1,
                                             text_thickness = 3,
                                             text_scale = 4)
    boxAnnotation = sv.BoxAnnotator(
        thickness = 1,
        text_thickness = 2,
        text_scale = 1)

    while True:
        ret, frame = vc.read()
        
        # Extract only the persons class, which means that only people are detected.
        result = model(frame, classes=0)[0]
    
        detections = sv.Detections.from_yolov8(result)   
        labels = [
            f"{model.model.names[class_id]} {confidence:0.2f}"
            for _, confidence, class_id,_ in detections
        ]
           
        frame = boxAnnotation.annotate(scene = frame, 
                                       detections = detections, 
                                       labels = labels)
        zone.trigger(detections = detections)
        argumentvalue = zone.trigger(detections = detections)
        frame = zone_annotator.annotate(scene=frame)
            
        # Add if displaying
        cv2.imshow("RAMMEN TIL PROGRAMMET", frame)
        
    
  #      if zone.trigger(detections = detections):
 #           writingToOutput(device, profilePath, outputList, startPort, portCount, 2)
        # If button(esc) is pushed, escape window.
        if (cv2.waitKey(30) == 27):
            break
        
       # return  zone.trigger(detections = detections)
        
#def writingToOutput(device, profilePath, outList, startPort, portCount, outPin):
#    ret = ErrorCode.Success
#    
#    instantDoCtrl = InstantDoCtrl(device)
#    instantDoCtrl.loadProfile = profilePath
#        
#    ret = instantDoCtrl.writeAny(startPort, portCount, outList[outPin])
#    instantDoCtrl.dispose()
    return 0


#def readingFromInput(device, profilePath, inputList, startPort, portCount):
#    ret = ErrorCode.Success
    
#    instantDiCtrl = InstantDiCtrl(device)
#    instantDiCtrl.loadProfile = profilePath
    
#    while not kbhit():
#        ret, data = instantDiCtrl.readAny(startPort, portCount)
#        if BioFailed(ret):
#            break

 #       if data[0] != 0:
 #           indexPort_0 = inputList.index(hex(data[0]))
 #           print(indexPort_0)
        
 #       if data[1] != 0:
 #           indexPort_1 = inputList.index(hex(data[1])) + 8
 #           print(indexPort_1)
    
 #   instantDiCtrl.dispose()
    
 #   if data[0] or data[1] == 0:
 #       return 0
 #   else:
 #       return indexPort_0, indexPort_1

        
    

def main():
    detection_area()


if __name__ == "__main__":
    main()
