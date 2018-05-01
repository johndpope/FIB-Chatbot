#!/usr/bin/env python
# -*- coding: utf-8 -*-

#-- General imports --#
from random import randint
import json

#-- 3rd party imports --#
from rasa_core.actions.action import Action
from rasa_core.events import SlotSet

#-- Local imports --#
from Fibot.api.api_raco import API_raco
from Fibot.chats import Chats
from Fibot.Data.data_types.lecture import Lecture, Schedule
from Fibot.Data.data_types.subject_spots import Subject_spots
from Fibot.Data.data_types.subject_teachers import Subject_teachers
from Fibot.Data.data_types.practical_work import Practical_schedule
from Fibot.Data.data_types.exam import Exam_schedule
from Fibot.Data.teachers import Teachers


class Not_understood(object):

    def __init__(self, language, type_):
        with open('./Data/error_responses.json', 'rb') as fp:
            self.messages = json.load(fp)
        self.type_ = type_
        self.language = language

    def __repr__(self):
        chosen_response = self.messages[self.type_][self.language][randint(0,len(self.messages[self.type_][self.language])-1)]
        return chosen_response

"""
    Could be improved by checking the slots given
    or by doing the query search to the db and see if there
    are several matches.
"""
class action_show_teacher_mail(Action):

    def name(self):
        return 'action_show_teacher_mail'

    def resets_topic(self):
        return True

    def run(self, dispatcher, tracker, domain):
        print(self.name())
        print(tracker.slots)
        teacher_name = tracker.get_slot("teacher_name")
        chat_id = tracker.sender_id
        user_lang = Chats().get_chat_lite(chat_id)['language']
        if teacher_name:
            teacher, dist = Teachers(language = user_lang).get_closer_teacher(teacher_name)
            if dist <= 5:
                mail = teacher.get_mail()
                dispatcher.utter_message("{}".format(mail))
            else:
                dispatcher.utter_message("{}".format(Not_understood(user_lang, 'wrong_teacher')))
        else:
            dispatcher.utter_message("{}".format(Not_understood(user_lang, 'not_understand')))
        tracker._reset_slots()
        return []


class action_show_teacher_office(Action):

    def name(self):
        return 'action_show_teacher_office'

    def resets_topic(self):
        return True

    def run(self, dispatcher, tracker, domain):
        print(self.name())
        print(tracker.slots)
        teacher_name = tracker.get_slot("teacher_name")
        chat_id = tracker.sender_id
        user_lang = Chats().get_chat_lite(chat_id)['language']
        if teacher_name:
            teacher, dist = Teachers(language = user_lang).get_closer_teacher(teacher_name)
            if dist <= 5:
                office = teacher.get_office()
                dispatcher.utter_message("{}".format(office))
            else:
                dispatcher.utter_message("{}".format(Not_understood(user_lang, 'wrong_teacher')))
        else:
            dispatcher.utter_message("{}".format(Not_understood(user_lang, 'not_understand')))
        tracker._reset_slots()
        return []


class action_show_subject_free_spots(Action):

    def name(self):
        return 'action_show_subject_free_spots'

    def resets_topic(self):
        return True

    def run(self, dispatcher, tracker, domain):
        print(self.name())
        print(tracker.slots)
        subject_acro = tracker.get_slot("subject_acronym")
        group = tracker.get_slot("group")
        chat_id = tracker.sender_id
        user_lang = Chats().get_chat_lite(chat_id)['language']
        if subject_acro:
            if API_raco().subject_exists(subject_acro.upper()):
                query = {'places-matricula': { 'field': 'assig', 'value': subject_acro.upper() }}
                response = API_raco().get_main(query)
                s_s = Subject_spots(response, user_lang)
                if group:
                    dispatcher.utter_message("{}".format(s_s.get_group_spots(group)))
                else:
                    for group in s_s.group_info.keys():
                        dispatcher.utter_message("{}".format(s_s.get_group_spots(group)))
            else:
                dispatcher.utter_message("{}".format(Not_understood(user_lang, 'wrong_subject')))
        else:
            dispatcher.utter_message("{}".format(Not_understood(user_lang, 'not_understand')))
        return []


class action_show_subject_classroom(Action):
    def name(self):
        return 'action_show_subject_classroom'

    def resets_topic(self):
        return True

    def run(self, dispatcher, tracker, domain):
        print(self.name())
        print(tracker.slots)
        subject_acro = tracker.get_slot("subject_acronym")
        chat_id = tracker.sender_id
        user_lang = Chats().get_chat_lite(chat_id)['language']
        if subject_acro:
            if API_raco().subject_exists(subject_acro.upper()):
                access_token = Chats().get_chat_lite(chat_id)['access_token']
                if not access_token: dispatcher.utter_message("{}".format(self.not_logged_message(user_lang)))
                elif not API_raco().user_enrolled_subject(subject_acro.upper(), access_token):
                    response = str(Not_understood(user_lang, 'not_enrolled'))
                    if '{}' in response:
                        dispatcher.utter_message(response.format(subject_acro.upper()))
                    else: dispatcher.utter_message(response)
                else:
                    query = {'horari': {'field': 'codi_assig' , 'value': subject_acro.upper()}}
                    response = API_raco().get_main(query, public = False, access_token = access_token)
                    for data in response:
                        lecture = Lecture(data, user_lang)
                        dispatcher.utter_message("{}".format(lecture))
            else:
                dispatcher.utter_message("{}".format(Not_understood(user_lang, 'wrong_subject')))
        else:
            dispatcher.utter_message("{}".format(Not_understood(user_lang, 'not_understand')))
        tracker._reset_slots()
        return []

    def not_logged_message(self, user_lang):
        messages = {
            'ca': "No estàs identificat amb el teu usuari del Racó. No puc accedir a la teva informació.",
            'es': "No estás identifcado con tu usuario del Racó. No puedo acceder a la tu información.",
            'en': "You have not logged in with your Racó account. I cannot see your information"
        }
        return messages[user_lang]


class action_show_subject_schedule(Action):
    def name(self):
        return 'action_show_subject_schedule'

    def resets_topic(self):
        return True

    def run(self, dispatcher, tracker, domain):
        print(self.name())
        print(tracker.slots)
        subject_acro = tracker.get_slot("subject_acronym")
        chat_id = tracker.sender_id
        user_lang = Chats().get_chat_lite(chat_id)['language']
        if subject_acro:
            if API_raco().subject_exists(subject_acro):
                access_token = Chats().get_chat_lite(chat_id)['access_token']
                if not access_token: dispatcher.utter_message("{}".format(self.not_logged_message(user_lang)))
                elif not API_raco().user_enrolled_subject(subject_acro.upper(), access_token):
                    response = str(Not_understood(user_lang, 'not_enrolled'))
                    if '{}' in response:
                        dispatcher.utter_message(response.format(subject_acro.upper()))
                    else: dispatcher.utter_message(response)
                else:
                    query = {'horari': {'field': 'codi_assig' , 'value': subject_acro.upper()}}
                    response = API_raco().get_main(query, public = False, access_token = access_token)
                    for data in response:
                        lecture = Lecture(data, user_lang)
                        dispatcher.utter_message("{}".format(lecture))
            else:
                dispatcher.utter_message("{}".format(Not_understood(user_lang, 'wrong_subject')))
        else:
            dispatcher.utter_message("{}".format(Not_understood(user_lang, 'not_understand')))
        tracker._reset_slots()
        return []

    def not_logged_message(self, user_lang):
        messages = {
            'ca': "No estàs identificat amb el teu usuari del Racó. No puc accedir a la teva informació.",
            'es': "No estás identifcado con tu usuario del Racó. No puedo acceder a la tu información.",
            'en': "You have not logged in with your Racó account. I cannot see your information."
        }
        return messages[user_lang]


class action_show_subject_teachers_mails(Action):

    def name(self):
        return 'action_show_subject_teachers_mails'

    def resets_topic(self):
        return True

    def run(self, dispatcher, tracker, domain):
        print(self.name())
        print(tracker.slots)
        subject_acro = tracker.get_slot("subject_acronym")
        chat_id = tracker.sender_id
        user_lang = Chats().get_chat_lite(chat_id)['language']
        if subject_acro:
            if API_raco().subject_exists(subject_acro.upper()):
                teachers_info = API_raco().get_subject_teachers(acronym = subject_acro.upper(), language = user_lang)
                teachers_info = Subject_teachers(subject_acro.upper(), teachers_info, user_lang)
                if teachers_info.amount < 4:
                    for response in teachers_info.get_mails():
                        dispatcher.utter_message("{}".format(response))
                else:
                    answers = {'ca': "Quin d'aquests professors t'interessa?\n",
                        'es': '¿Quién de estos te interesa?\n',
                        'en': 'Who out of this teachers are you interested in?\n'
                    }
                    answer = answers[user_lang]
                    for teacher in teachers_info.get_names():
                        answer = answer + teacher + '\n'
                    dispatcher.utter_message("{}".format(answer))
            else:
                dispatcher.utter_message("{}".format(Not_understood(user_lang, 'wrong_subject')))
        else:
            dispatcher.utter_message("{}".format(Not_understood(user_lang, 'not_understand')))
        tracker._reset_slots()
        return []


class action_show_subject_teachers_offices(Action):

    def name(self):
        return 'action_show_subject_teachers_offices'

    def resets_topic(self):
        return True

    def run(self, dispatcher, tracker, domain):
        print(self.name())
        print(tracker.slots)
        subject_acro = tracker.get_slot("subject_acronym").upper()
        chat_id = tracker.sender_id
        user_lang = Chats().get_chat_lite(chat_id)['language']
        if subject_acro:
            if API_raco().subject_exists(subject_acro.upper()):
                teachers_info = API_raco().get_subject_teachers(acronym = subject_acro.upper(), language = user_lang)
                teachers_info = Subject_teachers(subject_acro.upper(), teachers_info, user_lang)
                if teachers_info.amount < 4:
                    for response in teachers_info.get_offices():
                        dispatcher.utter_message("{}".format(response))
                else:
                    answers = {'ca': "Quin d'aquests professors t'interessa?\n",
                        'es': '¿Quién de estos te interesa?\n',
                        'en': 'Who out of this teachers are you interested in?\n'
                    }
                    answer = answers[user_lang]
                    for teacher in teachers_info.get_names():
                        answer = answer + teacher + '\n'
                    dispatcher.utter_message("{}".format(answer))
            else:
                dispatcher.utter_message("{}".format(Not_understood(user_lang, 'wrong_subject')))
        else:
            dispatcher.utter_message("{}".format(Not_understood(user_lang, 'not_understand')))
        tracker._reset_slots()
        return []


class action_show_subject_teachers_names(Action):

    def name(self):
        return 'action_show_subject_teachers_names'

    def resets_topic(self):
        return True

    def run(self, dispatcher, tracker, domain):
        print(self.name())
        print(tracker.slots)
        subject_acro = tracker.get_slot("subject_acronym").upper()
        chat_id = tracker.sender_id
        user_lang = Chats().get_chat_lite(chat_id)['language']
        if subject_acro:
            if API_raco().subject_exists(subject_acro.upper()):
                teachers_info = API_raco().get_subject_teachers(acronym = subject_acro.upper(), language = user_lang)
                teachers_info = Subject_teachers(subject_acro.upper(), teachers_info, user_lang)
                if teachers_info.amount < 4:
                    for response in teachers_info.get_names():
                        dispatcher.utter_message("{}".format(response))
                else:
                    answers = {'ca': "Quin d'aquests professors t'interessa?\n",
                        'es': '¿Quién de estos te interesa?\n',
                        'en': 'Who out of this teachers are you interested in?\n'
                    }
                    answer = answers[user_lang]
                    for teacher in teachers_info.get_names():
                        answer = answer + teacher + '\n'
                    dispatcher.utter_message("{}".format(answer))
            else:
                dispatcher.utter_message("{}".format(Not_understood(user_lang, 'wrong_subject')))
        else:
            dispatcher.utter_message("{}".format(Not_understood(user_lang, 'not_understand')))
        tracker._reset_slots()
        return []


class action_show_next_class(Action):

    def name(self):
        return 'action_show_next_class'

    def resets_topic(self):
        return True

    def run(self, dispatcher, tracker, domain):
        print(self.name())
        print(tracker.slots)
        chat_id = tracker.sender_id
        user_lang = Chats().get_chat_lite(chat_id)['language']
        access_token = Chats().get_chat_lite(chat_id)['access_token']
        schedule = API_raco().get_schedule(access_token, user_lang)
        schedule = Schedule(schedule, user_lang)
        answer = schedule.get_response()
        dispatcher.utter_message("{}".format(answer))
        tracker._reset_slots()
        return []


class action_show_next_exams(Action):

    def name(self):
        return 'action_show_next_exams'

    def resets_topic(self):
        return True

    def run(self, dispatcher, tracker, domain):
        print(self.name())
        print(tracker.slots)
        chat_id = tracker.sender_id
        user_lang = Chats().get_chat_lite(chat_id)['language']
        access_token = Chats().get_chat_lite(chat_id)['access_token']
        exams = list(API_raco().get_exams_user(access_token))
        e_e = Exam_schedule(exams, user_lang)
        exams = list(e_e.get_closest_exams(range = 120))
        if exams:
            for exam in exams:
                dispatcher.utter_message("{}".format(exam))
                tracker._reset_slots()
            return []
        dispatcher.utter_message("{}".format(Not_understood(user_lang, 'not_exams')))
        tracker._reset_slots()
        return []

class action_show_next_pracs(Action):

    def name(self):
        return 'action_show_next_pracs'

    def resets_topic(self):
        return True

    def run(self, dispatcher, tracker, domain):
        print(self.name())
        print(tracker.slots)
        chat_id = tracker.sender_id
        user_lang = Chats().get_chat_lite(chat_id)['language']
        access_token = Chats().get_chat_lite(chat_id)['access_token']
        pracs = list(API_raco().get_practiques(access_token))
        p_e = Practical_schedule(pracs, user_lang)
        pracs = list(p_e.get_closest_pracs(range = 120))
        if pracs:
            for prac in pracs:
                dispatcher.utter_message("{}".format(prac))
                tracker._reset_slots()
            return []
        dispatcher.utter_message("{}".format(Not_understood(user_lang, 'not_pracs')))
        tracker._reset_slots()
        return []
