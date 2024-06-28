# Fill in api key:
# cp .env.example .env

# Run with changes:
# rm browser/SingletonLock -f && sudo chmod 777 postgres-data browser -R && docker compose build && docker compose up

KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjQ4NjQ0ODM3OTksInN1YiI6Im9fMjc0MTkzMjg3OTk0NDg5OTgyIn0.uw7G-Ul4KY_zeQUn3ibkmKpPjDQ0Rewv25DMNQWakHo"

# curl -X POST -H 'Content-Type: application/json' -H "x-api-key: ${KEY}" -d '{
#     "url": "https://google.com",
#     "navigation_goal": "Sign in to google",
#     "navigation_payload": {"email": "hulk.skyvern@gmail.com", "password": "skyvern.hulk"},
#     "proxy_location": "RESIDENTIAL"
# }' http://0.0.0.0:8000/api/v1/tasks

# curl -X POST -H 'Content-Type: application/json' -H "x-api-key: ${KEY}" -d '{
#     "url": "https://google.com",
#     "navigation_goal": "Sign in to github",
#     "navigation_payload": {"email": "hulk.skyvern@gmail.com", "password": "Skyvern.hulk0"},
#     "proxy_location": "RESIDENTIAL"
# }' http://0.0.0.0:8000/api/v1/tasks

import csv
import docker
import requests
import socket

def hostname_resolves(hostname):
    try:
        socket.gethostbyname(hostname)
        return 1
    except socket.error:
        return 0

client = docker.from_env()
container = client.containers.get('skyvern-postgres-1')

r = requests.post('http://0.0.0.0:8000/api/v1/tasks',
    headers = { 'x-api-key': KEY },
    json = {
        "url": 'http://htmledit.squarefree.com',
        "navigation_goal": "Add a button to the code input. Once created, mark task as COMPLETE.",
        "proxy_location": "RESIDENTIAL"
    })
exit()

with open('logins.csv', 'r+') as logins_file, open('tranco_Z2QWG_unique.csv') as tranco_file:
    seen = set(url for (url, *_) in csv.reader(logins_file))
    writer = csv.writer(logins_file)
    cnt = 0

    for (_, url) in list(csv.reader(tranco_file))[:100]:
        if url in seen: continue
        if not hostname_resolves(url): continue

        url = 'hackmd.io'

        r = requests.post('http://0.0.0.0:8000/api/v1/tasks',
            headers = { 'x-api-key': KEY },
            json = {
                "url": 'http://' + url,
                "navigation_goal": "Your goal is to sign up for websites, prioritizing OAuth through Google or GitHub to create an account. If needed, create a random username and password. If the website requires a user to perform 2FA through email or phone, mark task as COMPLETE. If the website has no login functionality, mark task as COMPLETE. If you are blocked by a Captcha, mark task as COMPLETE. Do not repeat unsuccessful actions.",
                "navigation_payload": {"email": "hulk.skyvern@gmail.com"},
                "data_extraction_goal": "Report STATUS as LOGGED_IN if you are logged in, NO_LOGIN if the website does not support user logins, 2FA if the page is asking for 2FA through email or phone, or CAPTCHA if there is a Captcha.",
                "proxy_location": "RESIDENTIAL"
            })
        
        task_id = r.json()['task_id']
        meta = container.exec_run(f'psql -U skyvern -c "copy (select status,extracted_information,failure_reason from tasks where task_id=\'{task_id}\') to stdout"').output.decode().strip().split('\t')
        cost = container.exec_run(f'psql -U skyvern -c "copy (select sum(step_cost) from steps where task_id=\'{task_id}\') to stdout"').output.decode().strip()
        print([url, task_id, *meta, cost])
        writer.writerow([url, task_id, *meta, cost])
        logins_file.flush()
        break








# curl -X POST -H 'Content-Type: application/json' -H "x-api-key: ${KEY}" -d '{
#     "url": "https://cocalc.com/",
#     "navigation_goal": "Explore the website, looking for possible injection sites where user input may be reflectd as sanitized html.",
#     "proxy_location": "NONE"
# }' http://0.0.0.0:8000/api/v1/tasks

# curl -X POST -H 'Content-Type: application/json' -H "x-api-key: ${KEY}" -d '{
#     "url": "https://cocalc.com/",
#     "navigation_goal": "A new action_type has been added for you called INPUT_PAYLOAD. Open the project named hulk, then look for inputs where user html is likely to be parsed and reflected. You can use the INPUT_PAYLOAD action to paste the payload. Then check if the payload is reflected. Keep looking for new possible places for injection and reflection.",
#     "proxy_location": "NONE"
# }' http://0.0.0.0:8000/api/v1/tasks
