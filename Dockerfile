# 二开推荐阅读[如何提高项目构建效率](https://developers.weixin.qq.com/miniprogram/dev/wxcloudrun/src/scene/build/speed.html)
# 选择构建用基础镜像（选择原则：在包含所有用到的依赖前提下尽可能体积小）。如需更换，请到[dockerhub官方仓库](https://hub.docker.com/_/python?tab=tags)自行选择后替换。
# 已知alpine镜像与pytorch有兼容性问题会导致构建失败，如需使用pytorch请务必按需更换基础镜像。

FROM python:3.8-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install --no-install-recommends -y \
    libxslt-dev \
    libjpeg-dev \
    libfreetype-dev \
    zlib1g \
    libffi-dev \
    python3-dev \
    libc-dev

COPY .deploy/requirements.txt /app

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn


RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r /app/requirements.txt

FROM python:3.8-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    clang-format \
    ca-certificates \
    gettext && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get tzdata && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo Asia/Shanghai > /etc/timezone

RUN rm -rf /var/lib/apt/lists/*


RUN --mount=type=bind,from=builder,source=/app/wheels,target=/wheels pip install --no-cache /wheels/*

COPY . /app


## 选用国内镜像源以提高下载速度
#RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tencent.com/g' /etc/apk/repositories \
#&& apk add --update --no-cache python3 py3-pip \
#&& rm -rf /var/cache/apk/*


#RUN pip config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple \
#&& pip config set global.trusted-host mirrors.cloud.tencent.com \
#&& pip install --upgrade pip \
#&& pip install --user -r requirements.txt

# pip install scipy 等数学包失败，可使用 apk add py3-scipy 进 行， 参考安装 https://pkgs.alpinelinux.org/packages?name=py3-scipy&branch=v3.13




# 暴露端口
# 此处端口必须与「服务设置」-「流水线」以及「手动上传代码包」部署时填写的端口一致，否则会部署失败。
EXPOSE 80


# 执行启动命令
# 写多行独立的CMD命令是错误写法！只有最后一行CMD命令会被执行，之前的都会被忽略，导致业务报错。
# 请参考[Docker官方文档之CMD命令](https://docs.docker.com/engine/reference/builder/#cmd)
#CMD ["python3", "manage.py", "runserver", "0.0.0.0:80"]

ENTRYPOINT ["sh", "/app/.deploy/entrypoint.sh"]

# RUN python3 manage.py migrate --no-input
