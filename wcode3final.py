#!/usr/bin/env python3
import curses
import os
import re
import sys


os.environ.setdefault('ESCDELAY', '25')


SPLASH = """
            ▊  W O R T E X  C O D E  ▊
          --- Modern Terminal Text Editor ---

             [i]  Insert Moduna Geç
             [:]  Komut Modunu Aç (:w, :q)
             [/]  Arama Yap
             [u]  Değişikliği Geri Al

             Daha fazla bilgi için NORMAL modda
             :h veya :help yazabilirsiniz.
"""


COLOR_DEFAULT = 1
COLOR_KEYWORD = 2
COLOR_STRING = 3
COLOR_COMMENT = 4
COLOR_NUMBER = 5
COLOR_LINENUM = 6
COLOR_MATCH = 8
COLOR_BUILTIN = 9


COLOR_MODE_NORMAL = 10
COLOR_MODE_INSERT = 11
COLOR_MODE_VISUAL = 12
COLOR_STATUS_BG = 13


KEYWORDS = r'\b(def|class|return|if|else|elif|for|while|import|from|as|in|try|except|with|pass|lambda|and|or|not|is|None|True|False|self)\b'
BUILTINS = r'\b(print|len|range|str|int|float|dict|list|set|tuple|open|type|enumerate|zip|sum|max|min|abs|sorted|map|filter|input|exec|eval)\b'

def init_colors():
    if curses.has_colors():
        try:
            curses.use_default_colors()
            curses.init_pair(COLOR_DEFAULT, -1, -1)
            curses.init_pair(COLOR_KEYWORD, curses.COLOR_RED, -1)
            curses.init_pair(COLOR_STRING, curses.COLOR_YELLOW, -1)
            curses.init_pair(COLOR_COMMENT, curses.COLOR_GREEN, -1)
            curses.init_pair(COLOR_NUMBER, curses.COLOR_MAGENTA, -1)
            curses.init_pair(COLOR_LINENUM, curses.COLOR_CYAN, -1)
            curses.init_pair(COLOR_MATCH, curses.COLOR_BLACK, curses.COLOR_YELLOW)
            curses.init_pair(COLOR_BUILTIN, curses.COLOR_BLUE, -1)
            
            
            curses.init_pair(COLOR_MODE_NORMAL, curses.COLOR_BLACK, curses.COLOR_BLUE)
            curses.init_pair(COLOR_MODE_INSERT, curses.COLOR_BLACK, curses.COLOR_GREEN)
            curses.init_pair(COLOR_MODE_VISUAL, curses.COLOR_BLACK, curses.COLOR_MAGENTA)
            curses.init_pair(COLOR_STATUS_BG, curses.COLOR_WHITE, curses.COLOR_BLACK)
        except Exception:
            pass

class WortexEditor:
    def __init__(self, filename=None):
        self.filename = filename
        self.lines = [""]
        self.cursor_y = 0
        self.cursor_x = 0
        self.offset_y = 0
        self.offset_x = 0
        self.running = True
        self.is_dirty = False
        
        self.mode = "NORMAL"
        self.undo_stack = []
        self.status_message = "Yardım için NORMAL modda :h yazın"
        
        if filename and os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8', errors='replace') as f:
                    self.lines = f.read().splitlines()
                if not self.lines:
                    self.lines = [""]
            except Exception as e:
                self.status_message = f"Dosya yükleme hatası: {str(e)}"

    def save_undo_state(self):
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)
        self.undo_stack.append({
            'lines': list(self.lines),
            'cursor_x': self.cursor_x,
            'cursor_y': self.cursor_y,
            'is_dirty': self.is_dirty
        })

    def restore_undo_state(self):
        if self.undo_stack:
            state = self.undo_stack.pop()
            self.lines = state['lines']
            self.cursor_x = state['cursor_x']
            self.cursor_y = state['cursor_y']
            self.is_dirty = state['is_dirty']
            self.status_message = "Değişiklik geri alındı."
        else:
            self.status_message = "Geri alınacak değişiklik yok."

    def highlight_line(self, line):
        if not line:
            return [("", COLOR_DEFAULT)]
            
        color_map = [COLOR_DEFAULT] * len(line)
        
        for m in re.finditer(r'\b\d+\b', line):
            for i in range(m.start(), m.end()):
                color_map[i] = COLOR_NUMBER
                
        for m in re.finditer(BUILTINS, line):
            for i in range(m.start(), m.end()):
                color_map[i] = COLOR_BUILTIN
                
        for m in re.finditer(KEYWORDS, line):
            for i in range(m.start(), m.end()):
                color_map[i] = COLOR_KEYWORD
                
        for m in re.finditer(r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\'', line):
            for i in range(m.start(), m.end()):
                color_map[i] = COLOR_STRING
                
        comment_idx = -1
        for i, char in enumerate(line):
            if char == '#' and color_map[i] != COLOR_STRING:
                comment_idx = i
                break
                
        if comment_idx != -1:
            for i in range(comment_idx, len(line)):
                color_map[i] = COLOR_COMMENT
                
        segments = []
        curr_color = color_map[0]
        curr_start = 0
        for idx in range(1, len(line)):
            if color_map[idx] != curr_color:
                segments.append((line[curr_start:idx], curr_color))
                curr_start = idx
                curr_color = color_map[idx]
        segments.append((line[curr_start:], curr_color))
        return segments

    def slice_segments(self, segments, offset_x, max_width):
        sliced = []
        curr_idx = 0
        end_idx = offset_x + max_width
        
        for text, color in segments:
            text_len = len(text)
            seg_start = curr_idx
            seg_end = curr_idx + text_len
            
            if seg_end > offset_x and seg_start < end_idx:
                slice_start = max(0, offset_x - seg_start)
                slice_end = min(text_len, end_idx - seg_start)
                sliced.append((text[slice_start:slice_end], color))
                
            curr_idx = seg_end
            if curr_idx >= end_idx:
                break
                
        return sliced

    def scroll_to_cursor(self, height, width, num_width):
        usable_height = height - 2
        usable_width = width - num_width - 3
        
        if self.cursor_y < self.offset_y:
            self.offset_y = self.cursor_y
        elif self.cursor_y >= self.offset_y + usable_height:
            self.offset_y = self.cursor_y - usable_height + 1
            
        if self.cursor_x < self.offset_x:
            self.offset_x = self.cursor_x
        elif self.cursor_x >= self.offset_x + usable_width:
            self.offset_x = self.cursor_x - usable_width + 1

    def prompt(self, stdscr, message):
        height, width = stdscr.getmaxyx()
        curses.curs_set(1)
        input_str = ""
        
        while True:
            
            stdscr.addstr(height - 1, 0, " " * (width - 2))
            prompt_text = f"{message}{input_str}"
            if len(prompt_text) >= width - 1:
                prompt_text = prompt_text[-(width - 2):]
            stdscr.addstr(height - 1, 0, prompt_text, curses.color_pair(COLOR_STATUS_BG))
            stdscr.refresh()
            
            ch = stdscr.getch()
            if ch in (10, 13):
                break
            elif ch in (27,):
                input_str = None
                break
            elif ch in (127, 8, curses.KEY_BACKSPACE):
                input_str = input_str[:-1]
            elif 32 <= ch <= 126:
                input_str += chr(ch)
                
        curses.curs_set(1 if self.mode == "INSERT" else 2)
        return input_str

    def splash_screen(self, stdscr):
        curses.curs_set(0)
        while True:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            
            splash_lines = SPLASH.strip("\n").split("\n")
            start_y = max(1, (height - len(splash_lines)) // 2)
            
            for i, line in enumerate(splash_lines):
                if start_y + i < height:
                    x = max(0, (width - len(line)) // 2)
                    stdscr.addstr(start_y + i, x, line, curses.color_pair(COLOR_DEFAULT))
                    
            stdscr.refresh()
            
            ch = stdscr.getch()
            if ch in (ord('i'), ord('I')):
                self.lines = [""]
                self.filename = None
                self.mode = "INSERT"
                break
            elif ch in (ord('o'), ord('O')):
                filename = self.prompt(stdscr, "Dosya adı: ")
                if filename:
                    if os.path.exists(filename):
                        try:
                            with open(filename, 'r', encoding='utf-8', errors='replace') as f:
                                self.lines = f.read().splitlines()
                            if not self.lines:
                                self.lines = [""]
                            self.filename = filename
                            break
                        except Exception as e:
                            self.status_message = f"Hata: {str(e)}"
                    else:
                        self.filename = filename
                        self.lines = [""]
                        break
            elif ch in (ord('h'), ord('H')):
                self.show_help(stdscr)
            elif ch in (ord('q'), ord('Q'), 27):
                self.running = False
                return False
                
        curses.curs_set(1)
        return True

    def find_text(self, stdscr):
        query = self.prompt(stdscr, "/")
        if not query:
            self.status_message = "Arama iptal edildi."
            return
            
        found = False
        start_y = self.cursor_y
        start_x = self.cursor_x + 1
        
        for y in range(start_y, len(self.lines)):
            line = self.lines[y]
            x = line.find(query, start_x if y == start_y else 0)
            if x != -1:
                self.cursor_y = y
                self.cursor_x = x
                self.status_message = f"Eşleşme bulundu: Satır {y+1}, Sütun {x+1}"
                found = True
                break
                
        if not found:
            for y in range(0, start_y + 1):
                line = self.lines[y]
                x = line.find(query, 0)
                if x != -1 and (y < start_y or x < start_x):
                    self.cursor_y = y
                    self.cursor_x = x
                    self.status_message = f"Eşleşme bulundu (Başa sarıldı): Satır {y+1}, Sütun {x+1}"
                    found = True
                    break
                    
        if not found:
            self.status_message = f"'{query}' bulunamadı."

    def save_file(self, stdscr):
        if not self.filename:
            filename = self.prompt(stdscr, "Farklı Kaydet: ")
            if not filename:
                self.status_message = "Kaydetme iptal edildi."
                return
            self.filename = filename
            
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                f.write("\n".join(self.lines))
            self.is_dirty = False
            self.status_message = f"Yazıldı: '{self.filename}'"
        except Exception as e:
            self.status_message = f"Kaydetme hatası: {str(e)}"

    def confirm_exit(self, stdscr):
        if not self.is_dirty:
            self.running = False
            return True
            
        ans = self.prompt(stdscr, "Değişiklikler kaydedilsin mi? (y/n/c): ")
        if ans in ('y', 'Y'):
            self.save_file(stdscr)
            self.running = False
            return True
        elif ans in ('n', 'N'):
            self.running = False
            return True
        else:
            self.status_message = "Çıkış iptal edildi."
            return False

    def handle_command(self, stdscr):
        cmd = self.prompt(stdscr, ":")
        if not cmd:
            return
            
        if cmd == "w":
            self.save_file(stdscr)
        elif cmd == "q":
            self.confirm_exit(stdscr)
        elif cmd == "wq":
            self.save_file(stdscr)
            self.running = False
        elif cmd == "q!":
            self.running = False
        elif cmd in ("h", "help"):
            self.show_help(stdscr)
        else:
            self.status_message = f"Bilinmeyen komut: {cmd}"

    def show_help(self, stdscr):
        height, width = stdscr.getmaxyx()
        stdscr.erase()
        
        help_text = [
            "               WORTEX CODE EDITOR (NeoVim Style) KILAVUZU",
            "               ==========================================",
            "",
            "  Modlar ve Geçişler:",
            "  -------------------",
            "  i  : INSERT moduna geçer (Yazı yazma modu)",
            "  ESC: NORMAL moda geri döner (Hareket ve yönetim modu)",
            "",
            "  NORMAL Mod Kısayolları:",
            "  ------------------------",
            "  h, j, k, l : Sol, Aşağı, Yukarı, Sağ yön hareketleri",
            "  u          : Geri al (Undo)",
            "  x          : İmlecin üzerindeki karakteri siler",
            "  dd         : Mevcut satırı tamamen siler",
            "  /          : Dosya içinde arama motorunu açar",
            "  :          : Komut satırını açar",
            "",
            "  Komut Satırı Seçenekleri (:):",
            "  -----------------------------",
            "  :w   - Dosyayı kaydeder",
            "  :q   - Editörden çıkar",
            "  :wq  - Kaydedip çıkar",
            "  :q!  - Kaydetmeden zorla çıkar",
            "",
            "  Devam etmek için bir tuşa basın..."
        ]
        
        for i, line in enumerate(help_text):
            if i < height - 1:
                stdscr.addstr(i, 2, line[:width-3], curses.color_pair(COLOR_DEFAULT))
                
        stdscr.refresh()
        stdscr.getch()
        stdscr.erase()

    def main_loop(self, stdscr):
        init_colors()
        
        
        stdscr.idcok(False)
        stdscr.idlok(False)
        
        if not self.filename:
            if not self.splash_screen(stdscr):
                return
                
        stdscr.erase()
        
        while self.running:
            height, width = stdscr.getmaxyx()
            max_lines = len(self.lines)
            num_width = max(4, len(str(max_lines)) + 1)
            
            usable_height = height - 2
            usable_width = width - num_width - 3
            
            self.scroll_to_cursor(height, width, num_width)
            
            
            stdscr.erase()
            
            
            status_file = self.filename if self.filename else "[İsimsiz]"
            dirty_tag = " [+]" if self.is_dirty else ""
            top_bar = f"    WORTEXCODE  │  {status_file}{dirty_tag}  "
            top_bar = top_bar.ljust(width - 2)
            stdscr.addstr(0, 0, top_bar, curses.color_pair(COLOR_STATUS_BG) | curses.A_REVERSE)
            
            
            for screen_y in range(usable_height):
                file_y = self.offset_y + screen_y
                draw_y = screen_y + 1
                
                if file_y < max_lines:
                    line_num_str = f"{file_y + 1:>{num_width}} │"
                    
                    if file_y == self.cursor_y:
                        stdscr.addstr(draw_y, 0, line_num_str, curses.color_pair(COLOR_KEYWORD) | curses.A_BOLD)
                    else:
                        stdscr.addstr(draw_y, 0, line_num_str, curses.color_pair(COLOR_LINENUM))
                    
                    line_content = self.lines[file_y]
                    full_highlight = self.highlight_line(line_content)
                    visible_segments = self.slice_segments(full_highlight, self.offset_x, usable_width)
                    
                    curr_x = num_width + 2
                    for text, col in visible_segments:
                        if curr_x >= width - 2:
                            break
                        write_len = min(len(text), width - 2 - curr_x)
                        if write_len > 0:
                            style = curses.A_BOLD if file_y == self.cursor_y else curses.A_NORMAL
                            stdscr.addstr(draw_y, curr_x, text[:write_len], curses.color_pair(col) | style)
                            curr_x += write_len
                else:
                    stdscr.addstr(draw_y, 0, "~", curses.color_pair(COLOR_LINENUM))
                    
            
            mode_color = COLOR_MODE_NORMAL if self.mode == "NORMAL" else COLOR_MODE_INSERT
            mode_text = f" {self.mode} "
            
            file_info = f" {status_file} "
            pos_info = f" Satır: {self.cursor_y + 1}/{max_lines} | Sütun: {self.cursor_x + 1} "
            msg_info = f" {self.status_message} "
            
            
            stdscr.addstr(height - 1, 0, " " * (width - 2), curses.color_pair(COLOR_STATUS_BG))
            stdscr.addstr(height - 1, 0, mode_text, curses.color_pair(mode_color) | curses.A_BOLD)
            
            start_file_x = len(mode_text)
            stdscr.addstr(height - 1, start_file_x, file_info, curses.color_pair(COLOR_STATUS_BG) | curses.A_REVERSE)
            
            start_msg_x = start_file_x + len(file_info) + 1
            max_msg_len = width - len(pos_info) - start_msg_x - 3
            if max_msg_len > 0:
                stdscr.addstr(height - 1, start_msg_x, msg_info[:max_msg_len], curses.color_pair(COLOR_STATUS_BG))
                
            start_pos_x = max(0, width - len(pos_info) - 2)
            stdscr.addstr(height - 1, start_pos_x, pos_info, curses.color_pair(COLOR_STATUS_BG) | curses.A_REVERSE)
            
            
            cursor_screen_y = (self.cursor_y - self.offset_y) + 1
            cursor_screen_x = (num_width + 2) + (self.cursor_x - self.offset_x)
            
            cursor_screen_y = max(1, min(usable_height, cursor_screen_y))
            cursor_screen_x = max(num_width + 2, min(width - 2, cursor_screen_x))
            stdscr.move(cursor_screen_y, cursor_screen_x)
            
            stdscr.refresh()
            
            
            try:
                ch = stdscr.getch()
            except KeyboardInterrupt:
                self.status_message = "Klavye kesmesi algılandı. Çıkış için :q kullanın."
                continue
                
            if ch == curses.KEY_RESIZE:
                stdscr.erase()
                continue
                
            
            
            
            if self.mode == "NORMAL":
                if ch == ord('i'):
                    self.save_undo_state()
                    self.mode = "INSERT"
                    self.status_message = "Yazma Modu"
                elif ch == ord('a'):
                    self.save_undo_state()
                    if self.cursor_x < len(self.lines[self.cursor_y]):
                        self.cursor_x += 1
                    self.mode = "INSERT"
                    self.status_message = "Yazma Modu"
                elif ch == ord('o'):
                    self.save_undo_state()
                    self.lines.insert(self.cursor_y + 1, "")
                    self.cursor_y += 1
                    self.cursor_x = 0
                    self.mode = "INSERT"
                    self.status_message = "Yazma Modu"
                elif ch == ord('O'):
                    self.save_undo_state()
                    self.lines.insert(self.cursor_y, "")
                    self.cursor_x = 0
                    self.mode = "INSERT"
                    self.status_message = "Yazma Modu"
                elif ch == ord('u'):
                    self.restore_undo_state()
                elif ch == ord('x'):
                    self.save_undo_state()
                    line = self.lines[self.cursor_y]
                    if len(line) > 0 and self.cursor_x < len(line):
                        self.lines[self.cursor_y] = line[:self.cursor_x] + line[self.cursor_x + 1:]
                        self.is_dirty = True
                elif ch == ord('d'):
                    next_ch = stdscr.getch()
                    if next_ch == ord('d'):
                        self.save_undo_state()
                        if len(self.lines) > 1:
                            self.lines.pop(self.cursor_y)
                            self.cursor_y = min(self.cursor_y, len(self.lines) - 1)
                            self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
                        else:
                            self.lines = [""]
                            self.cursor_x = 0
                        self.is_dirty = True
                    else:
                        curses.ungetch(next_ch)
                elif ch == ord(':'):
                    self.handle_command(stdscr)
                elif ch == ord('/'):
                    self.find_text(stdscr)
                elif ch == ord('h') or ch == curses.KEY_LEFT:
                    if self.cursor_x > 0:
                        self.cursor_x -= 1
                elif ch == ord('l') or ch == curses.KEY_RIGHT:
                    if self.cursor_x < len(self.lines[self.cursor_y]):
                        self.cursor_x += 1
                elif ch == ord('k') or ch == curses.KEY_UP:
                    if self.cursor_y > 0:
                        self.cursor_y -= 1
                        self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
                elif ch == ord('j') or ch == curses.KEY_DOWN:
                    if self.cursor_y < max_lines - 1:
                        self.cursor_y += 1
                        self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))
                elif ch == curses.KEY_PPAGE:
                    self.cursor_y = max(0, self.cursor_y - usable_height)
                elif ch == curses.KEY_NPAGE:
                    self.cursor_y = min(max_lines - 1, self.cursor_y + usable_height)
                    
            
            
            
            elif self.mode == "INSERT":
                if ch == 27: 
                    self.mode = "NORMAL"
                    self.status_message = "Komut Modu"
                elif ch in (127, 8, curses.KEY_BACKSPACE):
                    if self.cursor_x > 0:
                        line = self.lines[self.cursor_y]
                        self.lines[self.cursor_y] = line[:self.cursor_x - 1] + line[self.cursor_x:]
                        self.cursor_x -= 1
                        self.is_dirty = True
                    elif self.cursor_y > 0:
                        prev_len = len(self.lines[self.cursor_y - 1])
                        self.lines[self.cursor_y - 1] += self.lines[self.cursor_y]
                        self.lines.pop(self.cursor_y)
                        self.cursor_y -= 1
                        self.cursor_x = prev_len
                        self.is_dirty = True
                elif ch in (10, 13, curses.KEY_ENTER):
                    line = self.lines[self.cursor_y]
                    self.lines[self.cursor_y] = line[:self.cursor_x]
                    
                    leading_spaces = len(line) - len(line.lstrip(' '))
                    extra_indent = 4 if line[:self.cursor_x].rstrip().endswith(':') else 0
                    new_line = " " * (leading_spaces + extra_indent) + line[self.cursor_x:]
                    
                    self.lines.insert(self.cursor_y + 1, new_line)
                    self.cursor_y += 1
                    self.cursor_x = leading_spaces + extra_indent
                    self.is_dirty = True
                elif ch == 9:
                    line = self.lines[self.cursor_y]
                    self.lines[self.cursor_y] = line[:self.cursor_x] + "    " + line[self.cursor_x:]
                    self.cursor_x += 4
                    self.is_dirty = True
                elif 32 <= ch <= 126:
                    line = self.lines[self.cursor_y]
                    self.lines[self.cursor_y] = line[:self.cursor_x] + chr(ch) + line[self.cursor_x:]
                    self.cursor_x += 1
                    self.is_dirty = True

def main():
    try:
        import locale
        locale.setlocale(locale.LC_ALL, '')
    except Exception:
        pass
        
    filename = sys.argv[1] if len(sys.argv) > 1 else None
    editor = WortexEditor(filename)
    curses.wrapper(editor.main_loop)

if __name__ == "__main__":
    main()