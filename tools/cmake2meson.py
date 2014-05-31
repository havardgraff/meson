#!/usr/bin/python3

# Copyright 2014 Jussi Pakkanen

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys, os
import re

class Token:
    def __init__(self, tid, value):
        self.tid = tid
        self.value = value
        self.lineno = 0
        self.colno = 0

class Statement():
    def __init__(self, name, args):
        self.name = name
        self.args = args

class Lexer:
    def __init__(self):
        self.token_specification = [
            # Need to be sorted longest to shortest.
            ('ignore', re.compile(r'[ \t]')),
            ('string', re.compile('"[^"]*?"')),
            ('id', re.compile('''[-+_0-9a-z/A-Z@.]+''')),
            ('eol', re.compile(r'\n')),
            ('comment', re.compile(r'\#.*')),
            ('lparen', re.compile(r'\(')),
            ('rparen', re.compile(r'\)')),
            ('varexp', re.compile(r'\${[-_0-9a-z/A-Z.]+}')),
        ]

    def lex(self, code):
        lineno = 1
        line_start = 0
        loc = 0;
        col = 0
        while(loc < len(code)):
            matched = False
            for (tid, reg) in self.token_specification:
                mo = reg.match(code, loc)
                if mo:
                    col = mo.start()-line_start
                    matched = True
                    loc = mo.end()
                    match_text = mo.group()
                    if tid == 'ignore' or tid == 'comment':
                        pass
                    elif tid == 'lparen':
                        yield(Token('lparen', '('))
                    elif tid == 'rparen':
                        yield(Token('rparen', ')'))
                    elif tid == 'string':
                        yield(Token('string', match_text[1:-1]))
                    elif tid == 'id':
                        yield(Token('id', match_text))
                    elif tid == 'eol':
                        #yield('eol')
                        lineno += 1
                        col = 1
                        line_start = mo.end()
                        pass
                    elif tid == 'varexp':
                        yield(Token('varexp', match_text[2:-1]))
                    else:
                        raise RuntimeError('Wharrgarbl')
                    break
            if not matched:
                raise RuntimeError('Lexer got confused line %d column %d' % (lineno, col))

class Parser():
    def __init__(self, code):
        self.stream = Lexer().lex(code)
        self.getsym()

    def getsym(self):
        try:
            self.current = next(self.stream)
        except StopIteration:
            self.current = Token('eof', '')

    def accept(self, s):
        if self.current.tid == s:
            self.getsym()
            return True
        return False

    def expect(self, s):
        if self.accept(s):
            return True
        raise RuntimeError('Expecting %s got %s.' % (s, self.current.tid), self.current.lineno, self.current.colno)

    def statement(self):
        name = self.current.value
        self.accept('id')
        args = []
        self.expect('lparen')
        arg = self.current.value
        while self.accept('string') or self.accept('varexp') or\
        self.accept('id'):
            args.append(arg)
            arg = self.current.value
        self.expect('rparen')
        return Statement(name, args)

    def parse(self):
        while not self.accept('eof'):
            yield(self.statement())

def convert(cmake_root):
    cfile = os.path.join(cmake_root, 'CMakeLists.txt')
    cmakecode = open(cfile).read()
    p = Parser(cmakecode)
    for t in p.parse():
        if t.name == 'add_subdirectory':
            print('\nRecursing to subdir', t.args[0], '\n')
            convert(os.path.join(cmake_root, t.args[0]))
        else:
            print(t.name, t.args)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(sys.argv[0], '<CMake project root>')
        sys.exit(1)
    try:
        convert(sys.argv[1])
    except Exception as e:
        print('Error:', e)
        sys.exit(1)