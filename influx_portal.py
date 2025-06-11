from os import environ
from datetime import datetime, UTC
#  pip install influxdb-client
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


class InfluxClient():
    # You can generate a Token from the "Tokens Tab" in the UI
    TOKEN = 'kgTVfHMPYfZ9oq2a-rD5HVQO2JR1q83qvaazPUE_MCpO-2ACnXIukiyyNHng7TA9x3CsdIAPdfNbb0HxJKdT2w=='
    ORG = 'Portal'

    def __init__(self, bucket: str) -> None:
        self.bucket = bucket
        self.client = InfluxDBClient(url=f"http://{environ['SERVER_IP']}:8086", token=InfluxClient.TOKEN)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def send(self, point: Point, add_timestamp=False):
        if add_timestamp:
            point = point.time(datetime.now(tz=UTC))
        self.write_api.write(self.bucket, InfluxClient.ORG, point)

    def close(self):
        self.write_api.close()
        self.client.close()
