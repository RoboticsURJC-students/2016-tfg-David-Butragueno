import numpy as np
import os
import sys
import time
import matplotlib.pyplot as plt

sys.path.insert(0, '/home/davidbutra/caffe/python')
import caffe
from google.protobuf import text_format
from caffe.proto import caffe_pb2

import cv2
import xml.etree.ElementTree as ET

input_image = '/home/davidbutra/data/VOCdevkit/VOC2012/JPEGImages/2007_000783.jpg'

class DetectionNet:

    def __init__(self):

        labelmap_file = '/home/davidbutra/caffe/data/VOC0712/labelmap_voc.prototxt'
        file = open(labelmap_file, 'r')
        self.labelmap = caffe_pb2.LabelMap()
        text_format.Merge(str(file.read()), self.labelmap)

        model_def = '/home/davidbutra/caffe/models/VGGNet/VOC0712/SSD_300x300/deploy.prototxt'
        model_weights = '/home/davidbutra/caffe/models/VGGNet/VOC0712/SSD_300x300/VGG_VOC0712_SSD_300x300_iter_120000.caffemodel'

        self.net = caffe.Net(model_def,      # defines the structure of the model
                        model_weights,  # contains the trained weights
                        caffe.TEST)     # use test mode (e.g., don't perform dropout)

        # fin caffe


    def get_labelname(self,labelmap, labels):
        num_labels = len(labelmap.item)
        labelnames = []
        if type(labels) is not list:
            labels = [labels]
        for label in labels:
            found = False
            for i in xrange(0, num_labels):
                if label == labelmap.item[i].label:
                    found = True
                    labelnames.append(labelmap.item[i].display_name)
                    break
            assert found == True
        return labelnames


    def detectiontest(self,img):


        transformer = caffe.io.Transformer({'data': self.net.blobs['data'].data.shape})
        transformer.set_transpose('data', (2, 0, 1))
        transformer.set_mean('data', np.array([104,117,123])) # mean pixel


        # set net to batch size of 1
        image_resize = 300
        self.net.blobs['data'].reshape(1,3,image_resize,image_resize)

        transformed_image = transformer.preprocess('data', img)

        self.net.blobs['data'].data[...] = transformed_image

        # Forward pass.
        startA = time.time()
        detections = self.net.forward()['detection_out']
        endA = time.time()

        print ('Executed in',  str((endA - startA)*1000))


        # Parse the outputs.
        det_label = detections[0,0,:,1]
        det_conf = detections[0,0,:,2]
        det_xmin = detections[0,0,:,3]
        det_ymin = detections[0,0,:,4]
        det_xmax = detections[0,0,:,5]
        det_ymax = detections[0,0,:,6]

        top_indices = []
        # Get detections with confidence higher than 0.6.
        for i in range(0, len(det_conf)):
            if (det_conf[i] >= 0.6):
                top_indices.append(i)

        #print(top_indices)

        top_conf = det_conf[top_indices]
        top_label_indices = det_label[top_indices].tolist()
        top_labels = self.get_labelname(self.labelmap, top_label_indices)
        top_xmin = det_xmin[top_indices]
        top_ymin = det_ymin[top_indices]
        top_xmax = det_xmax[top_indices]
        top_ymax = det_ymax[top_indices]

        ground_detection = []
        #for i in xrange(top_conf.shape[0]):
        for i in range(top_conf.shape[0]):
            positions = []
            xmin = int(round(top_xmin[i] * img.shape[1]))
            ymin = int(round(top_ymin[i] * img.shape[0]))
            xmax = int(round(top_xmax[i] * img.shape[1]))
            ymax = int(round(top_ymax[i] * img.shape[0]))
            positions.append(xmin)
            positions.append(ymin)
            positions.append(xmax)
            positions.append(ymax)
            ground_detection.append(positions)

            cv2.rectangle(img,(xmin,ymin),(xmax,ymax),(0,0,255),2) #Color BGR

        ground_truth = self.get_ground_truth(input_image, top_labels)

        for i in range(len(ground_truth)):
            xmin = int(round(float(ground_truth[i][0])))
            ymin = int(round(float(ground_truth[i][1])))
            xmax = int(round(float(ground_truth[i][2])))
            ymax = int(round(float(ground_truth[i][3])))

            cv2.rectangle(img,(xmin,ymin),(xmax,ymax),(0,255,0),2) #Color BGR


        return img


    def get_ground_truth(self, input_image, label_detection):

        annotation = input_image.split(".")

        annotation = annotation[0].split("/")

        file_annotations = "/" + annotation[1] + "/" +  annotation[2] + "/" + annotation[3] + "/" + annotation[4] + "/" + annotation[5] +"/" +       'Annotations' + "/" + annotation[7] + ".xml"

        file = open(file_annotations, 'r')

        tree = ET.parse(file)
        root = tree.getroot()

        positions_array = []


        for element in root.findall('object'):
            name = element.find('name').text
            print name
            for x in range(len(label_detection)):
                print x
                print label_detection[x]
                if name == label_detection[x]:
                    xmin = element[4][0].text
                    ymin = element[4][1].text
                    xmax = element[4][2].text
                    ymax = element[4][3].text
                    print xmin, ymin, xmax, ymax
                    positions = []
                    positions.append(xmin)
                    positions.append(ymin)
                    positions.append(xmax)
                    positions.append(ymax)
                    positions_array.append(positions)
                    print positions
                    print positions_array
                break
            #break
        return positions_array


net = DetectionNet()
image = cv2.imread(input_image)
#cv2.imshow("image", image)
#cv2.waitKey()
img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
img_rgb = cv2.cvtColor(img_gray,cv2.COLOR_GRAY2RGB)
print img_gray.shape, img_rgb.shape
detec = net.detectiontest(image)
#cv2.imwrite('/home/davibutra/Detection/Resultados/person.png')
cv2.imshow("image", detec)
cv2.waitKey()
