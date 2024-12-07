FROM python:3.12.8-slim

WORKDIR /app

COPY ./pyproject.toml .
RUN pip install .

COPY ./app app

EXPOSE 8000
CMD ["fastapi", "run", "app/main.py"]