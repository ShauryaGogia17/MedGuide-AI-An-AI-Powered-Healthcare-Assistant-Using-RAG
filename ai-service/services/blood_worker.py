"""Isolated TensorFlow worker; never imports or runs upstream Python source."""
import json
import io
import sys


def main():
    mode, checkpoint = sys.argv[1:3]
    import cv2
    import numpy as np
    import tensorflow as tf

    tf.compat.v1.disable_eager_execution()
    graph = tf.Graph()
    with graph.as_default():
        saver = tf.compat.v1.train.import_meta_graph(checkpoint + '.meta', clear_devices=True)
        image = graph.get_tensor_by_name('xPlaceholder:0')
        probabilities = graph.get_tensor_by_name('tiny_yolo/Reshape_1:0')
        if image.shape.as_list() != [None, 224, 224, 3]:
            raise ValueError('Unexpected checkpoint input shape')
    options = tf.compat.v1.ConfigProto(device_count={'GPU': 0}, intra_op_parallelism_threads=2, inter_op_parallelism_threads=1)
    with tf.compat.v1.Session(graph=graph, config=options) as session:
        saver.restore(session, checkpoint)
        if mode == 'status':
            batch = np.zeros((1, 224, 224, 3), dtype=np.float32)
        elif mode == 'infer':
            width, height = map(int, sys.argv[3:5])
            if min(width, height) < 32 or max(width, height) > 8192 or width * height > 16_000_000:
                raise ValueError('Unexpected image dimensions')
            pixels = sys.stdin.buffer.read(width * height * 3 + 1)
            if len(pixels) != width * height * 3:
                raise ValueError('Unexpected image byte count')
            rgb = np.frombuffer(pixels, dtype=np.uint8).reshape(height, width, 3)
            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            resized = cv2.resize(bgr, (224, 224), interpolation=cv2.INTER_LINEAR)
            batch = resized.reshape(1, 224, 224, 3).astype(np.float32) / 127.5 - 1.0
        else:
            raise ValueError('Unsupported worker mode')
        result = session.run(probabilities, feed_dict={image: batch})
    if result.shape != (1, 224, 224, 11) or not np.isfinite(result).all():
        raise ValueError('Unexpected checkpoint output')
    if mode == 'status':
        print(json.dumps({'ready': True, 'framework': 'TensorFlow ' + tf.__version__, 'input_size': [224, 224]}))
    else:
        output = io.BytesIO()
        np.save(output, result[0], allow_pickle=False)
        sys.stdout.buffer.write(output.getvalue())


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Keep native framework logs out of HTTP responses and avoid patient data.
        sys.stderr.write('blood_worker_failed type=' + type(error).__name__ + '\n')
        sys.exit(3)
