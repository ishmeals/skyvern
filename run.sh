#!/bin/bash

# Fill in api key:
# cp .env.example .env

# Run with changes:
# sudo chmod 777 postgres-data browser -R && docker compose build && docker compose up

KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjQ4NjA3MTIzODksInN1YiI6Im9fMjU3OTk1MjAzOTgwODA4NTk2In0.T6Fq_hcUCFJQwQs2jwz2L8rf1iiKNvJvLqQL1GLK8r8"

curl -X POST -H 'Content-Type: application/json' -H "x-api-key: ${KEY}" -d '{
    "url": "https://google.com",
    "webhook_callback_url": "",
    "navigation_goal": "This is a test. Do not do anything. Just report completed",
    "data_extraction_goal": "",
    "navigation_payload": "",
    "proxy_location": "NONE"
}' http://0.0.0.0:8000/api/v1/tasks

# curl -X POST -H 'Content-Type: application/json' -H "x-api-key: ${KEY}" -d '{
#     "url": "https://google.com",
#     "webhook_callback_url": "",
#     "navigation_goal": "Sign in. Email: wasd0123210@gmail.com Password: 0123210wasd",
#     "data_extraction_goal": "",
#     "navigation_payload": "",
#     "proxy_location": "NONE"
# }' http://0.0.0.0:8000/api/v1/tasks

# curl -X POST -H 'Content-Type: application/json' -H "x-api-key: ${KEY}" -d '{
#     "url": "https://www.adobe.com",
#     "webhook_callback_url": "",
#     "navigation_goal": "Your goal is to log in. Create an account if needed, preferably using the existing Google account. Report the credentials. If needed, the username should be wasd0123210 and the password F34*nz$H&po2 If you see a Captcha, quit and report an error.",
#     "data_extraction_goal": "",
#     "navigation_payload": "",
#     "proxy_location": "NONE"
# }' http://0.0.0.0:8000/api/v1/tasks
