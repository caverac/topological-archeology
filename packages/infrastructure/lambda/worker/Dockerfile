FROM public.ecr.aws/lambda/python:3.14-arm64

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY disk-evolution-src/ /tmp/disk-evolution-src/
RUN pip install --no-cache-dir /tmp/disk-evolution-src/ && rm -rf /tmp/disk-evolution-src/

COPY handler.py ${LAMBDA_TASK_ROOT}/

CMD ["handler.handler"]
