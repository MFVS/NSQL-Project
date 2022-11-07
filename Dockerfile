FROM python:3.9.0-slim

RUN mkdir /install
WORKDIR /install

COPY requirements.txt requirements.txt

# RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

ENV FLASK_APP app.py
WORKDIR /project
# COPY --from=builder /install /usr/local
ADD . /project
EXPOSE 5000
ENTRYPOINT ["python", "-m", "flask", "run", "--host=0.0.0.0"]