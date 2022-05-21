import csv
import logging
import datetime
import re
import sys
from urllib.error import HTTPError
from todoist_api_python.api import TodoistAPI

LOG_PATH = './logs/'


class Task:

    def __init__(self, project, content='', description='', priority=4, indent=1, due_string='', parent_id=''):
        self.project = project
        self.content = content
        self.description = description
        self.priority = priority
        self.due_string = due_string
        self.parent_id = parent_id
        self.indent = indent

    def push(self, api, all_labels=[]):
        self.content = self.content.replace(
            '$project', f'**{self.project.name}**')

        labels_in_content = re.findall(r'@[a-zA-Z]+', self.content)

        self.content = re.sub(r'@[a-zA-Z]+', '', self.content)

        task = api.add_task(
            content=self.content,
            description=self.description,
            due_string=self.due_string,
            due_lang='en',
            priority=self.normalize_priority(self.priority),
            parent_id=self.parent_id,
            project_id=self.project.id
        )

        label_ids = []

        for label_text in labels_in_content:
            label_text = label_text.replace('@', '')
            label = self.find_label(label_text, all_labels)

            if label == None:
                label = api.add_label(name=label_text)

            label_ids.append(label.id)

        api.update_task(task_id=task.id, label_ids=label_ids)

        return task

    def normalize_priority(self, input_prio):
        prio_normalization_mapping = {
            '1': 4,
            '2': 3,
            '3': 2,
            '4': 1,
        }
        return prio_normalization_mapping[str(input_prio)]

    def find_label(self, search_query, labels_list):
        for label in labels_list:
            if label.name == search_query.strip():
                return label

        return None


if __name__ == '__main__':

    print('Connecting to your Todoist Account...')

    with open('./todoist_api_key.txt') as api_key_file:
        api_key = api_key_file.read()

    try:
        api = TodoistAPI(api_key)
        api.get_projects()
    except:
        print('Unable to connect with your Account')
        print('Make sure your API key is in todoist_api_key.txt')
        exit()

    all_labels = api.get_labels()

    project_name = input('Project Name: ')
    project = api.add_project(name=project_name, color=31)

    template_name = input('Template Name: ')

    print('Constructing project...')

    task_list = []

    # Uses the official CSV exported by Todoist
    with open(f'./project_templates/{template_name}.csv') as template_csv:
        csv_reader = csv.reader(template_csv, delimiter=',')
        next(csv_reader)  # skip header
        for row in csv_reader:
            if row[0].strip() == '':
                continue

            task = Task(project)
            task.content = row[1].strip()
            task.priority = int(row[3].strip())
            task.due_string = row[7].strip()

            task.indent = int(row[4].strip())
            task_list.append(task)

    current_parent_id = project.id
    for i in range(len(task_list)):
        if i > 0:
            if task_list[i].indent > task_list[i-1].indent:
                current_parent_id = previous_task.id
            elif task_list[i].indent < task_list[i-1].indent:
                current_parent_id = project.id

            task_list[i].parent_id = current_parent_id

        previous_task = task_list[i].push(api, all_labels)
        print(f'Added {i+1} tasks')

    input('Done! Press ENTER to exit')
