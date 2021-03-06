import skimage
import skimage.io
import skimage.transform
import numpy as np
import tensorflow as tf
from scipy import misc
import matplotlib.pyplot as plt


VGG_MEAN = [103.939, 116.779, 123.68]
FLAGS = tf.app.flags.FLAGS
# synset = [l.strip() for l in open('synset.txt').readlines()]


'''
    load the image and resize it to fit the network
'''
def load_image_input(path):
    # load image
    img = skimage.io.imread(path)
    #Why do we need to scale it?
    img = img / 255.0
    assert (0 <= img).all() and (img <= 1.0).all()
    # print "Original Image Shape: ", img.shape
    # we crop image from center

    if FLAGS.inputImX is not 360:

        img = img[:FLAGS.inputImX,:]

        short_edge = min(img.shape[:2])
        yy = int((img.shape[0] - short_edge) / 2)
        xx = int((img.shape[1] - short_edge) / 2)
        crop_img = img[yy: yy + short_edge, xx: xx + short_edge]
        # resize to 224, 224
        resized_img = skimage.transform.resize(crop_img, (FLAGS.inputImX, FLAGS.inputImY),mode='constant')
        #show_image(resized_img)

        return resized_img

    elif FLAGS.inputImX is not 360:
        crop_img = img[:FLAGS.inputImX,:]
        return crop_img

    else:
        return img
'''
    load the labels image and resize it to fit the network
'''
def load_image_labels(path):
    img = skimage.io.imread(path)


    if FLAGS.inputImX is not 360:

        img = img[:FLAGS.inputImX,:]

        short_edge = min(img.shape[:2])
        yy = int((img.shape[0] - short_edge) / 2)
        xx = int((img.shape[1] - short_edge) / 2)
        crop_img = img[yy: yy + short_edge, xx: xx + short_edge]
        # resize to 224, 224
        resized_img = skimage.transform.resize(crop_img, (FLAGS.inputImX, FLAGS.inputImY),order=0,mode='constant')
        #resized_img = skimage.transform.resize(crop_img, (224, 224))
        resized_img = resized_img * 255
        #show_image(resized_img)
        return resized_img

    else:
        img = img * 255
        return img
'''
    load the depths image and resize it to fit the network
'''
def load_depths_input(path):
    # load image
    img = skimage.io.imread(path)
    #Why do we need to scale it?
    img = img / 65536.0
    assert (0 <= img).all() and (img <= 1.0).all()
    # print "Original Image Shape: ", img.shape
    # we crop image from center

    if FLAGS.inputImX is not 360:

        img = img[:FLAGS.inputImX,:]

        short_edge = min(img.shape[:2])
        yy = int((img.shape[0] - short_edge) / 2)
        xx = int((img.shape[1] - short_edge) / 2)
        crop_img = img[yy: yy + short_edge, xx: xx + short_edge]
        # resize to 224, 224
        resized_img = skimage.transform.resize(crop_img, (FLAGS.inputImX, FLAGS.inputImY),mode='constant')
        #show_image(resized_img)

        return resized_img*8
    else:
        return img*8

'''
    load the image and the depths and concatenate them to fit the network
'''
def load_image_depth_input(path,depthpath):
    img = load_image_input(path)
    depths = np.expand_dims(load_depths_input(depthpath),2)
    return np.concatenate((img,depths),axis=2)

'''
    plot an image for debuging
'''
def show_image(img):
    plt.imshow(img)
    plt.show()
    return img

'''
    transform a labels predictions in constant colored image
'''
def gray_to_RGB(img):
    with open("CamVid/colors.txt") as file:
        colors = []
        for line in file.readlines():
            l = line.split()
            colors.append((l[0],l[1],l[2]))

    #img = Image.fromarray(img, "L")
    gray_img = img
    shape = gray_img.shape
    RGB_img = np.zeros((shape[0],shape[1],3),dtype=np.uint8)
    for i,row in enumerate(gray_img):
        for j,label in enumerate(row):
            label = int(label)
            RGB_img[i,j,] = colors[label]
    return RGB_img
'''
    return the top1 string
'''
def print_prob(prob, file_path):
    synset = [l.strip() for l in open(file_path).readlines()]

    # print prob
    pred = np.argsort(prob)[::-1]

    # Get top1 label
    top1 = synset[pred[0]]
    print(("Top1: ", top1, prob[pred[0]]))
    # Get top5 label
    top5 = [(synset[pred[i]], prob[pred[i]]) for i in range(5)]
    print(("Top5: ", top5))
    return top1

'''
    converts from rgb to bgr to fit the vgg16 network
'''
def rgb2bgr(rgb):
    with tf.variable_scope("rgb2bgr"):
        rgb_scaled = rgb * 255.0
        # Convert RGB to BGR
        red, green, blue = tf.split(axis=3, num_or_size_splits=3, value=rgb_scaled)
        assert red.get_shape().as_list()[1:] == [FLAGS.inputImX, FLAGS.inputImY, 1]
        assert green.get_shape().as_list()[1:] == [FLAGS.inputImX, FLAGS.inputImY, 1]
        assert blue.get_shape().as_list()[1:] == [FLAGS.inputImX, FLAGS.inputImY, 1]
        #It normalizes the values of the image based on the means of the vgg
        bgr = tf.concat(axis=3, values=[
            blue - VGG_MEAN[0],
            green - VGG_MEAN[1],
            red - VGG_MEAN[2],
        ])
        assert bgr.get_shape().as_list()[1:] == [FLAGS.inputImX, FLAGS.inputImY, 3]
        return bgr

def show_comparison(datasetType, saver, sess, batch, segnet, images_ph, labels_ph, phase_ph):
    segnet.load_model(saver, sess)
    #Take some images from the training set and show them
    n_images=2
    feed, im_visual, label_visual = batch.get_visualization_images(nImages=n_images,datasetType=datasetType)
    fetches_visualization = [segnet.argmax_layer]
    feed_dict = {images_ph: feed, labels_ph: label_visual, phase_ph: 0}
    im_result = sess.run(fetches_visualization, feed_dict=feed_dict)
    im_result_arr=np.array(im_result).squeeze()

    plot_comparison(n_images=n_images,original=im_visual,groundtruth=label_visual,result=im_result_arr,datasetType=datasetType)


'''
    plots comparing the image, the groud truth labels and the predictions
'''
def plot_comparison(n_images, original, groundtruth, result,datasetType):
    f, axarr = plt.subplots(n_images, 3, sharex='col', sharey='row')
    axarr[0,0].set_title(datasetType + ' images')
    axarr[0,1].set_title('Ground truth labels')
    axarr[0,2].set_title('Prediction')
    for i in range(0,n_images):
        axarr[i,0].imshow(original[i])
        axarr[i,0].axis('off')
        axarr[i,1].imshow(gray_to_RGB(groundtruth[i]))
        axarr[i,1].axis('off')
        axarr[i,2].imshow(gray_to_RGB(result[i]))
        axarr[i,2].axis('off')
    plt.show()
'''
     Attach a lot of summaries to a Tensor (for TensorBoard visualization).
'''
def variable_summaries(var):
  with tf.name_scope('summaries'):
    mean = tf.reduce_mean(var)
    tf.summary.scalar('mean', mean)
    with tf.name_scope('stddev'):
      stddev = tf.sqrt(tf.reduce_mean(tf.square(var - mean)))
    tf.summary.scalar('stddev', stddev)
    tf.summary.scalar('max', tf.reduce_max(var))
    tf.summary.scalar('min', tf.reduce_min(var))
    tf.summary.histogram('histogram', var)
