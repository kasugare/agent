for i in {1..1000000}
do
 time  curl -X 'GET' 'http://127.0.0.1:18000/api/v1/call_api' -H 'accept: application/json' &
sleep 0.2
done

