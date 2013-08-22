import json
import smtplib
import requests
import datetime
import jinja2 as jinja

from dateutil import tz
from email.mime.text import MIMEText

config = json.loads(open('config.json').read())

for key, value in config.items():
	locals()[key] = value

now = datetime.datetime.now().replace(tzinfo=tz.gettz('UTC')).astimezone(tz.gettz(TIMEZONE))
print now
def pad(string):
	string = str(string)
	if len(string) == 1:
		return '0%s' % string
	return string

def get_assignee(entry):
	try:
		return entry['assigned_to']['name']
	except KeyError:
		return '--'

projects = []

for project_name, project_id in PROJECTS:
	url = '%(base_url)s/issues.json?key=%(key)s&status_id=*&project_id=%(project_id)s&updated_on=%%3D%(year)s-%(month)s-%(day)s' % {
		'base_url': BASE_URL,
		'key': API_KEY,
		'project_id': project_id,
		'year': now.year,
		'month': pad(now.month),
		'day': pad(now.day),
	}

	status_stats = {}
	user_stats = {}
	entries = []

	response = requests.get(url).json()

	for entry in response['issues']:
		entries.append({
			'subject': entry['subject'],
			'assignee': get_assignee(entry),
			'author': entry['author']['name'],
			'status': entry['status']['name'],
			'url': '%s/issues/%s' % (BASE_URL, entry['id'])
		})

		status_stats.setdefault(entry['status']['name'], 0)
		status_stats[entry['status']['name']] += 1

		if entry['status']['name'] == 'Closed':
			user_stats.setdefault(get_assignee(entry), 0)
			user_stats[get_assignee(entry)] += 1

	projects.append({
		'name': project_name,
		'users': user_stats,
		'statuses': status_stats,
		'entries': entries,
	})

templ = jinja.Template(open('email.html').read())

rendered = templ.render({'projects': projects})

f = open('out.html', 'w')
f.write(rendered)
f.close()

message = MIMEText(rendered)
message['Subject'] = SUBJECT % now.ctime()
message['From'] = FROM
message['To'] = ','.join(TO)

s = smtplib.SMTP('localhost')
s.sendmail(FROM, TO, message.as_string())
s.quit()
