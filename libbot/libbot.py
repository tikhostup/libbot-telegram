# -*- coding: utf-8 -*-
import bot_conf
import telebot
from telebot import types
import string
import logging
import time
import datetime

import mysql.connector
from mysql.connector import Error

# last update date: 18.11.2017
# author:           @tikhostup

bl = {}
bot = telebot.TeleBot(bot_conf.token)
logging.basicConfig(format='%(asctime)s | %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename="out.log", level = logging.INFO)
logging.info(u'Bot started!')

# start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if bl.get(message.chat.id) == 1: return
    bl[message.chat.id]=1
    try:
        conn = mysql.connector.connect()
        if conn.is_connected():
            chatID = message.chat.id
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE user_id=%d;" % chatID)
            row = cursor.fetchone()
            if row is None: # newbie
                logging.info(u'Command start user_id:' + str(message.chat.id) + u'('+message.chat.first_name + u') BL=' + str(bl.get(message.chat.id)))
                query="""INSERT INTO user (user_id, f_name, l_name) VALUES(%s, %s, %s)"""
                args=(chatID, message.chat.username, message.chat.first_name)
                cursor.execute(query, args)
                conn.commit()
                logging.info(u'New user user_id:'+str(message.chat.id)+' username (first_name):'+message.chat.first_name
                             + u'('+message.chat.first_name + u') BL=' + str(bl.get(message.chat.id)))
                bot.send_message(message.chat.id, u'Привет! Добро пожаловать в библиотеку Информзащиты')
            else: # user
                bot.send_message(message.chat.id, u'%s, рады видеть Вас снова! 😊' % row[2])
                logging.info(u'Command restart user_id:' + str(message.chat.id) + u'('+message.chat.first_name + u') BL=' + str(bl.get(message.chat.id)))
            bl[chatID] = 0
            main_menu(message, False, True)
    except Error as e:
        logging.info(u'Command start user_id:' + str(message.chat.id) + u'(' + message.chat.first_name + u') BL='
                     + str(bl.get(message.chat.id)) + u' Result=Ошибка! Команда старт!')
    finally:
        bl[message.chat.id]=0
        conn.close()


# inline-button
@bot.callback_query_handler(func=lambda call: True)
def inline(call):
    if call.data == "take_book":
        try:
            logging.info(u'Command VZYAT_INLINE user_id:' + str(call.message.chat.id) + u'(' + call.message.chat.first_name + u') BL=' + str(bl.get(call.message.chat.id)))
            conn = mysql.connector.connect()
            if conn.is_connected():
                haha = call.message.text
                cursor = conn.cursor()
                r_haha = haha[10:haha.index('\n', 0, len(haha))]
                cursor.execute("SELECT book_stat,book_reader FROM book WHERE book_name='%s';" % r_haha)
                row = cursor.fetchone()
                logging.info(u'Command VZYAT_INLINE user_id:' + str(call.message.chat.id) + u'(' + call.message.chat.first_name + u') BL='
                             + str(bl.get(call.message.chat.id)) + u' book_name='+r_haha + u' book_stat='+str(row[0]) + u' book_reader='+str(row[1]))

                if row is None:
                    bot.send_message(call.message.chat.id, text=u'😔 Данная книга сейчас не доступна...')
                    logging.info(u'Command VZYAT_INLINE user_id:' + str(call.message.chat.id) + u'(' + call.message.chat.first_name + u') BL='
                                 + str(bl.get(call.message.chat.id)) + u' book_name=' + r_haha + u' book_stat=' + str(row[0])
                                 + u' book_reader=' + str(row[1]) + u' Result=Данная книга сейчас не доступна')
                else:
                    if (row[0] == 2) and (row[1] == call.message.chat.id):
                        bot.send_message(call.message.chat.id, text=u'Вы уже взяли эту книгу! 😊')
                        logging.info(u'Command VZYAT_INLINE user_id:' + str(call.message.chat.id) + u'(' + call.message.chat.first_name + u') BL='
                                     + str(bl.get(call.message.chat.id)) + u' book_name=' + r_haha + u' book_stat=' + str(row[0])
                                     + u' book_reader=' + str(row[1]) + u' Result=Вы уже взяли эту книгу')
                    elif (row[0] == 2) and (row[1] != call.message.chat.id):
                        # request
                        cursor = conn.cursor(buffered=True)
                        cursor.execute("SELECT f_name FROM user WHERE user_id=%d;" % row[1])
                        row1 = cursor.fetchone()
                        bot.send_message(call.message.chat.id, text=u'Упс! Похоже, предыдущий читатель не отметил возврат книги. Пожалуйста, попросите его об этом: @' + str(row1[0]))
                        logging.info(u'Command VZYAT_INLINE user_id:' + str(call.message.chat.id) + u'(' + call.message.chat.first_name + u') BL='
                                     + str(bl.get(call.message.chat.id)) + u' book_name=' + r_haha + u' book_stat=' + str(row[0])
                                     + u' book_reader=' + str(row[1]) + u' Result=Упс! Похоже, предыдущий читатель не отметил возврат книги! Уведомить админа')
                    elif row[0] == 1:
                        query = """UPDATE book SET book_stat=%s, book_reader=%s WHERE book_name=%s;"""
                        args = (2, call.message.chat.id, r_haha)
                        cursor.execute(query, args)
                        conn.commit()
                        logging.info(u'Command VZYAT_INLINE user_id:' + str(call.message.chat.id) + u'(' + call.message.chat.first_name + u') BL='
                                     + str(bl.get(call.message.chat.id))+ u' book_name=' + r_haha + u' book_stat=' + str(row[0])
                                     + u' book_reader=' + str(row[1]) + u' Result=Приятного чтения!')
                        bot.send_message(chat_id=call.message.chat.id, text=u'Приятного чтения!')

                    bot.edit_message_text(chat_id=call.message.chat.id,message_id=call.message.message_id,text=u'😊')
        except Error as e:
            logging.error(u'Command VZYAT_INLINE user_id:' + str(call.message.chat.id) + u'(' + call.message.chat.first_name + u') BL='
                                     + str(bl.get(call.message.chat.id)) + u' book_name=' + r_haha + u' book_stat=' + str(row[0])
                                     + u' book_reader=' + str(row[1]) + u' Result=Ошибка! Взять книгу инлайн')
        finally:
            bl[call.message.chat.id] = 0
            conn.close()

    # return book
    if call.data == "takeoff_book":
        logging.info(u'Command VERNUT_INLINE user_id:' + str(call.message.chat.id) + u'(' + call.message.chat.first_name + u') BL=' + str(bl.get(call.message.chat.id)))
        try:
            conn = mysql.connector.connect()
            if conn.is_connected():
                haha = call.message.text
                cursor = conn.cursor()
                r_haha = haha[haha.index(' ',0,len(haha))+1:haha.index('\n',0, len(haha))]
                cursor.execute("SELECT book_stat,book_reader FROM book WHERE book_name='%s';" % r_haha)
                row = cursor.fetchone()

                if row is None:
                        bot.send_message(call.message.chat.id, text=u'😔 Данная книга сейчас не доступна...')
                        logging.info(u'Command VERNNUT_INLINE user_id:' + str(call.message.chat.id) + u'(' + call.message.chat.first_name + u') BL='
                                     + str(bl.get(call.message.chat.id)) + u' book_name=' + r_haha + u' book_stat=' + str(row[0])
                                     + u' book_reader=' + str(row[1]) + u' Result=Данная книга сейчас не доступна')
                else:
                    if (row[0] == 2) and (row[1] == call.message.chat.id):
                        query = """UPDATE book SET book_stat=%s, book_reader=%s WHERE book_name=%s;"""
                        args = (1, 0, r_haha)
                        cursor.execute(query, args)
                        conn.commit()
                        logging.info(u'Command VERNNUT_INLINE user_id:' + str(call.message.chat.id) + call.message.chat.first_name + u') BL='
                                     + str(bl.get(call.message.chat.id)) + u' book_name=' + r_haha + u' book_stat=' + str(row[0]) +
                                     u' book_reader=' + str(row[1]))
                    elif (row[0] == 2) and (row[1] != call.message.chat.id):
                        bot.send_message(call.message.chat.id, text=u'Эта книга уже на руках у другого человека!')
                        logging.info(u'Command VERNNUT_INLINE user_id:' + str(call.message.chat.id) + u'(' + call.message.chat.first_name + u') BL='
                                     + str(bl.get(call.message.chat.id)) + u' book_name=' + r_haha + u' book_stat=' + str(row[0])
                                     + u' book_reader=' + str(row[1]) + u' Result=Книга уже на руках у другого человека')
                    elif row[0] == 1:
                        bot.send_message(call.message.chat.id, text=u'Книга уже на полке! 😊')
                        logging.info(u'Command VERNNUT_INLINE user_id:' + str(call.message.chat.id) + call.message.chat.first_name + u') BL='
                                     + str(bl.get(call.message.chat.id)) + u' book_name=' + r_haha + u' book_stat=' + str(row[0]) +
                                     u' book_reader=' + str(row[1]) + u' Result=Книга уже на полке!')

                bot.edit_message_text(chat_id=call.message.chat.id,message_id=call.message.message_id,text=u'😊')
        except Error as e:
            logging.error(u'Command VERNNUT_INLINE user_id:' + str(call.message.chat.id) + u'(' + call.message.chat.first_name + u') BL='
                                     + str(bl.get(call.message.chat.id)) + u' book_name=' + r_haha + u' book_stat=' + str(row[0])
                                     + u' book_reader=' + str(row[1]) + u' Result=Ошибка! Вернуть книгу инлайн')
        finally:
            bl[call.message.chat.id] = 0
            conn.close()
    bot.send_message(chat_id=call.message.chat.id, text=u'Может что-то еще?')
    main_menu(call.message, False, False)


# main menu
def main_menu(message, a, b):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=a)
    keyboard.add(types.KeyboardButton(text=u'📗Взять книгy'), types.KeyboardButton(text=u'📚Книги y мeня'))
    keyboard.add(types.KeyboardButton(text=u'➡Eще'))
    if b == True: bot.send_message(message.chat.id, text=u'Пожалуйста, выберите действие', reply_markup=keyboard)
    logging.info(u'Command MAIN_MENU user_id:' + str(message.chat.id) + u'(' + message.chat.first_name + u') BL=' + str(bl.get(message.chat.id)))


# button "еще"
@bot.message_handler(regexp='^➡Eще')
def handler_get_list(message):
    if bl.get(message.chat.id) == 1: return
    logging.info(u'Command ESHE user_id:' + str(message.chat.id) + u'('+message.chat.first_name+u') BL=' + str(bl.get(message.chat.id)))
    bl[message.chat.id]=1

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text=u'✅Дoбавить книгу'), types.KeyboardButton(text=u'⬅Нa глaвнyю'))
    keyboard.add(types.KeyboardButton(text=u'✉Нaпиcать нaм'), types.KeyboardButton(text=u'ℹO нaс'))
    bot.send_message(message.chat.id, text=u'Пожалуйста, выберите действие', reply_markup=keyboard)

    bl[message.chat.id]=0


# button "о нас"
@bot.message_handler(regexp='^ℹO нaс')
def handler_about_us(message):
    logging.info(u'Command O_NAS user_id:' + str(message.chat.id) + u'('+message.chat.first_name+u') BL=' + str(bl.get(message.chat.id)))
    bot.send_message(message.chat.id,text=u'[Правила пользования - Ботом библиотеки ИЗ](http://telegra.ph/Biblioteka-IZ-11-16)',parse_mode="Markdown")
    main_menu(message, False, True)


# button "Книги у меня"
@bot.message_handler(regexp='^📚Книги y мeня')
def handler_get_list(message):
    logging.info(u'Command KNIGI_U_MENYA user_id:' + str(message.chat.id) + u'('+message.chat.first_name+u') BL=' + str(bl.get(message.chat.id)))
    if bl.get(message.chat.id) == 1: return
    bl[message.chat.id]=1

    try:
        # fix it in config
#        conn = mysql.connector.connect(host=bot_conf.h,port=bot_conf.p,database=bot_conf.d,user=bot_conf.u,password=bot_conf.p)
        conn = mysql.connector.connect()
        if conn.is_connected():
            cursor = conn.cursor(buffered=True)
            cursor.execute("SELECT book_name,book_writer,book_date,book_stat,book_reader FROM book WHERE book_reader=%s;" % message.chat.id)
            row = cursor.fetchone()
            if row is None:
                bot.send_message(message.chat.id, text=u'У вас нет книг на руках!')
                logging.info(u'Command VZYAT_INLINE user_id:' + str(message.chat.id) + u'(' + message.chat.first_name + u') BL='
                             + str(bl.get(message.chat.id)) + u' Result=У вас нет книг на руках!')
            else:
                i=1
                while row is not None:
                    keyboard = types.InlineKeyboardMarkup()
                    url_button = types.InlineKeyboardButton(text=u'Вернуть книгу', callback_data="takeoff_book")
                    keyboard.add(url_button)
                    bot.send_message(message.chat.id,
                                     text=u'*'+str(i) + u'.* ' + row[0] + u'\n*Автор:* ' + row[1] + u'\n*Дата получения:* ' + str(row[2]) + u'\n',
                                     reply_markup=keyboard, parse_mode="Markdown")
                    logging.info(u'Command KNIGI_U_MENYA user_id:' + str(message.chat.id) + u'('+message.chat.first_name+u') BL='
                                 + str(bl.get(message.chat.id)) + u' book_name=' + str(row[0]) + u' book_stat=' + str(row[3]) + u' book_reader=' + str(row[4]))
                    i=i+1
                    row = cursor.fetchone()
    except Error as e:
        print(e)
        logging.error(u'Command KNIGI_U_MENYA user_id:' + str(message.chat.id) + u'(' + message.chat.first_name + u') BL=' + str(bl.get(message.chat.id)))
    finally:
        main_menu(message, False, False)
        bl[message.chat.id]=0
        conn.close()


# button "на главную"
@bot.message_handler(regexp='^⬅Нa глaвнyю')
def handler_take_book(message):
    if bl.get(message.chat.id) == 1: return
    bl[message.chat.id] = 1
    logging.info(u'Command NA_GLAVNUYU user_id:' + str(message.chat.id) + u'('+message.chat.first_name+u') BL='+str(bl.get(message.chat.id)))
    main_menu(message, False, True)
    bl[message.chat.id] = 0


# button "взять книгу"
@bot.message_handler(regexp='^📗Взять книгy')
def handler_take_book(message):
    if bl.get(message.chat.id) == 1: return
    bl[message.chat.id]=1
    logging.info(u'Command VZYAT_KNIGU lev=1 user_id:' + str(message.chat.id) + u'('+message.chat.first_name+u') BL=' + str(bl.get(message.chat.id)))
    bot.send_message(message.chat.id, text=u'Какую книгу вы хотите взять?')
    sent = bot.send_message(message.chat.id, text=u'Пожалуйста, введите одно слово из названия книги')
    bot.register_next_step_handler(sent, take_book)


def take_book(message):
    try:
        conn = mysql.connector.connect()
        if conn.is_connected():
            cursor = conn.cursor(buffered=True)
            # first 5 books
            cursor.execute("SELECT book_name,book_writer,book_stat,book_reader FROM book WHERE book_name LIKE '%s%s%s' LIMIT 0,5;" % ("%", message.text, "%"))
            row = cursor.fetchone()
            if row is None:
                bot.send_message(message.chat.id, text=u'Хм, похоже, такой книги у нас нет. Пожалуйста, обратитесь к администратору: @sergioaldia')
                logging.info(u'Command VZYAT_INLINE lev=2 user_id:' + str(message.chat.id) + u'('+message.chat.first_name+u') BL=' + str(bl.get(message.chat.id))
                             +u'Хм, похоже, такой книги у нас нет. Пожалуйста, обратитесь к администратору: @sergioaldia')
            else:
                if (row[2] == 2) and (row[3] != message.chat.id):
                    # request
                    curs2 = conn.cursor(buffered=True)
                    curs2.execute("SELECT f_name FROM user WHERE user_id=%d;" % row[3])
                    row1 = curs2.fetchone()
                    if row1 is not None:
                        bot.send_message(message.chat.id,text=u'Упс! Похоже, предыдущий читатель не отметил возврат книги. Пожалуйста, попросите его об этом: @'+str(row1[0]))
                        logging.info(u'Command VZYAT_INLINE lev=2 user_id:' + str(message.chat.id) + u'(' + message.chat.first_name + u') BL=' + str(bl.get(message.chat.id))
                                + u'Упс! Похоже, предыдущий читатель не отметил возврат книги. Пожалуйста, попросите его об этом: @'+str(row1[0]))
                    else:
                        bot.send_message(message.chat.id,text=u'Упс! Похоже произошла ошибка! Обратитесь к администратору @sergioaldia')
                        logging.info(u'Command VZYAT_INLINE lev=2 user_id:' + str(message.chat.id) + u'(' + message.chat.first_name + u') BL=' +
                                     str(bl.get(message.chat.id)) + u'Упс! Похоже произошла ошибка! Обратитесь к администратору @sergioaldia')
                else:
                    i=1
                    while (i<6) and (row is not None):
                        keyboard = types.InlineKeyboardMarkup()
                        url_button = types.InlineKeyboardButton(text=u'Взять книгу', callback_data="take_book")
                        keyboard.add(url_button)
                        bot.send_message(message.chat.id, text=u'*Название:* ' + row[0] + u'\n*Автор:* ' + row[1], reply_markup=keyboard,parse_mode="Markdown")
                        row = cursor.fetchone()
                        i = i + 1

    except Error as e:
        logging.error(u'Command VZYAT_KNIGU lev=2 user_id:' + str(message.chat.id) + u'(' + message.chat.first_name + u') BL=' + str(bl.get(message.chat.id)) + u' Result=Ошибка! Кнопка взять книгу!')
    finally:
        bl[message.chat.id]=0
        conn.close()


# button "Добавить книгу"
@bot.message_handler(regexp='^✅Дoбавить книгу')
def handler_about_us(message):
    bot.send_message(message.chat.id,text=u'Данный функционал в разработке. Для добавления книги в бибилотеку обратитесь к администратору: @sergioaldia')
    main_menu(message, False, True)

# button "Написать нам"
@bot.message_handler(regexp='^✉Нaпиcать нaм')
def handler_about_us(message):
    bot.send_message(message.chat.id,text=u'Данный функционал в разработке. Для добавления книги в бибилотеку обратитесь к администратору: @sergioaldia')
    main_menu(message, False, True)

if __name__ == '__main__':
     bot.polling(none_stop=True)
