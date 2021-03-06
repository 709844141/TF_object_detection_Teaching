'''
运行命令：
python generate_tfrecord.py --csv_input=images/train/person.csv  --output_path=data/train.record
python generate_tfrecord.py --csv_input=images/test/person.csv  --output_path=data/test.record
'''

'''
文件说明：
使用方法及需要修改的地方：
1.
#下面这里改到自己的object_detection路径，也就是本py文件所在的路径，可以相对路径，也可以用绝对路径（其实你要是放在object_detection下的话，这个改成./就行了，但是改绝对路径肯定没错啦）
os.chdir('/Users/junbin/Documents/GitHub/TensorFlow/models/research/object_detection')

2.
# 修改标签名字
# 如果有多个标签，改为如下格式
def class_text_to_int(row_label):
    if row_label == '标签1':
        return 1
    elif row_label== '标签2':
        return 2
    ……
    else:
        None

3.
png或者.jpg，根据你用的图片的格式改

4.
#训练图片的csv文件保存在images下的train文件夹下，当然你也可以改名或者调整文件结构
path = os.path.join(os.getcwd(), 'images/train')

5.文件架构（generate_tfrecord.py本文件在object_detection目录中，该目录是tf的oj模型。对应有很多很多文件和文件夹，我只提到有用的或者需要自己修改的）
-images
    --train
        ---各种图片和xml文件
    --test
        ---各种图片和xml文件

'''



import os
import io
import pandas as pd
import tensorflow as tf

from PIL import Image
from object_detection.utils import dataset_util
from collections import namedtuple, OrderedDict

#这里改到自己的object_detection路径下，也就是本py文件所在的路径
os.chdir('/Users/junbin/Documents/GitHub/TensorFlow/models/research/object_detection')

flags = tf.app.flags
flags.DEFINE_string('csv_input', '', 'Path to the CSV input')
flags.DEFINE_string('output_path', '', 'Path to output TFRecord')
FLAGS = flags.FLAGS


# TO-DO replace this with label map
def class_text_to_int(row_label):
    if row_label == 'galsses':    #修改标签名
        return 1
    else:
        None


def split(df, group):
    data = namedtuple('data', ['filename', 'object'])
    gb = df.groupby(group)
    return [data(filename, gb.get_group(x)) for filename, x in zip(gb.groups.keys(), gb.groups)]


def create_tf_example(group, path):
    with tf.gfile.GFile(os.path.join(path, '{}'.format(group.filename)), 'rb') as fid:
        encoded_jpg = fid.read()
    encoded_jpg_io = io.BytesIO(encoded_jpg)
    image = Image.open(encoded_jpg_io)
    width, height = image.size

    filename = group.filename.encode('utf8')
    #.jpg或是.png
    image_format = b'jpg'
    xmins = []
    xmaxs = []
    ymins = []
    ymaxs = []
    classes_text = []
    classes = []

    for index, row in group.object.iterrows():
        xmins.append(row['xmin'] / width)
        xmaxs.append(row['xmax'] / width)
        ymins.append(row['ymin'] / height)
        ymaxs.append(row['ymax'] / height)
        classes_text.append(row['class'].encode('utf8'))
        classes.append(class_text_to_int(row['class']))

    tf_example = tf.train.Example(features=tf.train.Features(feature={
        'image/height': dataset_util.int64_feature(height),
        'image/width': dataset_util.int64_feature(width),
        'image/filename': dataset_util.bytes_feature(filename),
        'image/source_id': dataset_util.bytes_feature(filename),
        'image/encoded': dataset_util.bytes_feature(encoded_jpg),
        'image/format': dataset_util.bytes_feature(image_format),
        'image/object/bbox/xmin': dataset_util.float_list_feature(xmins),
        'image/object/bbox/xmax': dataset_util.float_list_feature(xmaxs),
        'image/object/bbox/ymin': dataset_util.float_list_feature(ymins),
        'image/object/bbox/ymax': dataset_util.float_list_feature(ymaxs),
        'image/object/class/text': dataset_util.bytes_list_feature(classes_text),
        'image/object/class/label': dataset_util.int64_list_feature(classes),
    }))
    return tf_example


def main(_):
    writer = tf.python_io.TFRecordWriter(FLAGS.output_path)
    #训练的图片保存在images文件夹下，当然你也可以改名或者调整文件结构
    path = os.path.join(os.getcwd(), 'images/train')
    examples = pd.read_csv(FLAGS.csv_input)
    grouped = split(examples, 'filename')
    for group in grouped:
        tf_example = create_tf_example(group, path)
        writer.write(tf_example.SerializeToString())

    writer.close()
    output_path = os.path.join(os.getcwd(), FLAGS.output_path)
    print('Successfully created the TFRecords: {}'.format(output_path))


if __name__ == '__main__':
    tf.app.run()