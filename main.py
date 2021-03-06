import tensorflow as tf
import numpy as np
import os
import sys

#os.environ["CUDA_VISIBLE_DEVICES"] = '3' ## <--- TO SELECT HPC GPU
script_dir = os.path.dirname(__file__) # <-- absolute dir the script is in
rel_path = "tensorflow-vgg"
abs_file_path = os.path.join(script_dir, rel_path)
sys.path.insert(0, abs_file_path)

import SegNet as sn
import SegDepth as sd
import utils
import training_ops
import batch
import SegNetFlags

SegNetFlags.define_FLAGS(False,True,True)
FLAGS = tf.app.flags.FLAGS
### DEFINING THE RUNNING OPTIONS ###
batch_size = 5

#Reset
tf.reset_default_graph()


### DEFINING THE PLACEHOLDERS ###
images_ph = tf.placeholder(tf.float32, [None, FLAGS.inputImX, FLAGS.inputImY, FLAGS.n_channels])
labels_ph= tf.placeholder(tf.int32, [None, FLAGS.inputImX, FLAGS.inputImY])
phase_ph = tf.placeholder(tf.bool, name='phase')

### BUILDING THE NETWORK ###
segnet = sd.SegNet(im_rgbd = images_ph, phase=phase_ph)

### DEFINING THE OPERATIONS ###
loss_op = training_ops.calc_loss(segnet.convD5_2, labels_ph, FLAGS.num_class)
#MFB_loss_op = training_ops.calc_MFB_loss(segnet.convD5_2, labels_ph, num_class,FLAGS)
MFB_loss_op = loss_op
train_op = training_ops.train_network(loss_op)
G_acc_op, C_acc_opp, G_accs_op, C_accs_opp  = training_ops.calc_accuracy(segnet.argmax_layer, labels_ph, FLAGS.num_class, phase_ph)

### BUILDING BATCH and TEST ###
batch = batch.batch()
fetches_test = [G_accs_op, C_acc_opp]
chunk_size = 10
list_feed_test_indices = []
test_len = batch.test_size
for s in range(0,test_len,chunk_size):
    if s+chunk_size-1 >= test_len:
        e = test_len
    else:
        e = s+chunk_size
    list_feed_test_indices.append((s,e))


init =  tf.group(tf.global_variables_initializer(), tf.local_variables_initializer())
saver = tf.train.Saver(tf.global_variables())

### TRAINING LOOP ###
print("running the train loop")
with tf.Session(config=tf.ConfigProto(gpu_options=(tf.GPUOptions(per_process_gpu_memory_fraction=0.9)))) as sess:
    merged = tf.summary.merge_all()
    tensorboard_writer = tf.summary.FileWriter(FLAGS.tensorboard_path, sess.graph) #Saves the graph in the Tensorboard folder
    sess.run(init)
    #current_epoch = 4
    #batch.epoch = 
    #segnet.load_model(saver, sess)
    print("number of trainable parameters : ",np.sum([np.prod(v.get_shape().as_list()) for v in tf.trainable_variables()]))
    for i in range(500000):

        imgIn, imgLabel = batch.get_train(batch_size)
        feed_dict = {images_ph: imgIn, labels_ph: imgLabel, phase_ph: 1}
        fetches_train = [segnet.argmax_layer, merged, train_op, loss_op, MFB_loss_op]
        img, summary, _ , loss, MFB_loss = sess.run(fetches = fetches_train, feed_dict=feed_dict)
        tensorboard_writer.add_summary(summary,i)

        if (i%10)==0:
            G_acc, C_acc = sess.run(fetches = [G_acc_op, C_acc_opp], feed_dict=feed_dict)
            print(i,"	Train loss",loss,"	MFB loss", MFB_loss,"	G_acc", G_acc, "	C_acc", C_acc)

        if batch.get_epoch() > current_epoch:
            print("new epoch")
            current_epoch= batch.get_epoch()
            G_acc_test = []
            C_acc_test = []
            for ind in list_feed_test_indices:
                b_test_im, b_test_lab = batch.get_batch_test(ind[0],ind[1])
                feed_test = {images_ph: b_test_im, labels_ph: b_test_lab, phase_ph: 0}
                res = sess.run(fetches_test, feed_dict=feed_test)

                G_acc_test.append(res[0])
                C_acc_test.append(res[1])
            G_acc_test = tf.concat(G_acc_test,axis = 0)
            #C_acc_test = tf.concat(C_acc_test,axis = 0)
            G_acc = tf.reduce_mean(G_acc_test).eval()
            C_acc = tf.reduce_mean(C_acc_test).eval()
            print("EPOCHS: ", current_epoch,"	Test G_acc", G_acc, "C_acc", C_acc)
            #After 5 epoch save the model
            if (current_epoch%2)==0:
                save_path = saver.save(sess, "./Models/model.ckpt", global_step = current_epoch)
                print("Model saved in file: %s" % save_path)


    utils.show_image(img[0])
