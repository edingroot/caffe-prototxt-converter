"""
caffe-prototxt-converter - PrototxtParser
Author: Chi Chang - edingroot [at] gmail.com
"""
import re


class PrototxtParser:
    """
    proto: stores dicts -
            {
                'type': 'scope',
                'name': scope name,
                'attrs': [ same structure ]
            } or
            {
                'type': 'attr',
                'name': attr name,
                'value': attr value
            }
    """
    proto = []
    trace_stack = []
    currNode = proto
    attr_replaces = {}
    apply_replaces = False
    ATTR_CHANGES_FILE = './config/attr_changes.txt'
    RE_ATTR = re.compile("^[a-z_]+ *: *")
    RE_VALUE = re.compile("^[^ ]+ *")
    RE_SCOPE_OPEN = re.compile("^[a-z_]+ *\{ *")
    RE_SCOPE_CLOSE = re.compile("^} *")
    MAX_NAME_LEN = 30
    MAX_VALUE_LEN = 50
    IDENT_SPACES = 2

    def __init__(self, apply_replaces=True):
        if apply_replaces:
            self.apply_replaces = True
            self.__load_attr_changes()

    def get_proto(self):
        return self.proto

    def set_proto(self, new_proto = None):
        if new_proto is None:
            self.proto = []
        else:
            self.proto = new_proto
        self.trace_stack = []
        self.currNode = self.proto

    def stringify(self):
        return self.__export(self.proto) + "\n"

    def __export(self, proto, ident_level=0):
        output = ''
        for attr in proto:
            if attr['type'] == 'scope':
                if attr['name'] == 'layer':
                    output += "\n"
                output += self.__ident(ident_level) + attr['name'] + " {\n"
                output += self.__export(attr['attrs'], ident_level + 1)
                output += self.__ident(ident_level) + "}\n"
            elif attr['type'] == 'attr':
                output += self.__ident(ident_level) + attr['name'] + ': ' + attr['value'] + "\n"
        return output

    def parse(self, filename):
        with open(filename, mode='r') as f:
            content = f.read()
            content = re.sub("#.*", "", content)  # remove comments
            content = re.sub("(\n\s*)+", " ", content).strip()  # replace \n and spaces in front of lines

            while content != '':
                res = self.__parse_next(content)

                if res['type'] == '{':
                    self.__enter_scope(res['name'])

                elif res['type'] == '}':
                    self.__exit_scope()

                elif res['type'] == 'attr':
                    if self.apply_replaces:
                        key = "%s@%s" % (res['name'], res['value'])
                        if key in self.attr_replaces:
                            new_entry = self.attr_replaces[key]
                            res['name'] = new_entry['name']
                            res['value'] = new_entry['value']
                    self.currNode.append(self.new_attr_object(res['name'], res['value']))

                content = res['tail']

            self.set_proto(self.proto)
            return self.proto

    def __parse_next(self, content):
        obj = re.search(self.RE_SCOPE_CLOSE, content[:self.MAX_NAME_LEN])
        if obj:
            res = obj.group()
            return {
                'type': '}',
                'tail': content[len(res):]
            }

        obj = re.search(self.RE_SCOPE_OPEN, content[:self.MAX_NAME_LEN])
        if obj:
            res = obj.group()
            return {
                'type': '{',
                'name': res.strip()[:-1].strip(),
                'tail': content[len(res):]
            }

        obj = re.search(self.RE_ATTR, content[:self.MAX_NAME_LEN])
        if obj:
            res = obj.group()
            value = re.match(self.RE_VALUE, content[len(res):len(res) + self.MAX_VALUE_LEN]).group()
            return {
                'type': 'attr',
                'name': res.strip()[:-1].strip(),
                'value': value.strip(),
                'tail': content[len(res) + len(value):]
            }

        print('Error parsing next')
        exit(1)

    def __enter_scope(self, tag_name):
        self.trace_stack.append(self.currNode)
        node = self.new_scope_object(tag_name)
        self.currNode.append(node)
        self.currNode = node['attrs']

    def __exit_scope(self):
        self.currNode = self.trace_stack.pop()

    @staticmethod
    def new_attr_object(name, value):
        return {
            'type': 'attr',
            'name': name,
            'value': value
        }

    @staticmethod
    def new_scope_object(name):
        return {
            'type': 'scope',
            'name': name,
            'attrs': []
        }

    def __load_attr_changes(self):
        with open(self.ATTR_CHANGES_FILE, mode='r') as f:
            lines = f.readlines()
            i = 0
            while i < len(lines):
                line1 = lines[i]
                line2 = lines[i + 1]

                index = line1.index(':')
                attr1 = line1[:index].strip()
                value1 = line1[index + 1:].strip()

                index = line2.index(':')
                attr2 = line2[:index].strip()
                value2 = line2[index + 1:].strip()

                self.attr_replaces["%s@%s" % (attr1, value1)] = {
                    'name': attr2,
                    'value': value2
                }
                i += 3  # skip one line

    def __ident(self, ident_level):
        return ' ' * ident_level * self.IDENT_SPACES
