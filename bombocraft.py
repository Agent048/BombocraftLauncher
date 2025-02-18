import tkinter as tk
import json
import os
import requests
import webbrowser
from tkinter import Entry, Button, Label, messagebox, StringVar, filedialog
from PIL import Image, ImageTk
import minecraft_launcher_lib
import subprocess
import threading
import platform
import urllib3

# Define and ensure Minecraft directory exists
minecraft_dir = os.path.join(os.getenv('APPDATA'), ".bombocraft")
os.makedirs(minecraft_dir, exist_ok=True)

# Config file path
CONFIG_FILE = os.path.join(minecraft_dir, "config.json")

# Load and save settings
def load_settings():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return {}
    return {}

def save_settings(settings):
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4)

settings = load_settings()

#ely.by auth
def elyby_login(username, password):
    url = "https://authserver.ely.by/auth/authenticate"
    payload = {
        "username": username,
        "password": password,
        "clientToken": "YOUR_ELY_BY_CLIENT_TOKEN"  # **REPLACE WITH YOUR CLIENT TOKEN**
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = response.json()
        settings["elyby"] = {
            "username": username,
            "accessToken": data["accessToken"],
            "uuid": data["selectedProfile"]["id"]
        }
        settings["use_elyby"] = "yes"
        save_settings(settings)
        messagebox.showinfo("Успешный вход", "Авторизация Ely.by выполнена успешно!")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Ошибка", f"Ошибка авторизации Ely.by: {e}")
    except (KeyError, TypeError) as e:
        messagebox.showerror("Ошибка", f"Некорректный ответ от сервера Ely.by: {e}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Непредвиденная ошибка: {e}")

def get_elyby_skin(username):
    try:
        url = f"https://ely.by/api/users/profiles/minecraft/{username}/skin"
        response = requests.get(url, stream=True)

        if response.status_code == 200:
            skin_path = os.path.join(minecraft_dir, f"{username}.png")
            with open(skin_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return skin_path
        elif response.status_code == 404:  # Handle "skin not found" specifically
            print(f"Скин не найден для {username}.") # No need for status code here
            return None
        else:
            print(f"Ошибка получения скина для {username}: {response.status_code}") # More general error
            return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении скина: {e}")
        return None







# Settings Window
def on_settings():
    settings_window = tk.Toplevel(root)
    settings_window.title("Настройки")
    settings_window.geometry("400x550")
    settings_window.configure(bg="#222222")

    resourcepack_var = StringVar(value=settings.get("resourcepack_folder", ""))
    java_version_var = StringVar(value=settings.get("java_version", "Java 17"))
    memory_var = StringVar(value=settings.get("memory", "2G"))

    Label(settings_window, text="Папка ресурспаков:", bg="#222222", fg="white").pack(pady=5)
    Entry(settings_window, textvariable=resourcepack_var, bg="#444444", fg="white", width=40).pack(pady=5)
    Button(settings_window, text="Выбрать", command=lambda: choose_resourcepack_folder(resourcepack_var), bg="#333333", fg="white").pack(pady=5)

    Label(settings_window, text="Версия Java:", bg="#222222", fg="white").pack(pady=5)
    Entry(settings_window, textvariable=java_version_var, bg="#444444", fg="white", width=40).pack(pady=5)

    Label(settings_window, text="Объем памяти (например, 2G, 4G, 8G):", bg="#222222", fg="white").pack(pady=5)
    Entry(settings_window, textvariable=memory_var, bg="#444444", fg="white", width=40).pack(pady=5)

    Label(settings_window, text="Логин Ely.by:", bg="#222222", fg="white").pack(pady=5)
    ely_username_var = StringVar(value=settings.get("elyby", {}).get("username", ""))
    username_entry = Entry(settings_window, textvariable=ely_username_var, bg="#444444", fg="white", width=40)
    username_entry.pack(pady=5)

    Label(settings_window, text="Пароль Ely.by:", bg="#222222", fg="white").pack(pady=5)
    ely_password_var = StringVar()
    password_entry = Entry(settings_window, textvariable=ely_password_var, show="*", bg="#444444", fg="white", width=40)
    password_entry.pack(pady=5)

    Button(settings_window, text="Войти через Ely.by", command=lambda: elyby_login(ely_username_var.get(), ely_password_var.get()), bg="#0055AA", fg="white").pack(pady=10)

    Button(settings_window, text="Сохранить", command=lambda: save_config(settings_window, resourcepack_var, java_version_var, memory_var), bg="#0055AA", fg="white").pack(pady=10)

    Button(settings_window, text="Отменить", command=settings_window.destroy, bg="#AA0000", fg="white").pack(pady=5)
    
def choose_resourcepack_folder(resourcepack_var):
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        resourcepack_var.set(folder_selected)

def save_config(settings_window, resourcepack_var, java_version_var, memory_var):
    settings["resourcepack_folder"] = resourcepack_var.get()
    settings["java_version"] = java_version_var.get()
    settings["memory"] = memory_var.get()
    save_settings(settings)

    settings_window.destroy()  # Закрываем окно после сохранения



    def cancel_config():
        settings_window.destroy()





# Save login details
def save_login(username, version):
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump({"username": username, "version": version}, file)

# Load login details
def load_login_and_version():
    if not os.path.exists(CONFIG_FILE):
        return "", ""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("username", ""), data.get("version", "")
    except (json.JSONDecodeError, FileNotFoundError):
        return "", ""

# Start Minecraft


def on_start():
    username = username_entry.get()  # Get the username from the entry field *inside* on_start()
    options = {
        'username': username,  # Now username is defined
        'uuid': '',
        'token': '',
    }

    if settings.get("use_elyby") == "yes" and "elyby" in settings:
        options["username"] = settings["elyby"]["username"]
        options["uuid"] = settings["elyby"]["uuid"]
        options["token"] = settings["elyby"]["accessToken"]
        skin_path = get_elyby_skin(settings["elyby"]["username"])
        if skin_path:
            options["skin"] = skin_path
    else:
        # If not using ely.by, use the entered username (or "Player" if blank)
        options["username"] = username if username else "Player" # Use username from entry field
        options["uuid"] = ""
        options["token"] = ""
        settings["username"] = username  # Save the username if not ely.by
        save_settings(settings) # Save it to config file
    try:
        minecraft_launcher_lib.install.install_minecraft_version(versionid=minecraft_version, minecraft_directory=minecraft_dir)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка установки Minecraft: {e}")
        return

    threading.Thread(target=launch_minecraft, args=(minecraft_version, options)).start()

    start_button.config(text="Запускается...", state=tk.DISABLED)
    root.after(5000, lambda: start_button.config(text="Запустить", state=tk.NORMAL))

# Launch Minecraft
def launch_minecraft(version, options):
    try:
        command = minecraft_launcher_lib.command.get_minecraft_command(version=version, minecraft_directory=minecraft_dir, options=options)

        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            subprocess.Popen(command, startupinfo=startupinfo)
        else:
            subprocess.Popen(command)

    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка запуска Minecraft: {e}")



# Placeholder for update check
def on_update_check():
    messagebox.showinfo("Обновления", "Функция проверки обновлений в разработке.")

# Open links
def open_telegram():
    webbrowser.open("https://t.me/+sbmktLlPSBQ1MzFk")

def open_discord():
    webbrowser.open("https://discord.gg/mpnsUzyfNr")

# Load icons
def load_icon(path, size=(36, 36)):
    try:
        img = Image.open(path)
        img = img.resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except FileNotFoundError:
        return None
    except Exception:
        return None

# Entry field events
def clear_entry(event, entry, default_text):
    if entry.get() == default_text:
        entry.delete(0, tk.END)
        entry.config(fg="white")

def restore_entry(event, entry, default_text):
    if not entry.get():
        entry.insert(0, default_text)
        entry.config(fg="#888888")

# Tkinter GUI
root = tk.Tk()
root.title("BomboCraft")
root.geometry("1000x600")
root.configure(bg='black')
root.resizable(False, False)


# Background image
try:
    bg_image = Image.open("images/background.png").resize((1000, 600), Image.Resampling.LANCZOS)
    bg_photo = ImageTk.PhotoImage(bg_image)
    bg_label = Label(root, image=bg_photo)
    bg_label.place(relwidth=1, relheight=1)
except FileNotFoundError:
    root.config(bg="#333333")
except Exception:
    root.config(bg="#333333")

# Main frame
frame = tk.Frame(root, bg='#222222', bd=5, highlightbackground='black', highlightthickness=2)
frame.place(relx=0.5, rely=0.5, anchor='center', relwidth=0.5, relheight=0.6)

title_label = Label(frame, text="BomboCraft", font=("Arial", 20, "bold"), fg="white", bg="#222222")
title_label.pack(pady=15)

# Username field
username_default = "Введите имя пользователя"
saved_username, saved_version = load_login_and_version()

username_entry = Entry(frame, font=("Arial", 14), bg="#444444", fg="white" if saved_username else "#888888",
                       insertbackground="white", relief=tk.FLAT)

if saved_username:
    username_entry.insert(0, saved_username)
else:
    username_entry.insert(0, username_default)

username_entry.bind("<FocusIn>", lambda event: clear_entry(event, username_entry, username_default))
username_entry.bind("<FocusOut>", lambda event: restore_entry(event, username_entry, username_default))
username_entry.pack(pady=10, ipadx=30, ipady=8, fill=tk.X, padx=15)


# Set Minecraft version
minecraft_version = saved_version if saved_version else "1.20.1"

# Start button
start_button = Button(frame, text="Запустить", font=("Arial", 16, "bold"), bg="black", fg="white", relief=tk.FLAT,
                      activebackground="#0055AA", activeforeground="white", cursor="hand2", bd=0, command=on_start)
start_button.pack(pady=15, ipadx=40, ipady=8, fill=tk.X, padx=15)

# Load icons
settings_icon = load_icon("images/settings.png")
update_icon = load_icon("images/update.png")
telegram_icon = load_icon("images/tg.png")
discord_icon = load_icon("images/ds.png")

# Buttons frame
buttons_frame = tk.Frame(frame, bg="#222222")
buttons_frame.pack(pady=15)

settings_button = Button(buttons_frame, image=settings_icon, bg="#333333", relief=tk.FLAT, command=on_settings)
settings_button.grid(row=0, column=0, padx=10)

update_button = Button(buttons_frame, image=update_icon, bg="#333333", relief=tk.FLAT, command=on_update_check)
update_button.grid(row=0, column=1, padx=10)

telegram_button = Button(buttons_frame, image=telegram_icon, bg="#0088cc", relief=tk.FLAT, command=open_telegram)
telegram_button.grid(row=0, column=2, padx=10)

discord_button = Button(buttons_frame, image=discord_icon, bg="#5865F2", relief=tk.FLAT, command=open_discord)
discord_button.grid(row=0, column=3, padx=10)

# Run application
root.mainloop()
