FROM python:3.12.14-slim
WORKDIR /app
COPY . /app
ENV PYTHONDONTWRITEBYTECODE=1 MEDCURA_DATA=/var/lib/medcura
RUN useradd --system --create-home medcura && mkdir -p /var/lib/medcura && chown medcura /var/lib/medcura
USER medcura
EXPOSE 8765
CMD ["python","run.py","--container"]

