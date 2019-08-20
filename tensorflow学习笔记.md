---
title: tensorflow学习笔记
date: 2017-11-20 15:28:37
categories: 机器学习
---

### Session

#### 会话(Session)

Session是tensorflow为了控制和输出文件所执行的语句，也就是说，如果使用了tensorflow,而你又想正常输出，那就需要创建一个会话，在会话中执行sess.run()来完成你的需求。

```
import tensorflow as tf

matrix1 = tf.constant([[1,3]])
matrix2 = tf.constant([[2],[4]])

result = tf.matmul(matrix1,matrix2)
#method1
sess = tf.Session()
print(sess.run(result))

#method2
with tf.Session() as sess :
    print(sess.run(result))
```

注意：对于张量的写法，无论是几维，最外面总是有个中括号，然后每一维一个中括号

#### 变量

tensorflow中变量必须用tf.Variable()函数来定义，而且应以完了之后必须用tf.initialize_all_varialbles()来初始化，其实这里的初始化也只是静态的初始化，最后还要在session中run一下，run()完之后变量算是真正得到了初始化，但是如果要输出某个变量的值，仍需要sess.run()将Session指针移过去

```
import tensorflow as tf

a = tf.Variable(tf.random_uniform([1,1],1,5))

init  = tf.initialize_all_variables()

with tf.Session() as sess:
    sess.run(init)
    print(sess.run(a))
```





#### 占位符（placeholder）

顾名思义，占位符在声明的时候并没有值给它初始化，这也就是它为什么叫占位符的原因，仅仅起到一个占位置的作用，那它什么时候有值呢？它会在session中被赋值，也就是说，如果程序中不算一开始就给值的话，可以用占位符的方式。

```
import tensorflow as tf

input1 = tf.placeholder(tf.float32,shape=[1,1])
input2 = tf.placeholder(tf.float32,shape=[1,1])

output = tf.add(input1,input2)

with tf.Session() as sess:
    result = sess.run(output,feed_dict={input1:[[1]],input2:[[1]]})
    print(result)    
```

placeholder最终在sess.run()中用feed_dict{}进行输入，需要注意的是，即便这里shape是[1,1],后面输入时仍是[[1]]的形式

### Tensorboard

关于tensorboard的使用，大概分为一下几步：

1. `tf.summary.histogram()或者tf.summary.scalar()来绘制图层`，从名字上讲，histogram绘制的是柱状图，scalar绘制的是折线图，但其实我并不认识histogram绘制的是什么东西
2. `merged = tf.summary.merge_all`将所有的summary汇总在一起
3. `writer = tf.summary.FileWriter()`将event文件写到指定目录下
4. `result = sess.run(merged,feed_dict={...})`
5. `writer.add_summary(result,i)`
6. 然后在命令行中`tensorboard --logdir event文件目录`

### Regression代码分析

这里是一个回归分析的例子

```
# -*- coding: utf-8 -*-
"""
Created on Sat Jan  6 16:20:17 2018

@author: Terry
"""


import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt

#这里定义了隐含层
def add_layer(inputs, in_size, out_size, activation_function=None):     #参数包括输入值，输入值大小，输出值大小，以及激励函数
    Weights = tf.Variable(tf.random_normal([in_size, out_size]))        #这个隐藏层做的事情就是计算：输入*权重+偏置
    biases = tf.Variable(tf.zeros([1, out_size]) + 0.1)                 #如果有激励函数则把结果放到激励函数里再计算一次
    Wx_plus_b = tf.matmul(inputs, Weights) + biases
    if activation_function is None:
        outputs = Wx_plus_b
    else:
        outputs = activation_function(Wx_plus_b)
    return outputs

# Make up some real data
#在这里输入数据
x_data = np.linspace(-1, 1, 300, dtype=np.float32)[:, np.newaxis]
noise = np.random.normal(0, 0.05, x_data.shape).astype(np.float32)
y_data = np.square(x_data) - 0.5 + noise

##plt.scatter(x_data, y_data)
##plt.show()

# define placeholder for inputs to network
#这里是输入层，xs,ys都是需要输入的数据，只不过是在后面输入，所以这里使用了占位符
xs = tf.placeholder(tf.float32, [None, 1])
ys = tf.placeholder(tf.float32, [None, 1])

# add hidden layer
#这里是隐藏层
l1 = add_layer(xs , 1, 10, activation_function=tf.nn.relu)
# add output layer
prediction = add_layer(l1, 10, 1, activation_function=None)

# the error between prediction and real data
loss = tf.reduce_mean(tf.reduce_sum(tf.square(ys-prediction), reduction_indices=[1]))
train_step = tf.train.GradientDescentOptimizer(0.1).minimize(loss)
# important step
sess = tf.Session()
# tf.initialize_all_variables() no long valid from
# 2017-03-02 if using tensorflow >= 0.12
if int((tf.__version__).split('.')[1]) < 12 and int((tf.__version__).split('.')[0]) < 1:
    init = tf.initialize_all_variables()
else:
    init = tf.global_variables_initializer()
sess.run(init)

for i in range(1000):
    # training
    sess.run(train_step, feed_dict={xs: x_data, ys: y_data})
    if i % 50 == 0:
        # to see the step improvement
        print(sess.run(loss, feed_dict={xs: x_data, ys: y_data}))
```



它的学习过程是这样的，对于两个初始值xs，ys,xs会经过某种变换到达ys，这里我们通过隐含层，会计算出来一个Output,通过训练不断减小ys（理想值）和output（实际值）的误差，来达到学习的效果



### Classification代码分析

```
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 25 11:04:49 2018

@author: Arrow
"""

import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data

mnist = input_data.read_data_sets('MNIST_data',one_hot=True) #one-hot vector表示除了某一位的数字是一其他的都是0

def add_layer(inputs,in_size,out_size,activation_function=None):
    Weights = tf.Variable(tf.random_normal([in_size,out_size]))
    biases = tf.Variable(tf.zeros([1,out_size])+0.1)
    Wx_plus_b = tf.matmul(inputs,Weights)+biases
    if activation_function is None:
        outputs = Wx_plus_b
    else:
        outputs = activation_function(Wx_plus_b)
    return outputs

def compute_accuracy(v_xs,v_ys):
    global prediction
    y_pre = sess.run(prediction,feed_dict={xs:v_xs})
    correct_prediction = tf.equal(tf.argmax(y_pre,1),tf.arg_max(v_ys,1))
    accuracy = tf.reduce_mean(tf.cast(correct_prediction,tf.float32))
    result = sess.run(accuracy,feed_dict={xs:v_xs,ys:v_ys})
    return result

#define placeholder for inputs to network
    
xs = tf.placeholder(tf.float32,[None,784])
ys = tf.placeholder(tf.float32,[None,10])

# add output layer
prediction = add_layer(xs,784,10,activation_function=tf.nn.softmax)

#the error between prediction and real data
    #这里使用交叉熵来计算误差，对数里面的是预测值，外面的是实际值
cross_entropy = tf.reduce_mean(-tf.reduce_sum(ys * tf.log(prediction),reduction_indices=[1]))
    #使用梯度下降，学习速率为0.5进行训练
train_step = tf.train.GradientDescentOptimizer(0.5).minimize(cross_entropy)

sess  = tf.Session()
#important step
sess.run(tf.global_variables_initializer())

for i in range(1000):
    #每次随机抓取100个数据点进行训练
    batch_xs,batch_ys = mnist.train.next_batch(100)
    sess.run(train_step,feed_dict={xs:batch_xs,ys:batch_ys})
    #每训练50步打印一下精度，这里有一个很精妙的做法，打印精度输入的是test中的image和label,
    #训练用的数据集是train,那么训练结果是如何用到test数据集中的呢，这主要得益于compute_accuracy中
    #的全局变量prediction,prediction会调用add_layer方法，用已经经过训练的Weights和biases同test数据集中
    #的输入进行计算，这样就会得到test数据集中的预测值
    if i % 50 ==0:
        print(compute_accuracy(mnist.test.images,mnist.test.labels))
```

### dropout fix overfitting

```
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 28 15:10:29 2018

@author: Arrow
"""

import tensorflow as tf
from sklearn.datasets import load_digits
from sklearn.cross_validation import train_test_split
from sklearn.preprocessing import LabelBinarizer

digits = load_digits()
X = digits.data
y = digits.target
y = LabelBinarizer().fit_transform(y)
X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=.3)

tf.reset_default_graph()

def add_layer(inputs,in_size,out_size,layer_name,activation_function=None):
    Weights = tf.Variable(tf.random_normal([in_size,out_size]))
    biases = tf.Variable(tf.zeros([1,out_size]))+0.1
    Wx_plus_b = tf.matmul(inputs,Weights)+biases
    Wx_plus_b = tf.nn.dropout(Wx_plus_b,keep_prob)
    if activation_function is None:
        outputs = Wx_plus_b
    else:
        outputs = activation_function(Wx_plus_b)
    tf.summary.histogram(layer_name+'/outputs',outputs)
    
    return outputs


#define placeholder for inputs to network
keep_prob = tf.placeholder(tf.float32)
xs = tf.placeholder(tf.float32,[None,64])
ys = tf.placeholder(tf.float32,[None,10])

# add output layer
l1 = add_layer(xs,64,50,'l1',activation_function=tf.nn.tanh)
prediction = add_layer(l1,50,10,'l2',activation_function=tf.nn.softmax)

# the loss between prediction and real data
cross_entropy = tf.reduce_mean(-tf.reduce_sum(ys*tf.log(prediction),reduction_indices=[1]))

tf.summary.scalar('loss',cross_entropy)
train_step = tf.train.GradientDescentOptimizer(0.5).minimize(cross_entropy)

sess = tf.Session()

merged = tf.summary.merge_all()
train_writer = tf.summary.FileWriter("logs/train",sess.graph)
test_writer = tf.summary.FileWriter("logs/test",sess.graph)

init = tf.global_variables_initializer()

sess.run(init)

for i in range(500):
    
    sess.run(train_step,feed_dict={xs:X_train,ys:y_train,keep_prob:0.5})
    
    if i % 50 == 0:
        train_result = sess.run(merged,feed_dict={xs:X_train,ys:y_train,keep_prob:1})
        test_result = sess.run(merged,feed_dict={xs:X_test,ys:y_test,keep_prob:1})
        train_writer.add_summary(train_result,i)
        test_writer.add_summary(test_result,i)
        
```

有点不太明白的是，loss生成的是两个event文件，为什么最后显示在一张图里，难道说是tensorflow自己把logdir下的两个文件夹下的两个文件合并了么



#### 遇到的问题

+ `InvalidArgumentError: You must feed a value for placeholder tensor 'Placeholder' with dtype float`

  一直以为是占位符的问题，后来发现是tensorboard的问题，因为上述代码中其实是要绘制两份图表，大概是因为tensorflow的`tf.merge_all_summaries()`使用一个默认的图来收集我们的所有操作，包括此前进行的一些错误操作，所以我在所有的tf操作之前加了代码`tf.reset_default_graph()`就好了，更多请参考

  [这里]: https://stackoverflow.com/questions/35114376/error-when-computing-summaries-in-tensorflow

#### 一些小问题

+ 在引入matplotlib时，有错误显示`spyder No module named 'PyQt4'`，几经折腾，最后发现系统中有新版本PyQt5而默认设置还是4，所以打开Tools -> Preferences -> IPython console -> Graphics -> Backened 修改为QT5

### Convolution Neural Network

CNN常用在图片识别，计算机视觉等领域，它大概操作如下：

1. 对于一张图片，它有长宽高，这里的高指的是它是黑白还是彩色的
2. 然后有个过滤器，在图片上进行扫描，每次会扫描图片上的一小部分区域，经过一次扫描，会把这个图片压缩成，长和宽更小，高度更厚的一个图片，这个过程就叫做卷积。每次扫描多大一块区域呢，我们把这个叫做patch,有时候也叫它Kernel,还有一个术语叫stride,表示扫描时移动的步幅。这个过程其实就是对特征的多次提取，其中的高度就表特征，这样的过程重复几次后，会得到一个长宽很小，高度很厚的图片，
3. 然后把它放到全连接神经网络中进行分类。

如果每次扫描时stride过大，可能会造成信息的损失，这时候就需要pooling 池化来减少 这个效果。

根据扫描中如何处理边界，有valid padding和same padding，valid padding表示只处理图片边缘内容，不会涉及边缘以外的东西，same padding表示将图片边缘以外的东西用0来填充

#### 代码分析

```
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 29 13:54:21 2018

@author: Arrow
"""

import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data
# number 1 to 10 data
mnist = input_data.read_data_sets('MNIST_data', one_hot=True)

def add_layer(inputs, in_size, out_size, activation_function=None,):
    # add one more layer and return the output of this layer
    Weights = tf.Variable(tf.random_normal([in_size, out_size]))
    biases = tf.Variable(tf.zeros([1, out_size]) + 0.1,)
    Wx_plus_b = tf.matmul(inputs, Weights) + biases
    if activation_function is None:
        outputs = Wx_plus_b
    else:
        outputs = activation_function(Wx_plus_b,)
    return outputs

def compute_accuracy(v_xs, v_ys):
    global prediction
    y_pre = sess.run(prediction, feed_dict={xs: v_xs, keep_prob: 1})
    correct_prediction = tf.equal(tf.argmax(y_pre,1), tf.argmax(v_ys,1))
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
    result = sess.run(accuracy, feed_dict={xs: v_xs, ys: v_ys, keep_prob: 1})
    return result

#输入形状，返回权重
def weight_variable(shape):
    #产生正太分布，stddev是标准差
    initial = tf.truncated_normal(shape,stddev=0.1)
    return tf.Variable(initial)

#输入形状，返回偏置
def biase_variable(shape):
    initial = tf.constant(0.1,shape=shape)
    return tf.Variable(initial)

#定义一个二维的卷积神经网络
def conv2d(x,W):
    # strides=[1,x_movesize,y_movesize,1]
    return tf.nn.conv2d(x,W,strides=[1,1,1,1],padding='SAME')

def max_pool_2x2(x):
    return tf.nn.max_pool(x,ksize=[1,2,2,1],strides=[1,2,2,1],padding='SAME')

# define placeholder for inputs to network
xs = tf.placeholder(tf.float32, [None, 784]) # 28x28
ys = tf.placeholder(tf.float32, [None, 10])
keep_prob = tf.placeholder(tf.float32)

    # -1 表示暂时不考虑图片输入数量多少这个维度，1表示channel的数量
x_image = tf.reshape(xs,[-1,28,28,1])

##conv1 layer
    # 卷积和patch 5X5,channel 1,output height 32
W_conv1 = weight_variable([5,5,1,32])
b_conv1 = biase_variable([32])
    #output size 28x28x32 (SAME padding不改变长宽)
h_conv1 = tf.nn.relu(conv2d(x_image,W_conv1)+b_conv1)
    #output size 14x14x32 (pooling的步长是2) 
h_pool1 = max_pool_2x2(h_conv1)

##conv2 layer
W_conv2 = weight_variable([5,5,32,64])
b_conv2 = biase_variable([64])
    #output size 14x14x64 (SAME padding不改变长宽)
h_conv2 = tf.nn.relu(conv2d(h_pool1,W_conv2)+b_conv2)
    #output size 7x7x64 (pooling的步长是2) 
h_pool2 = max_pool_2x2(h_conv2)

##func1 layer
W_fc1 = weight_variable([7*7*64,1024])
b_fc1 = biase_variable([1024])
    #[n_samples,7,7,64] >> [n_samples,7*7*64]
h_pool2_flat = tf.reshape(h_pool2,[-1,7*7*64])
h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat,W_fc1)+b_fc1)
h_fc1_drop = tf.nn.dropout(h_fc1,keep_prob)

## func2 layer
W_fc2 = weight_variable([1024,10])
b_fc2 = biase_variable([10])
prediction = tf.nn.softmax(tf.matmul(h_fc1_drop,W_fc2)+b_fc2)


# the error between prediction and real data
cross_entropy = tf.reduce_mean(-tf.reduce_sum(ys * tf.log(prediction),
                                              reduction_indices=[1]))       # loss
train_step = tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)

sess = tf.Session()
# important step

init = tf.global_variables_initializer()
sess.run(init)

for i in range(1000):
    batch_xs, batch_ys = mnist.train.next_batch(100)
    sess.run(train_step, feed_dict={xs: batch_xs, ys: batch_ys,keep_prob:0.5})
    if i % 50 == 0:
        print(compute_accuracy(mnist.test.images, mnist.test.labels))
```



### RNN

![](https://ws1.sinaimg.cn/large/005UcYzagy1fsvuidhktdj30rz0j1acl.jpg)

用来做classification的例子

```
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 15:04:48 2018

@author: Arrow
"""

import tensorflow as tf

from tensorflow.examples.tutorials.mnist import input_data



# set random seed for comparing the two result calculations

tf.set_random_seed(1)



# this is data

mnist = input_data.read_data_sets('MNIST_data', one_hot=True)



# hyperparameters

lr = 0.001

training_iters = 100000

batch_size = 128



n_inputs = 28   # MNIST data input (img shape: 28*28)

n_steps = 28    # time steps

n_hidden_units = 128   # neurons in hidden layer

n_classes = 10      # MNIST classes (0-9 digits)



# tf Graph input

x = tf.placeholder(tf.float32, [None, n_steps, n_inputs])

y = tf.placeholder(tf.float32, [None, n_classes])



# Define weights

weights = {

    # (28, 128)

    'in': tf.Variable(tf.random_normal([n_inputs, n_hidden_units])),

    # (128, 10)

    'out': tf.Variable(tf.random_normal([n_hidden_units, n_classes]))

}

biases = {

    # (128, )

    'in': tf.Variable(tf.constant(0.1, shape=[n_hidden_units, ])),

    # (10, )

    'out': tf.Variable(tf.constant(0.1, shape=[n_classes, ]))

}





def RNN(X, weights, biases):

    # hidden layer for input to cell

    ########################################



    # transpose the inputs shape from

    # X ==> (128 batch * 28 steps, 28 inputs)

    X = tf.reshape(X, [-1, n_inputs])



    # into hidden

    # X_in = (128 batch * 28 steps, 128 hidden)

    X_in = tf.matmul(X, weights['in']) + biases['in']

    # X_in ==> (128 batch, 28 steps, 128 hidden)

    X_in = tf.reshape(X_in, [-1, n_steps, n_hidden_units])



    # cell

    ##########################################



    # basic LSTM Cell.

    if int((tf.__version__).split('.')[1]) < 12 and int((tf.__version__).split('.')[0]) < 1:

        cell = tf.nn.rnn_cell.BasicLSTMCell(n_hidden_units, forget_bias=1.0, state_is_tuple=True)

    else:

        cell = tf.contrib.rnn.BasicLSTMCell(n_hidden_units)

    # lstm cell is divided into two parts (c_state, h_state)

    init_state = cell.zero_state(batch_size, dtype=tf.float32)



    # You have 2 options for following step.

    # 1: tf.nn.rnn(cell, inputs);

    # 2: tf.nn.dynamic_rnn(cell, inputs).

    # If use option 1, you have to modified the shape of X_in, go and check out this:

    # https://github.com/aymericdamien/TensorFlow-Examples/blob/master/examples/3_NeuralNetworks/recurrent_network.py

    # In here, we go for option 2.

    # dynamic_rnn receive Tensor (batch, steps, inputs) or (steps, batch, inputs) as X_in.

    # Make sure the time_major is changed accordingly.

    outputs, final_state = tf.nn.dynamic_rnn(cell, X_in, initial_state=init_state, time_major=False)



    # hidden layer for output as the final results

    #############################################

    # results = tf.matmul(final_state[1], weights['out']) + biases['out']



    # # or

    # unpack to list [(batch, outputs)..] * steps

    if int((tf.__version__).split('.')[1]) < 12 and int((tf.__version__).split('.')[0]) < 1:

        outputs = tf.unpack(tf.transpose(outputs, [1, 0, 2]))    # states is the last outputs

    else:

        outputs = tf.unstack(tf.transpose(outputs, [1,0,2]))

    results = tf.matmul(outputs[-1], weights['out']) + biases['out']    # shape = (128, 10)



    return results





pred = RNN(x, weights, biases)

cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=pred, labels=y))

train_op = tf.train.AdamOptimizer(lr).minimize(cost)


# tf.argmax()用来返回当前向量最大值的索引，第二个参数是1表示按行，是0表示按列
correct_pred = tf.equal(tf.argmax(pred, 1), tf.argmax(y, 1))

accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))



with tf.Session() as sess:

    # tf.initialize_all_variables() no long valid from

    # 2017-03-02 if using tensorflow >= 0.12

    if int((tf.__version__).split('.')[1]) < 12 and int((tf.__version__).split('.')[0]) < 1:

        init = tf.initialize_all_variables()

    else:

        init = tf.global_variables_initializer()

    sess.run(init)

    step = 0

    while step * batch_size < training_iters:

        batch_xs, batch_ys = mnist.train.next_batch(batch_size)

        batch_xs = batch_xs.reshape([batch_size, n_steps, n_inputs])

        sess.run([train_op], feed_dict={

            x: batch_xs,

            y: batch_ys,

        })

        if step % 20 == 0:

            print(sess.run(accuracy, feed_dict={

            x: batch_xs,

            y: batch_ys,

            }))

        step += 1


```



CNN做regression的例子

```
"""
Know more, visit my Python tutorial page: https://morvanzhou.github.io/tutorials/
My Youtube Channel: https://www.youtube.com/user/MorvanZhou
Dependencies:
tensorflow: 1.1.0
matplotlib
numpy
"""
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt


# Hyper Parameters
TIME_STEP = 10       # rnn time step
INPUT_SIZE = 1      # rnn input size
CELL_SIZE = 32      # rnn cell size
LR = 0.02           # learning rate

# show data
steps = np.linspace(0, np.pi*2, 100, dtype=np.float32)
x_np = np.sin(steps); y_np = np.cos(steps)    # float32 for converting torch FloatTensor
plt.plot(steps, y_np, 'r-', label='target (cos)'); plt.plot(steps, x_np, 'b-', label='input (sin)')
plt.legend(loc='best'); plt.show()

# tensorflow placeholders
tf_x = tf.placeholder(tf.float32, [None, TIME_STEP, INPUT_SIZE])        # shape(batch, 5, 1)
tf_y = tf.placeholder(tf.float32, [None, TIME_STEP, INPUT_SIZE])          # input y

# RNN
rnn_cell = tf.contrib.rnn.BasicRNNCell(num_units=CELL_SIZE)
init_s = rnn_cell.zero_state(batch_size=1, dtype=tf.float32)    # very first hidden state
outputs, final_s = tf.nn.dynamic_rnn(
    rnn_cell,                   # cell you have chosen
    tf_x,                       # input
    initial_state=init_s,       # the initial hidden state
    time_major=False,           # False: (batch, time step, input); True: (time step, batch, input)
)
outs2D = tf.reshape(outputs, [-1, CELL_SIZE])                       # reshape 3D output to 2D for fully connected layer
net_outs2D = tf.layers.dense(outs2D, INPUT_SIZE)
outs = tf.reshape(net_outs2D, [-1, TIME_STEP, INPUT_SIZE])          # reshape back to 3D

loss = tf.losses.mean_squared_error(labels=tf_y, predictions=outs)  # compute cost
train_op = tf.train.AdamOptimizer(LR).minimize(loss)

sess = tf.Session()
sess.run(tf.global_variables_initializer())     # initialize var in graph

plt.figure(1, figsize=(12, 5)); plt.ion()       # continuously plot

for step in range(60):
    start, end = step * np.pi, (step+1)*np.pi   # time range
    # use sin predicts cos
    steps = np.linspace(start, end, TIME_STEP)
    x = np.sin(steps)[np.newaxis, :, np.newaxis]    # shape (batch, time_step, input_size)
    y = np.cos(steps)[np.newaxis, :, np.newaxis]
    if 'final_s_' not in globals():                 # first state, no any hidden state
        feed_dict = {tf_x: x, tf_y: y}
    else:                                           # has hidden state, so pass it to rnn
        feed_dict = {tf_x: x, tf_y: y, init_s: final_s_}
    _, pred_, final_s_ = sess.run([train_op, outs, final_s], feed_dict)     # train

    # plotting
    plt.plot(steps, y.flatten(), 'r-'); plt.plot(steps, pred_.flatten(), 'b-')
    plt.ylim((-1.2, 1.2)); plt.draw(); plt.pause(0.05)

plt.ioff(); plt.show()
```

上述例子中，shape的变化很烦人呐



综合上述两个例子，LSTMRNN的核心过程，input_layer,cell,output_layer,对此tensorflow已经为我们做了很大的集成工作，需要注意的是，input_layer阶段需要进行reshape,不过用心的tf api似乎没有这个问题，然后就是output_layer部分也要reshape,cell阶段主要是构建cell, init state,并执行RNN，框架大概就是i这样了。



### 损失函数

#### 

对损失函数求导，从而知道如何调节参数能够使损失函数超降低的方向发展。



![](https://ws1.sinaimg.cn/large/005UcYzagy1fw37i01r6nj30fr06st8w.jpg)

上图就是一个用于训练模型的迭代的方法。

#### 梯度下降法

梯度，是由偏导数组成的矢量，而偏导数，指的是多元函数对某一个自变量的导数（保持其他变量不变），偏导数在几何上反应出来的就是这个函数沿着该自变量维度的一个增减情况，所以由偏导数组成的梯度，就可以描述函数在整个定义域上的一个起伏情况。

通过梯度下降的方法，我们能够更快的找到损失最小的点。

#### 学习速率

这里会有一个学习速率的概念，其表示每次训练的一个步长，学习速率并非越大越好，因为有时学习速率交大时，可能直接跳过损失函数最小的点。例如，如果梯度大小为 2.5，学习速率为 0.01，则梯度下降法算法会选择距离前一个点 0.025 的位置作为下一个点。