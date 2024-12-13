FROM nvcr.io/nvidia/tritonserver:23.07-py3

RUN apt update

RUN pip install --upgrade pip

RUN pip install --no-cache-dir gdown==4.6.0

COPY triton_repository /triton_repository

RUN mkdir -p /triton_repository/dirty_roberta/1 /triton_repository/clean_roberta/1

RUN gdown "1-bIuzuFMtdT_ocq66Nokpz7BbCJzFqXl&confirm=t" -O /triton_repository/dirty_roberta/1/model.onnx

WORKDIR /triton_repository
