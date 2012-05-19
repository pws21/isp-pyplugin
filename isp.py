# -*- coding: utf-8 -*-
import sys
import os
import traceback
from cgi import FieldStorage
from lxml import etree as et
import logging

DFLT_ENC = "UTF-8" # кодировка по умолчанию
# формат лог файла по умолчанию
DFLT_FMT = '%(asctime)s - %(addon_name)s[%(script_type)s] - %(levelname)s - %(REMOTE_USER)s[%(SESSION_LEVEL)s] - %(message)s'
DFLT_LOG = '/usr/local/ispmgr/var/isp-pyplugin.log' # лог файл по умолчанию
# Переменные окружения
ENV_KEYS = ['AUTHID',# уникальный номер сессии.
'REMOTE_USER', # имя пользователя, вызвавшего функцию.
'SESSION_LEVEL', # уровень пользователя, вызвавшего функцию.
'SESSION_LANG', # язык интерфейса пользователя.
'RECORDLIMIT', # ограничение на количество записей в таблице (из настроек пользователя). При формировании таблицы плагин не должен формировать больше строк, чем указано в данном параметре. При большом количестве данных необходимо формировать информационный баннер, сообщающий, что отображены не все данные.
'MGR', # имя продукта (например, ispmgr). Можно использовать, когда один и тот же плагин предназначен для использования с несколькими продуктами.
'MGR_DISTRIBUTION', # полное название дистрибутива продукта (например, ISPmanager-Lite)
'MGR_VERSION', # версия программного продукта.
'MSG_OSNAME', # операционная система, для которой сделана сборка данного продукта.
'LICID', # номер лицензии, который можно использовать для системы лицензирования ваших плагинов. Стоит обратить внимание, иногда лицензии продаются на диапазон адресов, в таком случае множество лицензий будут иметь одинаковый номер.
'HANDLER_STAGE'] # стадия выполнения. используется только при вызовах обработчиков событий, может принимать занчения "before", "after", "final". 

_logger = logging.getLogger('isp')

def err(code, msg=None, obj=None):
    """Возвращяет XML об ошибке"""
    if type(code) == int:
        code = str(code)
    xmldoc = doc()
    xmlerr = et.Element("error", code=code)
    if obj is not None:
        xmlerr.attrib["obj"] = obj
    if msg is not None:
        xmlerr.text = msg
    xmldoc.append(xmlerr)
    return xmldoc

def ok(text=None):
    """Возвращяет XML об успешном завершении"""
    xmldoc = doc()
    xmlok = et.Element("ok")
    if text is not None:
        xmlok.text = text
    xmldoc.append(xmlok)
    return xmldoc

def doc():
    """Возвращяет XML с элементом doc"""
    return et.Element("doc")

def xml2str(xml):
    """Переводит lxml.etree.Element в string пригодный для отдачи в ISP"""
    return et.tostring(xml, encoding=DFLT_ENC, xml_declaration=True)

def xml2pretty_str(xml):
    """Переводит lxml.etree.Element в форматированный string пригодный для отдачи в ISP"""
    return et.tostring(xml, encoding=DFLT_ENC, xml_declaration=True, pretty_print=True)

def get_env():
    """Получить переменные окружения"""
    return dict((key, os.environ.get(key, "")) for key in ENV_KEYS)

def get_tb(tb=None, short=True):
    """ Получить traceback """
    (_tt, _tv, _tb ) = sys.exc_info()
    tmp="%s:%s " % (_tt, _tv)

    if tb == None:
        tb = traceback.extract_stack()
    else:
        tb = traceback.extract_tb(tb)
    tmp = repr(traceback.format_exception(_tt, _tv, _tb))
    return tmp

class Plugin(object):
    """
    Класс от которого наследуются все плагины.
    """
    def __init__(self, name, stype='cgi'):
        """Инициализация"""
        self.name = name
        self.stype = stype
        self.logger = _logger
        self.logger.setLevel(logging.INFO)
        self.env = get_env()
        self.env.update({'addon_name':name, 'script_type':stype})
        self.addLogFileHandler(DFLT_LOG, DFLT_FMT)
        if self.is_cgi():
            self.params = FieldStorage(keep_blank_values=True)
        if self.is_xml():
            xmlstr = sys.stdin.read()
            self.stdin_xml = et.fromstring(xmlstr)

    def is_cgi(self):
        """Это плагин CGI типа?"""
        return self.stype == 'cgi'

    def is_xml(self):
        """Это плагин XML типа?"""
        return self.stype == 'xml'
    
    def execute(self, *args, **kwargs):
        """Метод запускающий выполнение плагина"""
        self.log.debug("Start %s" % self.name)
        status = "successfuly"
        try:
            self._main(*args, **kwargs)
        except Exception, e:
            er = err('8', obj="erroroccured")
            stack = get_tb()
            self.log.error(stack)
            print xml2str(er)
            status = "with errors"
        finally:
            self.log.debug("End %s %s" % (self.name,status))
    
    def form_submited(self):
        """Определяет была ли нажата кнопка submit формы"""
        if self.is_cgi:
            sok = self.params.getvalue('sok',None)
        elif self.is_xml:
            sok = self.stdin_xml.find('sok')
        return sok is not None

    def _main(self):
        """Метод подлежащий переопределению в подклассе. Здесь пишется основной код плагина."""
        raise NotImplementedError

    def addLogFileHandler(self, path, format=DFLT_FMT):
        """Добавляет лог файл"""
        fmt = logging.Formatter(format)
        handler = logging.FileHandler(path)
        handler.setFormatter(fmt)
        self.logger.addHandler(handler)
        self.log = logging.LoggerAdapter(self.logger, self.env)
