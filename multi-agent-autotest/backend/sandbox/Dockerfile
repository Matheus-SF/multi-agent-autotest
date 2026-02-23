FROM python:3.11-slim

RUN useradd -m sandbox

RUN pip install pytest pytest-cov --no-cache-dir

WORKDIR /code

USER sandbox

CMD ["pytest", "--cov=/code", "--cov-report=xml", "--cov-report=html"]