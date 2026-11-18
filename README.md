WCode 3.14

A lightweight, terminal-based text editor inspired by NeoVim, built with Python. It brings a simple modal editing experience, Python syntax highlighting, and essential text editing features right into your terminal.

You can just clone it into your terminal and use it as however you want. 

✨ Features

- NeoVim-inspired interface – Clean, minimalist terminal UI.
- Modal Editing – Switch between NORMAL and INSERT modes.
- Python Syntax Highlighting – Highlights keywords, strings, comments, numbers, and built-in functions.
- File Management – Open, edit, and save files directly.
- Undo Support – Easily revert your previous changes.
- Text Search – Find specific words or phrases inside your files.
- Navigation – Move around using "h", "j", "k", "l" or arrow keys.
- Line Editing – Delete characters, remove entire lines, and insert new lines.
- Auto Indentation – Automatically handles indentation when creating new lines.
- Scrolling – Navigate through larger files with vertical and horizontal scrolling.
- Custom Statusline – Displays the current mode, filename, cursor position, and editor messages.
- Built-in Help – Access the keyboard shortcuts and commands using ":help".

⚙️ Setup

WCode currently consists of a single Python script for least complicated programming. You'll need Python and Git to get started.

1. Install Python and Git

Android (Termux)

pkg update && pkg upgrade
pkg install python git

Linux (Ubuntu / Debian)

sudo apt update
sudo apt install python3 git

Linux (Fedora)

sudo dnf install python3 git

Linux (Arch)

sudo pacman -S python git

Windows

If you have Windows Package Manager (winget):

winget install Python.Python.3.13
winget install Git.Git

Alternatively, download Python from https://www.python.org/downloads/ and Git from https://git-scm.com/downloads/.

macOS

If you have Homebrew:

brew install python git

Alternatively, download Python from https://www.python.org/downloads/ and Git from https://git-scm.com/downloads/.

2. Clone the Repository

Once Python and Git are installed, clone the repository:

git clone https://github.com/wortex213433/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY

Replace "YOUR-REPOSITORY" with the actual repository name.

3. Thanks for Installing

No additional dependencies are required on Linux, macOS, or Termux. The editor uses Python's built-in modules.

On Windows, install "windows-curses" to enable terminal support:

py -m pip install windows-curses

🚀 How to Use It

Run the editor using:

py wcode3final.py

On Linux, macOS, or Termux, you can use:

python3 wcode3final.py

You can also open an existing file directly:

python3 wcode3final.py filename.py

Basic Controls

Key| Action
"i"| Enter INSERT mode
"ESC"| Return to NORMAL mode
"h j k l"| Navigate
"u"| Undo
"x"| Delete character
"dd"| Delete current line
"/"| Search
":"| Open command mode

Available Commands

Command| Action
":w"| Save file
":q"| Quit
":wq"| Save and quit
":q!"| Force quit without saving
":h" / ":help"| Open help

📸 Screenshots

Coming soon!

🛠️ Technologies

- Python 3 – Main programming language.
- curses – Terminal interface, keyboard input, and color handling.
- os – Environment variables and file operations.
- re – Regular expressions and syntax highlighting.
- sys – Command-line arguments.

No external dependencies are needed on Unix-like systems.
I'm still working on this to make a better version. If you have any advises, I'm down for them. And ironically I forgot to add a file renaming option. I'm working on making a better WCode while keeping the non-complicated.

🤝 Contributing

If you find something to improve, feel free to open a pull request!

For bigger changes, just open an issue first so we can discuss what you'd like to work on.

All contributions and suggestions are welcome!

You can also fork the repo to contribute!

📄 License

This project is licensed under the MIT License.

---

made by wortex213433


