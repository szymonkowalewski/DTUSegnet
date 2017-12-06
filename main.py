# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 22:17:52 2017

@author: Szymon
"""

import tensorflow as tf
import numpy as np
import time
import os
import sys

script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
rel_path = "tensorflow-vgg"
abs_file_path = os.path.join(script_dir, rel_path)
sys.path.insert(0, abs_file_path)

import SegNet as sn
import utils
import training_ops
import batch

#Reset
tf.reset_default_graph()

FLAGS = tf.app.flags.FLAGS
#224,224 // 360,480
tf.app.flags.DEFINE_integer('inputImX',352, 'Size of the x axis of the input image')
tf.app.flags.DEFINE_integer('inputImY',480, 'Size of the y axis of the input image')
tf.app.flags.DEFINE_bool('isTraining',True, 'Size of the y axis of the input image')
tf.app.flags.DEFINE_string('images_path', './Data/images/*.png', 'Path for the images')
tf.app.flags.DEFINE_string('labels_path', './Data/labels/*.png', 'Path for the labels images')
tf.app.flags.DEFINE_string('MBF_weights_path','Data/labels/class_weights.txt','path to the MBF weights')


timestr = time.strftime("%Y%m%d-%H%M%S")
tensorboard_path=os.path.join("./Tensorboard", timestr)
#sess = tf.InteractiveSession()

images_ph = tf.placeholder(tf.float32, [None, FLAGS.inputImX, FLAGS.inputImY, 3])
#imgIn = utils.load_image_input(".\\Data\\images\\0001TP_007140.png")
#imgIn = imgIn.reshape((1, FLAGS.inputImX, FLAGS.inputImY, 3))

labels_ph= tf.placeholder(tf.int32, [None, FLAGS.inputImX, FLAGS.inputImY])
#imgLabel = utils.load_image_labels(".\\Data\\labels\\0001TP_007140.png")
#imgLabel = imgLabel.reshape((1, FLAGS.inputImX, FLAGS.inputImY))
phase_ph = tf.placeholder(tf.bool, name='phase')


num_class = 12
segnet = sn.SegNet(num_class = num_class)
segnet.build(images_ph, phase_ph)

batch = batch.batch(FLAGS)

loss_op = training_ops.calc_loss(segnet.convD5_2, labels_ph, num_class)
MFB_loss_op = training_ops.calc_MFB_loss(segnet.convD5_2, labels_ph, num_class,FLAGS)
train_op = training_ops.train_network(loss_op)
G_acc_op, C_acc_opp = training_ops.calc_accuracy(segnet.argmax_layer, labels_ph,num_class)

init =  tf.group(tf.global_variables_initializer(), tf.local_variables_initializer())
print("running the train loop")
with tf.Session(config=tf.ConfigProto(gpu_options=(tf.GPUOptions(per_process_gpu_memory_fraction=0.5)))) as sess:
#with tf.device('/cpu:0'):
#    with tf.Session() as sess:
    merged = tf.summary.merge_all()
    tensorboard_writer = tf.summary.FileWriter(tensorboard_path, sess.graph) #Saves the graph in the Tensorboard folder
    sess.run(init)
    current_epoch = 0
    #Validation fetch and feed
    v_im, v_lab = batch.get_validation()
    fetches_valid = [G_acc_op, C_acc_opp]
    list_feed_valid = []
    for i in range(0,v_im.shape[0],10):
        list_feed_valid.append({images_ph: v_im[i:i+9], labels_ph: v_lab[i:i+9], phase_ph: 0})
	
    #feed_valid = {images_ph: v_im, labels_ph: v_lab}

    print("number of trainable parameters :",np.sum([np.prod(v.get_shape().as_list()) for v in tf.trainable_variables()]))
    for i in range(500000):

        imgIn, imgLabel = batch.get_train(5)

        feed_dict = {images_ph: imgIn, labels_ph: imgLabel, phase_ph: 1}
        fetches_train = [segnet.argmax_layer, merged, train_op, loss_op, MFB_loss_op]
        img, summary, _ , loss, MFB_loss = sess.run(fetches = fetches_train, feed_dict=feed_dict)
        #tensorboard_writer.add_summary(summary,i)

        if (i%10)==0:
            #utils.show_image(img[0])
            #utils.show_image(imgIn[0])
            #utils.show_image(imgLabel[0])
            G_acc, C_acc = sess.run(fetches = [G_acc_op, C_acc_opp], feed_dict=feed_dict)
            print(i,"	Test loss",loss,"	MFB loss", MFB_loss,"	G_acc", G_acc, "	C_acc", C_acc)

        if batch.get_epoch() > current_epoch:
            print("new epoch")
            current_epoch= batch.get_epoch()
            #G_acc, C_acc = sess.run(fetches_valid, feed_dict=feed_valid)
            C_acc = []
            G_acc = []
            for feed_valid in list_feed_valid:
                res = sess.run(fetches_valid, feed_dict=feed_valid)
                #ADDDDDD phase_ph = 0 here!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! to feed_valid
                G_acc.append(res[0])
                C_acc.append(res[1])
            G_acc = sum(G_acc)/len(G_acc)
            C_acc = sum(C_acc)/len(C_acc)
            print("NUMBER EPOCHS: ", current_epoch,"	Valid G_acc", G_acc, "C_acc", C_acc)
            #if current_epoch > -1:
            #if current_epoch % 10 == 0:
                #utils.show_image(img[0])
                #utils.show_image(img[1])
                #utils.show_image(img[2])
                #utils.show_image(img[3])
                #utils.show_image(img[4])
                #utils.show_image(imgLabel[0])
                #utils.show_image(img[1])
                #utils.show_image(imgLabel[1])
        #print("Train WTF "+res[0])
        # print("Loss")
        # print(res[1])
        # print("Accuracy")
        # print(res[2])
        #utils.gray_to_RGB(img[0])

    utils.show_image(img[0])
