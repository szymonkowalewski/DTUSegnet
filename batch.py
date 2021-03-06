import glob
import random
import utils
import numpy as np
import tensorflow as tf
import time
from random import randint

FLAGS = tf.app.flags.FLAGS
class batch:
    def __init__(self):
        self.depthIncluded = FLAGS.depthIncluded
        self.inRAM = FLAGS.inRAM
        start_time = time.time()
        self.train_images_filenames = sorted(glob.glob(FLAGS.train_images_path))
        self.train_labels_filenames = sorted(glob.glob(FLAGS.train_labels_path))
        self.test_images_filenames = sorted(glob.glob(FLAGS.test_images_path))
        self.test_labels_filenames = sorted(glob.glob(FLAGS.test_labels_path))
        self.val_images_filenames = sorted(glob.glob(FLAGS.validation_images_path))
        self.val_labels_filenames = sorted(glob.glob(FLAGS.validation_labels_path))
        if self.depthIncluded:
            self.channels = 4
            self.train_depths_filenames = sorted(glob.glob(FLAGS.train_depth_path))
            self.test_depths_filenames = sorted(glob.glob(FLAGS.test_depth_path))
        else:
            self.channels = 3
            self.train_depths_filenames = None
            self.test_depths_filenames = None            
        self.test_size = len(self.test_images_filenames)
        self.train_size = len(self.train_images_filenames)
        self.train_rand_idx = list(range(0,self.train_size))

        self.epoch = 0
        self.current_batch_train=0
        self.current_batch_test=0
        if self.inRAM:
            self.train_labels = np.asarray([utils.load_image_labels(i) for i in self.train_labels_filenames])
            self.test_labels = np.asarray([utils.load_image_labels(i) for i in self.test_labels_filenames])

            if self.depthIncluded:
                self.train_images = np.asarray([utils.load_image_depth_input(path,self.train_depths_filenames[i]) for i,path in enumerate(self.train_images_filenames)])
                self.test_images = np.asarray([utils.load_image_depth_input(path,self.test_depths_filenames[i]) for i,path in enumerate(self.test_images_filenames)])
            else:
                self.train_images = np.asarray([utils.load_image_input(i) for i in self.train_images_filenames])
                self.test_images = np.asarray([utils.load_image_input(i) for i in self.test_images_filenames])
        print(("build batch finished: %ds" % (time.time() - start_time)))
        print("train size: ",self.train_size,"  test size: ",self.test_size)

    def get_train(self,size):
        if self.current_batch_train + size > self.train_size:
            self.epoch += 1
            self.current_batch_train=0
            random.shuffle(self.train_rand_idx)
        b_im = np.zeros((size, FLAGS.inputImX, FLAGS.inputImY, self.channels))
        b_lab = np.zeros((size, FLAGS.inputImX, FLAGS.inputImY))
        if self.inRAM:
            for i in range(size):
                idx = self.train_rand_idx[self.current_batch_train+i]
                b_im[i] = self.train_images[idx]
                b_lab[i] = self.train_labels[idx]
        else:
            for i in range(size):
                idx = self.train_rand_idx[self.current_batch_train+i]
                if self.depthIncluded:
                    b_im[i] = utils.load_image_depth_input(self.train_images_filenames[idx],self.train_depths_filenames[idx])
                else:
                    b_im[i] = utils.load_image_input(self.train_images_filenames[idx])
                b_lab[i] = utils.load_image_labels(self.train_labels_filenames[idx])
        self.current_batch_train += size
        return b_im, b_lab

    def get_epoch(self):
        return self.epoch

    def get_test(self):
        if self.inRAM:
            return self.test_images, self.test_labels
        else:
            size = 5
            b_im = np.zeros((size, FLAGS.inputImX, FLAGS.inputImY, self.channels))
            b_lab = np.zeros((size, FLAGS.inputImX, FLAGS.inputImY))
            for i in range(size):
                b_im[i] = utils.load_image_input(self.test_images_filenames[i])
                b_lab[i] = utils.load_image_labels(self.test_labels_filenames[i])
            return b_im, b_lab\

    def get_train_all(self):
        if self.inRAM:
            return np.asarray(self.train_images), np.asarray(self.train_labels)
        else:
            size = 5
            tr_im = np.zeros((size, FLAGS.inputImX, FLAGS.inputImY, 3))
            tr_lab = np.zeros((size, FLAGS.inputImX, FLAGS.inputImY))
            for i in range(size):
                tr_im[i] = utils.load_image_input(self.train_images_filenames[i])
                tr_lab[i] = utils.load_image_labels(self.train_labels_filenames[i])
            return tr_im, tr_lab\

    def get_validation(self):
        self.val_images = np.asarray([utils.load_image_input(i) for i in self.val_images_filenames])
        self.val_labels = np.asarray([utils.load_image_labels(i) for i in self.val_labels_filenames])
        return self.val_images, self.val_labels

    def get_visualization_images(self, nImages, datasetType):
        '''Gets nImages random images from the test set to show'''
        if datasetType=="Train":
            input_imgs = self.train_images_filenames
            label_imgs = self.train_labels_filenames
            depth_imgs = self.train_depths_filenames
        elif datasetType=="Test":
            input_imgs = self.test_images_filenames
            label_imgs = self.test_labels_filenames
            depth_imgs = self.test_depths_filenames
        elif datasetType=="Validation":
            input_imgs=self.val_images_filenames
            label_imgs=self.val_labels_filenames
        else:
            return
        idx=[randint(1,len(input_imgs)-1) for i in range(0,nImages)]

        im_visual = np.zeros((nImages, FLAGS.inputImX, FLAGS.inputImY, 3))
        feed = np.zeros((nImages, FLAGS.inputImX, FLAGS.inputImY, self.channels))
        label_visual = np.zeros((nImages, FLAGS.inputImX, FLAGS.inputImY))
        for i in range(nImages):
            if self.depthIncluded:
                feed[i] = utils.load_image_depth_input(input_imgs[idx[i]],depth_imgs[idx[i]])
                im_visual[i] = utils.load_image_input(input_imgs[idx[i]])
            else:
                im_visual[i] = utils.load_image_input(input_imgs[idx[i]])
                feed[i] = im_visual[i]
            label_visual[i] = utils.load_image_labels(label_imgs[idx[i]])
        return feed, im_visual,label_visual

    def get_batch_test(self,s,e):
            b_im = np.zeros((e-s, FLAGS.inputImX, FLAGS.inputImY, self.channels))
            b_lab = np.zeros((e-s, FLAGS.inputImX, FLAGS.inputImY))
            if self.inRAM:
                for i,idx in enumerate(range(s,e)):
                    b_im[i] = self.test_images[idx]
                    b_lab[i] = self.test_labels[idx]
            else:
                for i,idx in enumerate(range(s,e)):
                    if self.depthIncluded:
                        b_im[i] = utils.load_image_depth_input(self.test_images_filenames[idx],self.test_depths_filenames[idx])
                    else:
                        b_im[i] = utils.load_image_input(self.test_images_filenames[idx])
                    b_lab[i] = utils.load_image_labels(self.test_labels_filenames[idx])
            return b_im, b_lab
