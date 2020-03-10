#!/usr/bin/python

import sqlite3
import sqlalchemy
from sqlalchemy import Column, Integer, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
import os
import sys
import getopt
import datetime


Base = declarative_base()
LEVELS = {"low": 0, "normal": 1, "warn": 2}


class TodoItem(Base):

    'meta data of a todo-item'

    __tablename__ = 'todos'

    global LEVELS
    id = Column(Integer, primary_key=True)
    level = Column(Integer, nullable=False, default=LEVELS['normal'])
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    is_finish = Column(Boolean, nullable=False, default=False)
    finished_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return '<TodoItem: id: {}, priority: {}, content: {}, \
            created_at: {}, is_finish: {}'.format(self.id, self.level,
                                                  self.content,
                                                  self.created_at,
                                                  self.is_finish)


class DataManager:

    global LEVELS

    def __init__(self):
        global Base
        pathStrList = ['.config', 'todo']
        curPath = os.environ['HOME']
        try:
            for path in pathStrList:
                curPath = os.path.join(curPath, path)
                if not (os.path.exists(curPath) and os.path.isdir(curPath)):
                    os.mkdir(curPath)

            curPath = os.path.join(curPath, 'todo.db')
            self.engine = sqlalchemy.create_engine('sqlite:///' + curPath,
                                                   echo=False)
            Base.metadata.create_all(self.engine)
            self.Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        except Exception as e:
            print("connect todo.db failed: " + e)

    def query(self):
        session = self.Session()
        levelsValue = list(LEVELS.values())
        levelsValue.sort(reverse=True)
        itemsAll = []
        for value in levelsValue:
            items = session.query(TodoItem).filter(
                    TodoItem.is_finish == False)                \
                        .filter(TodoItem.level == value)        \
                        .order_by(TodoItem.created_at.desc())   \
                        .all()
            itemsAll.extend(items)

        session.close()
        return itemsAll

    def query_finished(self):
        session = self.Session()
        levelsValue = list(LEVELS.values())
        levelsValue.sort(reverse=True)
        itemsAll = []
        for value in levelsValue:
            items = session.query(TodoItem).filter(
                    TodoItem.is_finish == True)  \
                        .filter(TodoItem.level == value)        \
                        .order_by(TodoItem.created_at.desc())   \
                        .all()
            itemsAll.extend(items)

        session.close()
        return itemsAll

    def query_all(self):
        session = self.Session()
        levelsValue = list(LEVELS.values())
        levelsValue.sort(reverse=True)
        itemsAll = []
        for value in levelsValue:
            items = session.query(TodoItem).filter(TodoItem.level == value)  \
                        .order_by(TodoItem.created_at.desc())                \
                        .all()
            itemsAll.extend(items)

        session.close()
        return itemsAll

    def add(self, level, content):
        session = self.Session()
        item = TodoItem()
        item.level = level
        item.content = content

        session.add(item)
        session.commit()
        session.close()

    def finish(self, id):
        session = self.Session()
        session.query(TodoItem).filter(TodoItem.id == id)   \
                               .update({"is_finish": True})
        session.commit()
        session.close()

    def remove(self, id):
        session = self.Session()
        session.query(TodoItem).filter(TodoItem.id == id).delete()
        session.commit()
        session.close()


def text_align(text, size):
    count = 0
    for w in text:
        if '\u4e00' <= w <= '\u9fff':
            count += 2
        else:
            count += 1
    if count % 2 == 1:
        count += 1
        text += ' '

    padSize = (size - count) // 2
    return (' ' * padSize) + text + (' ' * padSize)


def display_help():
    print("用法: todo.py [Options]... [Message|id]")
    print("=,= 这是一个Todo 记录程序，Write By 哈哈. \n")

    print("参数: ")
    print("\t-t, --todo=msg\t 增加一条记录 正文为msg")
    print("\t-l, --list\t 列出所有未完成项目")
    print("\t-d, --delete=id\t 删除指定id项目")
    print("\t-a, --all\t 列出全部项目，包括已完成")
    print("\t-p, --priority=normal\t 指定记录的优先级, \
          可选项为warn, normal, low, 默认值为normal")
    print("\t-v, --version\t 查看当前版本")
    print("\t-h, --help\t 列出帮助")


def wrong():
    print("参数错误，使用-h, --help查看帮助哦;)")


def display(items):
    global LEVELS

    redStart = '\033[0;31m'
    blueStart = '\033[0;32m'
    whiteStart = '\033[0;34m'
    colorEnd = '\033[0m'

    redContent = '\033[0;36m'
    blueContent = '\033[0;36m'
    whiteContent = '\033[0;36m'

    yellowStatus = '\033[0;33m'
    whiteStatus = '\033[0;35m'

    unfinished = 'Unfinish'
    finished = 'Finish'

    color_format = '{start_color:s}{icon:s}:{id:^3d}{end_color:s}' + \
                   '{context_color:s}{context:s}{end_color:s}' + \
                   '{status_color:s}{finished:^10s}{end_color:s}' + \
                   '{context_color:s}{time:^15s}{end_color:s}'

    if len(items) == 0:
        print("还真是一条计划也没有呢……")
        return

    for item in items:
        if item.level is LEVELS['warn']:
            print(color_format.format(**{'icon': "(°ー°〃)", 'id': item.id,
                                      'context': text_align(item.content, 24),
                                      'time': item.created_at
                                      .strftime('%Y-%m-%d'),
                                      'start_color': redStart,
                                      'end_color': colorEnd,
                                      'context_color': redContent,
                                      'status_color': (whiteStatus if item.is_finish else yellowStatus),
                                      'finished': (finished if item.is_finish else unfinished),
                                      }))
        elif item.level is LEVELS['normal']:
            print(color_format.format(**{'icon': " ￣ △ ￣", 'id': item.id,
                                      'context': text_align(item.content, 24),
                                      'time': item.created_at
                                      .strftime('%Y-%m-%d'),
                                      'start_color': blueStart,
                                      'end_color': colorEnd,
                                      'context_color': blueContent,
                                      'status_color': (whiteStatus if item.is_finish else yellowStatus),
                                      'finished': (finished if item.is_finish else unfinished),
                                      }))
        elif item.level is LEVELS['low']:
            print(color_format.format(**{'icon': "  ⊙ ▽ ⊙ ", 'id': item.id,
                                      'context': text_align(item.content, 24),
                                      'time': item.created_at
                                      .strftime('%Y-%m-%d'),
                                      'start_color': whiteStart,
                                      'end_color': colorEnd,
                                      'context_color': whiteContent,
                                      'status_color': (whiteStatus if item.is_finish else yellowStatus),
                                      'finished': (finished if item.is_finish else unfinished),
                                      }))
        else:
            print('todo data priority range error:')
            print(item)


class ArgFuncts:

    global LEVELS

    def __init__(self):
        self.todoItem = None
        self.level = LEVELS['normal']
        self.dataManager = DataManager()
        self.functs_map = {'-t': self.todo, '-l': self.list,
                           '-f': self.finished, '-d': self.delete,
                           '-a': self.all, '-p': self.priority,
                           '-v': self.version, '-h': self.help,
                           '--todo': self.todo, '--list': self.list,
                           '--finished': self.finished, '--delete': self.delete,
                           '--all': self.all, '--priority': self.priority,
                           '--version': self.version, '--help': self.help}

    def todo(self, message):
        if (message.strip() == ''):
            wrong()
            return 1
        self.todoItem = TodoItem()
        self.todoItem.content = message
        return 0

    def list(self, value):
        items = self.dataManager.query()
        display(items)
        return

    def finished(self, id):
        if not id.isdigit():
            wrong()
            return 1
        self.dataManager.finish(int(id))
        return 0

    def delete(self, id):
        if not id.isdigit():
            wrong()
            return 1
        self.dataManager.remove(int(id))
        return 0

    def all(self, value):
        items = self.dataManager.query_all()
        display(items)
        return 0

    def priority(self, pri):
        try:
            self.level = LEVELS[pri.lower()]
        except KeyError:
            wrong()
            print("w(ﾟДﾟ)w: 优先级只有low, normal, warn")
            return 1

        return 0

    def version(self, value):
        print("version: 0x0")
        return 0

    def help(self, value):
        display_help()
        return 0

    def filter(self, value):
        try:
            self.functs_map[value[0]](value[1])
        except KeyError as e:
            raise e
            wrong()
            print(self.functs_map)
            print("输入了无效的参数: {} error: {}".format(value[0], e))
            return 1

        return 0


def main():
    opts = None
    args = None
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 't:lf:d:ap:vh',
                                       ['todo', 'list', 'finished', 'delete',
                                       'all', 'priority', 'version', 'help'])
    except getopt.GetoptError:
        wrong()
        return

    argfuncts = ArgFuncts()

    if len(opts) == 0:
        argfuncts.filter(('-l', ''))
        return

    for cp in opts:
        ret = argfuncts.filter(cp)
        if ret != 0:
            break

    if argfuncts.todoItem is not None:
        argfuncts.dataManager.add(argfuncts.level, argfuncts.todoItem.content)
        argfuncts.filter(('-l', ''))

    return


if __name__ == '__main__':
    main()

