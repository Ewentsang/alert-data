#!/bin/bash

echo "正在使用清华镜像源安装依赖..."
echo ""

pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "依赖安装成功！"
else
    echo ""
    echo "安装失败，尝试使用阿里云镜像源..."
    pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
fi


