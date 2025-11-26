from html.parser import HTMLParser

class Validator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.void_elements = {
            'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
            'link', 'meta', 'param', 'source', 'track', 'wbr',
            'el-input', 'el-alert', 'uploadfilled', 'upload-filled', 'arrowleft', 'upload', 'documentadd', 'search', 'user', 'refresh', 'cpu', 'delete', 'rank' 
        }
        # Note: Components like el-input are not strictly void in HTML spec but often self-closed in Vue.
        # We need to handle self-closing tags.

    def handle_starttag(self, tag, attrs):
        if tag in self.void_elements:
            return
        self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in self.void_elements:
            return
        
        if not self.stack:
            print(f"Error: Unexpected closing tag </{tag}> at {self.getpos()}")
            return

        last_tag, pos = self.stack.pop()
        if last_tag != tag:
            print(f"Error: Expected </{last_tag}> (opened at {pos}) but found </{tag}> at {self.getpos()}")
            # Put it back if it's a mismatch that implies missing tag
            self.stack.append((last_tag, pos))

    def validate(self, content):
        # Only validate template part
        start = content.find('<template>')
        end = content.rfind('</template>')
        if start == -1 or end == -1:
            print("No template found")
            return

        template_content = content[start+10:end]
        # Remove self-closing tags for simpler parsing: <tag ... /> -> <tag ...></tag> or just ignore /
        # HTMLParser handles basic HTML. Vue templates are not strict XML.
        # Let's simple check: find <template and </template
        
        # A simple stack check using regex might be better for Vue templates due to self-closing components
        pass

import re

def validate_vue_template(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    template_match = re.search(r'<template>(.*)</template>', content, re.DOTALL)
    if not template_match:
        print("No template block found")
        return

    template_content = template_match.group(1)
    
    # Simple stack based parser
    # We need to tokenize: <tag>, </tag>, <tag />
    
    stack = []
    
    # Regex to match tags
    tag_re = re.compile(r'<(/?)(\\w[\\w-]*)([^>]*?)(/?)>')
    
    pos = 0
    lines = template_content.split('\n')
    
    # Helper to map pos to line/col
    def get_line_col(index):
        current_pos = 0
        for i, line in enumerate(lines):
            next_pos = current_pos + len(line) + 1 # +1 for newline
            if next_pos > index:
                return i + 1, index - current_pos + 1
            current_pos = next_pos
        return -1, -1

    for match in tag_re.finditer(template_content):
        is_closing = match.group(1) == '/'
        tag_name = match.group(2)
        attrs = match.group(3)
        is_self_closing = match.group(4) == '/'
        
        # print(f"Tag: {tag_name}, Closing: {is_closing}, Self: {is_self_closing}")

        if is_self_closing:
            continue
            
        void_tags = ['br', 'hr', 'img', 'input', 'meta', 'link']
        if tag_name.lower() in void_tags:
            continue

        if is_closing:
            if not stack:
                print(f"Error: Unexpected closing tag </{tag_name}> at {get_line_col(match.start())}")
                continue
                
            last_tag = stack.pop()
            if last_tag['name'] != tag_name:
                print(f"Error: Mismatched tag. Expected </{last_tag['name']}> (opened at {last_tag['line']}:{last_tag['col']}) but found </{tag_name}> at {get_line_col(match.start())}")
                # Put it back to continue checking?
                # stack.append(last_tag) 
                return
        else:
            line, col = get_line_col(match.start())
            stack.append({'name': tag_name, 'line': line, 'col': col})

    if stack:
        print("Error: Unclosed tags:")
        for tag in stack:
            print(f"  <{tag['name']}> at line {tag['line']}, col {tag['col']}")
    else:
        print("Template structure appears valid.")

validate_vue_template('frontend/src/views/ExamDetail.vue')