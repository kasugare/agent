curl --location --request POST 'http://127.0.0.1:8080/api/v1/predict/async/web' \
--header 'X-SAMPL-JOB-ID: test' \
--header 'X-SAMPL-MEMBER-ID: test' \
--header 'X-SAMPL-CALLBACK: http%3A%2F%2F127.0.0.1%3A9000%2Fv1%2Fsuccess' \
--header 'X-SAMPL-ERR-CALLBACK: http%3A%2F%2F127.0.0.1%3A9000%2Fv1%2Ferror' \
--header 'X-SAMPL-USER-DATA: test' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxOTU1RjdGM0NGOSIsImlhdCI6MTc0MTEzMDY0OCwidXNyX2lkIjoiMTk1NUY3RjNDRjkiLCJlbXBuIjoiNzk3ODciLCJlbWFpbCI6InJvb3RUZXN0QGhhbmFmbi5jb20iLCJjbXB5X2NkIjoiRFQiLCJleHAiOjE3NDM3NTUwNDh9.fm_lIm6vroZXK4QXtpmVuIcDhkOOo34Sky_vyXDfb1M' \
--form 'file=@"/Users/hanati/workspace/agent/test/dtm_adapter/test/dummy.py"' \
--form 'data="{\"job_id\": \"chauwli1keid9w01u84yuk1o2sidl23a\",\"job\": \"Detection\",\"project\": \"ocr\",\"blueprint\": \"detection\",\"conveyor\": \"application\",\"tags\": {\"uuid\": \"ldj9l29i09id9w01u84yuq0a9sidles1\",},\"data\": {\"user_id\": \"admin\",\"user_uid\": 1,\"site_uid\": 9,\"infer_uid\": 21,\"batch_uid\": \"ldj9l29i09id9w01u84yuq0a9sidles1\",\"uuid\": \"ldj9l29i09id9w01u84yuq0a9sidles1\"}}"'
