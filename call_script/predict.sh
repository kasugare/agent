curl --location --request POST 'http://127.0.0.1:8080/api/v1/predict/web' \
--header 'X-SAMPL-JOB-ID: test' \
--header 'X-SAMPL-MEMBER-ID: test' \
--header 'X-SAMPL-CALLBACK: http://127.0.0.1:9000/v1/success' \
--header 'X-SAMPL-ERR-CALLBACK: http://127.0.0.1:9000/v1/error' \
--header 'X-SAMPL-USER-DATA: test' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxOTU1RjdGM0NGOSIsImlhdCI6MTc0MTEzMDY0OCwidXNyX2lkIjoiMTk1NUY3RjNDRjkiLCJlbXBuIjoiNzk3ODciLCJlbWFpbCI6InJvb3RUZXN0QGhhbmFmbi5jb20iLCJjbXB5X2NkIjoiRFQiLCJleHAiOjE3NDM3NTUwNDh9.fm_lIm6vroZXK4QXtpmVuIcDhkOOo34Sky_vyXDfb1M' \
--form 'files=@"/Users/hanati/workspace/agent/test/dtm_adapter/test/dummy.py"' \
--form 'data="{}"'
