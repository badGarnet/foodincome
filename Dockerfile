FROM python:2.7

RUN mkdir /code
WORKDIR /code
ADD . /code/
RUN pip install -r requirements.txt

EXPOSE 33507
CMD ["python", "/code/foodincomeapp.py"]
