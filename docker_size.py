import sys
import subprocess
import json
import re

import matplotlib.pyplot as plt

BYTES_TO_MB = 1048576.0

def autopct_format(values):
    def my_format(pct):
        total = sum(values)
        val = int(round((pct*total/100.0)/BYTES_TO_MB))
        return '{:.1f}%\n({v:d}MB)'.format(pct, v=val)
    return my_format

def make_chart(layer_buckets_label_size, total_image_size):
    layer_labels = layer_buckets_label_size.keys()
    layer_sizes = layer_buckets_label_size.values()
    layer_mb = [value / BYTES_TO_MB for value in layer_sizes]

    layer_size_label = int(round(total_image_size/BYTES_TO_MB))

    # Create the bar chart
    plt.bar(layer_labels, layer_mb)
    plt.ylabel('Size in MB')
    plt.title('Docker Image Layer Sizes: {v:d}MB'.format(v=layer_size_label))
    plt.show()

image_name = sys.argv[1]
history_output = '['+subprocess.check_output(["docker", "history", "--no-trunc", "--format=json", "--human=false", image_name]).decode("utf-8").replace("\n", ",\n").strip(",\n")+']'
history_json = json.loads(history_output)

layer_buckets_label_size = {"other": 0, "node_modules": 0, "code": 0, "gems": 0, "ruby": 0, "libraries": 0}

total_image_size = 0
for layer in history_json:
    val = int(layer["Size"])
    total_image_size += val
    if re.search("pnpm install", layer["CreatedBy"]):
        layer_buckets_label_size["node_modules"] += val
    elif re.search("git clone .* https://github.com/discourse/discourse.git", layer["CreatedBy"]):
        layer_buckets_label_size["code"] += val
    elif re.search("bundle install", layer["CreatedBy"]):
        layer_buckets_label_size["gems"] += val
    elif re.search("apt-get -y install .* sudo", layer["CreatedBy"]):
        layer_buckets_label_size["libraries"] += val
    elif re.search("rustArch", layer["CreatedBy"]):
        layer_buckets_label_size["ruby"] += val
    else:
        layer_buckets_label_size["other"] += val

# zero values cannot be displayed
filtered_layer_buckets = {k: v for k, v in layer_buckets_label_size.items() if v > 0}
filtered_layer_buckets = dict(reversed(sorted(filtered_layer_buckets.items(), key=lambda item: item[1])))
make_chart(filtered_layer_buckets, total_image_size)
