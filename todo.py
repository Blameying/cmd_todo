#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy
from sqlalchemy import Column, Integer, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import and_, or_
import os
import sys
import getopt
import datetime
import json


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
                created_at: {}, is_finish: {}, finished_at: {}>'.format(self.id, self.level,
                                                                        self.content,
                                                                        self.created_at,
                                                                        self.is_finish, self.finished_at)

    def to_dic(self):
        return {'id': self.id, 'level': self.level, 'content': self.content,
                'created_at': str(self.created_at), 'is_finish': self.is_finish,
                'finished_at': str(self.finished_at)}


class TimeRecorder(Base):
    'model to record todo task time'

    __tablename__ = 'time_recoder'

    id = Column(Integer, primary_key=True)
    start = Column(DateTime, default=datetime.datetime.now, nullable=False)
    end = Column(DateTime, nullable=True)
    todo_id = Column(Integer, ForeignKey("todos.id")) 
    todo = relationship("TodoItem", backref="time")

    comment = Column(Text, default="")


class DataManager:

    global LEVELS
    pathStrList = ['.config', 'todo']
    curPath = os.environ['HOME']

    def __init__(self):
        global Base
        try:
            for path in self.pathStrList:
                self.curPath = os.path.join(self.curPath, path)
                if not (os.path.exists(self.curPath) and os.path.isdir(self.curPath)):
                    os.mkdir(self.curPath)

            self.engine = sqlalchemy.create_engine('sqlite:///' + \
                                                   os.path.join(self.curPath, "todo.db"),
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
        session.query(TimeRecorder).filter(TimeRecorder.todo_id == id).delete()
        session.query(TodoItem).filter(TodoItem.id == id).delete()
        session.commit()
        session.close()

    def start(self, id):
        session = self.Session()
        items = session.query(TimeRecorder).filter(and_(TimeRecorder.end == None,
            TimeRecorder.todo_id == id)).all()
        if len(items) != 0:
            print("该任务早已开始计时(￢_￢)")
        else:
            todoItem = session.query(TodoItem).filter(TodoItem.id == id).first()
            if todoItem == None:
                print("不存在id 为 {} 的任务(/= _ =)/~┴┴".format(id))
            else:
                timeRecorder = TimeRecorder()
                todoItem.time.append(timeRecorder)
                session.commit()
                print("start!!, 请抓紧时间!!")
        session.close()
        return 0
                
    def stop(self, id):
        session = self.Session()
        items = session.query(TimeRecorder).filter(and_(TimeRecorder.end == None,
            TimeRecorder.todo_id == id)).all()
        if len(items) == 0:
            print("不存在对应任务已经开始的记录(..•˘_˘•..)")
        else:
            items[0].end = datetime.datetime.now()
            self.timeComment(items[0])
            print("该次活动经历了: {}".format(items[0].end - items[0].start))
            session.commit()

        session.close()
        return 0

    def timetable(self, id):
        session = self.Session()
        items = session.query(TimeRecorder) \
            .filter(and_(TimeRecorder.todo_id == id, TimeRecorder.end != None)) \
            .order_by(TimeRecorder.start.desc())    \
            .all()
        if len(items) == 0:
            print("不存在对应任务的记录(..•˘_˘•..)")

        session.close()
        return items

    def timeComment(self, timeRecorder):
        filename = os.path.join(self.curPath, ".time_comment_tmp")
        fp = open(filename, "w")
        fp.write("\n#请输入你的评论，输入Esc:wq结束(正常vim的退出方式)" + \
                 "\n# #符号开头的为注释")
        fp.close()
        os.system("vim "+filename)
        fp = open(filename, "r")
        lines = fp.readlines()
        comment = ""
        for line in lines:
            if line.strip().startswith("#"):
                lines.remove(line)
            else:
                comment += line

        timeRecorder.comment = comment
        return timeRecorder
        

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
    print("\t-t, --todo msg\t 增加一条记录 正文为msg")
    print("\t-l, --list\t 列出所有未完成项目")
    print("\t-d, --delete id\t 删除指定id项目")
    print("\t-a, --all\t 列出全部项目，包括已完成")
    print("\t-p, --priority normal\t 指定记录的优先级, " +
          "可选项为warn, normal, low, 默认值为normal")
    print("\t    --export_json file\t 导出数据为json文件，file为文件路径")
    print("\t    --start id\t 开始记录时间，为了统计任务花费时间")
    print("\t    --end   id\t 停止记录时间，为了统计任务花费时间")
    print("\t    --timetable id\t 查看任务统计的时间表")
    print("\t-v, --version\t 查看当前版本")
    print("\t-h, --help\t 列出帮助")


def wrong():
    print("参数错误，使用-h, --help查看帮助哦;)")

def display_timetable(items):
    blueContent = '\033[0;36m'
    yellowStatus = '\033[0;33m'
    colorEnd = '\033[0m'

    total_time = datetime.timedelta()

    color_format = "{color_start:s}start: {start:s} \t" + \
                   "end: {end:s} \t spend:" + \
                   "{spend:s}{color_end:s}"
    for item in items:
        delta = item.end - item.start
        total_time += delta
        print(color_format.format(**{'color_start': blueContent, 'color_end': colorEnd,
                                  'start': str(item.start), 'end': str(item.end),
                                  'spend': str(delta)}))
        if item.comment.strip() != "":
            print(yellowStatus + item.comment + colorEnd)

    print(yellowStatus + "total: {}".format(str(total_time)) + colorEnd)


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
                           '--version': self.version, '--help': self.help,
                           '--export_json': self.export_json,
                           '--start': self.start, '--stop': self.stop,
                           '--timetable': self.timetable}

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

    def export_json(self, value):
        ret = []
        items = self.dataManager.query_all()
        for item in items:
            ret.append(item.to_dic())
        json_str = json.dumps(ret, ensure_ascii=False, indent=4, separators=(', ', ': '))

        if value == '':
            raise KeyError

        try:
            fp = open(value, 'w')
            fp.write(json_str)
        except IOError as e:
            print("文件读写错误: {}".format(e))
        finally:
            fp.close()

    def start(self, value):
        if not value.isdigit():
            wrong()
            return 1
        self.dataManager.start(int(value))
        return 0

    def stop(self, value):
        if not value.isdigit():
            wrong()
            return 1
        self.dataManager.stop(int(value))
        return 0

    def timetable(self, value):
        if not value.isdigit():
            wrong()
            return 1
        items = self.dataManager.timetable(int(value))
        display_timetable(items)
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
                                       ['todo=', 'list', 'finished=', 'delete=',
                                       'all', 'priority=', 'version', 'help', 'export_json=',
                                       'start=', 'stop=', 'timetable='])
    except getopt.GetoptError as e:
        wrong()
        print(e)
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

