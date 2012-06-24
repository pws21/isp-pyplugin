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

def _xml_err(code, text=None, obj=None, msg=None):
    """Возвращяет XML об ошибке"""
    if type(code) == int:
        code = str(code)
    xmldoc = doc()
    xmlerr = et.Element("error", code=code)
    if obj is not None:
        xmlerr.attrib["obj"] = obj
    if msg is not none:
        xmlerr.attrib["msg"] = msg
    if text is not None:
        xmlerr.text = text
    xmldoc.append(xmlerr)
    return xmldoc

class MgrError(Exception):
    """Класс ошибки панели.
       code - код ошибки
       obj - объект с которым связана ошибка
       msg - идентификатор сообщения
       text - текст ошибки
    """
    def __init__(self, code, obj=None, msg=None, text=None):
        self.code = code
        self.obj = obj
        self.msg = msg
        self.text = text

    def __str__(self):
        return "MGR-%s [%s]: (%s) %s" % (code, obj, msg, text)

    def as_xml(self):
        return _xml_err(self.code, self.text, self.obj, self.msg)

    def as_strxml(self):
        return xml2str(self.as_xml())

def query(func, keys, out='xml', mgr='ispmgr'):
    """This function allows to make query to control pannel
    func: function name
    keys: key+value array of arrays
    out: (optional) output type. Default is 'xml'. Possible
    alternative is 'devel'
    mgr: (optional) mgrname. Default is 'ispmgr'.
    Позаимствовано из lib/mgr.py и модифицировано ибо out работал не правильно, с моей версией BillManager, во всяком случае.
    Да и не хочется от этой либы зависть, т.к. она мало чего умеет.
    Возвращяет str, т.к. out формат не обязательно xml, может захочется работать с json.
    """
    from commands import getstatusoutput
    keys_str = ' '.join(map(lambda x: '='.join(x),keys))
    q = (mgr, out, func, keys_str)
    res,output = getstatusoutput('/usr/local/ispmgr/sbin/mgrctl -m %s -o %s %s %s' % q)
    return output

def err(code, msg=None, obj=None):
    """Возвращяет XML об ошибке"""
    return _xml_err(code, text=msg, obj=obj)

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

def str2xml(text):
    """Переводит str в lxml.etree.Element"""
    return et.fromstring(text)

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
        self.exception_hook = None
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
            if exception_hook is not None:
                exception_hook(me)
            self.log.error(get_tb())
            if type(e) == MgrError:
                print e.as_strxml()
            else:
                er = err('8', obj="erroroccured")
                print xml2str(er)
            status = "with errors"
        finally:
            self.log.debug("End %s %s" % (self.name,status))

    def set_exception_hook(self, callable_func):
        self.exception_hook = callable_func

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
