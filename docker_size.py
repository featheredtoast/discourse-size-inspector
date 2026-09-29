import sys
import subprocess
import json
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BYTES_TO_MB = 1048576.0

def autopct_format(values):
    def my_format(pct):
        total = sum(values)
        val = int(round((pct*total/100.0)/BYTES_TO_MB))
        return '{:.1f}%\n({v:d}MB)'.format(pct, v=val)
    return my_format

def get_image_details(image):
    return [
        image["name"],
        image["data"]["breakdown"]["node_modules"],
        image["data"]["breakdown"]["libraries"],
        image["data"]["breakdown"]["code_gems"],
        image["data"]["breakdown"]["ruby"],
        image["data"]["breakdown"]["redis_pg"],
        image["data"]["breakdown"]["runtime_deps"],
        image["data"]["breakdown"]["buildtime_deps"],
        image["data"]["breakdown"]["pups_run"],
        image["data"]["breakdown"]["other"],
    ]

def make_chart(images):
    print(get_image_details(images[0]))
    print(get_image_details(images[1]))
    df = pd.DataFrame([get_image_details(images[0]), get_image_details(images[1])],
                  columns=[
                      "image",
                      "node_modules",
                      "libraries",
                      "code_gems"
                      "ruby",
                      "redis_pg",
                      "runtime_deps",
                      "buildtime_deps",
                      "pups_run",
                      "other",
                  ])
    # view data
    print(df)

    # plot data in stack manner of bar type
    df.plot(x='image', kind='bar', stacked=True,
        title='Stacked Bar Graph by dataframe')
#    layer_labels = layer_buckets_label_size.keys()
#    layer_sizes = layer_buckets_label_size.values()
#    layer_mb = [value / BYTES_TO_MB for value in layer_sizes]
#
#    layer_size_label = int(round(total_image_size/BYTES_TO_MB))
#
#    # Create the bar chart
#    plt.bar(layer_labels, layer_mb)
#    plt.ylabel('Size in MB')
#    plt.title('Total: {v:d}MB'.format(v=layer_size_label))
    plt.show()

def collect_layer_details(image_name):
    history_output = '['+subprocess.check_output(["docker", "history", "--no-trunc", "--format=json", "--human=false", image_name]).decode("utf-8").replace("\n", ",\n").strip(",\n")+']'
    history_json = json.loads(history_output)

    layer_buckets_label_size = {"node_modules": 0, "libraries": 0, "code_gems": 0, "ruby": 0, "redis_pg": 0, "runtime_deps": 0, "buildtime_deps": 0, "pups_run": 0, "other": 0}

    total_image_size = 0
    for layer in history_json:
        val = int(layer["Size"])
        total_image_size += val
        if re.search("pnpm install", layer["CreatedBy"]):
            layer_buckets_label_size["node_modules"] += val
        elif re.search("git clone .* https://github.com/discourse/discourse.git", layer["CreatedBy"]):
            layer_buckets_label_size["code_gems"] += val
        elif re.search("bundle install", layer["CreatedBy"]):
            layer_buckets_label_size["code_gems"] += val
        elif re.search("COPY /var/www/discourse/vendor/bundle", layer["CreatedBy"]):
            layer_buckets_label_size["code_gems"] += val
        elif re.search("apt-get -y install .* sudo", layer["CreatedBy"]):
            layer_buckets_label_size["runtime_deps"] += val
        elif re.search("rustArch", layer["CreatedBy"]):
            layer_buckets_label_size["ruby"] += val
        elif re.search("COPY --chown=discourse:discourse /var/www/discourse/ /var/www/discourse", layer["CreatedBy"]):
            layer_buckets_label_size["code_gems"] += val
        elif re.search("COPY --chown=discourse:discourse(.*)node_modules", layer["CreatedBy"]):
            layer_buckets_label_size["node_modules"] += val
        elif re.search("apt-get -y install redis", layer["CreatedBy"]):
            layer_buckets_label_size["redis_pg"] += val
        elif re.search("postgresql-", layer["CreatedBy"]):
            layer_buckets_label_size["redis_pg"] += val
        elif re.search("cmake", layer["CreatedBy"]) or re.search("npm install -g pnpm", layer["CreatedBy"]):
            layer_buckets_label_size["buildtime_deps"] += val
        elif re.search("gnupg", layer["CreatedBy"]):
            layer_buckets_label_size["runtime_deps"] += val
        elif re.search("nginx-light", layer["CreatedBy"]) or re.search("locale-gen", layer["CreatedBy"]):
            layer_buckets_label_size["runtime_deps"] += val
        elif re.search("pups --skip-tags", layer["CreatedBy"]):
            layer_buckets_label_size["pups_run"] += val
        else:
            #print(layer["CreatedBy"])
            layer_buckets_label_size["other"] += val
    return {"total": total_image_size, "breakdown": layer_buckets_label_size}


image_name_1 = sys.argv[1]
image_name_2 = sys.argv[2]

images = [{"name": image_name_1, "data": collect_layer_details(image_name_1)},
          {"name": image_name_2, "data": collect_layer_details(image_name_2)}]
make_chart(images)
