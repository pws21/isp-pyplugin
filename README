isp-plugins
===========
http://github.com/pws21/isp-plugins

Что это такое?
--------------
Это малюсенькая либа, которую я сдела для упрощения написания плагинов к продуктам ISP Systems.

Как ей пользоваться?
--------------------
Самый простой вариант xml плагина, пропускающего все сквозь себя
    
    #!/usr/bin/python
    from isp import Plugin, xml2str

    class MyPlugin(Plugin):
        def _main(self):
            print xml2str(self.stdin_xml)
    
    if __name__ == "__main__":
        p = MyPlugin("MyPlugin","xml")
        p.execute()

Вот пример xml плагина чтобы сделать поле Name формы user.edit не редактируемым:

    #!/usr/bin/python
    # -*- coding: UTF-8 -*-
    from isp import Plugin, xml2str, xml2pretty_str, get_tb
    import logging
    import sys

    class ReadOnlyName(Plugin):
        def _main(self):
            xml = self.stdin_xml
            nm = None
            id = xml.find("id")
            # Не даем редактировать имя существующего пользователя
            if id is not None:
                self.log.debug("ID exists, it's editing")
                elements = xml.xpath("/doc/metadata/form/page/field[@name='name']/input")
                if elements.count == 1:
                    nm = elements[0]
                if nm is not None:
                    self.log.debug("Field found")
                    attrs = nm.attrib
                    attrs["readonly"] = "yes"

            print xml2pretty_str(xml)

    if __name__ == "__main__":
        try:
            pl = ReadOnlyName("ReadOnlyName", "xml")
            pl.logger.setLevel(logging.DEBUG)
            pl.execute()
        except:
            print get_tb()
    
И пример cgi плагина, проверяющего при регистрации имя пользователя по собственным правилам.

    #!/usr/bin/python
    # -*- coding: UTF-8 -*-

    from isp import Plugin, err, doc, xml2str, get_tb, ok
    import logging
    import re

    def valid_name(name):
        """validate name"""
        allowed = re.compile("^[A-Z][A-Z_\d-]{1,14}[A-Z\d]$",re.IGNORECASE)
        if allowed.match(name):
            return True
        else:
            return False

    class NameChecker(Plugin):
        def _main(self):
            #Проверка имени при регистрации
            username = self.params.getvalue('username')
            if self.form_submited():
                if valid_name(username):
                    self.log.info("Username [%s] is OK" % username)
                    print xml2str(ok())
                else:
                    self.log.info("Username [%s] already exists" % username)  
                    print xml2str(err(8, obj="invalidname"))
            else:
                self.log.debug('ShowForm')
                print xml2str(doc())
        

    if __name__ == "__main__":
        try:
            nc = NameChecker("NameChecker", "cgi")
            nc.logger.setLevel(logging.DEBUG)
            # Убираем дефолтный хэндлер(ы)
            nc.logger.handlers = []
            # Добавляем свой, чтобы писал лог этого плагина в другой файл
            nc.addLogFileHandler('/usr/local/ispmgr/var/nc.log')
            nc.execute()
        except:
            print get_tb()

XML описание плагинов возможно приведу поздже...