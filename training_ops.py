### This file implements training operations
# calc_loss       - to calculate the cross-entropy
# calc_accuracy   - to calculate the accuracy
# train_network   - to backpropagate the error through the network (1 training step)
import tensorflow as tf
import utils
import numpy as np
# 1) Define cross entropy loss
def calc_loss(predictions, labels, num_class):
    """computing cross entropy per sample, use softmax_cross_entropy_with_logits to avoid problems with log(0)
   	    cross_entropy = tf.nn.softmax_cross_entropy_with_logits(labels, predictions)
   	    I believe using that one the labels will have to be in [widthxheight] shape
   	    instead of 3d [widthxheightxclassnum]"""
    with tf.variable_scope("Loss"):
        reshaped_logits = tf.reshape(predictions, [-1, num_class])
        reshaped_labels = tf.reshape(labels, [-1])
        cross_entropy = tf.nn.sparse_softmax_cross_entropy_with_logits(labels=reshaped_labels, logits=reshaped_logits)
        #cross_entropy = tf.nn.sparse_softmax_cross_entropy_with_logits(labels=labels, logits=predictions)
   	    # Sum over all pixels
        #cross_entropy = tf.reduce_sum(cross_entropy, [1, 2])
   	    # Average over samples
   	    # Averaging makes the loss invariant to batch size, which is very nice.
        cross_entropy = tf.reduce_mean(cross_entropy)
        #Show cross entropy in tensorboard
        tf.summary.scalar("Cross_entropy", cross_entropy)
        return cross_entropy

# 1) Define cross entropy loss with Median Frequency Balancing
def calc_MFB_loss(predictions, labels, num_class,FLAGS):
    with tf.variable_scope("Loss"):
        #Acquisition of the MBF weights
        median_frequencies = []
        with open(FLAGS.MBF_weights_path) as file:
            for line in file.readlines():
                median_frequencies.append(float(line.split()[1]))
        median_frequencies = tf.convert_to_tensor(median_frequencies, dtype=tf.float32)

	#Flatten preds (pixels)
        flattened_predictions = tf.reshape(predictions, (tf.shape(predictions)[0],-1, num_class))
        # Flatten labels (pixels)
        flattened_labels = tf.reshape(labels, [tf.shape(labels)[0],-1])
        # One-hot labels
        one_hot_labels = tf.one_hot(flattened_labels, depth=num_class)
        #Calculate softmax of predictions
        softmax_predictions = tf.nn.softmax(flattened_predictions)
        test = (one_hot_labels * tf.log(softmax_predictions + 1e-10))
        test2 = tf.multiply(test,median_frequencies)

        #Calculate cross-entropy including median-frequency weighting
        cross_entropy = -tf.reduce_sum(test2, axis=[2])

	#Sum over all pixels
        cross_entropy = tf.reduce_sum(cross_entropy, axis=[1])

   	# Average over samples
   	# Averaging makes the loss invariant to batch size, which is very nice.
        cross_entropy = tf.reduce_mean(cross_entropy)
        #Show cross entropy in tensorboard
        tf.summary.scalar("Cross_entropy", cross_entropy)
        return cross_entropy

# 2) Define accuracy
def calc_accuracy(predictions, labels, num_class, phase_ph):
    with tf.variable_scope("Accuracy"):
        # Calculate the number of pixels with the same value in pred and lab
        predictions = tf.cast(predictions, tf.int32)
        equal_elements = tf.equal(predictions, labels)
        num_equal_elements = tf.reduce_sum(tf.cast(equal_elements, tf.int32),axis=[1,2])
        #Calculate global accuracy as fraction of matching pixels
        G_accuracies = tf.divide(num_equal_elements,tf.size(labels[0]))
        G_accuracy = tf.reduce_mean(G_accuracies)

        CM = tf.confusion_matrix(tf.reshape(labels,[-1]),tf.reshape(predictions,[-1]),num_class)
        CM_row_sum = tf.to_float(tf.reduce_sum(CM,1))
        CM_row_sum = tf.where(tf.greater(CM_row_sum, 0), CM_row_sum, tf.ones_like(CM_row_sum))
        CM_diag = tf.to_float(tf.diag_part(CM))
        C_accuracies = tf.div(CM_diag, CM_row_sum)
        C_accuracy = tf.reduce_mean(C_accuracies)
        #tf.summary.scalar("G_Accuracy", G_accuracy)
        #tf.summary.scalar("C_Accuracy", C_accuracy)
        return G_accuracy, C_accuracy, G_accuracies, C_accuracies

# 3) Define the training op
def train_network(loss):
    with tf.variable_scope("TrainOp"):
        #Add bn to training ops
        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        with tf.control_dependencies(update_ops):
            #optimizer = tf.train.MomentumOptimizer(learning_rate=0.1, momentum=0.9)
            optimizer = tf.train.AdamOptimizer(learning_rate=0.001)
            #optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.000001)
            # Computing our gradients
            grads_and_vars = optimizer.compute_gradients(loss)
            #utils.variable_summaries(grads_and_vars)
            #tf.summary.scalar("grads_and_vars", grads_and_vars)
            capped_gvs = grads_and_vars
    		# Applying the gradients
            #capped_gvs = [(tf.clip_by_norm(grad, 50), var) for grad, var in grads_and_vars]
            for grad, var in capped_gvs:
                tf.summary.histogram(var.name[:-2] + '/gradient', grad)
            # Applying the gradients
            train_op = optimizer.apply_gradients(capped_gvs)
            return train_op
