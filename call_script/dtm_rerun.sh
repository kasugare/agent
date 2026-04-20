curl --location --request POST http://127.0.0.1:8080/api/v1/rerun \
 -H "Content-Type: application/json" \
 -H "X-CALLBACKABLE: false" \
 -H "job-id: test"
