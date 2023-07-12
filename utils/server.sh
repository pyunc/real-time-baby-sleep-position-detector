curl -sSOL https://dlcdn.apache.org/kafka/3.5.0/kafka_2.13-3.5.0.tgz
tar -xzf kafka_2.13-3.5.0.tgz
./kafka_2.13-3.5.0/bin/zookeeper-server-start.sh -daemon ./kafka_2.13-3.5.0/config/zookeeper.properties
./kafka_2.13-3.5.0/bin/kafka-server-start.sh -daemon ./kafka_2.13-3.5.0/config/server.properties
echo "Waiting for 10 secs until kafka and zookeeper services are up and running"
sleep 10

./kafka_2.13-3.5.0/bin/kafka-topics.sh --create --bootstrap-server 127.0.0.1:9092 --replication-factor 1 --partitions 1 --reset-offsets --to-earliest --all-topics --execute
./kafka_2.13-3.5.0/bin/kafka-topics.sh --create --bootstrap-server 127.0.0.1:9092 --replication-factor 1 --partitions 1 --topic RAW_SENSORS
./kafka_2.13-3.5.0/bin/kafka-topics.sh --create --bootstrap-server 127.0.0.1:9092 --replication-factor 1 --partitions 1 --topic     

