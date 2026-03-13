from kafka import KafkaConsumer

try:
    consumer = KafkaConsumer(bootstrap_servers=['localhost:9092'])
    print("연결 성공:", consumer.topics())
    consumer.close()
except Exception as e:
    print(f"연결 실패: {e}")